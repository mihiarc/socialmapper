# Parallel Development Environment Setup

This document describes the parallel development environment created for the frontend-backend separation of SocialMapper.

## 🏗️ What Was Implemented

### 1. Separate Development Directories

**Backend API (`socialmapper-api/`)**
- Isolated directory for the FastAPI backend server
- Independent requirements.txt with API-specific dependencies
- Setup script for automated environment creation
- Environment configuration template
- README with development instructions

**Frontend UI (`socialmapper-ui/`)**
- Isolated directory for the Streamlit frontend application
- Independent requirements.txt with UI-specific dependencies
- Setup script for automated environment creation
- Environment configuration template
- README with development instructions

### 2. Isolated Virtual Environments

Each component has its own setup script that:
- Creates an isolated Python virtual environment
- Installs component-specific dependencies
- Configures environment variables
- Provides clear instructions for running the component

**Backend Setup:**
```bash
cd socialmapper-api
./setup-dev.sh
source venv/bin/activate
uvicorn api_server.main:app --reload --port 8000
```

**Frontend Setup:**
```bash
cd socialmapper-ui
./setup-dev.sh
source venv/bin/activate
streamlit run streamlit_app.py --server.port 8501
```

### 3. Feature Flag System

A comprehensive feature flag system that allows gradual rollout:

**UI Modes:**
- `monolithic`: Original embedded UI (default)
- `separated`: New API-based architecture
- `hybrid`: Both modes available

**Key Features:**
- Environment variable configuration
- Backward compatibility layer
- Migration notices for users
- Deprecation warnings for legacy imports
- CLI management commands

**Configuration:**
```bash
# Copy the example configuration
cp .env.feature-flags-example .env

# Set UI mode
SOCIALMAPPER_UI_MODE=separated
SOCIALMAPPER_ENABLE_API_SERVER=true
SOCIALMAPPER_ENABLE_SEPARATED_UI=true
```

**Python API Management:**
```python
# Use Python API for configuration
from socialmapper import SocialMapperClient
client = SocialMapperClient()
client.configure_backend(enable_api=True, ui_mode="separated")
```

## 📁 Directory Structure

```
socialmapper/
├── socialmapper-api/           # Backend API server
│   ├── README.md              # Backend setup instructions
│   ├── requirements.txt       # API dependencies
│   ├── .env.example          # Backend configuration template
│   └── setup-dev.sh          # Automated setup script
├── socialmapper-ui/           # Frontend Streamlit app
│   ├── README.md             # Frontend setup instructions
│   ├── requirements.txt      # UI dependencies
│   ├── .env.example         # Frontend configuration template
│   └── setup-dev.sh         # Automated setup script
├── socialmapper/config/
│   └── feature_flags.py      # Feature flag system
# CLI removed - use Python API instead
├── socialmapper/ui/
│   └── compatibility.py      # Backward compatibility layer
├── .env.feature-flags-example # Feature flag configuration template
└── test_feature_flags.py     # Verification test script
```

## 🔧 Configuration Files

### Backend API Configuration (`.env`)
```bash
CENSUS_API_KEY=your_census_api_key_here
CORS_ORIGINS=["http://localhost:8501"]
API_HOST=0.0.0.0
API_PORT=8000
MAX_CONCURRENT_JOBS=10
RESULT_TTL_HOURS=24
RATE_LIMIT_PER_MINUTE=60
```

### Frontend UI Configuration (`.env`)
```bash
API_BASE_URL=http://localhost:8000
API_TIMEOUT=300
POLL_INTERVAL=2.0
MAX_FILE_SIZE_MB=10
PAGE_TITLE=SocialMapper
PAGE_ICON=🗺️
```

### Feature Flags Configuration (`.env`)
```bash
SOCIALMAPPER_UI_MODE=monolithic
SOCIALMAPPER_ENABLE_API_SERVER=false
SOCIALMAPPER_ENABLE_SEPARATED_UI=false
SOCIALMAPPER_SHOW_MIGRATION_NOTICE=true
SOCIALMAPPER_ALLOW_LEGACY_IMPORTS=true
SOCIALMAPPER_DEPRECATION_WARNINGS=true
```

## 🚀 Usage Examples

### Current Monolithic Mode (Default)
```bash
# No changes needed - existing functionality preserved
streamlit run streamlit_app.py
```

### Separated Mode
```bash
# 1. Configure feature flags
echo "SOCIALMAPPER_UI_MODE=separated" > .env
echo "SOCIALMAPPER_ENABLE_API_SERVER=true" >> .env
echo "SOCIALMAPPER_ENABLE_SEPARATED_UI=true" >> .env

# 2. Start backend
cd socialmapper-api
./setup-dev.sh
source venv/bin/activate
uvicorn api_server.main:app --reload --port 8000

# 3. Start frontend (in another terminal)
cd socialmapper-ui
./setup-dev.sh
source venv/bin/activate
streamlit run streamlit_app.py --server.port 8501
```

### Hybrid Mode (Both UIs Available)
```python
# Configure for hybrid mode using Python API
from socialmapper import SocialMapperClient
client = SocialMapperClient()
client.configure_backend(ui_mode="hybrid")

# Both the original and new UIs will be available
```

## ✅ Verification

Run the test script to verify everything is working:

```bash
python3 test_feature_flags.py
```

This tests:
- Feature flag system functionality
- Python API integration
- Development environment setup
- File structure validation

## 🔄 Migration Path

The feature flag system provides a smooth migration path:

1. **Phase 1**: Current monolithic mode (no changes)
2. **Phase 2**: Hybrid mode (both UIs available for testing)
3. **Phase 3**: Separated mode (new architecture)
4. **Phase 4**: Remove legacy UI code (future task)

## 🛠️ Next Steps

With the parallel development environment ready, you can now:

1. **Start Backend Development**: Implement the FastAPI server in `socialmapper-api/`
2. **Start Frontend Development**: Create the separated Streamlit app in `socialmapper-ui/`
3. **Test Both Modes**: Use feature flags to switch between architectures
4. **Gradual Migration**: Move users from monolithic to separated mode

The foundation is now in place for independent development and deployment of the frontend and backend components!