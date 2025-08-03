.PHONY: help build build-dev up up-dev down logs test lint clean

# Default target
help:
	@echo "SocialMapper Development Commands:"
	@echo ""
	@echo "  make build         - Build production Docker images"
	@echo "  make build-dev     - Build development Docker images"
	@echo "  make up            - Start production services"
	@echo "  make up-dev        - Start development services with hot reload"
	@echo "  make down          - Stop all services"
	@echo "  make logs          - View service logs"
	@echo "  make test          - Run all tests"
	@echo "  make test-api      - Run API tests"
	@echo "  make test-ui       - Run UI tests"
	@echo "  make lint          - Run linters"
	@echo "  make clean         - Clean up containers and volumes"
	@echo ""

# Build production images
build:
	docker-compose build

# Build development images
build-dev:
	docker-compose -f docker-compose.dev.yml build

# Start production services
up:
	docker-compose up -d

# Start development services
up-dev:
	docker-compose -f docker-compose.dev.yml up

# Stop all services
down:
	docker-compose down
	docker-compose -f docker-compose.dev.yml down

# View logs
logs:
	docker-compose logs -f

# Run all tests
test: test-api test-ui

# Run API tests
test-api:
	cd socialmapper-api && python -m pytest -v

# Run UI tests
test-ui:
	cd socialmapper-ui && npm test

# Run linters
lint: lint-api lint-ui

# Lint API code
lint-api:
	cd socialmapper-api && ruff check .

# Lint UI code
lint-ui:
	cd socialmapper-ui && npm run lint

# Clean up
clean:
	docker-compose down -v
	docker-compose -f docker-compose.dev.yml down -v
	docker system prune -f

# Install development dependencies locally
install-dev:
	cd socialmapper-api && pip install -e ".[dev]"
	cd socialmapper-ui && npm install

# Format code
format:
	cd socialmapper-api && ruff format .
	cd socialmapper-ui && npm run format

# Check types
typecheck:
	cd socialmapper-api && python scripts/type_check.py
	cd socialmapper-ui && npm run typecheck