@echo off
echo Starting 3 Chat Clients...
echo.

REM Start first client
echo Starting Client 1...
start "Chat Client 1" python chat_app.py

REM Wait a moment before starting next client
timeout /t 2 /nobreak >nul

REM Start second client
echo Starting Client 2...
start "Chat Client 2" python chat_app.py

REM Wait a moment before starting next client
timeout /t 2 /nobreak >nul

REM Start third client
echo Starting Client 3...
start "Chat Client 3" python chat_app.py

echo.
echo All 3 clients started!
echo.
echo Instructions for testing message history:
echo 1. Client 1: Login as "UserA", create group "TestGroup", send some messages
echo 2. Client 2: Login as "UserB", join "TestGroup" - should see UserA's messages
echo 3. Client 3: Login as "UserC", join "TestGroup" - should see all previous messages
echo.
echo Press any key to exit...
pause >nul
