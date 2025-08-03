# SocialMapper Frontend UI

This is the Streamlit-based frontend interface for SocialMapper.

## Development Setup

1. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure backend connection:
```bash
cp .env.example .env
# Edit .env to set API_BASE_URL=http://localhost:8000
```

4. Run the Streamlit app:
```bash
streamlit run streamlit_app.py --server.port 8501
```

## Configuration

The frontend connects to the backend API. Configure in `.env`:
- `API_BASE_URL`: Backend API URL (default: http://localhost:8000)
- `API_TIMEOUT`: Request timeout in seconds (default: 300)
- `POLL_INTERVAL`: Status polling interval in seconds (default: 2.0)