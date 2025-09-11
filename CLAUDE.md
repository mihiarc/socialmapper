# SocialMapper - Claude Integration Guide

SocialMapper is a comprehensive platform for community accessibility analysis and demographic mapping.

## Table of Contents

- [Quick Start](#quick-start)
- [Docker Setup](#docker-setup)

## Quick Start

### Prerequisites

- Python 3.11 or higher
- Census API key (free from https://api.census.gov/data/key_signup.html)
- Docker and Docker Compose (for containerized setup)

### Installation

```bash
# Clone the repository
git clone https://github.com/mihiarc/socialmapper.git
cd socialmapper

# Create virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -e .

# Copy and configure environment
cp .env.example .env
# Edit .env with your Census API key
```

### Basic Usage

Run the SocialMapper application:

```bash
uv run python -m socialmapper
```

## Docker Setup

### Development Environment

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

### Production Environment

```bash
# Use production configuration
docker-compose -f docker-compose.prod.yml up -d
```

