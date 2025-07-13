"""Custom CSS styles for the Streamlit application."""


def get_custom_css() -> str:
    """Return custom CSS styles for the application with dark mode support."""
    return """
    <style>
        /* Light mode styles (default) */
        .main-header {
            font-size: 3rem;
            font-weight: bold;
            color: #1f77b4;
            text-align: center;
            margin-bottom: 1rem;
        }
        
        .sub-header {
            font-size: 1.5rem;
            color: #666;
            text-align: center;
            margin-bottom: 2rem;
        }
        
        .metric-card {
            background-color: #f0f2f6;
            padding: 1rem;
            border-radius: 0.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .success-message {
            padding: 1rem;
            border-radius: 0.5rem;
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
        }
        
        .error-message {
            padding: 1rem;
            border-radius: 0.5rem;
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
        }
        
        .info-box {
            background-color: #e7f3ff;
            border-left: 4px solid #2196F3;
            padding: 1rem;
            margin: 1rem 0;
        }
        
        /* Dark mode styles */
        @media (prefers-color-scheme: dark) {
            .main-header {
                color: #4dabf7;
            }
            
            .sub-header {
                color: #aaa;
            }
            
            .metric-card {
                background-color: #1e1e1e;
                box-shadow: 0 2px 4px rgba(255,255,255,0.1);
            }
            
            .success-message {
                background-color: #1e3a1e;
                border: 1px solid #2e5a2e;
                color: #8fce8f;
            }
            
            .error-message {
                background-color: #3a1e1e;
                border: 1px solid #5a2e2e;
                color: #ce8f8f;
            }
            
            .info-box {
                background-color: #1e2a3a;
                border-left: 4px solid #4dabf7;
            }
        }
        
        /* Dark theme class for dynamic theme detection */
        .dark-theme .main-header {
            color: #4dabf7;
        }
        
        .dark-theme .sub-header {
            color: #aaa;
        }
        
        .dark-theme .metric-card {
            background-color: #1e1e1e;
            box-shadow: 0 2px 4px rgba(255,255,255,0.1);
        }
        
        .dark-theme .success-message {
            background-color: #1e3a1e;
            border: 1px solid #2e5a2e;
            color: #8fce8f;
        }
        
        .dark-theme .error-message {
            background-color: #3a1e1e;
            border: 1px solid #5a2e2e;
            color: #ce8f8f;
        }
        
        .dark-theme .info-box {
            background-color: #1e2a3a;
            border-left: 4px solid #4dabf7;
        }
        
        /* Modern UI enhancements */
        .stButton > button {
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        
        /* Fragment loading animation */
        @keyframes pulse {
            0% { opacity: 0.6; }
            50% { opacity: 1; }
            100% { opacity: 0.6; }
        }
        
        .fragment-loading {
            animation: pulse 2s ease-in-out infinite;
        }
        
        /* Top navigation styles (if available) */
        .stNavigation {
            background: linear-gradient(90deg, #1f77b4 0%, #4dabf7 100%);
        }
        
        .dark-theme .stNavigation {
            background: linear-gradient(90deg, #0d3d6b 0%, #1f77b4 100%);
        }
    </style>
    """
