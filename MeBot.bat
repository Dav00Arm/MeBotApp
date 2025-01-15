@echo off
echo Enter your OpenAI API key:
set /p OPENAI_API_KEY=
docker pull dav00arm/mebot:latest
docker run --name mebot-container -d -p 8000:8000 -e OPENAI_API_KEY=%OPENAI_API_KEY% dav00arm/mebot:latest

echo Waiting for the application to start...

REM Loop to check if the app is running
:check_loop
curl -s http://localhost:8000 >nul 2>nul
if %ERRORLEVEL% neq 0 (
    timeout /t 2 >nul
    goto check_loop
)

echo Application is ready! Opening in browser...
start http://localhost:8000
pause
