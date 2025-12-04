@echo off
setlocal

REM --- Configuration ---
set VENV_DIR=.venv_monitor_net
set PYTHON_SCRIPT=monitor_net.py
set REQUIREMENTS_FILE=requirements.txt

REM --- Script Setup ---
REM Get the directory where this batch script is located
set SCRIPT_DIR=%~dp0
REM Remove trailing backslash if SCRIPT_DIR is root of a drive e.g. C:if "%SCRIPT_DIR:~-1%"=="" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

set VENV_PATH=%SCRIPT_DIR%\%VENV_DIR%
set PYTHON_EXEC_VENV=%VENV_PATH%\Scripts\python.exe
set PIP_EXEC_VENV=%VENV_PATH%\Scripts\pip.exe
set SCRIPT_TO_RUN_PATH=%SCRIPT_DIR%\%PYTHON_SCRIPT%
set REQUIREMENTS_FILE_PATH=%SCRIPT_DIR%\%REQUIREMENTS_FILE%

echo --- Network Latency Monitor (Windows Batch Runner) ---

REM 1. Check for Python (basic check, assumes python is Python 3 or py launcher works)
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: Python not found in PATH. Please install Python 3 and ensure it's in PATH.
    goto:eof
)
REM A more thorough check might involve parsing `python --version` output.
REM Or using `py -3 --version` if the Python Launcher for Windows is assumed.

REM 2. Create the virtual environment if it doesn't exist
if not exist "%VENV_PATH%" (
    echo INFO: Creating virtual environment in "%VENV_PATH%"...
    python -m venv "%VENV_PATH%"
    if %ERRORLEVEL% neq 0 (
        echo ERROR: Failed to create virtual environment. Check if Python is correctly installed.
        goto:eof
    )
    echo INFO: Virtual environment created successfully.
) else (
    echo INFO: Virtual environment "%VENV_DIR%" already exists.
)

REM 3. Install/update dependencies using the virtual environment's pip
if exist "%REQUIREMENTS_FILE_PATH%" (
    REM Basic check for existence. Robustly checking for non-empty is harder in pure batch.
    echo INFO: Installing/updating dependencies from "%REQUIREMENTS_FILE_PATH%"...
    "%PIP_EXEC_VENV%" install --disable-pip-version-check --no-cache-dir -r "%REQUIREMENTS_FILE_PATH%"
    if %ERRORLEVEL% neq 0 (
        echo ERROR: Failed to install dependencies. Check "%REQUIREMENTS_FILE_PATH%" and your internet connection.
        goto:eof
    )
    echo INFO: Dependencies installed/updated successfully.
) else (
    echo INFO: "%REQUIREMENTS_FILE_PATH%" not found, skipping dependency installation.
)

REM 4. Execute the Python script using the virtual environment's Python interpreter
if not exist "%SCRIPT_TO_RUN_PATH%" (
    echo ERROR: Python script "%PYTHON_SCRIPT%" not found in "%SCRIPT_DIR%".
    goto:eof
)

echo INFO: Executing script "%PYTHON_SCRIPT%" with arguments: %*
echo --------------------------------------------------
"%PYTHON_EXEC_VENV%" "%SCRIPT_TO_RUN_PATH%" %*

set SCRIPT_EXIT_CODE=%ERRORLEVEL%
echo --------------------------------------------------
echo INFO: Script "%PYTHON_SCRIPT%" finished with exit code: %SCRIPT_EXIT_CODE%.

exit /b %SCRIPT_EXIT_CODE%

endlocal
