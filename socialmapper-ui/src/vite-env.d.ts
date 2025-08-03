/// <reference types="vite/client" />

interface ImportMetaEnv {
  // API Configuration
  readonly VITE_API_URL: string
  readonly VITE_API_KEY?: string
  readonly VITE_API_TIMEOUT?: string
  readonly VITE_API_RETRY_ATTEMPTS?: string
  readonly VITE_API_RETRY_DELAY?: string

  // Feature Flags
  readonly VITE_ENABLE_CUSTOM_POIS?: string
  readonly VITE_ENABLE_BATCH_ANALYSIS?: string
  readonly VITE_ENABLE_ADVANCED_FILTERS?: string
  readonly VITE_ENABLE_EXPERIMENTAL?: string

  // Map Configuration
  readonly VITE_MAP_CENTER_LAT?: string
  readonly VITE_MAP_CENTER_LNG?: string
  readonly VITE_MAP_DEFAULT_ZOOM?: string
  readonly VITE_MAP_MIN_ZOOM?: string
  readonly VITE_MAP_MAX_ZOOM?: string
  readonly VITE_MAP_TILE_PROVIDER?: string
  readonly VITE_MAPBOX_TOKEN?: string

  // UI Configuration
  readonly VITE_UI_THEME?: string
  readonly VITE_UI_DATE_FORMAT?: string
  readonly VITE_UI_NUMBER_FORMAT?: string
  readonly VITE_UI_MAX_TOAST_MESSAGES?: string
  readonly VITE_UI_TOAST_DURATION?: string

  // Analysis Configuration
  readonly VITE_ANALYSIS_DEFAULT_TRAVEL_TIME?: string
  readonly VITE_ANALYSIS_MAX_TRAVEL_TIME?: string
  readonly VITE_ANALYSIS_DEFAULT_TRAVEL_MODE?: string
  readonly VITE_ANALYSIS_POLLING_INTERVAL?: string
  readonly VITE_ANALYSIS_MAX_POLLING_ATTEMPTS?: string

  // Development Configuration
  readonly VITE_DEV_ENABLE_DEVTOOLS?: string
  readonly VITE_DEV_ENABLE_LOGGING?: string
  readonly VITE_DEV_LOG_LEVEL?: string
  readonly VITE_DEV_MOCK_API?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}