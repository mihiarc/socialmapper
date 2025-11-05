# SocialMapper Deployment Guide

Complete guide for deploying SocialMapper in various environments from local development to production cloud platforms.

## Table of Contents

- [Local Development](#local-development)
- [Docker Deployment](#docker-deployment)
- [Cloud Deployment](#cloud-deployment)
  - [AWS](#aws-deployment)
  - [Google Cloud Platform](#google-cloud-platform)
  - [Microsoft Azure](#microsoft-azure)
- [Production Configuration](#production-configuration)
- [Environment Variables](#environment-variables)
- [Monitoring & Observability](#monitoring--observability)
- [Scaling Considerations](#scaling-considerations)
- [Troubleshooting](#troubleshooting)

---

## Local Development

### Setting Up Development Environment

#### Prerequisites

- Python 3.11 or higher (3.11, 3.12, 3.13 supported)
- pip or uv package manager
- Census API key (free from https://api.census.gov/data/key_signup.html)
- Git

#### Installation Steps

```bash
# 1. Clone the repository
git clone https://github.com/mihiarc/socialmapper.git
cd socialmapper

# 2. Create virtual environment (using uv - recommended)
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Or using standard venv
python -m venv .venv
source .venv/bin/activate

# 3. Install SocialMapper in development mode
uv pip install -e .

# Or using pip
pip install -e .

# 4. Verify installation
uv run python -c "import socialmapper; print(socialmapper.__version__)"
```

### Environment Configuration

Create a `.env` file in your project root:

```bash
# Copy example environment file
cp .env.example .env

# Edit with your credentials
# Required
CENSUS_API_KEY=your_census_api_key_here

# Optional
MAPBOX_ACCESS_TOKEN=your_mapbox_token_here
SOCIALMAPPER_DEFAULT_MAP_LAT=45.5152
SOCIALMAPPER_DEFAULT_MAP_LNG=-122.6784
SOCIALMAPPER_DEFAULT_MAP_ZOOM=12
```

### Running Locally with Demo Mode

SocialMapper includes demo data for testing without API keys:

```python
from socialmapper import demo

# Run quick start demo (no API key required)
result = demo.quick_start("Portland, OR")
print(f"Found {result['poi_count']} libraries")
print(f"Population: {result['total_population']:,}")

# List available demo locations
demo.list_available_demos()
```

### Running with Real API Keys

```python
from socialmapper import (
    create_isochrone,
    get_census_blocks,
    get_census_data,
    get_poi,
    create_map
)

# Create isochrone
iso = create_isochrone(
    location=(45.5152, -122.6784),
    travel_time=15,
    travel_mode="drive"
)

# Get census data
blocks = get_census_blocks(polygon=iso)
geoids = [b['geoid'] for b in blocks]
census_data = get_census_data(
    location=geoids,
    variables=["population", "median_income"],
    year=2023
)

# Create visualization
for block in blocks:
    geoid = block['geoid']
    block['population'] = census_data.data.get(
        geoid, {}
    ).get('population', 0)

map_result = create_map(
    data=blocks,
    column='population',
    title='Population Distribution',
    save_path='population_map.png'
)
```

---

## Docker Deployment

### Basic Dockerfile

Create a `Dockerfile` in your project root:

```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libgeos-dev \
    libgdal-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster package installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy application files
COPY . .

# Install Python dependencies
RUN uv pip install --system -e .

# Create cache directory with proper permissions
RUN mkdir -p /app/cache && chmod 777 /app/cache

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV SOCIALMAPPER_CACHE_DIR=/app/cache

# Expose port for web services (if applicable)
EXPOSE 8000

# Run your application
CMD ["python", "-m", "your_app"]
```

### Docker Compose Setup

Create a `docker-compose.yml` file:

```yaml
version: '3.8'

services:
  socialmapper:
    build: .
    container_name: socialmapper-app
    environment:
      - CENSUS_API_KEY=${CENSUS_API_KEY}
      - MAPBOX_ACCESS_TOKEN=${MAPBOX_ACCESS_TOKEN}
      - SOCIALMAPPER_CACHE_DIR=/app/cache
      # Performance configuration
      - SOCIALMAPPER_PERFORMANCE_PRESET=balanced
      - SOCIALMAPPER_NETWORK_CACHE_SIZE_GB=5
      - SOCIALMAPPER_GEOCODING_CACHE_SIZE_MB=500
      - SOCIALMAPPER_CENSUS_CACHE_SIZE_MB=250
    volumes:
      # Mount cache directory for persistence
      - ./cache:/app/cache
      # Mount your application code (for development)
      - ./your_app:/app/your_app
    ports:
      - "8000:8000"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import socialmapper"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  cache:
    driver: local
```

### Building and Running with Docker

```bash
# Build the image
docker build -t socialmapper-app:latest .

# Run with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f socialmapper

# Stop services
docker-compose down

# Stop and remove volumes (clears cache)
docker-compose down -v
```

### Docker Best Practices

1. **Use Multi-Stage Builds** for smaller images:

```dockerfile
# Build stage
FROM python:3.11-slim AS builder
WORKDIR /build
COPY . .
RUN pip install --user -e .

# Runtime stage
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
```

2. **Cache Dependencies** separately:

```dockerfile
# Copy only requirements first
COPY pyproject.toml .
RUN uv pip install --system .

# Then copy application code
COPY . .
```

3. **Use .dockerignore** to exclude unnecessary files:

```text
.git
.venv
__pycache__
*.pyc
.env
.DS_Store
*.log
cache/
.pytest_cache
```

---

## Cloud Deployment

### AWS Deployment

#### AWS Lambda (Serverless)

Deploy SocialMapper as serverless functions for on-demand processing.

**1. Create Lambda Deployment Package**

```bash
# Create deployment directory
mkdir lambda_package
cd lambda_package

# Install dependencies
pip install socialmapper -t .

# Add your Lambda function
cat > lambda_function.py << 'EOF'
import json
from socialmapper import create_isochrone, get_census_data, get_census_blocks

def lambda_handler(event, context):
    """
    AWS Lambda handler for SocialMapper operations.

    Event format:
    {
        "operation": "create_isochrone",
        "location": [45.5152, -122.6784],
        "travel_time": 15,
        "travel_mode": "drive"
    }
    """
    try:
        operation = event.get('operation')

        if operation == 'create_isochrone':
            result = create_isochrone(
                location=tuple(event['location']),
                travel_time=event.get('travel_time', 15),
                travel_mode=event.get('travel_mode', 'drive')
            )

        elif operation == 'census_analysis':
            iso = create_isochrone(
                location=tuple(event['location']),
                travel_time=event.get('travel_time', 15)
            )
            blocks = get_census_blocks(polygon=iso)
            geoids = [b['geoid'] for b in blocks]
            result = get_census_data(
                location=geoids,
                variables=event.get('variables', ['population'])
            )
            # Convert to JSON-serializable format
            result = {
                "data": result.data,
                "location_type": result.location_type,
                "query_info": result.query_info
            }
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Invalid operation'})
            }

        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
EOF

# Create deployment package
zip -r ../socialmapper-lambda.zip .
cd ..
```

**2. Deploy to Lambda**

```bash
# Using AWS CLI
aws lambda create-function \
  --function-name socialmapper-processor \
  --runtime python3.11 \
  --role arn:aws:iam::ACCOUNT_ID:role/lambda-execution-role \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://socialmapper-lambda.zip \
  --timeout 300 \
  --memory-size 1024 \
  --environment Variables="{CENSUS_API_KEY=your_key_here}" \
  --ephemeral-storage Size=2048

# Update function code
aws lambda update-function-code \
  --function-name socialmapper-processor \
  --zip-file fileb://socialmapper-lambda.zip
```

**3. Configure Environment Variables with AWS Secrets Manager**

```bash
# Store API key in Secrets Manager
aws secretsmanager create-secret \
  --name socialmapper/census-api-key \
  --secret-string "your_census_api_key_here"

# Update Lambda to use secrets (requires Lambda layer or code modification)
```

**4. API Gateway Integration**

```bash
# Create REST API
aws apigateway create-rest-api \
  --name "SocialMapper API" \
  --description "API for SocialMapper demographic analysis"

# Configure POST method to invoke Lambda
# (See AWS API Gateway documentation for complete setup)
```

#### AWS EC2 (Persistent Service)

For long-running applications or complex workflows:

**1. Launch EC2 Instance**

```bash
# Launch Ubuntu instance
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t3.medium \
  --key-name your-key-pair \
  --security-groups socialmapper-sg \
  --user-data file://install-script.sh
```

**2. Installation Script (install-script.sh)**

```bash
#!/bin/bash
# Update system
apt-get update && apt-get upgrade -y

# Install Python 3.11
apt-get install -y python3.11 python3.11-venv git

# Install spatial dependencies
apt-get install -y libgeos-dev libgdal-dev

# Clone and install SocialMapper
cd /home/ubuntu
git clone https://github.com/mihiarc/socialmapper.git
cd socialmapper
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e .

# Set up systemd service (optional)
cat > /etc/systemd/system/socialmapper.service << EOF
[Unit]
Description=SocialMapper Application
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/socialmapper
Environment="CENSUS_API_KEY=your_key_here"
ExecStart=/home/ubuntu/socialmapper/.venv/bin/python -m your_app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl enable socialmapper
systemctl start socialmapper
```

**3. S3 for Cache Storage**

```python
# Example: Use S3 for distributed cache
import boto3
from pathlib import Path

s3 = boto3.client('s3')
BUCKET = 'socialmapper-cache'

def save_cache_to_s3(cache_key, data):
    """Upload cache to S3 for sharing across instances."""
    s3.put_object(
        Bucket=BUCKET,
        Key=f'cache/{cache_key}',
        Body=data
    )

def load_cache_from_s3(cache_key):
    """Load cache from S3."""
    try:
        response = s3.get_object(
            Bucket=BUCKET,
            Key=f'cache/{cache_key}'
        )
        return response['Body'].read()
    except s3.exceptions.NoSuchKey:
        return None
```

---

### Google Cloud Platform

#### Cloud Functions

**1. Create function directory structure**

```text
socialmapper-function/
├── main.py
├── requirements.txt
└── .env.yaml
```

**2. main.py**

```python
import functions_framework
from socialmapper import create_isochrone, get_census_data, get_census_blocks

@functions_framework.http
def socialmapper_handler(request):
    """HTTP Cloud Function for SocialMapper operations."""
    request_json = request.get_json(silent=True)

    if not request_json:
        return {'error': 'Invalid request'}, 400

    operation = request_json.get('operation')

    try:
        if operation == 'isochrone':
            result = create_isochrone(
                location=tuple(request_json['location']),
                travel_time=request_json.get('travel_time', 15),
                travel_mode=request_json.get('travel_mode', 'drive')
            )
        elif operation == 'census':
            iso = create_isochrone(
                location=tuple(request_json['location']),
                travel_time=request_json.get('travel_time', 15)
            )
            blocks = get_census_blocks(polygon=iso)
            result = get_census_data(
                location=[b['geoid'] for b in blocks],
                variables=request_json.get('variables', ['population'])
            )
            # Serialize for JSON
            result = {
                "data": result.data,
                "location_type": result.location_type
            }
        else:
            return {'error': 'Invalid operation'}, 400

        return result, 200

    except Exception as e:
        return {'error': str(e)}, 500
```

**3. requirements.txt**

```text
functions-framework==3.*
socialmapper>=0.9.0
```

**4. Deploy to Cloud Functions**

```bash
# Deploy function
gcloud functions deploy socialmapper-processor \
  --runtime python311 \
  --trigger-http \
  --allow-unauthenticated \
  --entry-point socialmapper_handler \
  --timeout 300s \
  --memory 1024MB \
  --set-env-vars CENSUS_API_KEY=your_key_here

# Or use Secret Manager
gcloud functions deploy socialmapper-processor \
  --runtime python311 \
  --trigger-http \
  --entry-point socialmapper_handler \
  --set-secrets 'CENSUS_API_KEY=census-api-key:latest'
```

#### Cloud Run (Containerized)

**1. Create Cloud Run Dockerfile**

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN pip install socialmapper

ENV PORT=8080
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app
```

**2. Deploy to Cloud Run**

```bash
# Build and push to Container Registry
gcloud builds submit --tag gcr.io/PROJECT_ID/socialmapper

# Deploy to Cloud Run
gcloud run deploy socialmapper-service \
  --image gcr.io/PROJECT_ID/socialmapper \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --timeout 300s \
  --set-env-vars CENSUS_API_KEY=your_key_here
```

#### Cloud Storage for Cache

```python
from google.cloud import storage

client = storage.Client()
bucket = client.bucket('socialmapper-cache')

def save_to_gcs(key, data):
    """Upload cache to GCS."""
    blob = bucket.blob(f'cache/{key}')
    blob.upload_from_string(data)

def load_from_gcs(key):
    """Load cache from GCS."""
    blob = bucket.blob(f'cache/{key}')
    if blob.exists():
        return blob.download_as_bytes()
    return None
```

---

### Microsoft Azure

#### Azure Functions

**1. Create Azure Function**

```bash
# Install Azure Functions Core Tools
npm install -g azure-functions-core-tools@4

# Create function app
func init SocialMapperFunction --python
cd SocialMapperFunction
func new --name SocialMapperProcessor --template "HTTP trigger"
```

**2. Edit __init__.py**

```python
import logging
import json
import azure.functions as func
from socialmapper import create_isochrone, get_census_data, get_census_blocks

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('SocialMapper function triggered')

    try:
        req_body = req.get_json()
        operation = req_body.get('operation')

        if operation == 'isochrone':
            result = create_isochrone(
                location=tuple(req_body['location']),
                travel_time=req_body.get('travel_time', 15),
                travel_mode=req_body.get('travel_mode', 'drive')
            )
        elif operation == 'census':
            iso = create_isochrone(
                location=tuple(req_body['location']),
                travel_time=req_body.get('travel_time', 15)
            )
            blocks = get_census_blocks(polygon=iso)
            result = get_census_data(
                location=[b['geoid'] for b in blocks],
                variables=req_body.get('variables', ['population'])
            )
            result = {
                "data": result.data,
                "location_type": result.location_type
            }
        else:
            return func.HttpResponse(
                json.dumps({'error': 'Invalid operation'}),
                status_code=400
            )

        return func.HttpResponse(
            json.dumps(result),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        return func.HttpResponse(
            json.dumps({'error': str(e)}),
            status_code=500
        )
```

**3. requirements.txt**

```text
azure-functions
socialmapper>=0.9.0
```

**4. Deploy to Azure**

```bash
# Create Function App
az functionapp create \
  --resource-group socialmapper-rg \
  --consumption-plan-location eastus \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --name socialmapper-func \
  --storage-account socialmapperstorage

# Configure app settings
az functionapp config appsettings set \
  --name socialmapper-func \
  --resource-group socialmapper-rg \
  --settings CENSUS_API_KEY=your_key_here

# Deploy
func azure functionapp publish socialmapper-func
```

#### Azure Container Apps

**1. Build and push container**

```bash
# Login to Azure Container Registry
az acr login --name socialmapperregistry

# Build and push
docker build -t socialmapperregistry.azurecr.io/socialmapper:latest .
docker push socialmapperregistry.azurecr.io/socialmapper:latest
```

**2. Deploy Container App**

```bash
az containerapp create \
  --name socialmapper-app \
  --resource-group socialmapper-rg \
  --environment socialmapper-env \
  --image socialmapperregistry.azurecr.io/socialmapper:latest \
  --target-port 8000 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 5 \
  --secrets census-api-key=your_key_here \
  --env-vars CENSUS_API_KEY=secretref:census-api-key
```

#### Azure Key Vault for Secrets

```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

credential = DefaultAzureCredential()
client = SecretClient(
    vault_url="https://socialmapper-vault.vault.azure.net/",
    credential=credential
)

# Retrieve secret
census_key = client.get_secret("census-api-key").value
```

#### Azure Blob Storage for Cache

```python
from azure.storage.blob import BlobServiceClient

connection_string = "your_connection_string"
blob_service = BlobServiceClient.from_connection_string(connection_string)
container = blob_service.get_container_client("cache")

def save_to_blob(key, data):
    """Upload cache to Azure Blob Storage."""
    blob = container.get_blob_client(f'cache/{key}')
    blob.upload_blob(data, overwrite=True)

def load_from_blob(key):
    """Load cache from Azure Blob Storage."""
    blob = container.get_blob_client(f'cache/{key}')
    if blob.exists():
        return blob.download_blob().readall()
    return None
```

---

## Production Configuration

### Performance Tuning

SocialMapper provides three performance presets optimized for different use cases:

#### Fast Preset (Maximum Speed)

Optimized for speed with higher memory usage:

```python
from socialmapper.performance import get_performance_config

# Configure for maximum speed
config = get_performance_config(preset='fast')
# - Network cache: 10GB
# - Geocoding cache: 1GB
# - Census cache: 500MB
# - Cache TTL: 24 hours
# - Connection pool: 20 connections
```

#### Balanced Preset (Default)

Good balance between speed and resource usage:

```python
config = get_performance_config(preset='balanced')
# - Network cache: 5GB
# - Geocoding cache: 500MB
# - Census cache: 250MB
# - Cache TTL: 7 days
# - Connection pool: 10 connections
```

#### Memory-Efficient Preset

Minimized memory footprint for resource-constrained environments:

```python
config = get_performance_config(preset='memory_efficient')
# - Network cache: 2GB
# - Geocoding cache: 100MB
# - Census cache: 50MB
# - Cache TTL: 30 days
# - Connection pool: 5 connections
```

#### Custom Configuration

Fine-tune individual parameters:

```python
config = get_performance_config(
    preset='balanced',
    cache_ttl_hours=48,  # Override specific setting
    http_pool_connections=15
)
```

### Caching Configuration

#### Local Disk Cache

```python
from socialmapper.performance import CacheManager

# Initialize cache manager
cache = CacheManager(
    cache_dir='/var/cache/socialmapper',
    max_size_gb=10,
    ttl_hours=168  # 7 days
)

# Use cache
result = cache.get('my_key')
if result is None:
    result = expensive_operation()
    cache.set('my_key', result)
```

#### Cache Statistics

```python
from socialmapper.performance import get_cache_stats

stats = get_cache_stats()
print(f"Cache hit rate: {stats['hit_rate']:.1%}")
print(f"Total size: {stats['total_size_mb']:.1f} MB")
print(f"Items cached: {stats['item_count']}")
```

### Rate Limiting Setup

To avoid hitting API rate limits:

```python
import time
from functools import wraps

def rate_limit(calls_per_second=10):
    """Decorator to limit API calls."""
    min_interval = 1.0 / calls_per_second
    last_called = [0.0]

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            wait_time = min_interval - elapsed
            if wait_time > 0:
                time.sleep(wait_time)
            result = func(*args, **kwargs)
            last_called[0] = time.time()
            return result
        return wrapper
    return decorator

@rate_limit(calls_per_second=5)
def fetch_census_data(geoids):
    """Rate-limited census data fetch."""
    return get_census_data(geoids, ['population'])
```

### Logging Configuration

```python
import logging
from logging.handlers import RotatingFileHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(
            'socialmapper.log',
            maxBytes=10485760,  # 10MB
            backupCount=5
        ),
        logging.StreamHandler()
    ]
)

# Set SocialMapper log level
logging.getLogger('socialmapper').setLevel(logging.INFO)

# Reduce noise from dependencies
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)
```

### Error Tracking (Sentry Integration)

```python
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

# Initialize Sentry
sentry_sdk.init(
    dsn="your-sentry-dsn",
    environment="production",
    traces_sample_rate=1.0,
    integrations=[
        LoggingIntegration(
            level=logging.INFO,
            event_level=logging.ERROR
        )
    ]
)

# Errors will be automatically tracked
try:
    result = create_isochrone(location, travel_time)
except Exception as e:
    # Exception automatically sent to Sentry
    raise
```

---

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `CENSUS_API_KEY` | Census Bureau API key | `abc123def456...` |

### Optional Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `MAPBOX_ACCESS_TOKEN` | Mapbox token for enhanced maps | None | `pk.eyJ1...` |
| `SOCIALMAPPER_CACHE_DIR` | Cache directory path | `.cache` | `/var/cache/socialmapper` |
| `SOCIALMAPPER_DEFAULT_MAP_LAT` | Default map latitude | 45.5152 | `40.7128` |
| `SOCIALMAPPER_DEFAULT_MAP_LNG` | Default map longitude | -122.6784 | `-74.0060` |
| `SOCIALMAPPER_DEFAULT_MAP_ZOOM` | Default map zoom level | 12 | `10` |

### Performance Configuration Variables

| Variable | Description | Default | Options |
|----------|-------------|---------|---------|
| `SOCIALMAPPER_PERFORMANCE_PRESET` | Performance preset | `balanced` | `fast`, `balanced`, `memory_efficient` |
| `SOCIALMAPPER_NETWORK_CACHE_SIZE_GB` | Network cache size (GB) | 5 | 1-100 |
| `SOCIALMAPPER_GEOCODING_CACHE_SIZE_MB` | Geocoding cache size (MB) | 500 | 10-10000 |
| `SOCIALMAPPER_CENSUS_CACHE_SIZE_MB` | Census cache size (MB) | 250 | 10-5000 |
| `SOCIALMAPPER_CACHE_TTL_HOURS` | Cache time-to-live (hours) | 168 | 1-8760 |
| `SOCIALMAPPER_HTTP_POOL_CONNECTIONS` | HTTP connection pool size | 10 | 1-100 |
| `SOCIALMAPPER_HTTP_TIMEOUT_SECONDS` | HTTP request timeout | 30 | 5-300 |

### Security Best Practices

1. **Never commit secrets to version control:**

```bash
# Add to .gitignore
echo ".env" >> .gitignore
echo "*.key" >> .gitignore
```

2. **Use secret management services:**

```bash
# AWS Secrets Manager
export CENSUS_API_KEY=$(aws secretsmanager get-secret-value \
  --secret-id socialmapper/census-api-key \
  --query SecretString --output text)

# GCP Secret Manager
export CENSUS_API_KEY=$(gcloud secrets versions access latest \
  --secret="census-api-key")

# Azure Key Vault
export CENSUS_API_KEY=$(az keyvault secret show \
  --name census-api-key \
  --vault-name socialmapper-vault \
  --query value -o tsv)
```

3. **Rotate API keys regularly:**

```python
# Use key rotation strategy
from datetime import datetime, timedelta

def is_key_expired(key_created_date):
    """Check if API key should be rotated (90 days)."""
    return datetime.now() - key_created_date > timedelta(days=90)
```

---

## Monitoring & Observability

### Health Check Endpoints

Implement health checks for container orchestration:

```python
from flask import Flask, jsonify
import socialmapper

app = Flask(__name__)

@app.route('/health')
def health_check():
    """Basic health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'version': socialmapper.__version__
    }), 200

@app.route('/ready')
def readiness_check():
    """Readiness check with dependency validation."""
    checks = {
        'socialmapper': True,
        'census_api': check_census_api_connectivity(),
        'cache': check_cache_writable()
    }

    all_ready = all(checks.values())
    status_code = 200 if all_ready else 503

    return jsonify({
        'ready': all_ready,
        'checks': checks
    }), status_code

def check_census_api_connectivity():
    """Verify Census API is accessible."""
    try:
        # Simple test query
        result = get_census_data(
            location=["060750201001"],
            variables=["population"]
        )
        return True
    except:
        return False

def check_cache_writable():
    """Verify cache directory is writable."""
    from pathlib import Path
    cache_dir = Path('.cache')
    return cache_dir.exists() and cache_dir.is_dir()
```

### Performance Metrics

Track key performance indicators:

```python
import time
from functools import wraps

class PerformanceMonitor:
    """Track performance metrics for operations."""

    def __init__(self):
        self.metrics = {
            'request_count': 0,
            'total_time': 0,
            'error_count': 0,
            'operations': {}
        }

    def track(self, operation_name):
        """Decorator to track operation performance."""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start = time.time()
                try:
                    result = func(*args, **kwargs)
                    self.metrics['request_count'] += 1
                    return result
                except Exception as e:
                    self.metrics['error_count'] += 1
                    raise
                finally:
                    duration = time.time() - start
                    self.metrics['total_time'] += duration

                    if operation_name not in self.metrics['operations']:
                        self.metrics['operations'][operation_name] = {
                            'count': 0,
                            'total_time': 0
                        }

                    self.metrics['operations'][operation_name]['count'] += 1
                    self.metrics['operations'][operation_name]['total_time'] += duration

            return wrapper
        return decorator

    def get_stats(self):
        """Get performance statistics."""
        return {
            'total_requests': self.metrics['request_count'],
            'total_errors': self.metrics['error_count'],
            'avg_response_time': (
                self.metrics['total_time'] / self.metrics['request_count']
                if self.metrics['request_count'] > 0 else 0
            ),
            'operations': {
                name: {
                    'count': stats['count'],
                    'avg_time': stats['total_time'] / stats['count']
                }
                for name, stats in self.metrics['operations'].items()
            }
        }

# Usage
monitor = PerformanceMonitor()

@monitor.track('create_isochrone')
def create_isochrone_tracked(*args, **kwargs):
    return create_isochrone(*args, **kwargs)

# Expose metrics endpoint
@app.route('/metrics')
def metrics():
    return jsonify(monitor.get_stats())
```

### Cache Statistics Monitoring

```python
from socialmapper.performance import get_cache_stats

@app.route('/cache/stats')
def cache_stats():
    """Expose cache statistics."""
    stats = get_cache_stats()
    return jsonify(stats)

# Prometheus-compatible metrics
@app.route('/metrics/prometheus')
def prometheus_metrics():
    """Export metrics in Prometheus format."""
    stats = get_cache_stats()
    monitor_stats = monitor.get_stats()

    metrics = []
    metrics.append(f'cache_hit_rate {stats["hit_rate"]}')
    metrics.append(f'cache_size_mb {stats["total_size_mb"]}')
    metrics.append(f'cache_item_count {stats["item_count"]}')
    metrics.append(f'total_requests {monitor_stats["total_requests"]}')
    metrics.append(f'total_errors {monitor_stats["total_errors"]}')
    metrics.append(f'avg_response_time_seconds {monitor_stats["avg_response_time"]}')

    return '\n'.join(metrics), 200, {'Content-Type': 'text/plain'}
```

### Logging Best Practices

```python
import logging
import json
from pythonjsonlogger import jsonlogger

# Structured logging for production
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(
    '%(asctime)s %(name)s %(levelname)s %(message)s'
)
logHandler.setFormatter(formatter)

logger = logging.getLogger('socialmapper')
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

# Log with context
def log_operation(operation, **context):
    """Log operation with structured context."""
    logger.info(
        f'Operation: {operation}',
        extra={
            'operation': operation,
            **context
        }
    )

# Usage
log_operation(
    'create_isochrone',
    location=(45.5152, -122.6784),
    travel_time=15,
    result_area_km2=125.4
)
```

---

## Scaling Considerations

### Horizontal Scaling Patterns

#### Stateless Service Design

Ensure your application can scale horizontally:

```python
# ✓ Good - Stateless design
def process_location(location, travel_time):
    """Process location without relying on instance state."""
    iso = create_isochrone(location, travel_time)
    blocks = get_census_blocks(polygon=iso)
    return get_census_data([b['geoid'] for b in blocks], ['population'])

# ✗ Avoid - Stateful design
class LocationProcessor:
    def __init__(self):
        self.cached_results = {}  # Don't use instance-level cache

    def process(self, location):
        if location in self.cached_results:
            return self.cached_results[location]
        # ...
```

#### Shared Cache Strategy

Use distributed caching for multiple instances:

```python
import redis
import pickle

# Redis-based shared cache
redis_client = redis.Redis(
    host='cache.example.com',
    port=6379,
    db=0,
    decode_responses=False
)

def get_cached_isochrone(location, travel_time):
    """Get cached isochrone with Redis."""
    cache_key = f'iso:{location}:{travel_time}'

    # Try cache first
    cached = redis_client.get(cache_key)
    if cached:
        return pickle.loads(cached)

    # Generate and cache
    result = create_isochrone(location, travel_time)
    redis_client.setex(
        cache_key,
        timedelta(hours=24),
        pickle.dumps(result)
    )

    return result
```

### Load Balancing

#### Nginx Configuration

```nginx
upstream socialmapper_backend {
    least_conn;
    server app1.example.com:8000;
    server app2.example.com:8000;
    server app3.example.com:8000;
}

server {
    listen 80;
    server_name api.socialmapper.example.com;

    location / {
        proxy_pass http://socialmapper_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        # Timeout for long-running operations
        proxy_read_timeout 300s;
        proxy_connect_timeout 10s;
    }

    location /health {
        proxy_pass http://socialmapper_backend/health;
        proxy_connect_timeout 2s;
    }
}
```

### Cost Optimization

#### Batch Processing

Process multiple locations efficiently:

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def batch_process_locations(locations, max_workers=5):
    """Process multiple locations in parallel."""
    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        futures = {
            executor.submit(
                process_location, loc['coords'], loc['travel_time']
            ): loc['name']
            for loc in locations
        }

        # Collect results
        for future in as_completed(futures):
            location_name = futures[future]
            try:
                result = future.result()
                results.append({
                    'location': location_name,
                    'data': result
                })
            except Exception as e:
                logger.error(f'Failed to process {location_name}: {e}')

    return results
```

#### Optimize API Calls

Minimize Census API requests:

```python
def efficient_multi_location_analysis(locations):
    """Analyze multiple locations with optimized API calls."""
    # 1. Collect all GEOIDs first
    all_geoids = set()
    location_geoids = {}

    for loc_name, coords in locations.items():
        iso = create_isochrone(coords, travel_time=15)
        blocks = get_census_blocks(polygon=iso)
        geoids = [b['geoid'] for b in blocks]

        location_geoids[loc_name] = geoids
        all_geoids.update(geoids)

    # 2. Single Census API call for all GEOIDs
    all_census_data = get_census_data(
        location=list(all_geoids),
        variables=['population', 'median_income']
    )

    # 3. Distribute results to locations
    results = {}
    for loc_name, geoids in location_geoids.items():
        results[loc_name] = {
            geoid: all_census_data.data[geoid]
            for geoid in geoids
        }

    return results
```

---

## Troubleshooting

### Common Deployment Issues

#### Issue: ModuleNotFoundError

```bash
# Problem: SocialMapper not found
ModuleNotFoundError: No module named 'socialmapper'

# Solution: Ensure proper installation
pip install socialmapper
# Or for development
pip install -e .
```

#### Issue: Census API Key Not Found

```python
# Problem
MissingAPIKeyError: Census API key not found

# Solution 1: Set environment variable
export CENSUS_API_KEY='your_key_here'

# Solution 2: Use .env file
echo "CENSUS_API_KEY=your_key_here" > .env

# Solution 3: Set programmatically (not recommended for production)
import os
os.environ['CENSUS_API_KEY'] = 'your_key_here'
```

#### Issue: Permission Denied for Cache Directory

```bash
# Problem: Cannot write to cache
PermissionError: [Errno 13] Permission denied: '/app/cache'

# Solution: Fix permissions
mkdir -p /app/cache
chmod 777 /app/cache

# Or in Dockerfile
RUN mkdir -p /app/cache && chmod 777 /app/cache
```

#### Issue: Network Timeout

```python
# Problem: Requests timing out
requests.exceptions.Timeout: HTTPSConnectionPool

# Solution: Increase timeout
from socialmapper.performance import get_performance_config

config = get_performance_config(
    preset='balanced',
    http_timeout_seconds=60  # Increase from default 30s
)
```

### Debug Mode

Enable detailed logging for troubleshooting:

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger('socialmapper').setLevel(logging.DEBUG)

# Run operation
try:
    result = create_isochrone(location, travel_time)
except Exception as e:
    logger.exception('Detailed error trace:')
    raise
```

### Performance Debugging

Identify bottlenecks:

```python
import cProfile
import pstats
from io import StringIO

def profile_operation():
    """Profile an operation to find bottlenecks."""
    profiler = cProfile.Profile()
    profiler.enable()

    # Run your operation
    result = create_isochrone((45.5152, -122.6784), travel_time=15)

    profiler.disable()

    # Print stats
    s = StringIO()
    stats = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    stats.print_stats(20)  # Top 20 functions

    print(s.getvalue())
    return result
```

### Network Connectivity

Test API connectivity:

```python
import requests

def test_census_api():
    """Test Census API connectivity."""
    try:
        response = requests.get(
            'https://api.census.gov/data.json',
            timeout=10
        )
        if response.status_code == 200:
            print('✓ Census API accessible')
            return True
        else:
            print(f'✗ Census API returned {response.status_code}')
            return False
    except Exception as e:
        print(f'✗ Cannot reach Census API: {e}')
        return False

def test_osm_api():
    """Test OpenStreetMap connectivity."""
    try:
        response = requests.get(
            'https://overpass-api.de/api/status',
            timeout=10
        )
        if response.status_code == 200:
            print('✓ OSM Overpass API accessible')
            return True
        else:
            print(f'✗ OSM API returned {response.status_code}')
            return False
    except Exception as e:
        print(f'✗ Cannot reach OSM API: {e}')
        return False

# Run diagnostics
print('Running connectivity tests...')
test_census_api()
test_osm_api()
```

### Memory Issues

Monitor and optimize memory usage:

```python
from socialmapper.performance import get_memory_stats

# Check memory usage
stats = get_memory_stats()
print(f'Memory used: {stats["used_gb"]:.2f} GB')
print(f'Memory available: {stats["available_gb"]:.2f} GB')

# Clear memory if needed
from socialmapper.performance import clear_memory_cache
if stats['used_percent'] > 80:
    clear_memory_cache()
    print('Memory cache cleared')
```

---

## Additional Resources

- [API Reference](api-reference.md) - Complete API documentation
- [Performance Guide](performance.md) - Performance optimization tips
- [Security Guide](security.md) - Security best practices
- [Production Checklist](production-checklist.md) - Pre-deployment checklist
- [GitHub Issues](https://github.com/mihiarc/socialmapper/issues) - Report bugs
- [Discussions](https://github.com/mihiarc/socialmapper/discussions) - Community support

---

## Support

For deployment assistance:
- 📧 Email: mihiarc@example.com
- 💬 GitHub Discussions: https://github.com/mihiarc/socialmapper/discussions
- 🐛 Bug Reports: https://github.com/mihiarc/socialmapper/issues

---

**Version**: 0.9.0
**Last Updated**: 2025-11-05
