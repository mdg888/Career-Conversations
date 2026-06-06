import { useState, useEffect } from 'react'
import { api, Chatbot } from '../../services/api'
import DocumentUpload from './DocumentUpload'
import ChatbotSettings from './ChatbotSettings'
import ContactCaptures from './ContactCaptures'

interface Props {
  chatbot: Chatbot
  onChatbotUpdated: (updated: Chatbot) => void
  onChatbotDeleted: () => void
}

type Tab = 'documents' | 'settings' | 'contacts' | 'questions'

export default function Dashboard({ chatbot, onChatbotUpdated, onChatbotDeleted }: Props) {
  const [tab, setTab] = useState<Tab>('documents')
  const [unknownQuestions, setUnknownQuestions] = useState<{ id: string; question: string; asked_at: string }[]>([])

  useEffect(() => {
    if (tab === 'questions') {
      api.unknownQuestions(chatbot.id).then(setUnknownQuestions).catch(console.error)
    }
  }, [tab, chatbot.id])

  const tabs: { key: Tab; label: string }[] = [
    { key: 'documents', label: 'Documents' },
    { key: 'settings', label: 'Settings' },
    { key: 'contacts', label: 'Contacts' },
    { key: 'questions', label: 'Unknown Questions' },
  ]

  return (
    <div>
      <div style={{ display: 'flex', gap: '0.5rem', borderBottom: '2px solid #e5e7eb', marginBottom: '1.5rem' }}>
        {tabs.map(t => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            style={{
              padding: '0.6rem 1.2rem',
              border: 'none',
              background: 'none',
              cursor: 'pointer',
              fontWeight: tab === t.key ? 700 : 400,
              borderBottom: tab === t.key ? '2px solid #2563eb' : '2px solid transparent',
              color: tab === t.key ? '#2563eb' : '#6b7280',
              marginBottom: '-2px',
              fontSize: '0.9rem',
            }}
          >{t.label}</button>
        ))}
      </div>

      {tab === 'documents' && <DocumentUpload chatbot={chatbot} />}
      {tab === 'settings' && <ChatbotSettings key={chatbot.id} chatbot={chatbot} onUpdated={onChatbotUpdated} onDeleted={onChatbotDeleted} />}
      {tab === 'contacts' && <ContactCaptures chatbotId={chatbot.id} />}
      {tab === 'questions' && (
        <div>
          <h3 style={{ marginTop: 0 }}>Unanswered Questions</h3>
          {unknownQuestions.length === 0
            ? <p style={{ color: '#6b7280' }}>No unanswered questions yet.</p>
            : unknownQuestions.map(q => (
              <div key={q.id} style={{
                padding: '0.75rem', marginBottom: '0.5rem',
                background: '#fef9c3', borderRadius: '8px', border: '1px solid #fde68a',
              }}>
                <div style={{ fontWeight: 500 }}>{q.question}</div>
                <div style={{ fontSize: '0.75rem', color: '#92400e', marginTop: '0.25rem' }}>
                  {new Date(q.asked_at).toLocaleString()}
                </div>
              </div>
            ))
          }
        </div>
      )}
    </div>
  )
}
