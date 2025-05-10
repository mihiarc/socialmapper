@echo off
setlocal

echo Checking for uv...
where uv >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo uv not found, installing...
    powershell -Command "iwr -useb https://astral.sh/uv/install.ps1 | iex"
) else (
    echo uv found.
)

echo Checking for virtual environment...
if not exist .venv (
    echo Creating virtual environment...
    uv venv
) else (
    echo Virtual environment found.
)

echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo Installing SocialMapper package with uv...
uv pip install --upgrade -e .[streamlit]

echo.
echo Installation completed successfully!
echo To activate the environment, run:
echo   .venv\Scripts\activate.bat
echo.
echo To run the Streamlit app, run:
echo   python -m socialmapper.streamlit_app
echo or
echo   streamlit run socialmapper\streamlit_app.py 