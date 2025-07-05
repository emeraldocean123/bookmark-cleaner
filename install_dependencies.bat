@echo off
echo Installing Bookmark Cleaner Dependencies...
echo =============================================

python -m pip install --upgrade pip
echo.

echo Installing beautifulsoup4...
python -m pip install beautifulsoup4
echo.

echo Installing requests...
python -m pip install requests
echo.

echo Installing lxml...
python -m pip install lxml
echo.

echo Installation complete!
echo.
echo To test the setup, run:
echo python test_setup.py
echo.
echo To process your bookmarks, run:
echo python bookmark_cleaner.py
pause
