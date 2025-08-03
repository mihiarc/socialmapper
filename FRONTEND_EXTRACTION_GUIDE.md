# Frontend Extraction Guide

This guide explains how to extract the `socialmapper-ui` directory to create a new `socialmapper-frontend` repository.

## Current Structure

The repository currently contains:
- **socialmapper/** - Main Python backend package 
- **socialmapper-api/** - FastAPI backend service
- **socialmapper-ui/** - React frontend application (to be extracted)

## Extraction Steps

### 1. Create New Repository

```bash
# Create new repository on GitHub called 'socialmapper-frontend'
git clone https://github.com/mihiarc/socialmapper-frontend.git
cd socialmapper-frontend
```

### 2. Copy Frontend Contents

```bash
# Copy the socialmapper-ui contents to the new repository
cp -r /path/to/socialmapper/socialmapper-ui/* .
cp -r /path/to/socialmapper/socialmapper-ui/.* . # Include hidden files
```

### 3. Update Configuration

The frontend will need to be updated to:
- Point to the backend API service
- Update package.json name and description
- Update README files
- Configure CI/CD for frontend deployment

### 4. Backend Integration

The frontend should connect to:
- **Development**: `http://localhost:8000` (local socialmapper-api)
- **Production**: Your deployed backend service URL

## Files to Extract

The following should be moved to the new frontend repository:

### Core Application
- `socialmapper-ui/src/` - React application source
- `socialmapper-ui/package.json` - Dependencies
- `socialmapper-ui/package-lock.json` - Lock file
- `socialmapper-ui/vite.config.ts` - Build configuration
- `socialmapper-ui/tsconfig.json` - TypeScript configuration

### Configuration Files
- `socialmapper-ui/Dockerfile` - Container configuration
- `socialmapper-ui/nginx.conf` - Web server config
- `socialmapper-ui/tailwind.config.js` - Styling
- `socialmapper-ui/postcss.config.js` - CSS processing

### Documentation & Testing
- `socialmapper-ui/README*.md` - Documentation
- `socialmapper-ui/docs/` - Component documentation
- `socialmapper-ui/e2e/` - End-to-end tests
- `socialmapper-ui/playwright.config.*` - Test configuration

### Build & Development
- `socialmapper-ui/setup-dev.sh` - Development setup
- `socialmapper-ui/build.production.sh` - Production build

## After Extraction

Once extracted, you can remove the `socialmapper-ui/` directory from this repository:

```bash
rm -rf socialmapper-ui/
```

## Repository Structure After Separation

### socialmapper (this repo - backend only)
```
socialmapper/
├── socialmapper/          # Main Python package
├── socialmapper-api/      # FastAPI backend service  
├── tests/                 # Backend tests
├── docs/                  # Backend documentation
├── examples/              # Python examples
└── pyproject.toml         # Backend dependencies
```

### socialmapper-frontend (new repo)
```
socialmapper-frontend/
├── src/                   # React application
├── e2e/                   # Frontend tests
├── docs/                  # Frontend documentation
├── package.json           # Frontend dependencies
├── Dockerfile             # Frontend container
└── README.md              # Frontend README
```

This separation provides:
- **Clear separation of concerns**
- **Independent deployment cycles**
- **Technology-specific optimization**
- **Easier maintenance and contribution**