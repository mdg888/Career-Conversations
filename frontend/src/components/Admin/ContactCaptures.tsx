import { useState, useEffect } from 'react'
import { api, ContactCapture } from '../../services/api'

export default function ContactCaptures({ chatbotId }: { chatbotId: string }) {
  const [contacts, setContacts] = useState<ContactCapture[]>([])

  useEffect(() => {
    api.contacts(chatbotId).then(setContacts).catch(console.error)
  }, [chatbotId])

  return (
    <div>
      <h3 style={{ marginTop: 0 }}>Captured Contacts</h3>
      {contacts.length === 0
        ? <p style={{ color: '#6b7280' }}>No contacts captured yet.</p>
        : (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
            <thead>
              <tr style={{ background: '#f3f4f6' }}>
                {['Name', 'Email', 'Notes', 'Captured'].map(h => (
                  <th key={h} style={{ padding: '0.6rem 1rem', textAlign: 'left', borderBottom: '1px solid #e5e7eb' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {contacts.map(c => (
                <tr key={c.id} style={{ borderBottom: '1px solid #e5e7eb' }}>
                  <td style={{ padding: '0.6rem 1rem' }}>{c.name ?? '—'}</td>
                  <td style={{ padding: '0.6rem 1rem' }}>{c.email}</td>
                  <td style={{ padding: '0.6rem 1rem', color: '#6b7280' }}>{c.notes ?? '—'}</td>
                  <td style={{ padding: '0.6rem 1rem', color: '#6b7280', whiteSpace: 'nowrap' }}>
                    {new Date(c.captured_at).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )
      }
    </div>
  )
}
