import { useState } from 'react'
import { api, Chatbot } from '../../services/api'

interface Props {
  chatbot: Chatbot
  onUpdated: (updated: Chatbot) => void
  onDeleted: () => void
}

const TONES = ['professional', 'friendly', 'casual', 'formal', 'concise']
const MODELS = ['gpt-4o-mini', 'gpt-4o', 'gpt-4-turbo']

export default function ChatbotSettings({ chatbot, onUpdated, onDeleted }: Props) {
  const [form, setForm] = useState({
    name: chatbot.name,
    description: chatbot.description ?? '',
    tone: chatbot.tone,
    greeting: chatbot.greeting ?? '',
    fallback_message: chatbot.fallback_message ?? '',
    model: chatbot.model,
  })
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [deleting, setDeleting] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)

  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) =>
    setForm(prev => ({ ...prev, [k]: e.target.value }))

  const deleteChatbot = async () => {
    setDeleting(true)
    try {
      await api.chatbots.delete(chatbot.id)
      onDeleted()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Delete failed')
      setDeleting(false)
      setConfirmDelete(false)
    }
  }

  const save = async () => {
    setSaving(true)
    setError(null)
    try {
      const updated = await api.chatbots.update(chatbot.id, form)
      onUpdated(updated)
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Save failed')
    } finally {
      setSaving(false)
    }
  }

  const field = (label: string, key: keyof typeof form, type: 'input' | 'textarea' | 'select', opts?: string[]) => (
    <div style={{ marginBottom: '1.25rem' }}>
      <label style={{ display: 'block', fontWeight: 600, marginBottom: '0.35rem', fontSize: '0.9rem' }}>{label}</label>
      {type === 'textarea'
        ? <textarea
            value={form[key]}
            onChange={set(key)}
            rows={3}
            style={{ width: '100%', padding: '0.6rem', borderRadius: '8px', border: '1px solid #d1d5db', fontSize: '0.9rem', boxSizing: 'border-box' }}
          />
        : type === 'select'
        ? <select value={form[key]} onChange={set(key)} style={{ padding: '0.6rem', borderRadius: '8px', border: '1px solid #d1d5db', fontSize: '0.9rem' }}>
            {(opts ?? []).map(o => <option key={o} value={o}>{o}</option>)}
          </select>
        : <input
            value={form[key]}
            onChange={set(key)}
            style={{ width: '100%', padding: '0.6rem', borderRadius: '8px', border: '1px solid #d1d5db', fontSize: '0.9rem', boxSizing: 'border-box' }}
          />
      }
    </div>
  )

  return (
    <div style={{ maxWidth: '600px' }}>
      <h3 style={{ marginTop: 0 }}>Chatbot Settings</h3>
      {field('Name', 'name', 'input')}
      {field('Description', 'description', 'textarea')}
      {field('Tone', 'tone', 'select', TONES)}
      {field('Greeting message', 'greeting', 'input')}
      {field('Fallback message', 'fallback_message', 'input')}
      {field('Model', 'model', 'select', MODELS)}
      {error && <div style={{ color: '#dc2626', marginBottom: '1rem' }}>{error}</div>}
      <button
        onClick={save}
        disabled={saving}
        style={{
          padding: '0.65rem 1.5rem', background: saved ? '#16a34a' : '#2563eb',
          color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer', fontSize: '0.95rem',
        }}
      >
        {saving ? 'Saving…' : saved ? '✓ Saved' : 'Save Changes'}
      </button>

      <div style={{ marginTop: '3rem', paddingTop: '1.5rem', borderTop: '1px solid #fee2e2' }}>
        <h4 style={{ marginTop: 0, color: '#991b1b' }}>Danger Zone</h4>
        {confirmDelete ? (
          <div>
            <p style={{ color: '#7f1d1d', marginTop: 0 }}>
              This will permanently delete <strong>{chatbot.name}</strong> and all its documents, chat history, and embeddings. This cannot be undone.
            </p>
            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <button
                onClick={deleteChatbot}
                disabled={deleting}
                style={{ padding: '0.6rem 1.2rem', background: '#dc2626', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer' }}
              >{deleting ? 'Deleting…' : 'Yes, delete permanently'}</button>
              <button
                onClick={() => setConfirmDelete(false)}
                disabled={deleting}
                style={{ padding: '0.6rem 1.2rem', background: '#e5e7eb', color: '#374151', border: 'none', borderRadius: '8px', cursor: 'pointer' }}
              >Cancel</button>
            </div>
          </div>
        ) : (
          <button
            onClick={() => setConfirmDelete(true)}
            style={{ padding: '0.6rem 1.2rem', background: 'white', color: '#dc2626', border: '1px solid #dc2626', borderRadius: '8px', cursor: 'pointer' }}
          >Delete this chatbot</button>
        )}
      </div>
    </div>
  )
}
