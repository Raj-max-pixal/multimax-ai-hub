import { useState, useRef, useEffect, useCallback } from 'react'
import {
  UploadCloud,
  FileText,
  Trash2,
  Send,
  MessageSquare,
  CheckCircle2,
  Bot,
  User,
  Loader2,
  Plus
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { useToast } from '../contexts/ToastContext'
import { cn } from '../lib/utils'

const API_BASE = '/api'

interface Document {
  id: string
  filename: string
  saved_filename: string
  file_type: string
  file_size: number
  chunk_count: number
  status: string
}

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
}

export default function PDFChat() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [selectedDocumentIds, setSelectedDocumentIds] = useState<string[]>([])
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isStreaming, setIsStreaming] = useState(false)
  const [isDragging, setIsDragging] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const { addToast } = useToast()

  // Load documents on mount
  useEffect(() => {
    const loadDocuments = async () => {
      try {
        const response = await fetch(`${API_BASE}/documents`)
        const data = await response.json()
        setDocuments(data.documents || [])
      } catch (error) {
        console.error('Failed to load documents:', error)
      }
    }
    loadDocuments()
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isStreaming])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const files = Array.from(e.dataTransfer.files)
    await handleFileUpload(files)
  }, [])

  const handleFileSelect = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    if (files.length > 0) {
      await handleFileUpload(files)
      e.target.value = ''
    }
  }, [])

  const handleFileUpload = async (files: File[]) => {
    try {
      const formData = new FormData()
      files.forEach(file => formData.append('files', file))
      
      setIsLoading(true)
      const response = await fetch(`${API_BASE}/documents/upload`, {
        method: 'POST',
        body: formData
      })
      
      if (!response.ok) throw new Error('Upload failed')
      
      const data = await response.json()
      setDocuments(prev => [...prev, ...data.documents])
      addToast(`Successfully uploaded ${data.documents.length} document(s)!`, 'success')
    } catch (error) {
      console.error('Upload error:', error)
      addToast('Failed to upload documents', 'error')
    } finally {
      setIsLoading(false)
    }
  }

  const handleDeleteDocument = async (doc: Document) => {
    try {
      const response = await fetch(`${API_BASE}/documents/${doc.id}`, {
        method: 'DELETE'
      })
      
      if (!response.ok) throw new Error('Delete failed')
      
      setDocuments(prev => prev.filter(d => d.id !== doc.id))
      setSelectedDocumentIds(prev => prev.filter(id => id !== doc.id))
      addToast('Document deleted', 'success')
    } catch (error) {
      console.error('Delete error:', error)
      addToast('Failed to delete document', 'error')
    }
  }

  const toggleDocumentSelection = (docId: string) => {
    setSelectedDocumentIds(prev => 
      prev.includes(docId) 
        ? prev.filter(id => id !== docId) 
        : [...prev, docId]
    )
  }

  const handleSubmit = async (e?: React.FormEvent) => {
    e?.preventDefault()
    if (!input.trim() || selectedDocumentIds.length === 0 || isLoading) return
    
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim()
    }
    
    const assistantMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: ''
    }
    
    setMessages(prev => [...prev, userMessage, assistantMessage])
    setInput('')
    setIsLoading(true)
    setIsStreaming(true)
    
    try {
      const response = await fetch(`${API_BASE}/documents/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: userMessage.content,
          document_ids: selectedDocumentIds
        })
      })
      
      if (!response.ok) throw new Error('Chat failed')
      
      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      let fullContent = ''
      
      if (reader) {
        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          
          const chunk = decoder.decode(value)
          const lines = chunk.split('\n')
          
          for (const line of lines) {
            if (line.trim()) {
              try {
                const data = JSON.parse(line)
                if (data.message?.content) {
                  fullContent += data.message.content
                  setMessages(prev => prev.map(m => 
                    m.id === assistantMessage.id ? { ...m, content: fullContent } : m
                  ))
                }
              } catch (e) {
                // Ignore parse errors for partial JSON
              }
            }
          }
        }
      }
    } catch (error) {
      console.error('Chat error:', error)
      setMessages(prev => prev.map(m => 
        m.id === assistantMessage.id 
          ? { ...m, content: 'Sorry, I encountered an error. Please try again.' } 
          : m
      ))
      addToast('Failed to get response', 'error')
    } finally {
      setIsLoading(false)
      setIsStreaming(false)
    }
  }

  const copyToClipboard = async (text: string) => {
    await navigator.clipboard.writeText(text)
    addToast('Copied to clipboard!', 'success')
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  return (
    <div className="flex h-[calc(100vh-140px)] gap-6">
      {/* Documents Sidebar */}
      <div className="w-80 flex flex-col bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl overflow-hidden">
        <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
          <h2 className="font-semibold text-lg text-slate-800 dark:text-slate-100">
            Documents
          </h2>
          <button
            onClick={() => fileInputRef.current?.click()}
            className="p-2 bg-green-500 hover:bg-green-600 text-white rounded-lg transition-all"
            title="Upload Documents"
          >
            <Plus className="w-5 h-5" />
          </button>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".pdf,.txt,.md,.docx"
            onChange={handleFileSelect}
            className="hidden"
          />
        </div>
        
        {/* Upload Area */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={cn(
            "mx-4 my-3 p-4 border-2 border-dashed rounded-xl cursor-pointer transition-all",
            isDragging 
              ? "border-green-500 bg-green-50 dark:bg-green-500/10" 
              : "border-slate-300 dark:border-slate-700 hover:border-green-400 hover:bg-slate-50 dark:hover:bg-slate-800"
          )}
        >
          <div className="flex flex-col items-center text-center">
            <UploadCloud className={cn(
              "w-10 h-10 mb-2",
              isDragging ? "text-green-500" : "text-slate-400"
            )} />
            <p className="text-sm font-medium text-slate-600 dark:text-slate-400">
              {isDragging ? "Drop files here" : "Click or drag to upload"}
            </p>
            <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">
              PDF, TXT, MD, DOCX â€¢ Max 10MB
            </p>
          </div>
        </div>
        
        {/* Documents List */}
        <div className="flex-1 overflow-y-auto p-3 space-y-2">
          {documents.map(doc => (
            <div
              key={doc.id}
              className={cn(
                "group flex items-start gap-3 p-3 rounded-xl transition-all cursor-pointer",
                selectedDocumentIds.includes(doc.id)
                  ? "bg-green-500/10 border border-green-500/20"
                  : "hover:bg-slate-100 dark:hover:bg-slate-800"
              )}
              onClick={() => toggleDocumentSelection(doc.id)}
            >
              <div className="p-2 bg-slate-100 dark:bg-slate-800 rounded-lg">
                <FileText className="w-5 h-5 text-slate-500" />
              </div>
              <div className="flex-1 min-w-0">
                <p className={cn(
                  "font-medium truncate text-sm",
                  selectedDocumentIds.includes(doc.id) ? "text-green-600 dark:text-green-400" : "text-slate-700 dark:text-slate-300"
                )}>
                  {doc.filename}
                </p>
                <p className="text-xs text-slate-500 mt-0.5">
                  {formatFileSize(doc.file_size)} â€¢ {doc.chunk_count} chunks
                </p>
              </div>
              <div className="flex items-center gap-1">
                {selectedDocumentIds.includes(doc.id) && (
                  <CheckCircle2 className="w-4 h-4 text-green-500" />
                )}
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    handleDeleteDocument(doc)
                  }}
                  className="p-1.5 hover:bg-red-100 dark:hover:bg-red-500/20 rounded-lg text-slate-500 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
          
          {documents.length === 0 && !isLoading && (
            <div className="flex flex-col items-center justify-center h-48 text-center px-4">
              <FileText className="w-10 h-10 text-slate-300 dark:text-slate-600 mb-3" />
              <p className="text-sm text-slate-500 dark:text-slate-400">
                No documents uploaded yet
              </p>
              <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">
                Upload a document to get started
              </p>
            </div>
          )}
        </div>
      </div>
      
      {/* Chat Area */}
      <div className="flex-1 flex flex-col bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-200 dark:border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-green-400 to-green-600 rounded-xl flex items-center justify-center">
              <FileText className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="font-semibold text-slate-800 dark:text-slate-100">
                Chat with Documents
              </h2>
              <p className="text-sm text-slate-500">
                {selectedDocumentIds.length === 0 
                  ? "Select one or more documents to start" 
                  : `Selected ${selectedDocumentIds.length} document(s)`}
              </p>
            </div>
          </div>
        </div>
        
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="w-24 h-24 bg-gradient-to-br from-green-400/20 to-green-600/20 rounded-full flex items-center justify-center mb-6">
                <MessageSquare className="w-12 h-12 text-green-500" />
              </div>
              <h3 className="text-xl font-semibold text-slate-800 dark:text-slate-100 mb-2">
                Ask Questions About Your Documents
              </h3>
              <p className="text-slate-500 dark:text-slate-400 max-w-md mb-8">
                Upload documents and select them to start asking questions.
                The AI will use the document content to answer your questions.
              </p>
            </div>
          ) : (
            messages.map((msg) => (
              <div
                key={msg.id}
                className={cn(
                  "flex gap-4 max-w-4xl",
                  msg.role === "user" ? "ml-auto flex-row-reverse" : "mr-auto"
                )}
              >
                <div className={cn(
                  "w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0",
                  msg.role === "user"
                    ? "bg-gradient-to-br from-blue-500 to-blue-600"
                    : "bg-gradient-to-br from-green-500 to-green-600"
                )}>
                  {msg.role === "user" ? <User className="w-5 h-5 text-white" /> : <Bot className="w-5 h-5 text-white" />}
                </div>
                <div className={cn("flex-1", msg.role === "user" && "text-right")}>
                  <div className={cn(
                    "rounded-2xl px-4 py-3 inline-block text-left max-w-full",
                    msg.role === "user"
                      ? "bg-gradient-to-r from-blue-500 to-blue-600 text-white"
                      : "bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-100"
                  )}>
                    {msg.role === "assistant" ? (
                      <div className="prose prose-slate dark:prose-invert max-w-none">
                        <ReactMarkdown
                          remarkPlugins={[remarkGfm]}
                          components={{
                            code({ node, inline, className, children, ...props }: any) {
                              const match = /language-(\w+)/.exec(className || "")
                              return !inline && match ? (
                                <div className="relative my-2">
                                  <SyntaxHighlighter
                                    style={vscDarkPlus}
                                    language={match[1]}
                                    PreTag="div"
                                    className="rounded-xl"
                                    {...props}
                                  >
                                    {String(children).replace(/\n$/, "")}
                                  </SyntaxHighlighter>
                                  <button
                                    onClick={() => copyToClipboard(String(children))}
                                    className="absolute top-2 right-2 p-1.5 bg-slate-800/80 hover:bg-slate-700 rounded-lg text-slate-300 hover:text-white transition-all"
                                  >
                                    <FileText className="w-4 h-4" />
                                  </button>
                                </div>
                              ) : (
                                <code className={cn("bg-slate-200 dark:bg-slate-700 px-1.5 py-0.5 rounded text-sm", className)} {...props}>
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
                </div>
              </div>
            ))
          )}
          
          {isLoading && (
            <div className="flex gap-4 max-w-4xl mr-auto">
              <div className="w-10 h-10 bg-gradient-to-br from-green-500 to-green-600 rounded-full flex items-center justify-center">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <div className="bg-slate-100 dark:bg-slate-800 rounded-2xl px-4 py-3 flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-green-500" />
                <span className="text-sm text-slate-500">Thinking...</span>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
        
        {/* Input */}
        <div className="p-4 border-t border-slate-200 dark:border-slate-800">
          <form onSubmit={handleSubmit} className="relative">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault()
                  handleSubmit()
                }
              }}
              placeholder={selectedDocumentIds.length === 0 
                ? "Select at least one document to chat..." 
                : "Ask a question about your documents..."
              }
              disabled={selectedDocumentIds.length === 0}
              className={cn(
                "w-full px-4 py-3 pr-24 bg-slate-100 dark:bg-slate-800 border-0 rounded-xl text-slate-700 dark:text-slate-200 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-green-500 resize-none",
                selectedDocumentIds.length === 0 && "opacity-50 cursor-not-allowed"
              )}
              rows={1}
              style={{ maxHeight: '200px' }}
            />
            <div className="absolute right-2 bottom-2">
              {isLoading ? (
                <div className="px-4 py-2 bg-slate-200 dark:bg-slate-700 text-slate-500 rounded-xl font-medium flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Loading
                </div>
              ) : (
                <button
                  type="submit"
                  disabled={!input.trim() || selectedDocumentIds.length === 0}
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
