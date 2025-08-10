# SocialMapper UI

React-based web interface for SocialMapper point of interest accessibility analysis platform.

## Features

- **Interactive Analysis Wizard**: Step-by-step configuration interface
- **Demo Scenarios**: Pre-built analysis scenarios for instant demonstration
- **Real-time Progress Tracking**: Live updates of analysis jobs with Server-Sent Events
- **Interactive Visualizations**: Maps, charts, and data exploration
- **Multi-format Export**: CSV, GeoJSON, Parquet, and GeoParquet support
- **Responsive Design**: Works on desktop, tablet, and mobile devices

## Quick Start

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Access to SocialMapper API backend

### Development Setup

1. **Install dependencies**:
```bash
npm install
```

2. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Start development server**:
```bash
npm run dev
```

The app will be available at `http://localhost:3000`.

### Environment Variables

```bash
# API Configuration
VITE_API_URL=http://localhost:8000
VITE_API_TIMEOUT=30000

# Mapbox (required for mapping)
VITE_MAPBOX_TOKEN=your_mapbox_token_here

# Application
VITE_APP_TITLE=SocialMapper
VITE_APP_VERSION=1.0.0
```

## Architecture

### Technology Stack

- **React 18** with TypeScript
- **Vite** for fast development and optimized builds
- **Ant Design** for consistent UI components
- **Redux Toolkit + RTK Query** for state management and API caching
- **Mapbox GL JS** for interactive mapping
- **React Router** for client-side routing

### Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── common/         # Shared components
│   └── layout/         # Layout components
├── pages/              # Page components
├── services/           # API clients and external services
├── store/              # Redux store and slices
│   ├── api/           # RTK Query API definitions
│   └── slices/        # Redux slices
├── types/              # TypeScript type definitions
├── utils/              # Utility functions
├── styles/             # Global styles
└── test/               # Test utilities
```

### Key Components

- **AppLayout**: Main application layout with navigation
- **Dashboard**: Landing page with overview and quick actions
- **DemoScenarios**: Pre-built analysis scenarios (Project 1.1)
- **AnalysisWizard**: Visual configuration interface (Project 1.2)
- **Results**: Analysis results display with visualizations
- **ProgressPanel**: Real-time job progress tracking

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm run test` - Run tests with Vitest
- `npm run test:ui` - Run tests with UI
- `npm run test:coverage` - Run tests with coverage

## Docker Deployment

### Development
```bash
docker-compose -f docker-compose.dev.yml up
```

### Production
```bash
docker-compose up -d
```

The application includes:
- Multi-stage Docker build for optimized production images
- Nginx configuration for SPA routing and API proxying
- Health check endpoints
- Security headers and GZIP compression

## API Integration

The frontend integrates with the SocialMapper FastAPI backend through:

- **Type-safe API client** generated from backend models
- **RTK Query** for caching and synchronization
- **Real-time updates** via Server-Sent Events
- **Comprehensive error handling** with user-friendly messages

### Main API Endpoints

- `POST /api/v1/analysis/location` - Submit analysis
- `GET /api/v1/analysis/{job_id}/status` - Get job status  
- `GET /api/v1/results/{job_id}` - Get results
- `GET /api/v1/results/{job_id}/export` - Export data
- `GET /api/v1/metadata/*` - Get metadata (POI types, census variables)

## Development Guidelines

### Code Style
- TypeScript strict mode enabled
- ESLint configuration with React hooks rules
- Consistent naming conventions (camelCase for variables, PascalCase for components)

### State Management
- Use Redux Toolkit for global state
- RTK Query for server state and caching
- Local useState for component-specific state

### Testing
- Vitest for unit and integration tests
- Testing Library for React component testing
- Mock service worker for API mocking

## Production Considerations

- **Performance**: Code splitting, lazy loading, optimized bundle sizes
- **Security**: HTTPS, CSP headers, input sanitization
- **Accessibility**: WCAG 2.1 compliance, keyboard navigation, screen reader support
- **Monitoring**: Error tracking, performance metrics, user analytics integration

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

## License

This project is part of the SocialMapper platform. See LICENSE for details.