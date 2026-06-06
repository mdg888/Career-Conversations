import { useState, useEffect, useRef } from 'react'
import { api, Document, Chatbot } from '../../services/api'

const ALLOWED = ['txt', 'pdf', 'docx', 'md', 'png', 'jpg', 'jpeg', 'webp', 'tiff']

interface Props {
  chatbot: Chatbot
}

export default function DocumentUpload({ chatbot }: Props) {
  const [docs, setDocs] = useState<Document[]>([])
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  const load = () => api.documents.list(chatbot.id).then(setDocs).catch(console.error)

  useEffect(() => { load() }, [chatbot.id])

  const upload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    const ext = file.name.split('.').pop()?.toLowerCase() ?? ''
    if (!ALLOWED.includes(ext)) {
      setError(`Unsupported type .${ext}. Allowed: ${ALLOWED.join(', ')}`)
      return
    }
    setError(null)
    setUploading(true)
    try {
      await api.documents.upload(chatbot.id, file)
      await load()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Upload failed')
    } finally {
      setUploading(false)
      if (fileRef.current) fileRef.current.value = ''
    }
  }

  const remove = async (docId: string) => {
    await api.documents.delete(chatbot.id, docId)
    await load()
  }

  const rebuild = async (docId: string) => {
    await api.documents.rebuild(chatbot.id, docId)
    await load()
  }

  const statusColor = (s: string) =>
    s === 'ready' ? '#16a34a' : s === 'failed' ? '#dc2626' : '#d97706'

  return (
    <div>
      <h3 style={{ marginTop: 0 }}>Knowledge Base Documents</h3>
      <div style={{ marginBottom: '1rem' }}>
        <label style={{
          display: 'inline-block', padding: '0.6rem 1.2rem',
          background: uploading ? '#93c5fd' : '#2563eb',
          color: 'white', borderRadius: '8px', cursor: uploading ? 'not-allowed' : 'pointer',
          fontSize: '0.9rem',
        }}>
          {uploading ? 'Uploading…' : '+ Upload Document'}
          <input
            ref={fileRef}
            type="file"
            accept={ALLOWED.map(e => `.${e}`).join(',')}
            onChange={upload}
            disabled={uploading}
            style={{ display: 'none' }}
          />
        </label>
        <span style={{ marginLeft: '0.75rem', fontSize: '0.8rem', color: '#6b7280' }}>
          Supported: {ALLOWED.join(', ')} · Max 20 MB
        </span>
      </div>
      {error && <div style={{ color: '#dc2626', marginBottom: '1rem' }}>{error}</div>}
      {docs.length === 0
        ? <p style={{ color: '#6b7280' }}>No documents uploaded yet. Upload files to build the knowledge base.</p>
        : docs.map(doc => (
          <div key={doc.id} style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            padding: '0.75rem 1rem', marginBottom: '0.5rem',
            background: '#f9fafb', borderRadius: '8px', border: '1px solid #e5e7eb',
          }}>
            <div>
              <span style={{ fontWeight: 500 }}>{doc.filename}</span>
              <span style={{
                marginLeft: '0.75rem', fontSize: '0.75rem',
                color: statusColor(doc.status), fontWeight: 600,
              }}>● {doc.status}</span>
              {doc.error && <div style={{ fontSize: '0.75rem', color: '#dc2626' }}>{doc.error}</div>}
            </div>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              {doc.status === 'failed' && (
                <button onClick={() => rebuild(doc.id)} style={{
                  padding: '0.3rem 0.7rem', background: '#fef3c7',
                  border: '1px solid #fbbf24', borderRadius: '6px', cursor: 'pointer', fontSize: '0.8rem',
                }}>Rebuild</button>
              )}
              <button onClick={() => remove(doc.id)} style={{
                padding: '0.3rem 0.7rem', background: '#fee2e2',
                border: '1px solid #fca5a5', borderRadius: '6px', cursor: 'pointer', fontSize: '0.8rem',
                color: '#991b1b',
              }}>Delete</button>
            </div>
          </div>
        ))
      }
    </div>
  )
}
