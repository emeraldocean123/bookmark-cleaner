@echo off
echo Installing Bookmark Cleaner Dependencies...
echo =============================================

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.7+ from https://www.python.org/
    pause
    exit /b 1
)

echo Upgrading pip...
python -m pip install --upgrade pip
if %errorlevel% neq 0 (
    echo Error: Failed to upgrade pip
    pause
    exit /b 1
)
echo.

echo Installing dependencies from requirements.txt...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Error: Failed to install dependencies
    pause
    exit /b 1
)
echo.

echo Installation complete!
echo.
echo To test the setup, run:
echo python test_setup.py
echo.
echo To process your bookmarks, run:
echo python bookmark_cleaner.py [path_to_bookmarks.html]
echo.
echo For help, run:
echo python bookmark_cleaner.py --help
pause
