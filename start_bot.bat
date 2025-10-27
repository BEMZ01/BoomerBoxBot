@echo off
echo Starting BoomerBox Discord Bot...
echo.
echo Make sure your .env file is configured with:
echo   - DISCORD_TOKEN
echo   - COBALT_API_URL
echo   - COBALT_API_KEY
echo.
cd /d "%~dp0"
.venv\Scripts\python.exe main.py
pause

