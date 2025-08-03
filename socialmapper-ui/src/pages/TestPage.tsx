export function TestPage() {
  return (
    <div style={{ padding: '20px', background: '#f0f0f0', minHeight: '100vh' }}>
      <h1 style={{ color: '#333', fontSize: '32px' }}>Test Page</h1>
      <p style={{ color: '#666' }}>If you can see this, React is working!</p>
      <div style={{ marginTop: '20px', padding: '10px', background: 'white', borderRadius: '8px' }}>
        <h2>Debug Info:</h2>
        <ul>
          <li>React: Working ✓</li>
          <li>Component: Rendered ✓</li>
          <li>Styles: Inline styles working ✓</li>
        </ul>
      </div>
    </div>
  )
}