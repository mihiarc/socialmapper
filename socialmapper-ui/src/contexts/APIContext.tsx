import { createContext, useContext, ReactNode, useMemo } from 'react'
import { SocialMapperAPIClient } from '@/services'
import { config } from '@/config'
import { useErrorHandler } from '@/hooks/useErrorHandler'

interface APIContextValue {
  client: SocialMapperAPIClient
}

const APIContext = createContext<APIContextValue | undefined>(undefined)

interface APIProviderProps {
  children: ReactNode
  apiUrl?: string
  apiKey?: string
}

export function APIProvider({ 
  children, 
  apiUrl,
  apiKey
}: APIProviderProps) {
  const { handleAPIError } = useErrorHandler()
  
  const client = useMemo(() => {
    // Check localStorage for API key if not provided via props
    const savedApiKey = localStorage.getItem('socialmapper_api_key')
    const effectiveApiKey = apiKey || savedApiKey || config.api.apiKey
    
    return new SocialMapperAPIClient({
      baseURL: apiUrl || config.api.baseURL,
      apiKey: effectiveApiKey,
      timeout: config.api.timeout,
      onError: (error) => {
        if (config.development.enableLogging) {
          console.error('API Error:', error)
        }
        handleAPIError(error)
      }
    })
  }, [apiUrl, apiKey, handleAPIError])

  return (
    <APIContext.Provider value={{ client }}>
      {children}
    </APIContext.Provider>
  )
}

export function useAPI() {
  const context = useContext(APIContext)
  if (!context) {
    throw new Error('useAPI must be used within APIProvider')
  }
  return context.client
}