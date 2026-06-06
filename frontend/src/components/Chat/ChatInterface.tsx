import { useRef, useEffect } from 'react'
import { api, ChatMessage, Chatbot } from '../../services/api'
import MessageBubble from './MessageBubble'
import SourceCitations from './SourceCitations'

export interface DisplayMessage {
  role: 'user' | 'assistant'
  content: string
  sources?: string[]
}

interface Props {
  chatbot: Chatbot
  messages: DisplayMessage[]
  sessionId: string | undefined
  onMessagesChange: (updater: (prev: DisplayMessage[]) => DisplayMessage[]) => void
  onSessionIdChange: (id: string) => void
  loading: boolean
  onLoadingChange: (v: boolean) => void
}

export default function ChatInterface({
  chatbot, messages, sessionId,
  onMessagesChange, onSessionIdChange,
  loading, onLoadingChange,
}: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const history: ChatMessage[] = messages.map(m => ({ role: m.role, content: m.content }))

  const send = async () => {
    const text = inputRef.current?.value.trim()
    if (!text || loading) return
    inputRef.current!.value = ''

    onMessagesChange(prev => [...prev, { role: 'user', content: text }])
    onLoadingChange(true)
    try {
      const resp = await api.chat(chatbot.id, text, history, sessionId)
      onSessionIdChange(resp.session_id)
      onMessagesChange(prev => [...prev, {
        role: 'assistant',
        content: resp.reply,
        sources: resp.sources,
      }])
    } catch (e: unknown) {
      onMessagesChange(prev => [...prev, {
        role: 'assistant',
        content: e instanceof Error ? `Error: ${e.message}` : 'Something went wrong.',
      }])
    } finally {
      onLoadingChange(false)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ flex: 1, overflowY: 'auto', padding: '1rem' }}>
        {messages.map((m, i) => (
          <div key={i}>
            <MessageBubble role={m.role} content={m.content} />
            {m.sources && m.sources.length > 0 && <SourceCitations sources={m.sources} />}
          </div>
        ))}
        {loading && <div style={{ color: '#888', padding: '0.5rem' }}>Thinking…</div>}
        <div ref={bottomRef} />
      </div>
      <div style={{ display: 'flex', padding: '1rem', borderTop: '1px solid #eee', gap: '0.5rem' }}>
        <input
          ref={inputRef}
          onKeyDown={e => e.key === 'Enter' && !e.shiftKey && send()}
          placeholder={`Ask ${chatbot.name}…`}
          disabled={loading}
          style={{
            flex: 1, padding: '0.75rem', borderRadius: '8px',
            border: '1px solid #ddd', fontSize: '1rem',
          }}
        />
        <button
          onClick={send}
          disabled={loading}
          style={{
            padding: '0.75rem 1.5rem', borderRadius: '8px',
            background: '#2563eb', color: 'white',
            border: 'none', cursor: 'pointer', fontSize: '1rem',
          }}
        >Send</button>
      </div>
    </div>
  )
}
