@echo off
rem Starts LAGER in Docker and opens it in the browser.
rem Requirement: Docker Desktop is installed and running.

set IMAGE=arinashelashen/lager:latest
set PORT=5000

docker info >nul 2>&1
if errorlevel 1 (
    echo Docker Desktop is not running.
    echo Please start Docker Desktop, wait until it says "running", and try again.
    pause
    exit /b 1
)

rem Remove a LAGER container left over from an earlier session
docker rm -f lager >nul 2>&1

echo Starting LAGER...
docker pull %IMAGE% >nul 2>&1
docker run -d --rm --name lager -p 127.0.0.1:%PORT%:5000 %IMAGE% >nul
if errorlevel 1 (
    echo LAGER could not be started. Is the image "%IMAGE%" available?
    pause
    exit /b 1
)

timeout /t 8 /nobreak >nul
start "" http://localhost:%PORT%

echo.
echo LAGER is running at http://localhost:%PORT%
echo Keep this window open while you work.
echo Press any key to stop LAGER.
pause >nul
docker stop lager >nul
