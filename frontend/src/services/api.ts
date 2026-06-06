const BASE = '/api'

export interface Chatbot {
  id: string
  name: string
  description: string | null
  tone: string
  greeting: string | null
  fallback_message: string | null
  model: string
  created_at: string
  updated_at: string
}

export interface ChatbotCreate {
  name: string
  description?: string
  tone?: string
  greeting?: string
  fallback_message?: string
  model?: string
}

export interface Document {
  id: string
  chatbot_id: string
  filename: string
  file_type: string
  status: string
  error: string | null
  created_at: string
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface ChatResponse {
  reply: string
  session_id: string
  sources: string[]
}

export interface ContactCapture {
  id: string
  chatbot_id: string
  email: string
  name: string | null
  notes: string | null
  captured_at: string
}

export interface UnknownQuestion {
  id: string
  chatbot_id: string
  question: string
  asked_at: string
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...init?.headers },
    ...init,
  })
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: resp.statusText }))
    throw new Error(err.detail || resp.statusText)
  }
  if (resp.status === 204) return undefined as unknown as T
  return resp.json()
}

export const api = {
  chatbots: {
    list: () => request<Chatbot[]>('/chatbots'),
    get: (id: string) => request<Chatbot>(`/chatbots/${id}`),
    create: (data: ChatbotCreate) => request<Chatbot>('/chatbots', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
    update: (id: string, data: Partial<ChatbotCreate>) => request<Chatbot>(`/chatbots/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
    delete: (id: string) => request<void>(`/chatbots/${id}`, { method: 'DELETE' }),
  },

  documents: {
    list: (chatbotId: string) => request<Document[]>(`/chatbots/${chatbotId}/documents`),
    upload: async (chatbotId: string, file: File): Promise<Document> => {
      const form = new FormData()
      form.append('file', file)
      const resp = await fetch(`${BASE}/chatbots/${chatbotId}/documents`, {
        method: 'POST',
        body: form,
      })
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({ detail: resp.statusText }))
        throw new Error(err.detail || resp.statusText)
      }
      return resp.json()
    },
    delete: (chatbotId: string, docId: string) =>
      request<void>(`/chatbots/${chatbotId}/documents/${docId}`, { method: 'DELETE' }),
    rebuild: (chatbotId: string, docId: string) =>
      request<Document>(`/chatbots/${chatbotId}/documents/${docId}/rebuild`, { method: 'POST' }),
  },

  chat: (chatbotId: string, message: string, history: ChatMessage[], sessionId?: string) =>
    request<ChatResponse>(`/chatbots/${chatbotId}/chat`, {
      method: 'POST',
      body: JSON.stringify({ message, history, session_id: sessionId }),
    }),

  contacts: (chatbotId: string) =>
    request<ContactCapture[]>(`/chatbots/${chatbotId}/contacts`),

  unknownQuestions: (chatbotId: string) =>
    request<UnknownQuestion[]>(`/chatbots/${chatbotId}/unknown-questions`),
}
