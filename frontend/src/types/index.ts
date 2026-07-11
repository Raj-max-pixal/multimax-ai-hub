export interface User {
  id: string
  email: string
  avatar_url?: string
  full_name?: string
}

export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: string | Date
}

export interface Conversation {
  id: string
  title: string
  messages: Message[]
  created_at: string | Date
  updated_at: string | Date
  pinned?: boolean
}
