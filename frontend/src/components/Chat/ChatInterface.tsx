import { useState, useRef, useEffect } from 'react'
import { api, ChatMessage, Chatbot } from '../../services/api'
import MessageBubble from './MessageBubble'
import SourceCitations from './SourceCitations'

interface Props {
  chatbot: Chatbot
}

interface DisplayMessage {
  role: 'user' | 'assistant'
  content: string
  sources?: string[]
}

export default function ChatInterface({ chatbot }: Props) {
  const [messages, setMessages] = useState<DisplayMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState<string | undefined>()
  const [error, setError] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (chatbot.greeting) {
      setMessages([{ role: 'assistant', content: chatbot.greeting }])
    }
  }, [chatbot.id, chatbot.greeting])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const history: ChatMessage[] = messages.map(m => ({ role: m.role, content: m.content }))

  const send = async () => {
    const text = input.trim()
    if (!text || loading) return
    setInput('')
    setError(null)
    setMessages(prev => [...prev, { role: 'user', content: text }])
    setLoading(true)
    try {
      const resp = await api.chat(chatbot.id, text, history, sessionId)
      setSessionId(resp.session_id)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: resp.reply,
        sources: resp.sources,
      }])
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Something went wrong')
    } finally {
      setLoading(false)
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
        {loading && (
          <div style={{ color: '#888', padding: '0.5rem' }}>Thinking…</div>
        )}
        {error && (
          <div style={{ color: 'red', padding: '0.5rem' }}>{error}</div>
        )}
        <div ref={bottomRef} />
      </div>
      <div style={{ display: 'flex', padding: '1rem', borderTop: '1px solid #eee', gap: '0.5rem' }}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
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
          disabled={loading || !input.trim()}
          style={{
            padding: '0.75rem 1.5rem', borderRadius: '8px',
            background: '#2563eb', color: 'white',
            border: 'none', cursor: 'pointer', fontSize: '1rem',
          }}
        >
          Send
        </button>
      </div>
    </div>
  )
}
