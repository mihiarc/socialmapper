import { useState, useEffect } from 'react'
import { Settings, Key, Save, AlertCircle, CheckCircle, Eye, EyeOff } from 'lucide-react'
import { config } from '@/config'

export function SettingsPage() {
  const [apiKey, setApiKey] = useState('')
  const [showApiKey, setShowApiKey] = useState(false)
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle')
  const [rateLimit, setRateLimit] = useState(60)
  const [authEnabled, setAuthEnabled] = useState(false)

  useEffect(() => {
    // Load settings from localStorage
    const savedApiKey = localStorage.getItem('socialmapper_api_key') || ''
    const savedRateLimit = localStorage.getItem('socialmapper_rate_limit') || '60'
    const savedAuthEnabled = localStorage.getItem('socialmapper_auth_enabled') === 'true'
    
    setApiKey(savedApiKey)
    setRateLimit(parseInt(savedRateLimit))
    setAuthEnabled(savedAuthEnabled)
  }, [])

  const handleSave = () => {
    setSaveStatus('saving')
    
    try {
      // Save to localStorage
      localStorage.setItem('socialmapper_api_key', apiKey)
      localStorage.setItem('socialmapper_rate_limit', rateLimit.toString())
      localStorage.setItem('socialmapper_auth_enabled', authEnabled.toString())
      
      // Reload the page to apply new settings
      setTimeout(() => {
        setSaveStatus('saved')
        setTimeout(() => {
          window.location.reload()
        }, 1000)
      }, 500)
    } catch (error) {
      console.error('Failed to save settings:', error)
      setSaveStatus('error')
      setTimeout(() => setSaveStatus('idle'), 3000)
    }
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center space-x-3">
        <Settings className="w-8 h-8 text-primary-600 dark:text-primary-400" />
        <h1 className="text-3xl font-display font-bold gradient-text">Settings</h1>
      </div>

      <div className="grid gap-6 max-w-2xl">
        {/* API Configuration */}
        <div className="card glow-effect">
          <div className="flex items-center space-x-2 mb-6">
            <Key className="w-6 h-6 text-primary-600 dark:text-primary-400" />
            <h2 className="text-xl font-semibold">API Configuration</h2>
          </div>

          <div className="space-y-4">
            {/* API Key */}
            <div>
              <label htmlFor="api-key" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                API Key
              </label>
              <div className="relative">
                <input
                  id="api-key"
                  type={showApiKey ? 'text' : 'password'}
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="Enter your API key (optional)"
                  className="input pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowApiKey(!showApiKey)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center"
                >
                  {showApiKey ? (
                    <EyeOff className="w-5 h-5 text-gray-400 hover:text-gray-600" />
                  ) : (
                    <Eye className="w-5 h-5 text-gray-400 hover:text-gray-600" />
                  )}
                </button>
              </div>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                Optional: Add an API key for enhanced features and higher rate limits
              </p>
            </div>

            {/* Authentication Toggle */}
            <div>
              <label className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  checked={authEnabled}
                  onChange={(e) => setAuthEnabled(e.target.checked)}
                  className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                />
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Enable API authentication
                </span>
              </label>
              <p className="mt-1 ml-7 text-sm text-gray-500 dark:text-gray-400">
                Require API key for all requests (backend must be configured to enforce this)
              </p>
            </div>

            {/* Rate Limit */}
            <div>
              <label htmlFor="rate-limit" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Rate Limit (requests per minute)
              </label>
              <input
                id="rate-limit"
                type="number"
                min="1"
                max="300"
                value={rateLimit}
                onChange={(e) => setRateLimit(parseInt(e.target.value) || 60)}
                className="input w-32"
              />
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                Maximum requests per minute (default: 60)
              </p>
            </div>
          </div>
        </div>

        {/* Current Configuration */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Current Configuration</h3>
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between">
              <dt className="text-gray-600 dark:text-gray-400">API Base URL:</dt>
              <dd className="font-mono text-gray-900 dark:text-gray-100">{config.api.baseURL}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-600 dark:text-gray-400">API Timeout:</dt>
              <dd className="font-mono text-gray-900 dark:text-gray-100">{config.api.timeout / 1000}s</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-600 dark:text-gray-400">Poll Interval:</dt>
              <dd className="font-mono text-gray-900 dark:text-gray-100">{config.analysis.pollingInterval / 1000}s</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-600 dark:text-gray-400">API Key Source:</dt>
              <dd className="text-gray-900 dark:text-gray-100">
                {apiKey ? 'Local Storage' : config.api.apiKey ? 'Environment Variable' : 'Not Set'}
              </dd>
            </div>
          </dl>
        </div>

        {/* Save Button */}
        <div className="flex items-center justify-between">
          <button
            onClick={handleSave}
            disabled={saveStatus === 'saving'}
            className={`btn flex items-center space-x-2 ${
              saveStatus === 'saved' ? 'btn-success' : 
              saveStatus === 'error' ? 'btn-danger' : 
              'btn-primary'
            }`}
          >
            {saveStatus === 'saving' ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                <span>Saving...</span>
              </>
            ) : saveStatus === 'saved' ? (
              <>
                <CheckCircle className="w-5 h-5" />
                <span>Saved! Reloading...</span>
              </>
            ) : saveStatus === 'error' ? (
              <>
                <AlertCircle className="w-5 h-5" />
                <span>Error saving</span>
              </>
            ) : (
              <>
                <Save className="w-5 h-5" />
                <span>Save Settings</span>
              </>
            )}
          </button>

          {saveStatus === 'idle' && apiKey && (
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Settings will be applied after save
            </p>
          )}
        </div>
      </div>
    </div>
  )
}