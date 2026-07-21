export interface User {
  id: string
  email: string
  username: string
  display_name: string
  role: string
  is_active: boolean
  is_verified: boolean
  avatar_url: string
}

export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: string | Date
  attachments?: ChatAttachment[]
}

export interface Conversation {
  id: string
  title: string
  messages: Message[]
  created_at: string | Date
  updated_at: string | Date
  pinned?: boolean
  folder?: string
  personaId?: string
  shared?: boolean
  shareId?: string
}

export interface ChatAttachment {
  id: string
  name: string
  type: string
  size: number
  url?: string
  previewUrl?: string
  base64?: string
  status?: 'ready' | 'uploaded' | 'error'
  documentId?: string
}
