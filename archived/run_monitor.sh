#!/bin/bash

# --- Configuration ---
# Virtual environment directory name
VENV_DIR=".venv_monitor_net"
# Python script to execute
PYTHON_SCRIPT="monitor_net.py"
# Requirements file name
REQUIREMENTS_FILE="requirements.txt"

# --- Script Setup ---
# Ensures the script operates relative to its own location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

# Full paths to executables and files within the script's directory
VENV_PATH="$SCRIPT_DIR/$VENV_DIR"
PYTHON_EXEC="$VENV_PATH/bin/python" # Path to python interpreter in venv
PIP_EXEC="$VENV_PATH/bin/pip"       # Path to pip in venv
SCRIPT_TO_RUN_PATH="$SCRIPT_DIR/$PYTHON_SCRIPT"
REQUIREMENTS_FILE_PATH="$SCRIPT_DIR/$REQUIREMENTS_FILE"

# --- Main Script Logic ---
echo "--- Network Latency Monitor ---"

# 1. Check if Python 3 is available on the system
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found. Please install Python 3."
    exit 1
fi

# 2. Create the virtual environment if it doesn't exist
if [ ! -d "$VENV_PATH" ]; then
    echo "INFO: Creating virtual environment in '$VENV_PATH'..."
    python3 -m venv "$VENV_PATH"
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment. Check if 'python3-venv' package (or similar) is installed."
        exit 1
    fi
    echo "INFO: Virtual environment created successfully."
else
    echo "INFO: Virtual environment '$VENV_DIR' already exists."
fi

# 3. Install/update dependencies using the virtual environment's pip
if [ -s "$REQUIREMENTS_FILE_PATH" ]; then
    echo "INFO: Installing/updating dependencies from '$REQUIREMENTS_FILE' in the virtual environment..."
    # "$@" passes all command-line arguments received by run_monitor.sh to pip install 
    # (though unlikely to be used by pip here) and more importantly, 
    # to the python script later.
    "$PIP_EXEC" install --disable-pip-version-check --no-cache-dir -r "$REQUIREMENTS_FILE_PATH"
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install dependencies. Check '$REQUIREMENTS_FILE' and your internet connection."
        exit 1
    fi
    echo "INFO: Dependencies installed/updated successfully."
else
    echo "INFO: '$REQUIREMENTS_FILE' is empty or not found in '$SCRIPT_DIR', skipping dependency installation."
fi

# 4. Execute the Python script using the virtual environment's Python interpreter
#    First, check if the Python script itself exists
if [ ! -f "$SCRIPT_TO_RUN_PATH" ]; then
    echo "ERROR: Python script '$PYTHON_SCRIPT' not found in '$SCRIPT_DIR'."
    exit 1
fi

echo "INFO: Executing script '$PYTHON_SCRIPT' with arguments: $@" # Display arguments being passed
echo "--------------------------------------------------"
# Execute the python script, passing all arguments received by run_monitor.sh
# The Python script's stdout/stderr will go to the terminal.
"$PYTHON_EXEC" "$SCRIPT_TO_RUN_PATH" "$@"

# $? contains the exit code of the last executed command (the python script)
exit_status=$?
echo "--------------------------------------------------"
echo "INFO: Script '$PYTHON_SCRIPT' finished with exit code: $exit_status."

exit $exit_status
