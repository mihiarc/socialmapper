# SocialMapper Deployment Guide

This guide covers deployment options for the SocialMapper frontend-backend architecture.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Development Deployment](#development-deployment)
- [Production Deployment](#production-deployment)
- [Configuration](#configuration)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

## Prerequisites

- Docker and Docker Compose installed
- Census Bureau API key (get one free at https://api.census.gov/data/key_signup.html)
- (Optional) Mapbox token for enhanced maps

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/yourusername/socialmapper.git
cd socialmapper
```

2. Copy the environment template:
```bash
cp .env.example .env
```

3. Edit `.env` and add your Census API key:
```bash
CENSUS_API_KEY=your_actual_census_api_key
```

4. Build and start the services:
```bash
make build
make up
```

5. Access the application:
- Frontend: http://localhost
- API Documentation: http://localhost:8000/docs

## Development Deployment

For development with hot reload:

```bash
# Start development services
make up-dev

# View logs
make logs

# Run tests
make test

# Stop services
make down
```

The development setup includes:
- API with auto-reload on code changes
- Frontend with Vite hot module replacement
- Volume mounts for live code updates

## Production Deployment

### Using Docker Compose

1. Build production images:
```bash
make build
```

2. Start services:
```bash
docker-compose up -d
```

3. Check service health:
```bash
docker-compose ps
```

### Using Docker Swarm

1. Initialize swarm:
```bash
docker swarm init
```

2. Create secrets:
```bash
echo "your_census_api_key" | docker secret create census_api_key -
```

3. Deploy stack:
```bash
docker stack deploy -c docker-compose.yml socialmapper
```

### Using Kubernetes

See `k8s/` directory for Kubernetes manifests (coming soon).

## Configuration

### Backend Configuration

Environment variables for the API server:

| Variable | Description | Default |
|----------|-------------|---------|
| `SOCIALMAPPER_API_CORS_ORIGINS` | Allowed CORS origins | `http://localhost` |
| `SOCIALMAPPER_API_CENSUS_API_KEY` | Census Bureau API key | Required |
| `SOCIALMAPPER_API_RATE_LIMIT_PER_MINUTE` | Rate limit per client | `60` |
| `SOCIALMAPPER_API_API_AUTH_ENABLED` | Enable API key auth | `false` |
| `SOCIALMAPPER_API_API_KEYS` | Comma-separated API keys | Empty |
| `SOCIALMAPPER_API_MAX_CONCURRENT_JOBS` | Max concurrent analyses | `10` |
| `SOCIALMAPPER_API_RESULT_TTL_HOURS` | Result retention time | `24` |

### Frontend Configuration

Environment variables for the React app (build-time):

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_BASE_URL` | Backend API URL | `http://localhost:8000` |
| `VITE_API_TIMEOUT` | API request timeout (ms) | `300000` |
| `VITE_POLL_INTERVAL` | Job status poll interval (ms) | `2000` |
| `VITE_MAX_FILE_SIZE_MB` | Max upload file size | `10` |
| `VITE_DEFAULT_MAP_LAT` | Default map latitude | `45.5152` |
| `VITE_DEFAULT_MAP_LNG` | Default map longitude | `-122.6784` |
| `VITE_ENABLE_BATCH_ANALYSIS` | Enable batch processing | `false` |

### API Authentication

To enable API key authentication:

1. Set `SOCIALMAPPER_API_API_AUTH_ENABLED=true`
2. Add API keys to `SOCIALMAPPER_API_API_KEYS` (comma-separated)
3. Clients must include `X-API-Key` header in requests

### SSL/TLS Configuration

For production, use a reverse proxy (nginx, traefik) with SSL certificates:

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:80;
    }
}
```

## Monitoring

### Health Checks

- API Health: `GET /api/v1/health`
- API Status: `GET /api/v1/status`

### Logging

View logs:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f ui
```

### Metrics

The API exposes rate limiting headers:
- `X-RateLimit-Limit`: Request limit per minute
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Reset timestamp

## Scaling

### Horizontal Scaling

Scale the API service:
```bash
docker-compose up -d --scale api=3
```

For production scaling, use:
- Docker Swarm with replicas
- Kubernetes with HPA
- Load balancer (nginx, HAProxy)

### Database Backend

For production workloads, add PostgreSQL:

1. Uncomment database service in `docker-compose.yml`
2. Set database environment variables
3. Update API to use database for job storage

### Caching

Add Redis for improved performance:

1. Uncomment Redis service in `docker-compose.yml`
2. Configure API to use Redis for:
   - Rate limiting state
   - Analysis result caching
   - Job queue management

## Backup and Recovery

### Data Backup

Backup analysis results:
```bash
docker run --rm -v socialmapper_api-results:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/results-$(date +%Y%m%d).tar.gz -C /data .
```

### Restore Data

```bash
docker run --rm -v socialmapper_api-results:/data \
  -v $(pwd)/backups:/backup \
  alpine tar xzf /backup/results-20240115.tar.gz -C /data
```

## Troubleshooting

### Common Issues

1. **API not accessible**
   - Check if services are running: `docker-compose ps`
   - Verify port mappings: `docker port socialmapper-api`
   - Check logs: `docker-compose logs api`

2. **CORS errors**
   - Verify `SOCIALMAPPER_API_CORS_ORIGINS` includes your frontend URL
   - Check browser console for specific CORS error

3. **Rate limiting**
   - Check `X-RateLimit-*` headers in response
   - Increase `SOCIALMAPPER_API_RATE_LIMIT_PER_MINUTE` if needed

4. **Analysis failures**
   - Verify Census API key is valid
   - Check API logs for specific errors
   - Ensure sufficient system resources

### Debug Mode

Enable debug logging:
```bash
# API
docker-compose exec api sh
export LOG_LEVEL=DEBUG
# Restart the service

# Frontend
# Open browser developer tools
localStorage.setItem('debug', 'socialmapper:*')
```

### Performance Tuning

1. **API Performance**
   - Increase worker processes in Dockerfile
   - Add Redis for caching
   - Use PostgreSQL for job persistence

2. **Frontend Performance**
   - Enable CDN for static assets
   - Configure nginx caching headers
   - Use production build (`npm run build`)

## Security Considerations

1. **API Security**
   - Enable API key authentication for production
   - Use HTTPS with valid certificates
   - Implement request signing for sensitive operations

2. **Network Security**
   - Use Docker networks to isolate services
   - Configure firewall rules
   - Limit exposed ports

3. **Data Security**
   - Encrypt sensitive data at rest
   - Use secure environment variable management
   - Regular security updates

## Support

For issues and questions:
- Check the [documentation](./docs)
- Open an issue on GitHub
- Contact the development team