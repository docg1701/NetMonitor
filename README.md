# Real-time Network Latency Monitor

A Python command-line tool to monitor and graph your internet connection latency in real-time directly in the terminal. This tool now supports Linux, macOS, and Windows.

![Screenshot of Network Monitor](screenshot2.webp)

## Overview

This script provides a continuously updating text-based graph of network ping latency to a specified host. It also displays key statistics such as current, average, minimum, and maximum latency, total monitoring time, and a count of consecutive ping failures. Failures are clearly marked on the graph.

The tool is configurable via command-line arguments for the target host, ping interval, Y-axis maximum reference, and the number of Y-axis ticks, or alternatively, through a `monitor_config.ini` file. It leverages the native `ping` command of the underlying operating system.

## Features

* **Real-time Latency Graph:** Displays a scrolling graph of ping times directly in your terminal using `plotext`.
* **Cross-Platform:** Uses the native `ping` command of Linux, macOS, and Windows.
* **Configurable Parameters:**
    * Target host or IP address.
    * Interval between pings (in seconds).
    * Reference maximum for the Y-axis of the graph (in ms).
    * Approximate number of ticks on the Y-axis.
* **CSV Data Logging:** Optionally log all ping data (timestamp, host, resolved IP, latency in ms, success status) to a specified CSV file for later analysis. The CSV file includes the following columns: `Timestamp`, `MonitoredHost`, `ResolvedIP`, `LatencyMS`, `IsSuccess`.
* **Failure Indication:** Ping failures are visually distinguished on the graph with red 'X' markers at the base (0ms line), while the main data line shows 0ms for these points to maintain Y-axis scaling.
* **Key Statistics:** Shows current latency, average of valid pings, minimum and maximum valid pings, total monitoring duration, and current consecutive ping failures.
* **Environment Setup Script:** Includes a `run_monitor.sh` script (for Linux/macOS/bash environments) to automatically create a Python virtual environment and install dependencies.
* **User-Friendly Display:** Uses ANSI escape codes for a smoother, non-flickering display update and hides the cursor during operation (terminal feature handling is best on POSIX systems).

## Platform Compatibility

This tool is designed to run on:
*   **Linux:** Fully featured, including `termios` for terminal settings restoration on exit.
*   **macOS (Darwin):** Fully featured, including `termios`.
*   **Windows:** Functionally supported. The native Windows `ping` command is used.
    *   Terminal restoration via `termios` is skipped (as `termios` is POSIX-specific). Basic ANSI escape codes for cursor control are attempted and should work in modern Windows terminals (like Windows Terminal or PowerShell Core).
    *   Users may need to run the script directly using `python monitor_net.py` (see "How to Use on Windows").

## Requirements

*   Python 3.6 or newer.
*   The native `ping` utility for your OS must be installed and accessible in your system's PATH.
    *   Linux/macOS: Usually pre-installed or part of `iputils-ping` (Linux).
    *   Windows: `ping.exe` is a standard system utility.
*   Python dependencies (installed by `run_monitor.sh` or manually with `pip`):
    *   `plotext` (for creating graphs in the terminal)
    *   `pytest` (for running tests, development only)
    *   `pytest-mock` (for running tests, development only)

## Setup Instructions

1.  **Clone the Repository (or Download Files):**
    If you have Git installed, clone the repository:
    ```bash
    git clone https://github.com/galvani4987/monitor_net.git
    cd monitor_net
    ```
    Alternatively, download the files (`monitor_net.py`, `run_monitor.sh`, `requirements.txt`) into a directory on your system.

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

## How to Use

### For Linux, macOS, or Windows with Bash (e.g., Git Bash):

The `run_monitor.sh` script is the recommended way to start the latency monitor. It performs the following actions:
* Checks for Python 3.
* Creates a Python virtual environment named `.venv_monitor_net` within the project directory (if it doesn't already exist).
* Activates the virtual environment and installs (or updates) the Python dependencies listed in `requirements.txt`.
* Executes the main `monitor_net.py` script with any provided arguments.

**Running with Default Settings:**
To start monitoring with the default settings (pinging `1.1.1.1` every `1.0` seconds, graph Y-axis reference up to `200ms`, and `6` Y-axis ticks):
```bash
./run_monitor.sh
```

**Using Command-Line Arguments:**
You can customize the behavior by passing arguments to `run_monitor.sh`. These arguments are then forwarded to the `monitor_net.py` script.

**Syntax:**
```bash
./run_monitor.sh [host] [-i INTERVAL] [--ymax YMAX] [--yticks YTICKS]
```

### For Windows (without Bash, e.g., Command Prompt / PowerShell):

1.  **Ensure Python 3 is in your PATH.**
2.  **Create a virtual environment (recommended):**
    ```cmd
    python -m venv .venv_monitor_net
    ```
3.  **Activate the virtual environment:**
    ```cmd
    .\.venv_monitor_net\Scripts\activate
    ```
4.  **Install dependencies:**
    ```cmd
    pip install -r requirements.txt
    ```
5.  **Run the script:**
    ```cmd
    python monitor_net.py [host] [-i INTERVAL] [--ymax YMAX] [--yticks YTICKS]
    ```

**Available Arguments (for `monitor_net.py`):**

* `host`: (Positional, Optional) The host or IP address you want to ping.
    * Default: `1.1.1.1` (as defined by `DEFAULT_HOST_ARG` in the script)
* `-i INTERVAL`, `--interval INTERVAL`: (Optional) The time in seconds between each ping. Accepts float values (e.g., 0.5).
    * Default: `1.0` second (as defined by `DEFAULT_PING_INTERVAL_SECONDS_ARG`)
* `--ymax YMAX`: (Optional) Sets the reference maximum value for the Y-axis of the graph, in milliseconds. The graph will display at least up to this value but will auto-expand if latency spikes exceed it.
    * Default: `200.0` ms (as defined by `DEFAULT_GRAPH_Y_MAX_ARG`)
* `--yticks YTICKS`: (Optional) Specifies the desired approximate number of discrete tick marks (and their labels) to display on the Y-axis.
    * Default: `6` (as defined by `DEFAULT_Y_TICKS_ARG`)
* `-o FILEPATH`, `--output-file FILEPATH`: (Optional) Path to a CSV file where latency data will be logged. Each ping attempt (success or failure) will be appended as a new row. If the file doesn't exist, it will be created, including a header row.

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
```

**Supported Keys and Types:**
*   `host`: The default host or IP address to ping. (Type: string)
*   `interval`: The default interval between pings in seconds. (Type: float)
*   `ymax`: The default reference maximum Y-axis value for the graph in milliseconds. (Type: float)
*   `yticks`: The default approximate number of Y-axis ticks. (Type: int)
*   `output_file`: Path to the CSV file for logging data. If the path is relative, it's relative to where the script is run. (Type: string)

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
* `requirements.txt`: A file listing the Python package dependencies.
* `ROADMAP.md`: Outlines potential future improvements and features.
* `README.md`: This file, providing documentation for the project.
* `.gitignore`: Specifies intentionally untracked files that Git should ignore.
* `screenshot*.*`: Example screenshots of the monitor in action.

## Troubleshooting

* **`CRITICAL ERROR: 'ping' command not found...`**: Ensure the `ping` utility is installed on your system and is in your system's PATH.
* **Graph not displaying well / `WARNING: Calculated plot area is too small...`**: Try increasing the height and width of your terminal window. The script attempts to adapt, but very small terminal sizes can limit graph rendering.
* **Python errors**: Ensure you have Python 3.6+ installed and that dependencies from `requirements.txt` are installed in your active environment.

## Contributing

This is a small personal project, but if you have suggestions or improvements:
1.  Fork the repository.
2.  Create a new branch for your feature or bug fix.
3.  Make your changes.
4.  Submit a pull request with a clear description of your changes.
