import { useState } from 'react'
import { api, Chatbot } from '../../services/api'

interface Props {
  chatbot: Chatbot
  onUpdated: (updated: Chatbot) => void
}

const TONES = ['professional', 'friendly', 'casual', 'formal', 'concise']
const MODELS = ['gpt-4o-mini', 'gpt-4o', 'gpt-4-turbo']

export default function ChatbotSettings({ chatbot, onUpdated }: Props) {
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

  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) =>
    setForm(prev => ({ ...prev, [k]: e.target.value }))

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
    </div>
  )
}
