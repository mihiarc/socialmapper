@echo off
:: setup_env.bat - Windows setup script for Community Mapper

echo ===== Community Mapper Environment Setup =====
echo This script will set up the environment for Community Mapper.

:: Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Python is not installed or not in PATH. Please install Python first.
    echo Visit https://www.python.org/downloads/ to download and install Python.
    pause
    exit /b 1
)

:: Check if uv is installed
pip show uv >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo uv is not installed. Installing uv...
    pip install uv
    if %ERRORLEVEL% neq 0 (
        echo Failed to install uv. Please check your pip installation.
        pause
        exit /b 1
    )
)

:: Create virtual environment using uv
echo Creating virtual environment with uv...
uv venv
echo Virtual environment created.

:: Activate virtual environment and install dependencies
echo Installing dependencies...
call .venv\Scripts\activate.bat
uv pip install -r requirements.txt
echo Dependencies installed.

:: Create required directories
echo Creating required directories...
if not exist pages mkdir pages
if not exist examples mkdir examples
if not exist output mkdir output
if not exist output\pois mkdir output\pois
if not exist output\isochrones mkdir output\isochrones
if not exist output\block_groups mkdir output\block_groups
if not exist output\census_data mkdir output\census_data
if not exist output\maps mkdir output\maps
echo Directories created.

:: Create .env file for Census API key if it doesn't exist
if not exist .env (
    echo Creating .env file...
    echo # Census API key (get one at https://api.census.gov/data/key_signup.html) > .env
    echo CENSUS_API_KEY=your-census-api-key >> .env
    echo .env file created. Please edit it to add your Census API key.
) else (
    echo .env file already exists.
)

echo.
echo ===== Setup Complete =====
echo To run the Community Mapper Streamlit app:
echo 1. Make sure the virtual environment is activated:
echo    .venv\Scripts\activate
echo 2. Run the Streamlit app:
echo    streamlit run app.py
echo.
echo For more information, see STREAMLIT_README.md
echo.

pause 