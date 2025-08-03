# API Authentication and Rate Limiting

This document describes the authentication and rate limiting features of the SocialMapper API.

## Authentication

### Overview

The SocialMapper API supports optional API key authentication. When enabled, clients must provide a valid API key in the `X-API-Key` header for all requests (except public endpoints).

### Configuration

Authentication is configured through environment variables:

```bash
# Enable/disable authentication (default: false)
SOCIALMAPPER_API_AUTH_ENABLED=true

# Comma-separated list of valid API keys
SOCIALMAPPER_API_KEYS=key1,key2,key3
```

### Public Endpoints

The following endpoints do not require authentication:
- `/api/v1/health` - Health check
- `/api/v1/status` - Server status
- `/docs` - API documentation
- `/redoc` - Alternative API documentation
- `/openapi.json` - OpenAPI schema

### Using API Keys

#### Backend (Python)
```python
import httpx

headers = {"X-API-Key": "your-api-key"}
response = httpx.get("http://localhost:8000/api/v1/census/variables", headers=headers)
```

#### Frontend (JavaScript/TypeScript)
```typescript
const client = new SocialMapperAPIClient({
  baseURL: 'http://localhost:8000',
  apiKey: 'your-api-key'
});
```

#### cURL
```bash
curl -H "X-API-Key: your-api-key" http://localhost:8000/api/v1/census/variables
```

### Error Responses

When authentication fails, the API returns a 401 Unauthorized response:

```json
{
  "error_code": "AUTHENTICATION_ERROR",
  "message": "API key required. Please provide a valid API key in the X-API-Key header.",
  "timestamp": "2024-01-20T10:30:45.123456",
  "auth_method": "api_key"
}
```

## Rate Limiting

### Overview

The API implements rate limiting to prevent abuse and ensure fair usage. By default, clients are limited to 60 requests per minute.

### Configuration

Rate limiting is configured through environment variables:

```bash
# Maximum requests per minute per client (default: 60)
SOCIALMAPPER_API_RATE_LIMIT_PER_MINUTE=60
```

### Rate Limit Headers

All API responses include rate limit information in headers:

- `X-RateLimit-Limit` - Maximum requests allowed per minute
- `X-RateLimit-Remaining` - Remaining requests in current window
- `X-RateLimit-Reset` - Unix timestamp when the rate limit resets
- `Retry-After` - Seconds to wait before retrying (only on 429 responses)

Example:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1705745460
```

### Rate Limit Exceeded

When the rate limit is exceeded, the API returns a 429 Too Many Requests response:

```json
{
  "error_code": "RATE_LIMIT_ERROR",
  "message": "Rate limit exceeded. Please try again later.",
  "limit": 60,
  "window_seconds": 60,
  "retry_after_seconds": 30,
  "remaining_requests": 0,
  "timestamp": "2024-01-20T10:30:45.123456"
}
```

### Client IP Detection

The rate limiter identifies clients by IP address, checking in order:
1. `X-Forwarded-For` header (for proxies/load balancers)
2. `X-Real-IP` header
3. Direct client IP

## Frontend Configuration

The React frontend includes a Settings page where users can configure their API key:

1. Navigate to `/settings` in the application
2. Enter your API key (optional)
3. Toggle authentication on/off
4. Configure rate limits (informational only)
5. Save settings

Settings are stored in browser localStorage and automatically applied to all API requests.

## Testing

Use the provided test script to verify authentication and rate limiting:

```bash
cd socialmapper-api
python test_auth_rate_limit.py
```

The test script will:
- Test API access without authentication
- Test API access with authentication
- Trigger rate limiting by making rapid requests
- Show rate limit headers

## Security Considerations

1. **API Key Storage**: In production, store API keys securely:
   - Use environment variables or secure key management services
   - Never commit API keys to version control
   - Rotate keys regularly

2. **HTTPS**: Always use HTTPS in production to prevent API key interception

3. **Key Generation**: Use cryptographically secure methods to generate API keys:
   ```python
   import secrets
   api_key = secrets.token_urlsafe(32)
   ```

4. **Rate Limiting**: Consider implementing:
   - Per-API-key rate limits
   - Different limits for authenticated vs anonymous users
   - IP-based blocking for persistent abuse

## Future Enhancements

Potential improvements for production use:

1. **Database Storage**: Store API keys in a database with metadata:
   - User/organization association
   - Permissions/scopes
   - Creation/expiration dates
   - Usage statistics

2. **OAuth 2.0**: Implement OAuth for more robust authentication

3. **JWT Tokens**: Use JSON Web Tokens for stateless authentication

4. **Redis Cache**: Use Redis for distributed rate limiting across multiple servers

5. **Webhook Support**: Add webhooks for long-running analysis jobs

6. **API Key Management UI**: Build admin interface for key management