import { BrowserRouter as Router } from 'react-router-dom'

export default function AppMinimal() {
  // Test if the issue is with CSS classes
  return (
    <Router>
      <div style={{ minHeight: '100vh', padding: '20px', background: 'white' }}>
        <h1>Testing CSS Classes:</h1>
        
        <div className="gradient-text" style={{ fontSize: '24px', marginBottom: '10px' }}>
          This should have gradient text (if CSS is working)
        </div>
        
        <div className="glass" style={{ padding: '20px', marginBottom: '10px' }}>
          This should have glass effect (if CSS is working)
        </div>
        
        <div className="modern-card" style={{ padding: '20px' }}>
          This should be a modern card (if CSS is working)
        </div>
        
        <div style={{ marginTop: '20px', padding: '10px', border: '1px solid #ccc' }}>
          <p>If you see styled elements above, CSS is working.</p>
          <p>If they look plain, there's a CSS issue.</p>
        </div>
      </div>
    </Router>
  )
}