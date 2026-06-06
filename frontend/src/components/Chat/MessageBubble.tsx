interface Props {
  role: 'user' | 'assistant'
  content: string
}

export default function MessageBubble({ role, content }: Props) {
  const isUser = role === 'user'
  return (
    <div style={{
      display: 'flex',
      justifyContent: isUser ? 'flex-end' : 'flex-start',
      marginBottom: '0.75rem',
    }}>
      <div style={{
        maxWidth: '75%',
        padding: '0.75rem 1rem',
        borderRadius: isUser ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
        background: isUser ? '#2563eb' : '#f3f4f6',
        color: isUser ? 'white' : '#111',
        fontSize: '0.95rem',
        lineHeight: 1.5,
        whiteSpace: 'pre-wrap',
      }}>
        {content}
      </div>
    </div>
  )
}
