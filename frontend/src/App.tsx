import { useState, useEffect } from 'react'
import { api, Chatbot } from './services/api'
import ChatInterface, { DisplayMessage } from './components/Chat/ChatInterface'
import Dashboard from './components/Admin/Dashboard'

type View = 'chat' | 'admin'

interface ChatState {
  messages: DisplayMessage[]
  sessionId: string | undefined
}

export default function App() {
  const [chatbots, setChatbots] = useState<Chatbot[]>([])
  const [selected, setSelected] = useState<Chatbot | null>(null)
  const [view, setView] = useState<View>('chat')
  const [creating, setCreating] = useState(false)
  const [newName, setNewName] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [chatStates, setChatStates] = useState<Record<string, ChatState>>({})
  const [chatLoading, setChatLoading] = useState<Record<string, boolean>>({})

  const loadBots = () =>
    api.chatbots.list()
      .then(bots => {
        setChatbots(bots)
        if (bots.length && !selected) setSelected(bots[0])
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))

  useEffect(() => { loadBots() }, [])

  useEffect(() => {
    if (!selected) return
    setChatStates(prev => {
      if (prev[selected.id]) return prev
      const greeting = selected.greeting || `Hi! I'm ${selected.name}. How can I help you?`
      return {
        ...prev,
        [selected.id]: { messages: [{ role: 'assistant', content: greeting }], sessionId: undefined },
      }
    })
  }, [selected?.id])

  const createBot = async () => {
    if (!newName.trim()) return
    const bot = await api.chatbots.create({ name: newName.trim() })
    await loadBots()
    setSelected(bot)
    setCreating(false)
    setNewName('')
    setView('admin')
  }

  if (loading) return <div style={{ padding: '2rem', color: '#6b7280' }}>Loading…</div>

  const chatState = selected
    ? (chatStates[selected.id] ?? { messages: [], sessionId: undefined })
    : null
  const isChatLoading = selected ? (chatLoading[selected.id] ?? false) : false

  const handleMessagesChange = (updater: (prev: DisplayMessage[]) => DisplayMessage[]) => {
    if (!selected) return
    const id = selected.id
    setChatStates(prev => ({
      ...prev,
      [id]: { ...prev[id], messages: updater(prev[id]?.messages ?? []) },
    }))
  }

  const handleSessionIdChange = (sessionId: string) => {
    if (!selected) return
    const id = selected.id
    setChatStates(prev => ({ ...prev, [id]: { ...prev[id], sessionId } }))
  }

  const handleLoadingChange = (v: boolean) => {
    if (!selected) return
    setChatLoading(prev => ({ ...prev, [selected.id]: v }))
  }

  return (
    <div style={{ display: 'flex', height: '100vh', fontFamily: 'system-ui, sans-serif' }}>
      {/* Sidebar */}
      <div style={{
        width: '240px', background: '#1e293b', color: 'white',
        display: 'flex', flexDirection: 'column', flexShrink: 0,
      }}>
        <div style={{ padding: '1.25rem 1rem', borderBottom: '1px solid #334155' }}>
          <div style={{ fontWeight: 700, fontSize: '1rem' }}>AI Profile Chatbot</div>
          <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '0.2rem' }}>Your chatbots</div>
        </div>

        <div style={{ flex: 1, overflowY: 'auto', padding: '0.75rem 0' }}>
          {chatbots.map(bot => (
            <button
              key={bot.id}
              onClick={() => { setSelected(bot); setView('chat') }}
              style={{
                display: 'block', width: '100%', textAlign: 'left',
                padding: '0.65rem 1rem', border: 'none', cursor: 'pointer',
                background: selected?.id === bot.id ? '#334155' : 'transparent',
                color: 'white', fontSize: '0.9rem',
              }}
            >{bot.name}</button>
          ))}
        </div>

        {creating
          ? (
            <div style={{ padding: '0.75rem' }}>
              <input
                autoFocus
                value={newName}
                onChange={e => setNewName(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && createBot()}
                placeholder="Chatbot name"
                style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: 'none', boxSizing: 'border-box' }}
              />
              <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
                <button onClick={createBot} style={{ flex: 1, padding: '0.4rem', background: '#2563eb', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer' }}>Create</button>
                <button onClick={() => setCreating(false)} style={{ flex: 1, padding: '0.4rem', background: '#475569', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer' }}>Cancel</button>
              </div>
            </div>
          )
          : (
            <button
              onClick={() => setCreating(true)}
              style={{
                margin: '0.75rem', padding: '0.6rem',
                background: '#2563eb', color: 'white', border: 'none',
                borderRadius: '8px', cursor: 'pointer', fontSize: '0.9rem',
              }}
            >+ New Chatbot</button>
          )
        }
      </div>

      {/* Main content */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {selected ? (
          <>
            {/* Top bar */}
            <div style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              padding: '0.75rem 1.5rem', borderBottom: '1px solid #e5e7eb',
              background: 'white',
            }}>
              <div>
                <span style={{ fontWeight: 600, fontSize: '1rem' }}>{selected.name}</span>
                {selected.description && (
                  <span style={{ marginLeft: '0.75rem', color: '#6b7280', fontSize: '0.85rem' }}>{selected.description}</span>
                )}
              </div>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                {(['chat', 'admin'] as View[]).map(v => (
                  <button
                    key={v}
                    onClick={() => setView(v)}
                    style={{
                      padding: '0.4rem 1rem', border: '1px solid #e5e7eb',
                      borderRadius: '6px', cursor: 'pointer', fontSize: '0.85rem',
                      background: view === v ? '#2563eb' : 'white',
                      color: view === v ? 'white' : '#374151',
                    }}
                  >{v === 'chat' ? 'Chat' : 'Admin'}</button>
                ))}
              </div>
            </div>

            {/* Content — both views stay mounted so chat history survives tab switches */}
            <div style={{ flex: 1, overflow: 'hidden', display: view === 'chat' ? 'flex' : 'none', flexDirection: 'column' }}>
              <ChatInterface
                chatbot={selected}
                messages={chatState?.messages ?? []}
                sessionId={chatState?.sessionId}
                onMessagesChange={handleMessagesChange}
                onSessionIdChange={handleSessionIdChange}
                loading={isChatLoading}
                onLoadingChange={handleLoadingChange}
              />
            </div>
            <div style={{ flex: 1, overflowY: 'auto', display: view === 'admin' ? 'block' : 'none', padding: '1.5rem', boxSizing: 'border-box' }}>
              <Dashboard
                chatbot={selected}
                onChatbotUpdated={updated => {
                  setSelected(updated)
                  setChatbots(prev => prev.map(b => b.id === updated.id ? updated : b))
                }}
                onChatbotDeleted={() => {
                  const id = selected.id
                  const remaining = chatbots.filter(b => b.id !== id)
                  setChatbots(remaining)
                  setChatStates(prev => { const next = { ...prev }; delete next[id]; return next })
                  setChatLoading(prev => { const next = { ...prev }; delete next[id]; return next })
                  setSelected(remaining[0] ?? null)
                  setView('chat')
                }}
              />
            </div>
          </>
        ) : (
          <div style={{
            flex: 1, display: 'flex', flexDirection: 'column',
            alignItems: 'center', justifyContent: 'center', color: '#6b7280',
          }}>
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🤖</div>
            <h2 style={{ margin: 0 }}>No chatbots yet</h2>
            <p>Click <strong>+ New Chatbot</strong> in the sidebar to get started.</p>
            {error && <div style={{ color: '#dc2626' }}>{error}</div>}
          </div>
        )}
      </div>
    </div>
  )
}
