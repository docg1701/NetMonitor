# Real-time Network Latency Monitor

A Python command-line tool to monitor and graph your internet connection latency in real-time directly in the terminal. This tool now supports Linux, macOS, and Windows.

![Screenshot of Network Monitor](screenshot2.webp)

## Overview

This script provides a continuously updating text-based graph of network ping latency to a specified host. It also displays key statistics such as current, average, minimum, and maximum latency, total monitoring time, and a count of consecutive ping failures. Failures are clearly marked on the graph.

Configuration is managed via CLI arguments or a `monitor_config.ini` file. The script uses the OS's native `ping` command.

## Features

* **Real-time Latency Graph:** Displays a scrolling graph of ping times directly in your terminal using `plotext`.
* **Cross-Platform:** Uses the native `ping` command of Linux, macOS, and Windows.
* **Configurable Parameters:**
    * Target host or IP address.
    * Interval between pings (in seconds).
    * Reference maximum for the Y-axis of the graph (in ms).
    * Approximate number of ticks on the Y-axis.
* **CSV Data Logging:** Optionally log all ping data (timestamp, host, resolved IP, latency in ms, success status) to a specified CSV file for later analysis. The CSV file includes the following columns: `Timestamp`, `MonitoredHost`, `ResolvedIP`, `LatencyMS`, `IsSuccess`.
* **Failure Indication:** Ping failures are visually distinguished on the graph with red 'X' markers at the base (0ms line), while the main data line shows 0ms for these points to maintain Y-axis scaling. A 'connection LOST' alert is triggered after a configurable number of consecutive failures (default is 3).
* **Key Statistics:** Shows current latency, average, P50 (Median), P95, P99, minimum, and maximum of successful pings, standard deviation (consistency of ping times), jitter (variation in delay between consecutive pings), packet loss percentage, total monitoring duration, and current consecutive ping failures.
* **Environment Setup Script:** Includes a `run_monitor.sh` script (for Linux/macOS/bash environments) to automatically create a Python virtual environment and install dependencies.
* **User-Friendly Display:** Uses ANSI escape codes for a smoother, non-flickering display update and hides the cursor during operation (terminal feature handling is best on POSIX systems).

### Pause and Resume
The monitor can be paused and resumed using the `SIGUSR1` signal. This is useful if you need to temporarily stop monitoring without exiting the script.

To pause or resume, send the `SIGUSR1` signal to the monitor's process ID (PID). You can find the PID using tools like `pgrep -f monitor_net.py` or `ps aux | grep monitor_net.py`.

Example command to send the signal:
```bash
kill -SIGUSR1 <PID>
```
Replace `<PID>` with the actual process ID.

*Note: This feature is generally available on Linux and macOS. It may not be available on Windows due to differences in signal handling.*

## Platform Compatibility

This tool is designed to run on:
*   **Linux:** Fully featured, including `termios` for terminal settings restoration on exit.
*   **macOS (Darwin):** Fully featured, including `termios`.
*   **Windows:** Functionally supported. The native Windows `ping` command is used.
    *   Terminal restoration via `termios` is skipped (as `termios` is POSIX-specific). Basic ANSI escape codes for cursor control are attempted and should work in modern Windows terminals (like Windows Terminal or PowerShell Core).

## Requirements

*   Python 3.8 or newer. This is required due to features like percentile statistics (which use `statistics.quantiles`) and modern packaging standards.
*   The native `ping` utility for your OS must be installed and accessible in your system's PATH.
    *   Linux/macOS: Usually pre-installed or part of `iputils-ping` (Linux).
    *   Windows: `ping.exe` is a standard system utility.
*   Python runtime dependencies (automatically installed if using `pip install .` or via helper scripts):
    *   `plotext` (for creating graphs in the terminal)
*   For development dependencies (like `pytest`, `flake8`, etc.), please see the "Installation" section on how to install them using `pip install .[dev]`.

## Getting the Code

1.  **Clone the Repository (or Download Files):**
    If you have Git installed, clone the repository:
    ```bash
    git clone https://github.com/galvani4987/monitor_net.git
    cd monitor_net
    ```
    Alternatively, download the files (`monitor_net.py`, `run_monitor.sh`, `run_monitor.bat`, `requirements.txt`, `pyproject.toml`) into a directory on your system.

2.  **Navigate to the Project Directory:**
    Open your terminal (or command prompt) and change to the directory where you cloned or downloaded the files.
    ```bash
    cd path/to/monitor_net
    ```

3.  **Make the `run_monitor.sh` Script Executable (Linux/macOS):**
    This step is crucial for running the setup and application script on Linux and macOS.
    ```bash
    chmod +x run_monitor.sh
    ```

## Installation

Once the package is available on PyPI, you can install it using pip:

```bash
pip install net-latency-monitor
```

This will install the script and its dependencies. After installation, you should be able
to run the monitor directly from your terminal:

```bash
netmonitor your.target.host
```

### Installing from TestPyPI (for testing)

If you want to install a pre-release or test version from TestPyPI, you can use:

```bash
pip install --index-url https://test.pypi.org/simple/ net-latency-monitor
```

### From Local Clone (Recommended for development or direct use)

After cloning the repository (see "Getting the Code"), you can install the package locally. This is useful for development or if you want to use the `netmonitor` command directly from your environment.

1.  Navigate to the project root directory (where `pyproject.toml` is located).
2.  Ensure you have Python 3.8+ and pip installed.
3.  It's highly recommended to use a Python virtual environment:
    ```bash
    python -m venv .venv_monitor_net
    source .venv_monitor_net/bin/activate  # On Linux/macOS
    # .\.venv_monitor_net\Scripts\activate.bat  # On Windows (cmd) - Note: use .bat
    # .\.venv_monitor_net\Scripts\Activate.ps1 # On Windows (PowerShell)
    ```
4.  Install the package (this will also install `plotext` and other dependencies):
    ```bash
    pip install .
    ```
5.  To install development dependencies (like `pytest`, `flake8`, etc.) as well:
    ```bash
    pip install .[dev]
    ```
After installation, the `netmonitor` command should be available in your PATH (if the virtual environment is active).

*(Note: If this package were published to PyPI, you could install it with `pip install net-latency-monitor`.)*

## Development using Makefile

A `Makefile` is provided to simplify common development tasks. To use it, ensure you have `make` installed on your system.

Here are some of the most useful targets:

*   `make venv`: Creates the Python virtual environment in `./.venv_monitor_net`.
*   `make install-dev`: Sets up the virtual environment (if needed) and installs the project in editable mode along with all development dependencies (pytest, flake8, black, etc.) as defined in `pyproject.toml`. This is typically the first command a developer should run.
*   `make test`: Runs the `pytest` test suite using the Python interpreter from the virtual environment.
*   `make clean`: Removes the virtual environment, build artifacts, and Python cache files (`__pycache__`, `*.pyc`).
*   `make help`: Displays a list of all available Makefile targets and their descriptions.

It is recommended to run `make install-dev` first to prepare your development environment. Subsequently, `make test` can be used to run tests, and `make clean` to tidy up the project directory.

## How to Use

There are several ways to run the network latency monitor:

### 1. Using the `netmonitor` Command (After Package Installation)

If you have installed the package as described in the "Installation" section, this is the recommended way to run the monitor.

```bash
netmonitor [host] [options]
# Example:
netmonitor example.com -i 0.5 --output-file log.csv
```
This command will use the Python environment where `net-latency-monitor` was installed.
All arguments listed under "Available Arguments" can be used.

### 2. Using Helper Scripts (for development or direct run without package installation)

These scripts manage a local virtual environment and run `monitor_net.py` directly.

#### Using `run_monitor.sh` (Linux/macOS/Windows with Bash)

For users on Linux, macOS, or Windows environments that support Bash (like Git Bash). It performs the following actions:
* Checks for Python 3.
* Creates a Python virtual environment named `.venv_monitor_net` within the project directory (if it doesn't already exist).
* Activates the virtual environment.
* Installs or updates the Python dependencies listed in `requirements.txt`.
* Executes the main `monitor_net.py` script, forwarding any provided arguments.

**Running with Default Settings:**
To start monitoring with the default settings (pinging `1.1.1.1` every `1.0` seconds, graph Y-axis reference up to `200ms`, and `6` Y-axis ticks):
```bash
./run_monitor.sh
```

**Using Command-Line Arguments:**
You can customize the behavior by passing arguments to `run_monitor.sh`. These arguments are then forwarded to `monitor_net.py`.
**Syntax:**
```bash
./run_monitor.sh [host] [options]
# Example:
./run_monitor.sh example.com -i 0.5 --output-file log.csv 
```
The available options are detailed in the "Available Arguments (for `monitor_net.py`)" section below.

#### Using `run_monitor.bat` (Windows Command Prompt / PowerShell)

For users on Windows using the native Command Prompt or PowerShell. It automates:
* A basic check for Python 3 in PATH.
* Creation of a Python virtual environment (`.venv_monitor_net`) if missing.
* Installation or update of dependencies from `requirements.txt` using pip from the virtual environment.
* Execution of `monitor_net.py`, passing along any command-line arguments.

**Running with Default Settings:**
Double-click `run_monitor.bat` or run from the command line:
```cmd
run_monitor.bat
```

**Using Command-Line Arguments:**
Arguments are passed to `monitor_net.py`.
```cmd
run_monitor.bat [host] [options]
REM Example:
run_monitor.bat example.com -i 0.5 --output-file log.csv
```
The available options are detailed in the "Available Arguments (for `monitor_net.py`)" section below.

### 3. Manual Setup (Any Platform)

If you prefer not to use the helper scripts or install the package, you can set up the environment and run the script manually:
1.  Ensure Python 3.8+ is installed and in your PATH.
2.  Create a virtual environment (recommended):
    ```bash
    python -m venv .venv_monitor_net 
    ```
3.  Activate the virtual environment:
    *   Linux/macOS: `source .venv_monitor_net/bin/activate`
    *   Windows (cmd): `.\.venv_monitor_net\Scripts\activate.bat`
    *   Windows (PowerShell): `.\.venv_monitor_net\Scripts\Activate.ps1`
4.  Install dependencies:
    ```bash
    pip install -r requirements.txt 
    ```
    (Note: `requirements.txt` now primarily lists runtime dependencies. For development tools, consider `pip install .[dev]` after cloning if you also want to edit the source and have dev tools.)
5.  Run the script:
    ```bash
    python monitor_net.py [host] [options]
    ```

**Available Arguments (for `monitor_net.py` or `netmonitor` command):**

* `host`: (Positional, Optional) The host or IP address you want to ping.
    * Default: `1.1.1.1`
* `-i INTERVAL`, `--interval INTERVAL`: (Optional) The time in seconds between each ping. Accepts float values (e.g., 0.5).
    * Default: `1.0` second
* `--ymax YMAX`: (Optional) Sets the reference maximum value for the Y-axis of the graph, in milliseconds. The graph will display at least up to this value but will auto-expand if latency spikes exceed it.
    * Default: `200.0` ms
* `--yticks YTICKS`: (Optional) Specifies the desired approximate number of discrete tick marks (and their labels) to display on the Y-axis.
    * Default: `6`
* `-o FILEPATH`, `--output-file FILEPATH`: (Optional) Path to a CSV file where latency data will be logged. Each ping attempt (success or failure) will be appended as a new row. If the file doesn't exist, it will be created, including a header row.
    * Default: None
* `-at THRESHOLD`, `--alert-threshold THRESHOLD`: (Optional) Number of consecutive ping failures to trigger a connection LOST alert. Must be an integer >= 1. 
    * Default: 3

## Configuration File (`monitor_config.ini`)

Beyond command-line arguments, `monitor_net.py` can be configured using an INI file named `monitor_config.ini`. This file allows you to set your preferred defaults without needing to type them as command-line arguments every time.

**Location:**
The `monitor_config.ini` file must be placed in the same directory as the `monitor_net.py` script.

**Precedence of Settings:**
The script determines the final settings using the following order of precedence:
1.  **Command-line arguments:** If a setting is provided as a command-line argument, it will always be used, overriding any other source. (Highest precedence)
2.  **Values from `monitor_config.ini`:** If a setting is not provided via a command-line argument, the script will look for it in the configuration file.
3.  **Built-in script defaults:** If a setting is not found in either the command-line arguments or the configuration file, the script's hardcoded default value will be used. (Lowest precedence)

**File Structure and Example:**
The configuration file must contain a section named `[MonitorSettings]`. Supported keys under this section are:

```ini
[MonitorSettings]
host = your.default.host.com
interval = 2.0
ymax = 100.0
yticks = 4
output_file = /path/to/your/latency_log.csv
alert_threshold = 5
```

**Supported Keys and Types:**
*   `host`: The default host or IP address to ping. (Type: string)
*   `interval`: The default interval between pings in seconds. (Type: float)
*   `ymax`: The default reference maximum Y-axis value for the graph in milliseconds. (Type: float)
*   `yticks`: The default approximate number of Y-axis ticks. (Type: int)
*   `output_file`: Path to the CSV file for logging data. If the path is relative, it's relative to where the script is run. (Type: string)
*   `alert_threshold`: Number of consecutive failures before triggering a "connection LOST" alert. (Type: integer, must be >= 1)

If the `monitor_config.ini` file contains invalid values (e.g., non-numeric for `interval`), that specific setting will be ignored with a warning message, and the script will fall back to the built-in script default (unless a command-line argument for that setting is provided).

**Examples (cross-platform, adjust execution for Windows as shown above):**

* Monitor the host `1.1.1.1` with a ping interval of 1.5 seconds:
    ```bash
    # Linux/macOS/Bash:
    ./run_monitor.sh 1.1.1.1 --interval 1.5
    # Windows (cmd/powershell, venv active):
    # python monitor_net.py 1.1.1.1 --interval 1.5
    ```

* Monitor the default host with a Y-axis reference up to 100ms and 5 Y-axis ticks:
    ```bash
    # Linux/macOS/Bash:
    ./run_monitor.sh --ymax 100 --yticks 5
    # Windows (cmd/powershell, venv active):
    # python monitor_net.py --ymax 100 --yticks 5
    ```

* Monitor `example.com`, logging results to `ping_log.csv` in the current directory:
    ```bash
    # Linux/macOS/Bash:
    ./run_monitor.sh example.com --output-file ./ping_log.csv
    # Windows (cmd/powershell, venv active):
    # python monitor_net.py example.com --output-file .\ping_log.csv
    ```

**Stopping the Monitor:**
To stop the script, press `Ctrl+C` in the terminal where it is running.

## Files in the Project

* `monitor_net.py`: The main Python script containing the monitoring and plotting logic.
* `run_monitor.sh`: A shell script (for Linux/macOS/Bash) that automates the setup of the Python virtual environment, installation of dependencies, and execution of `monitor_net.py`.
* `run_monitor.bat`: A Windows batch script that automates the setup of the Python virtual environment, installation of dependencies, and execution of `monitor_net.py`.
* `requirements.txt`: A file listing the Python package dependencies.
* `pyproject.toml`: Defines project metadata and build dependencies for packaging.
* `ROADMAP.md`: Outlines potential future improvements and features.
* `README.md`: This file, providing documentation for the project.
* `.gitignore`: Specifies intentionally untracked files that Git should ignore.
* `screenshot*.*`: Example screenshots of the monitor in action.

## Troubleshooting

* **`CRITICAL ERROR: 'ping' command not found...`**: Ensure the `ping` utility is installed on your system and is in your system's PATH.
* **Graph not displaying well / `WARNING: Calculated plot area is too small...`**: Try increasing the height and width of your terminal window. The script attempts to adapt, but very small terminal sizes can limit graph rendering.
* **Python errors**: Ensure you have Python 3.8+ installed and that dependencies from `requirements.txt` are installed in your active environment.

## Contributing

This is a small personal project, but if you have suggestions or improvements:
1.  Fork the repository.
2.  Create a new branch for your feature or bug fix.
3.  Make your changes.
4.  Submit a pull request with a clear description of your changes.
