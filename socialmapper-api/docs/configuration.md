# SocialMapper Configuration Guide

This guide covers configuration for both the backend API server and frontend UI application.

## Backend Configuration (API Server)

The backend uses environment variables with the prefix `SOCIALMAPPER_API_`. Configuration is managed through Pydantic settings.

### Configuration File

Create a `.env` file in the `socialmapper-api` directory based on `.env.example`:

```bash
cp .env.example .env
```

### Environment Variables

#### Essential Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SOCIALMAPPER_API_CENSUS_API_KEY` | Census Bureau API key | - | Yes |
| `SOCIALMAPPER_API_CORS_ORIGINS` | Allowed CORS origins (comma-separated) | `http://localhost:5173,http://localhost:3000,http://localhost:8501` | No |

#### Server Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `SOCIALMAPPER_API_HOST` | Server host | `0.0.0.0` |
| `SOCIALMAPPER_API_PORT` | Server port | `8000` |
| `SOCIALMAPPER_API_API_TITLE` | API title | `SocialMapper API` |
| `SOCIALMAPPER_API_API_VERSION` | API version | `0.1.0` |

#### Job Processing

| Variable | Description | Default |
|----------|-------------|---------|
| `SOCIALMAPPER_API_MAX_CONCURRENT_JOBS` | Maximum concurrent analysis jobs | `10` |
| `SOCIALMAPPER_API_RESULT_TTL_HOURS` | Result time-to-live in hours | `24` |
| `SOCIALMAPPER_API_CLEANUP_INTERVAL_MINUTES` | Cleanup scheduler interval | `60` |

#### API Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `SOCIALMAPPER_API_RATE_LIMIT_PER_MINUTE` | Rate limit per client | `60` |
| `SOCIALMAPPER_API_API_AUTH_ENABLED` | Enable API key authentication | `false` |
| `SOCIALMAPPER_API_API_KEYS` | Valid API keys (comma-separated) | - |
| `SOCIALMAPPER_API_RESULT_STORAGE_PATH` | Result storage path | `./results` |

#### External APIs

| Variable | Description | Default |
|----------|-------------|---------|
| `SOCIALMAPPER_API_OSM_API_TIMEOUT` | OpenStreetMap API timeout (seconds) | `30` |
| `SOCIALMAPPER_API_CENSUS_API_TIMEOUT` | Census API timeout (seconds) | `30` |

#### Analysis Limits

| Variable | Description | Default |
|----------|-------------|---------|
| `SOCIALMAPPER_API_DEFAULT_TRAVEL_TIME_MINUTES` | Default travel time | `15` |
| `SOCIALMAPPER_API_MAX_TRAVEL_TIME_MINUTES` | Maximum travel time | `60` |
| `SOCIALMAPPER_API_MAX_POI_TYPES_PER_REQUEST` | Maximum POI types per request | `10` |
| `SOCIALMAPPER_API_MAX_CENSUS_VARIABLES_PER_REQUEST` | Maximum census variables | `20` |

#### Development

| Variable | Description | Default |
|----------|-------------|---------|
| `SOCIALMAPPER_API_DEBUG_MODE` | Enable debug mode | `false` |
| `SOCIALMAPPER_API_LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | `INFO` |

## Frontend Configuration (UI)

The frontend uses Vite environment variables with the prefix `VITE_`.

### Configuration File

Create a `.env` file in the `socialmapper-ui` directory:

```bash
cp .env.example .env
```

### Environment Variables

#### API Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `VITE_API_URL` | Backend API URL | `http://localhost:8000` | Yes |
| `VITE_API_KEY` | API key (if auth enabled) | - | No |
| `VITE_API_TIMEOUT` | API request timeout (ms) | `30000` | No |
| `VITE_API_RETRY_ATTEMPTS` | Retry attempts for failed requests | `3` | No |
| `VITE_API_RETRY_DELAY` | Delay between retries (ms) | `1000` | No |

#### Feature Flags

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_ENABLE_CUSTOM_POIS` | Enable custom POI upload | `true` |
| `VITE_ENABLE_BATCH_ANALYSIS` | Enable batch analysis | `true` |
| `VITE_ENABLE_ADVANCED_FILTERS` | Enable advanced filters | `false` |
| `VITE_ENABLE_EXPERIMENTAL` | Enable experimental features | `false` |

#### Map Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_MAP_CENTER_LAT` | Default map center latitude | `40.7128` |
| `VITE_MAP_CENTER_LNG` | Default map center longitude | `-74.0060` |
| `VITE_MAP_DEFAULT_ZOOM` | Default zoom level | `10` |
| `VITE_MAP_MIN_ZOOM` | Minimum zoom level | `3` |
| `VITE_MAP_MAX_ZOOM` | Maximum zoom level | `18` |
| `VITE_MAP_TILE_PROVIDER` | Tile provider (openstreetmap, mapbox, stadia) | `openstreetmap` |
| `VITE_MAPBOX_TOKEN` | Mapbox token (required if using mapbox) | - |

#### UI Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_UI_THEME` | UI theme (light, dark, system) | `system` |
| `VITE_UI_DATE_FORMAT` | Date format | `MM/DD/YYYY` |
| `VITE_UI_NUMBER_FORMAT` | Number format locale | `en-US` |
| `VITE_UI_MAX_TOAST_MESSAGES` | Maximum toast messages | `5` |
| `VITE_UI_TOAST_DURATION` | Toast duration (ms) | `5000` |

#### Analysis Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_ANALYSIS_DEFAULT_TRAVEL_TIME` | Default travel time (minutes) | `15` |
| `VITE_ANALYSIS_MAX_TRAVEL_TIME` | Maximum travel time (minutes) | `60` |
| `VITE_ANALYSIS_DEFAULT_TRAVEL_MODE` | Default mode (walk, bike, drive, transit) | `walk` |
| `VITE_ANALYSIS_POLLING_INTERVAL` | Job polling interval (ms) | `2000` |
| `VITE_ANALYSIS_MAX_POLLING_ATTEMPTS` | Maximum polling attempts | `300` |

#### Development

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_DEV_ENABLE_DEVTOOLS` | Enable development tools | `true` |
| `VITE_DEV_ENABLE_LOGGING` | Enable console logging | `true` |
| `VITE_DEV_LOG_LEVEL` | Log level (debug, info, warn, error) | `info` |
| `VITE_DEV_MOCK_API` | Use mock API | `false` |

## Configuration Validation

Both frontend and backend include configuration validation:

### Backend Validation

The backend uses Pydantic for validation. Invalid configuration will prevent server startup with clear error messages.

### Frontend Validation

The frontend uses Zod for runtime validation. Configuration errors are caught by the `ConfigErrorBoundary` component, which displays:

- Detailed error messages
- Configuration warnings
- Options to reset configuration or view documentation

### Health Checks

The frontend provides configuration health checks:

```typescript
import { configHealthCheck } from '@/config';

if (!configHealthCheck.valid) {
  console.error('Configuration errors:', configHealthCheck.errors);
}

if (configHealthCheck.warnings.length > 0) {
  console.warn('Configuration warnings:', configHealthCheck.warnings);
}
```

## Production Deployment

### Backend

1. Set production values in environment:
   ```bash
   export SOCIALMAPPER_API_DEBUG_MODE=false
   export SOCIALMAPPER_API_LOG_LEVEL=WARNING
   export SOCIALMAPPER_API_API_AUTH_ENABLED=true
   export SOCIALMAPPER_API_API_KEYS=your-secure-api-keys
   ```

2. Use a secrets manager for sensitive values like API keys

### Frontend

1. Build with production environment:
   ```bash
   VITE_API_URL=https://api.socialmapper.com npm run build
   ```

2. Ensure feature flags are set appropriately for production

## Troubleshooting

### Configuration Not Loading

1. Check file location (`.env` in project root)
2. Verify variable naming (correct prefix)
3. Check for syntax errors in `.env` file

### Validation Errors

1. Review error messages in console/logs
2. Check type constraints (numbers, URLs, etc.)
3. Verify required fields are present

### CORS Issues

1. Ensure frontend URL is in `SOCIALMAPPER_API_CORS_ORIGINS`
2. Include protocol (http/https) in origins
3. Restart backend after changing CORS settings