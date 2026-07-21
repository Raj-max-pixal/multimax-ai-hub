import { useState, useRef, useEffect, useCallback } from 'react'
import {
  Send,
  Plus,
  MessageSquare,
  Trash2,
  Copy,
  RotateCcw, 
  Square,
  ChevronDown,
  Search,
  Bot,
  User,
  Edit,
  Pin,
  UploadCloud,
  Sparkles,
  Download,
  Share2,
  Library,
  FileText,
  X
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { motion, AnimatePresence } from 'framer-motion'
import { chatWithOllama, filterEmptyChatMessages, getOllamaModels, uploadDocument } from '../lib/api'
import { useToast } from '../contexts/ToastContext'
import { cn } from '../lib/utils'
import type { Message, Conversation, ChatAttachment } from '../types'

type Persona = {
  id: string
  name: string
  systemPrompt: string
}

const PERSONAS: Persona[] = [
  { id: 'general', name: 'General', systemPrompt: 'You are Multimax AI Hub, a helpful, practical AI assistant.' },
  { id: 'coder', name: 'Coder', systemPrompt: 'You are a senior coding assistant. Be precise, explain tradeoffs, and provide production-ready code.' },
  { id: 'researcher', name: 'Researcher', systemPrompt: 'You are a rigorous research assistant. Structure answers, compare evidence, and call out uncertainty.' },
  { id: 'teacher', name: 'Teacher', systemPrompt: 'You are a patient study coach. Explain simply, use examples, and create short checks for understanding.' }
]

const PROMPT_LIBRARY = [
  { title: 'Summarize', prompt: 'Summarize this clearly, then list key action items:\n\n' },
  { title: 'Review code', prompt: 'Review this code for bugs, security, performance, and readability. Suggest exact fixes:\n\n' },
  { title: 'Explain simply', prompt: 'Explain this step by step with a simple example:\n\n' },
  { title: 'Research plan', prompt: 'Create a research plan with questions, search terms, and report outline for:\n\n' }
]

function formatFileSize(size: number) {
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / (1024 * 1024)).toFixed(1)} MB`
}

function fileToDataUrl(file: File) {
  return new Promise<string>((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result))
    reader.onerror = () => reject(reader.error)
    reader.readAsDataURL(file)
  })
}

function dataUrlToBase64(dataUrl: string) {
  return dataUrl.includes(',') ? dataUrl.split(',')[1] : dataUrl
}

export default function AIChat() {
  const [conversations, setConversations] = useState<Conversation[]>(() => {
    const saved = localStorage.getItem('multimax_conversations')
    return saved ? JSON.parse(saved) : []
  })
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null)
  const [input, setInput] = useState('')
  const [editingMessageId, setEditingMessageId] = useState<string | null>(null)
  const [editInput, setEditInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isStreaming, setIsStreaming] = useState(false)
  const [models, setModels] = useState<{ name: string }[]>([
    { name: 'phi3:latest' },
    { name: 'llama3:latest' },
    { name: 'qwen3:4b' }
  ])
  const [selectedModel, setSelectedModel] = useState('phi3:latest')
  const [showModels, setShowModels] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [folderFilter, setFolderFilter] = useState('All')
  const [selectedPersonaId, setSelectedPersonaId] = useState('general')
  const [showPrompts, setShowPrompts] = useState(false)
  const [pendingAttachments, setPendingAttachments] = useState<ChatAttachment[]>([])
  const [abortController, setAbortController] = useState<AbortController | null>(null)
  const [isRenaming, setIsRenaming] = useState<string | null>(null)
  const [renameInput, setRenameInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const { addToast } = useToast()

  const currentConversation = conversations.find(c => c.id === currentConversationId)
  const selectedPersona = PERSONAS.find(p => p.id === selectedPersonaId) || PERSONAS[0]
  const folders = ['All', ...Array.from(new Set(conversations.map(c => c.folder || 'General')))]

  useEffect(() => {
    localStorage.setItem('multimax_conversations', JSON.stringify(conversations))
  }, [conversations])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [currentConversation?.messages, isStreaming])

  useEffect(() => {
    const loadModels = async () => {
      try {
        const data = await getOllamaModels()
        if (data.models) setModels(data.models)
      } catch (e) {
        console.log('Using default models')
      }
    }
    loadModels()
  }, [])

  const createNewConversation = useCallback(() => {
    const newConversation: Conversation = {
      id: Date.now().toString(),
      title: 'New Conversation',
      messages: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      pinned: false,
      folder: folderFilter === 'All' ? 'General' : folderFilter,
      personaId: selectedPersonaId
    }
    setConversations(prev => [newConversation, ...prev])
    setCurrentConversationId(newConversation.id)
    return newConversation.id
  }, [folderFilter, selectedPersonaId])

  const deleteConversation = useCallback((id: string) => {
    setConversations(prev => prev.filter(c => c.id !== id))
    if (currentConversationId === id) {
      setCurrentConversationId(null)
    }
    addToast('Conversation deleted', 'success')
  }, [currentConversationId, addToast])

  const togglePin = useCallback((id: string) => {
    setConversations(prev => prev.map(c =>
      c.id === id ? { ...c, pinned: !c.pinned } : c
    ).sort((a, b) => (b.pinned ? 1 : 0) - (a.pinned ? 1 : 0)))
  }, [])

  const startRename = useCallback((conv: Conversation) => {
    setIsRenaming(conv.id)
    setRenameInput(conv.title)
  }, [])

  const saveRename = useCallback(() => {
    if (!isRenaming) return
    setConversations(prev => prev.map(c =>
      c.id === isRenaming ? { ...c, title: renameInput } : c
    ))
    setIsRenaming(null)
    setRenameInput('')
    addToast('Conversation renamed', 'success')
  }, [isRenaming, renameInput, addToast])

  const deleteMessage = useCallback((id: string) => {
    if (!currentConversationId) return
    setConversations(prev => prev.map(c => {
      if (c.id === currentConversationId) {
        return {
          ...c,
          messages: c.messages.filter(m => m.id !== id)
        }
      }
      return c
    }))
    addToast('Message deleted', 'success')
  }, [currentConversationId, addToast])

  const editMessage = useCallback((msg: Message) => {
    setEditingMessageId(msg.id)
    setEditInput(msg.content)
  }, [])

  const saveEdit = useCallback(async () => {
    if (!currentConversationId || !editingMessageId) return
    setConversations(prev => prev.map(c => {
      if (c.id === currentConversationId) {
        const idx = c.messages.findIndex(m => m.id === editingMessageId)
        if (idx !== -1) {
          const newMessages = [...c.messages.slice(0, idx), {
            ...c.messages[idx],
            content: editInput
          }, ...c.messages.slice(idx + 1)]
          return { ...c, messages: newMessages }
        }
      }
      return c
    }))
    setEditingMessageId(null)
    setEditInput('')
    addToast('Message updated', 'success')
  }, [currentConversationId, editingMessageId, editInput, addToast])

  const clearChat = useCallback(() => {
    if (!currentConversationId) return
    setConversations(prev => prev.map(c => {
      if (c.id === currentConversationId) {
        return { ...c, messages: [] }
      }
      return c
    }))
    addToast('Chat cleared', 'success')
  }, [currentConversationId, addToast])

  const copyToClipboard = async (text: string) => {
    await navigator.clipboard.writeText(text)
    addToast('Copied to clipboard!', 'success')
  }

  const exportChat = (format: 'markdown' | 'json') => {
    if (!currentConversation) return
    const body = format === 'json'
      ? JSON.stringify(currentConversation, null, 2)
      : [`# ${currentConversation.title}`, '', `Model: ${selectedModel}`, `Persona: ${selectedPersona.name}`, '', ...currentConversation.messages.map(m => `## ${m.role}\n\n${m.content}\n`)].join('\n')
    const blob = new Blob([body], { type: format === 'json' ? 'application/json' : 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${currentConversation.title.replace(/[^a-z0-9]+/gi, '-').toLowerCase()}.${format === 'json' ? 'json' : 'md'}`
    a.click()
    URL.revokeObjectURL(url)
    addToast('Chat exported', 'success')
  }

  const shareChat = async () => {
    if (!currentConversation) return
    const shareId = currentConversation.shareId || `share_${Date.now().toString(36)}`
    setConversations(prev => prev.map(c => c.id === currentConversation.id ? { ...c, shared: true, shareId } : c))
    await navigator.clipboard.writeText(`${window.location.origin}${window.location.pathname}?shared=${shareId}`)
    addToast('Share link copied', 'success')
  }

  const updateConversationFolder = (id: string, folder: string) => {
    setConversations(prev => prev.map(c => c.id === id ? { ...c, folder: folder.trim() || 'General' } : c))
  }

  const handleFilesSelected = async (files: FileList | null) => {
    if (!files?.length) return
    const attachments: ChatAttachment[] = []
    for (const file of Array.from(files)) {
      const attachment: ChatAttachment = {
        id: `${Date.now()}_${file.name}`,
        name: file.name,
        type: file.type || 'application/octet-stream',
        size: file.size,
        status: 'ready'
      }
      if (file.type.startsWith('image/')) {
        try {
          const dataUrl = await fileToDataUrl(file)
          attachment.previewUrl = dataUrl
          attachment.base64 = dataUrlToBase64(dataUrl)
          attachment.status = 'ready'
        } catch (error: any) {
          attachment.status = 'error'
          addToast(error.message || `Failed to read ${file.name}`, 'error')
        }
      } else if (file.type === 'application/pdf') {
        try {
          const result = await uploadDocument(file)
          attachment.status = 'uploaded'
          attachment.documentId = result.documents?.[0]?.id
        } catch (error: any) {
          attachment.status = 'error'
          addToast(error.message || `Failed to upload ${file.name}`, 'error')
        }
      }
      attachments.push(attachment)
    }
    setPendingAttachments(prev => [...prev, ...attachments])
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const removePendingAttachment = (id: string) => {
    setPendingAttachments(prev => prev.filter(file => file.id !== id))
  }

  const regenerateResponse = async () => {
    if (!currentConversation || currentConversation.messages.length < 1) return
    const lastUserMessage = [...currentConversation.messages].reverse().find(m => m.role === 'user')
    if (!lastUserMessage) return
    const messagesWithoutLastAI = currentConversation.messages.slice(0, -1)
    setConversations(prev => prev.map(c => {
      if (c.id === currentConversationId) {
        return { ...c, messages: messagesWithoutLastAI }
      }
      return c
    }))
    setInput(lastUserMessage.content)
    setTimeout(() => handleSubmit(), 100)
  }

  const handleSubmit = async (e?: React.FormEvent) => {
    e?.preventDefault()
    if ((!input.trim() && pendingAttachments.length === 0) || isLoading) return

    // Ensure we have a conversation BEFORE proceeding
    let activeConversationId = currentConversationId
    if (!activeConversationId) {
      const newId = Date.now().toString()
      const newConversation: Conversation = {
        id: newId,
        title: input.trim().slice(0, 30) + (input.trim().length > 30 ? '...' : ''),
        messages: [],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        pinned: false,
        folder: folderFilter === 'All' ? 'General' : folderFilter,
        personaId: selectedPersonaId
      }
      setConversations(prev => [newConversation, ...prev])
      setCurrentConversationId(newId)
      activeConversationId = newId
      console.log('Created new conversation with id:', newId)
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim() || 'Please analyze the attached file(s).',
      timestamp: new Date().toISOString(),
      attachments: pendingAttachments
    }
    const assistantMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString()
    }

    // Add messages using the active ID (not the stale state variable)
    setConversations(prev => {
      const existing = prev.find(c => c.id === activeConversationId)
      if (existing) {
        return prev.map(c => {
          if (c.id === activeConversationId) {
            return {
              ...c,
              messages: [...c.messages, userMessage, assistantMessage],
              updated_at: new Date().toISOString()
            }
          }
          return c
        })
      }
      return prev
    })

    setInput('')
    setPendingAttachments([])
    setIsLoading(true)
    setIsStreaming(true)
    const controller = new AbortController()
    setAbortController(controller)

    try {
      // Build messages array from localStorage to avoid stale closures
      const stored = JSON.parse(localStorage.getItem('multimax_conversations') || '[]')
      const activeConv = stored.find((c: Conversation) => c.id === activeConversationId)
      const conversationMessages = activeConv?.messages || []
      
      // Get the latest input (userMessage was already created above and captures the value before setInput(''))
      const attachmentContext = userMessage.attachments?.length ? '\n\nAttached files:\n' + userMessage.attachments.map(file => '- ' + file.name + ' (' + file.type + ', ' + formatFileSize(file.size) + ')' + (file.documentId ? ', document id: ' + file.documentId : '')).join('\n') : ''
      const messages = filterEmptyChatMessages([
        { role: 'system' as const, content: selectedPersona.systemPrompt },
        ...conversationMessages,
        { role: 'user' as const, content: userMessage.content + attachmentContext }
      ])
      
      console.log('Sending request to backend:', { model: selectedModel, messagesCount: messages.length })
      console.log('Full request payload:', JSON.stringify({ model: selectedModel, messages }))
      
      const response = await chatWithOllama(selectedModel, messages, controller.signal)
      console.log('Response status:', response.status, response.statusText)
      
      if (!response.ok) {
        const errorBody = await response.text()
        console.error('Response error body:', errorBody)
        throw new Error(`Server returned ${response.status}: ${response.statusText}. Body: ${errorBody}`)
      }
      
      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      let fullResponse = ''
      let buffer = '' // Accumulate partial JSON lines across chunks
      
      if (reader) {
        while (true) {
          const { done, value } = await reader.read()
          if (done) {
            // Process any remaining data in buffer
            if (buffer.trim()) {
              console.log('Processing remaining buffer:', buffer)
              try {
                const data = JSON.parse(buffer)
                console.log('Parsed remaining buffer data:', data)
                if (data.message?.content) {
                  fullResponse += data.message.content
                  setConversations(prev => prev.map(c => {
                    if (c.id === activeConversationId) {
                      return {
                        ...c,
                        messages: c.messages.map(m =>
                          m.id === assistantMessage.id
                            ? { ...m, content: fullResponse }
                            : m
                        )
                      }
                    }
                    return c
                  }))
                }
              } catch (e) {
                console.error('Failed to parse remaining buffer:', e, 'buffer:', buffer)
              }
            }
            break
          }
          
          const chunk = decoder.decode(value, { stream: true })
          console.log('Raw chunk received:', chunk.length > 200 ? chunk.substring(0, 200) + '...' : chunk)
          
          buffer += chunk
          const lines = buffer.split('\n')
          
          // The last element might be an incomplete line, keep it in buffer
          buffer = lines.pop() || ''
          
          for (const line of lines) {
            if (line.trim()) {
              try {
                const data = JSON.parse(line)
                console.log('Parsed line data:', data)
                
                if (data.message?.content) {
                  fullResponse += data.message.content
                  setConversations(prev => prev.map(c => {
                    if (c.id === activeConversationId) {
                      return {
                        ...c,
                        messages: c.messages.map(m =>
                          m.id === assistantMessage.id
                            ? { ...m, content: fullResponse }
                            : m
                        )
                      }
                    }
                    return c
                  }))
                } else if (data.done) {
                  console.log('Streaming complete. Full response:', fullResponse)
                } else {
                  console.log('Unexpected response format:', data)
                }
              } catch (e) {
                console.error('Chunk parse error:', e, 'line:', line)
              }
            }
          }
        }
      }
      console.log('Final full AI response:', fullResponse)
      
      // If we got an empty response, show a clear error
      if (!fullResponse && !controller.signal.aborted) {
        const errorMsg = 'AI response was empty. The model may be loading or busy.'
        console.error(errorMsg)
        addToast(errorMsg, 'error')
        setConversations(prev => prev.map(c => {
          if (c.id === activeConversationId) {
            return {
              ...c,
              messages: c.messages.map(m =>
                m.id === assistantMessage.id
                  ? { ...m, content: `Error: ${errorMsg}` }
                  : m
              )
            }
          }
          return c
        }))
      }
    } catch (error: any) {
      console.error('Request failed:', error)
      if (error.name !== 'AbortError') {
        const errorMessage = error.response?.data?.detail || error.message || 'Failed to get response'
        addToast(errorMessage, 'error')
        setConversations(prev => prev.map(c => {
          if (c.id === activeConversationId) {
            return {
              ...c,
              messages: c.messages.map(m =>
                m.id === assistantMessage.id
                  ? { ...m, content: `Error: ${errorMessage}` }
                  : m
              )
            }
          }
          return c
        }))
      }
    } finally {
      setIsLoading(false)
      setIsStreaming(false)
      setAbortController(null)
    }
  }

  const stopGeneration = () => {
    abortController?.abort()
  }

  const filteredConversations = conversations.filter(c => {
    const query = searchQuery.toLowerCase()
    const matchesFolder = folderFilter === 'All' || (c.folder || 'General') === folderFilter
    const matchesSearch = c.title.toLowerCase().includes(query) || c.messages.some(m => m.content.toLowerCase().includes(query))
    return matchesFolder && matchesSearch
  })

  return (
    <div className="flex h-[calc(100vh-140px)] gap-6">
      {/* Sidebar */}
      <div className="w-80 flex flex-col bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl overflow-hidden">
        <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
          <h2 className="font-semibold text-lg text-slate-800 dark:text-slate-100">
            Conversations
          </h2>
          <button
            onClick={createNewConversation}
            className="p-2 bg-green-500 hover:bg-green-600 text-white rounded-lg transition-all"
            title="New Chat"
          >
            <Plus className="w-5 h-5" />
          </button>
        </div>
        <div className="p-3 space-y-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <input
              type="text"
              placeholder="Search..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-slate-100 dark:bg-slate-800 border-0 rounded-xl text-slate-700 dark:text-slate-200 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-green-500"
            />
          </div>
          <select
            value={folderFilter}
            onChange={(e) => setFolderFilter(e.target.value)}
            className="w-full px-3 py-2 bg-slate-100 dark:bg-slate-800 border-0 rounded-xl text-slate-700 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-green-500"
          >
            {folders.map(folder => <option key={folder} value={folder}>{folder}</option>)}
          </select>
        </div>
        <div className="flex-1 overflow-y-auto p-3 space-y-2">
          {filteredConversations.map(conv => (
            <div
              key={conv.id}
              className={cn(
                'group relative flex items-center gap-3 p-3 rounded-xl transition-all cursor-pointer',
                currentConversationId === conv.id
                  ? 'bg-green-500/10 border border-green-500/20'
                  : 'hover:bg-slate-100 dark:hover:bg-slate-800'
              )}
              onClick={() => setCurrentConversationId(conv.id)}
            >
              {conv.pinned && <Pin className="w-4 h-4 text-green-500 absolute top-2 right-2" />}
              <div className="p-2 bg-slate-100 dark:bg-slate-800 rounded-lg">
                <MessageSquare className="w-5 h-5 text-slate-500" />
              </div>
              {isRenaming === conv.id ? (
                <input
                  value={renameInput}
                  onChange={(e) => setRenameInput(e.target.value)}
                  onBlur={saveRename}
                  onKeyDown={(e) => e.key === 'Enter' && saveRename()}
                  className="flex-1 bg-transparent border-0 text-slate-800 dark:text-slate-100 focus:outline-none"
                  autoFocus
                />
              ) : (
                <div className="flex-1 min-w-0">
                  <p className={cn(
                    "font-medium truncate",
                    currentConversationId === conv.id ? 'text-green-600 dark:text-green-400' : 'text-slate-700 dark:text-slate-300'
                  )}>
                    {conv.title}
                  </p>
                  <p className="text-xs text-slate-500">
                    {new Date(conv.updated_at).toLocaleDateString()}
                  </p>
                </div>
              )}
              <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                  onClick={(e) => { e.stopPropagation(); togglePin(conv.id) }}
                  className="p-1.5 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-lg text-slate-500"
                  title={conv.pinned ? 'Unpin' : 'Pin'}
                >
                  <Pin className="w-4 h-4" />
                </button>
                <button
                  onClick={(e) => { e.stopPropagation(); startRename(conv) }}
                  className="p-1.5 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-lg text-slate-500"
                  title="Rename"
                >
                  <Edit className="w-4 h-4" />
                </button>
                <button
                  onClick={(e) => { e.stopPropagation(); deleteConversation(conv.id) }}
                  className="p-1.5 hover:bg-red-100 dark:hover:bg-red-500/20 rounded-lg text-slate-500 hover:text-red-500"
                  title="Delete"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-200 dark:border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-green-400 to-green-600 rounded-xl flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="font-semibold text-slate-800 dark:text-slate-100">
                {currentConversation?.title || 'New Chat'}
              </h2>
              <p className="text-sm text-slate-500">
                {currentConversation?.messages.length || 0} messages
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {currentConversation && (
              <>
                <input
                  value={currentConversation.folder || 'General'}
                  onChange={(e) => updateConversationFolder(currentConversation.id, e.target.value)}
                  className="w-28 px-3 py-2 bg-slate-100 dark:bg-slate-800 rounded-xl text-sm text-slate-700 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-green-500"
                  title="Folder"
                />
                <button onClick={() => exportChat('markdown')} className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg text-slate-500" title="Export Markdown">
                  <Download className="w-5 h-5" />
                </button>
                <button onClick={shareChat} className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg text-slate-500" title="Share Chat">
                  <Share2 className="w-5 h-5" />
                </button>
              </>
            )}
            <select
              value={selectedPersonaId}
              onChange={(e) => setSelectedPersonaId(e.target.value)}
              className="px-3 py-2 bg-slate-100 dark:bg-slate-800 rounded-xl text-sm text-slate-700 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-green-500"
              title="Persona"
            >
              {PERSONAS.map(persona => <option key={persona.id} value={persona.id}>{persona.name}</option>)}
            </select>
            {currentConversation && currentConversation.messages.length > 0 && (
              <button
                onClick={clearChat}
                className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg text-slate-500"
                title="Clear Chat"
              >
                <Trash2 className="w-5 h-5" />
              </button>
            )}
            <div className="relative">
              <button
                onClick={() => setShowModels(!showModels)}
                className="flex items-center gap-2 px-4 py-2 bg-slate-100 dark:bg-slate-800 rounded-xl text-sm font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-200 dark:hover:bg-slate-700 transition-all"
              >
                <Bot className="w-4 h-4" />
                {selectedModel}
                <ChevronDown className="w-4 h-4" />
              </button>
              <AnimatePresence>
                {showModels && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="absolute right-0 top-full mt-2 w-56 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-xl overflow-hidden z-50"
                  >
                    {models.map(m => (
                      <button
                        key={m.name}
                        onClick={() => {
                          setSelectedModel(m.name)
                          setShowModels(false)
                        }}
                        className={cn(
                          'w-full px-4 py-2.5 text-left text-sm hover:bg-slate-100 dark:hover:bg-slate-800 transition-all',
                          selectedModel === m.name ? 'text-green-600 dark:text-green-400 font-medium' : 'text-slate-700 dark:text-slate-200'
                        )}
                      >
                        {m.name}
                      </button>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </div>
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {!currentConversation || currentConversation.messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center">
              <div className="w-24 h-24 bg-gradient-to-br from-green-400/20 to-green-600/20 rounded-full flex items-center justify-center mb-6">
                <MessageSquare className="w-12 h-12 text-green-500" />
              </div>
              <h3 className="text-xl font-semibold text-slate-800 dark:text-slate-100 mb-2">
                Start a Conversation
              </h3>
              <p className="text-slate-500 dark:text-slate-400 max-w-md mb-8">
                Ask anything or upload a document to get started.
              </p>
              <div className="flex gap-3 flex-wrap max-w-md">
                {[
                  'Explain quantum computing',
                  'Write a Python script',
                  'Help with email'
                ].map(prompt => (
                  <button
                    key={prompt}
                    onClick={() => {
                      setInput(prompt)
                      setTimeout(() => handleSubmit(), 50)
                    }}
                    className="flex-1 text-left px-4 py-3 bg-slate-100 dark:bg-slate-800 rounded-xl text-sm text-slate-700 dark:text-slate-200 hover:bg-slate-200 dark:hover:bg-slate-700 transition-all"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            currentConversation.messages.map((msg) => (
              <div
                key={msg.id}
                className={cn(
                  'flex gap-4 max-w-4xl',
                  msg.role === 'user' ? 'ml-auto flex-row-reverse' : 'mr-auto'
                )}
              >
                <div className={cn(
                  'w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0',
                  msg.role === 'user'
                    ? 'bg-gradient-to-br from-blue-500 to-blue-600'
                    : 'bg-gradient-to-br from-green-500 to-green-600'
                )}>
                  {msg.role === 'user' ? <User className="w-5 h-5 text-white" /> : <Bot className="w-5 h-5 text-white" />}
                </div>
                <div className={cn('flex-1', msg.role === 'user' && 'text-right')}>
                  {editingMessageId === msg.id ? (
                    <div className="bg-slate-100 dark:bg-slate-800 rounded-2xl p-4">
                      <textarea
                        value={editInput}
                        onChange={(e) => setEditInput(e.target.value)}
                        className="w-full bg-transparent border-0 text-slate-800 dark:text-slate-100 focus:outline-none resize-none"
                        autoFocus
                        rows={3}
                      />
                      <div className="flex justify-end gap-2 mt-3">
                        <button
                          onClick={() => setEditingMessageId(null)}
                          className="px-3 py-1 text-sm text-slate-500 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-lg"
                        >
                          Cancel
                        </button>
                        <button
                          onClick={saveEdit}
                          className="px-3 py-1 text-sm bg-green-500 text-white rounded-lg hover:bg-green-600"
                        >
                          Save
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className={cn(
                      'rounded-2xl px-4 py-3 inline-block text-left max-w-full',
                      msg.role === 'user'
                        ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white'
                        : 'bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-100'
                    )}>
                      {msg.attachments?.length ? (
                        <div className="mb-3 flex flex-wrap gap-2">
                          {msg.attachments.map(file => (
                            <div key={file.id} className="rounded-xl bg-white/15 dark:bg-slate-700/70 p-2 text-xs">
                              {file.previewUrl ? (
                                <img src={file.previewUrl} alt={file.name} className="mb-2 max-h-40 max-w-60 rounded-lg object-contain" />
                              ) : null}
                              <div className="flex items-center gap-2">
                                <FileText className="w-3.5 h-3.5" />
                                <span>{file.name}</span>
                                <span className="opacity-70">{formatFileSize(file.size)}</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : null}                      {msg.role === 'assistant' ? (
                        <div className="prose prose-slate dark:prose-invert max-w-none">
                          <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            components={{
                              code({ node, inline, className, children, ...props }: any) {
                                const match = /language-(\w+)/.exec(className || '')
                                return !inline && match ? (
                                  <div className="relative my-2">
                                    <SyntaxHighlighter
                                      style={vscDarkPlus}
                                      language={match[1]}
                                      PreTag="div"
                                      className="rounded-xl"
                                      {...props}
                                    >
                                      {String(children).replace(/\n$/, '')}
                                    </SyntaxHighlighter>
                                    <button
                                      onClick={() => copyToClipboard(String(children))}
                                      className="absolute top-2 right-2 p-1.5 bg-slate-800/80 hover:bg-slate-700 rounded-lg text-slate-300 hover:text-white transition-all"
                                    >
                                      <Copy className="w-4 h-4" />
                                    </button>
                                  </div>
                                ) : (
                                  <code className={cn('bg-slate-200 dark:bg-slate-700 px-1.5 py-0.5 rounded text-sm', className)} {...props}>
                                    {children}
                                  </code>
                                )
                              }
                            }}
                          >
                            {msg.content}
                          </ReactMarkdown>
                        </div>
                      ) : (
                        <p className="whitespace-pre-wrap">{msg.content}</p>
                      )}
                    </div>
                  )}
                  {!isLoading && !editingMessageId && (
                    <div className="flex gap-1 mt-2 justify-start">
                      <button
                        onClick={() => copyToClipboard(msg.content)}
                        className="p-1.5 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg text-slate-500"
                        title="Copy"
                      >
                        <Copy className="w-4 h-4" />
                      </button>
                      {msg.role === 'user' && (
                        <button
                          onClick={() => editMessage(msg)}
                          className="p-1.5 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg text-slate-500"
                          title="Edit"
                        >
                          <Edit className="w-4 h-4" />
                        </button>
                      )}
                      {msg.role === 'assistant' && (
                        <button
                          onClick={regenerateResponse}
                          className="p-1.5 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg text-slate-500"
                          title="Regenerate"
                        >
                          <RotateCcw className="w-4 h-4" />
                        </button>
                      )}
                      <button
                        onClick={() => deleteMessage(msg.id)}
                        className="p-1.5 hover:bg-red-50 dark:hover:bg-red-500/10 rounded-lg text-slate-500 hover:text-red-500"
                        title="Delete"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
          {isLoading && (
            <div className="flex gap-4 max-w-4xl mr-auto">
              <div className="w-10 h-10 bg-gradient-to-br from-green-500 to-green-600 rounded-full flex items-center justify-center">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <div className="bg-slate-100 dark:bg-slate-800 rounded-2xl px-4 py-3">
                <div className="flex gap-2">
                  <div className="w-2.5 h-2.5 bg-green-500 rounded-full animate-bounce" />
                  <div className="w-2.5 h-2.5 bg-green-500 rounded-full animate-bounce" style={{ animationDelay: '0.15s' }} />
                  <div className="w-2.5 h-2.5 bg-green-500 rounded-full animate-bounce" style={{ animationDelay: '0.3s' }} />
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
        {/* Input */}
        <div className="p-4 border-t border-slate-200 dark:border-slate-800">
          {showPrompts && (
            <div className="mb-3 grid grid-cols-1 md:grid-cols-4 gap-2">
              {PROMPT_LIBRARY.map(prompt => (
                <button key={prompt.title} type="button" onClick={() => { setInput(prev => `${prev}${prompt.prompt}`); setShowPrompts(false) }} className="text-left p-3 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700">
                  <span className="block text-sm font-medium text-slate-800 dark:text-slate-100">{prompt.title}</span>
                </button>
              ))}
            </div>
          )}
          {pendingAttachments.length > 0 && (
            <div className="mb-3 flex flex-wrap gap-2">
              {pendingAttachments.map(file => (
                <div key={file.id} className="flex items-center gap-2 rounded-xl bg-slate-100 dark:bg-slate-800 px-3 py-2 text-sm text-slate-700 dark:text-slate-200">
                  {file.previewUrl ? <img src={file.previewUrl} alt={file.name} className="h-10 w-10 rounded-lg object-cover" /> : <FileText className="w-4 h-4" />}
                  <span>{file.name}</span>
                  <span className="text-xs text-slate-500">{formatFileSize(file.size)}</span>
                  <button type="button" onClick={() => removePendingAttachment(file.id)} className="text-slate-500 hover:text-red-500"><X className="w-4 h-4" /></button>
                </div>
              ))}
            </div>
          )} 
          <form onSubmit={handleSubmit} className="relative">
            <div className="flex gap-2 mb-2">
              <button type="button" onClick={() => setShowPrompts(!showPrompts)} className="flex items-center gap-2 px-3 py-1.5 bg-slate-100 dark:bg-slate-800 text-slate-500 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-700 transition-all text-sm">
                <Library className="w-4 h-4" />
                <span>Prompt Library</span>
              </button>
              <button type="button" onClick={() => fileInputRef.current?.click()} className="flex items-center gap-2 px-3 py-1.5 bg-slate-100 dark:bg-slate-800 text-slate-500 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-700 transition-all text-sm">
                <UploadCloud className="w-4 h-4" />
                <span>Upload image/PDF/file</span>
              </button>
              <input ref={fileInputRef} type="file" className="hidden" multiple accept="image/*,.pdf,.txt,.md,.csv,.json,.doc,.docx" onChange={(e) => handleFilesSelected(e.target.files)} />
            </div>
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  handleSubmit()
                }
              }}
              placeholder={`Message ${selectedPersona.name}...`}
              className="w-full px-4 py-3 pr-24 bg-slate-100 dark:bg-slate-800 border-0 rounded-xl text-slate-700 dark:text-slate-200 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-green-500 resize-none"
              rows={1}
              style={{ maxHeight: '200px' }}
            />
            <div className="absolute right-2 bottom-2 flex gap-2">
              {isLoading ? (
                <button
                  type="button"
                  onClick={stopGeneration}
                  className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-xl font-medium transition-all flex items-center gap-2"
                > 
                
                  <Square className="w-4 h-4" />
                  Stop
                </button>
              ) : (
                <button
                  type="submit"
                  disabled={!input.trim() && pendingAttachments.length === 0}
                  className="px-4 py-2 bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 disabled:opacity-50 text-white rounded-xl font-medium transition-all flex items-center gap-2"
                >
                  <Send className="w-4 h-4" />
                  Send
                </button>
              )}
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
