interface Props {
  sources: string[]
}

export default function SourceCitations({ sources }: Props) {
  if (!sources.length) return null
  return (
    <div style={{
      fontSize: '0.78rem', color: '#6b7280',
      marginBottom: '0.75rem', paddingLeft: '1rem',
    }}>
      Sources: {sources.map((s, i) => (
        <span key={i} style={{
          background: '#f3f4f6', borderRadius: '4px',
          padding: '2px 6px', marginLeft: '4px',
        }}>{s}</span>
      ))}
    </div>
  )
}
