#!/bin/bash

# SocialMapper Deployment Script
# This script builds and deploys the SocialMapper application using Docker

set -e

# Configuration
COMPOSE_FILE="docker-compose.yml"
PROD_COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    log_info "Checking requirements..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check environment file
    if [[ ! -f "$ENV_FILE" ]]; then
        log_warn "Environment file not found. Creating from template..."
        create_env_file
    fi
}

create_env_file() {
    cat > "$ENV_FILE" << EOF
# SocialMapper Environment Configuration

# Census API Key (required)
# Get yours at: https://api.census.gov/data/key_signup.html
CENSUS_API_KEY=your_census_api_key_here

# API Authentication (for production)
# Comma-separated list of API keys
API_KEYS=key1,key2,key3

# Other optional settings
# SOCIALMAPPER_API_LOG_LEVEL=info
# SOCIALMAPPER_API_RATE_LIMIT_PER_MINUTE=60
EOF
    
    log_warn "Please edit $ENV_FILE and add your Census API key before continuing."
    exit 1
}

build_images() {
    log_info "Building Docker images..."
    
    # Build API image
    log_info "Building API image..."
    docker build -t socialmapper-api:latest ./socialmapper-api
    
    # Build UI image
    log_info "Building UI image..."
    docker build -t socialmapper-ui:latest ./socialmapper-ui
}

deploy_dev() {
    log_info "Deploying in development mode..."
    
    # Use docker-compose or docker compose based on availability
    if command -v docker-compose &> /dev/null; then
        docker-compose -f "$COMPOSE_FILE" up -d
    else
        docker compose -f "$COMPOSE_FILE" up -d
    fi
    
    log_info "Development deployment complete!"
    log_info "API available at: http://localhost:8000"
    log_info "UI available at: http://localhost:80"
}

deploy_prod() {
    log_info "Deploying in production mode..."
    
    # Check for production compose file
    if [[ ! -f "$PROD_COMPOSE_FILE" ]]; then
        log_error "Production compose file not found: $PROD_COMPOSE_FILE"
        exit 1
    fi
    
    # Use docker-compose or docker compose based on availability
    if command -v docker-compose &> /dev/null; then
        docker-compose -f "$PROD_COMPOSE_FILE" up -d
    else
        docker compose -f "$PROD_COMPOSE_FILE" up -d
    fi
    
    log_info "Production deployment complete!"
    log_info "Please configure your reverse proxy for SSL termination."
}

stop_services() {
    log_info "Stopping services..."
    
    if command -v docker-compose &> /dev/null; then
        docker-compose down
    else
        docker compose down
    fi
}

show_logs() {
    if command -v docker-compose &> /dev/null; then
        docker-compose logs -f
    else
        docker compose logs -f
    fi
}

show_status() {
    if command -v docker-compose &> /dev/null; then
        docker-compose ps
    else
        docker compose ps
    fi
}

# Main script
case "${1:-}" in
    build)
        check_requirements
        build_images
        ;;
    dev|development)
        check_requirements
        build_images
        deploy_dev
        ;;
    prod|production)
        check_requirements
        build_images
        deploy_prod
        ;;
    stop)
        stop_services
        ;;
    logs)
        show_logs
        ;;
    status)
        show_status
        ;;
    *)
        echo "SocialMapper Deployment Script"
        echo ""
        echo "Usage: $0 {build|dev|prod|stop|logs|status}"
        echo ""
        echo "Commands:"
        echo "  build       Build Docker images"
        echo "  dev         Deploy in development mode"
        echo "  prod        Deploy in production mode"
        echo "  stop        Stop all services"
        echo "  logs        Show service logs"
        echo "  status      Show service status"
        echo ""
        exit 1
        ;;
esac