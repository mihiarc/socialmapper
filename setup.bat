@echo off
:: Setup script for Community Mapper (Windows)

echo Checking Python installation...

:: Check if Python is available
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: Python not found. Please install Python 3.7+ to continue.
    exit /b 1
)

:: Check Python version
for /f "tokens=*" %%a in ('python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"') do set VERSION=%%a
set REQUIRED_VERSION=3.7

:: Simple version check (this is not perfect but works for most cases)
if %VERSION% LSS %REQUIRED_VERSION% (
    echo Error: Python %REQUIRED_VERSION%+ is required, but you have %VERSION%
    exit /b 1
)

echo Setting up Community Mapper environment...

:: Run the setup_env.py script with the --all flag
python setup_env.py --all

:: Check if the setup was successful
if %ERRORLEVEL% neq 0 (
    echo Setup failed. Please check the error messages above.
    exit /b 1
)

echo Setup completed successfully!
echo.
echo Virtual environment created in .venv directory
echo.
echo To run examples:
echo   python example.py --config your_config.yaml
echo   python example.py --examples-only
echo.
echo To analyze an isochrone:
echo   python run_isochrone_census.py isochrones\your_isochrone.geojson --states 20 --output results\output.geojson 