import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
// import AppMinimal from './AppMinimal.tsx'
import './index.css'

console.log('Main.tsx loaded - switching back to full App')

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)