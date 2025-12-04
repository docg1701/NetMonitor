# Improvement Roadmap for the Real-time Network Latency Monitor

This document outlines the implementation plan for the suggested improvements to the `monitor_net` project. Each section represents an area of improvement with its respective steps.

## Phase 1: Foundations and Style

### 1.1. Code Style Consistency
* **Objective:** Ensure clean, readable, and standardized code.
* **Tools:** `ruff` for linting and formatting.
* **Steps:**
    * [X] Install `ruff` and `black` in the development environment (`pip install ruff black`).
    * [X] Run `ruff check monitor_net.py` and fix all reported warnings and errors.
    * [X] Run `black monitor_net.py` to format the code automatically.
    * [X] Add a configuration file for `flake8` (e.g., `.flake8`) if customizations are needed. (Superseded by ruff configuration in `pyproject.toml`)
    * [X] Consider adding a pre-commit hook (e.g., with `pre-commit`) to automate style checking before each commit. (Ruff hooks for linting and formatting added in `.pre-commit-config.yaml`)

### 1.2. Constants for ANSI Codes and "Magic Numbers"
* **Objective:** Improve readability and maintainability by replacing hardcoded values with named constants.
* **Main File:** `monitor_net.py`
* **Steps:**
    * [X] Identify all ANSI escape codes (e.g., `\033[H`, `\033[J`, `\033[?25l`, `\033[?25h`) in `monitor_net.py`.
    * [X] Define named constants for each ANSI code at the beginning of the script (e.g., `ANSI_CURSOR_HOME = "\033[H"`).
    * [X] Identify "magic numbers" (e.g., `15` for `overhead_lines`, `MAX_DATA_POINTS = 200`, `CONSECUTIVE_FAILURES_ALERT_THRESHOLD = 3`, `STATUS_MESSAGE_RESERVED_LINES = 3`). Some are already constants; check if all relevant ones are covered.
    * [X] Replace all occurrences of hardcoded values with the defined constants.

## Phase 2: Major Refactoring

### 2.1. Encapsulation with Classes
* **Objective:** Improve code organization, reduce the use of global variables, and facilitate future testing and extensions.
* **Main File:** `monitor_net.py`
* **Steps:**
    * [X] Define a new class, for example, `NetworkMonitor`, in `monitor_net.py`.
    * [X] Move global state variables (e.g., `latency_plot_values`, `latency_history_real_values`, `consecutive_ping_failures`, `connection_status_message`, `total_monitoring_time_seconds`) to become instance attributes of the class (initialized in `__init__`).
    * [X] Move default configuration variables (e.g., `DEFAULT_HOST`, `DEFAULT_PING_INTERVAL_SECONDS`) to become class or instance attributes, as appropriate. CLI arguments can update instance attributes.
    * [X] Convert main functions (`measure_latency`, `update_display_and_status`, and the `while True` loop logic within `main`) into methods of the `NetworkMonitor` class.
    * [X] The class's `__init__` method can receive parsed CLI arguments to configure the instance.
    * [X] The original `main` function will be simplified to:
        * Parse CLI arguments.
        * Instantiate `NetworkMonitor` with these arguments.
        * Call a main method of the instance (e.g., `monitor.run()`) that contains the monitoring loop.
    * [X] Ensure that `KeyboardInterrupt` handling and cursor/terminal restoration (`termios`) are managed correctly within the class or by the `run` method.

### 2.2. Refactoring Long Functions
* **Objective:** Increase clarity and modularity of the `update_display_and_status` function (which will become a class method).
* **Target Method:** `NetworkMonitor.update_display_and_status` (after refactoring 2.1).
* **Steps:**
    * [X] Analyze the `update_display_and_status` method and identify distinct logical blocks.
    * [X] For each block, create a new private method (prefixed with an underscore) within the `NetworkMonitor` class. Suggestions:
        * `[X] _display_status_message(self)`
        * `[X] _prepare_plot_area(self)` (to get terminal size, calculate `plot_height`, `plot_width`)
        * `[X] _configure_plot_axes_and_labels(self)`
        * `[X] _plot_latency_series(self)` (for `pltx.plot` and `pltx.scatter`)
        * `[X] _render_plot(self)` (for `pltx.show()`)
        * `[X] _display_statistics(self)`
    * [X] The original `update_display_and_status` method will call these new private methods in sequence.

## Phase 3: Features and Robustness

### 3.1. Enhanced Error Handling and Logging
* **Objective:** Implement a more flexible and structured logging system.
* **Main File:** `monitor_net.py`
* **Steps:**
    * [X] Import Python's `logging` module.
    * [X] Configure a basic logger at the beginning of the script or in the `NetworkMonitor` class's `__init__` (e.g., `logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')`).
    * [X] Replace `print()` and `sys.stdout.write()` calls used for status messages, warnings, and errors with logger calls (e.g., `logger.info()`, `logger.warning()`, `logger.error()`, `logger.critical()`, `logger.debug()`).
    * [X] Review the `FileNotFoundError` exception handling for the `ping` command to ensure the message is clear and logged appropriately via the logger, avoiding duplication.

### 3.2. Clarity in Failure Plotting Logic (Review)
* **Objective:** Ensure that the logic for representing failures on the graph is clear and well-documented.
* **Main File:** `monitor_net.py`
* **Steps:**
    * [X] Review and add detailed comments explaining why `latency_plot_values` uses `0` for failures and `latency_history_real_values` uses `None`, and how both are used in plotting.
    * [X] (Optional) Consider if a unified data structure for each history point (e.g., a `collections.namedtuple` or a small `DataPoint` class with attributes like `real_value` and `plot_value`) would simplify logic or improve readability. If there's no clear benefit, maintain the current structure with good comments. (Added a # FUTURE comment).

### 3.3. Review of Docstrings and Comments
* **Objective:** Ensure all code is well-documented.
* **Main File:** `monitor_net.py`
* **Steps:**
    * [X] Go through all classes and methods/functions.
    * [X] Write or update docstrings for each, explaining its purpose, arguments (types and description), what it returns, and any exceptions it might raise. Use a standard format (e.g., reStructuredText or Google style).
    * [X] Add/review inline comments for complex code sections or non-obvious logic.

## Phase 4: Testing and Maintenance

### 4.1. Implementation of Automated Tests
* **Objective:** Create a test suite to ensure code correctness and facilitate future refactorings.
* **Tools:** `unittest` (standard) or `pytest`.
* **Steps:**
    * [X] Choose a testing framework (`pytest` is generally recommended for its simplicity).
    * [X] Create a test directory (e.g., `tests/`).
    * [X] Set up the environment to run tests.
    * [X] Write unit tests for:
        * [X] The `ping` output parsing method (within `measure_latency`), covering different valid output formats, failure cases, and timeouts. (This may require mocking `subprocess.run`). (Done for `_measure_latency`)
        * [X] Functions/methods that perform statistical calculations. (Done for `_calculate_average_latency`, etc.)
        * [X] CLI argument validation. (Done for `main()`)
        * [X] (If a class is implemented) Test class initialization and the logic of its main methods.
    * [X] Consider simple integration tests that simulate running the monitor for a few cycles (can be more complex). (Done for `run()` method)
    * [X] Integrate test execution into a script or Makefile. (Makefile includes a 'test' target using pytest)

### 4.2. Improvements to `run_monitor.sh` Script (Minor)
* **Objective:** Small adjustments for robustness.
* **Main File:** `run_monitor.sh`
* **Steps:**
    * [X] (Optional) Add a check if the `REQUIREMENTS_FILE` (`requirements.txt`) is empty before calling `pip install -r`. If empty, perhaps skip the installation step or issue a message. `pip` usually handles this well, so it's low priority. (Implemented this check)

## Additional Considerations
* **Version Control:** Use Git and make small, descriptive commits for each step or logical group of changes.
* **Branches:** Consider using feature branches for major improvements (e.g., refactoring to a class, implementing tests).
* **Code Review:** If possible, have someone else review the changes.

This roadmap is a suggestion and can be adjusted as needed. It is recommended to first focus on improvements that will have the greatest impact on code organization and maintainability.

## Phase 5: Core Functionality Expansion

### 5.1. Cross-Platform Compatibility (Windows/macOS)
*   **Objective:** Allow the `monitor_net.py` script to run on Windows and macOS in addition to Linux.
*   **Considerations:**
    *   [X] Abstract ping functionality:
        *   [X] Detect OS (e.g., using `platform.system()`).
        *   [X] Use different ping commands (`ping -n 1` for Windows, `ping -c 1` for macOS/Linux).
        *   [X] Adapt regex for parsing ping output for each platform.
    *   [X] Investigate cross-platform terminal control alternatives if `termios` (POSIX-specific) or `plotext` present issues. (Plotext aims to be cross-platform, but terminal interactions can vary).
    *   [ ] Test thoroughly on all target platforms (Windows, macOS, common Linux distributions).
    *   [X] Update `README.md` with platform-specific notes if any.

### 5.2. Configuration File Support
*   **Objective:** Allow users to specify settings (host, interval, ymax, yticks, etc.) via a configuration file (e.g., INI, YAML, JSON) instead of only CLI arguments.
*   **Considerations:**
    *   [X] Choose a configuration file format (e.g., `configparser` for INI, `PyYAML` for YAML, `json` for JSON). Add new dependency if needed.
    *   [X] Implement logic to find and read settings from a configuration file (e.g., `monitor_config.ini` in the user's home directory or script directory).
    *   [X] Define precedence: CLI arguments should override configuration file settings, which override built-in defaults.
    *   [X] Update help messages to mention the configuration file.
    *   [X] Provide a sample configuration file.

## Phase 6: Data & Insights

### 6.1. Output Options / Data Export
*   **Objective:** Allow users to save latency data and statistics to a file.
*   **Considerations:**
    *   [X] Add CLI arguments to specify an output file and format (e.g., `--output-file data.csv --output-format csv`).
    *   [X] Support formats like CSV, JSON.
    *   [X] Decide what data to save (timestamps, latency, failures, summary statistics).
    *   [X] Implement file writing logic, possibly appending data periodically.

### 6.2. More Advanced Statistics/Analysis
*   **Objective:** Provide more insightful statistics beyond basic min/max/avg.
*   **Considerations:**
    *   [X] Calculate standard deviation to show variability.
    *   [X] Calculate jitter (variation in latency between pings).
    *   [X] Show a histogram or percentile distribution of latencies over the session. (Percentiles implemented)
    *   [X] Track packet loss percentage more explicitly.
    *   [X] (Added for percentiles implementation) Calculate and display key percentiles (P50, P95, P99).
    *   [X] (Added for tests) Write unit tests for new statistical calculation methods.
    *   [X] (Added for docs) Document new statistics in README.

## Phase 7: User Experience & Distribution

### 7.1. Code Packaging and Distribution
*   **Objective:** Make the script easier to install and run for end-users.
*   **Considerations:**
    *   [X] Create a `setup.py` or `pyproject.toml` file.
    *   [X] Define entry points so the script can be run as a command after installation (e.g., `netmonitor` instead of `python monitor_net.py`).
    *   [X] Consider packaging as a wheel and distributing on PyPI.
    *   [X] Update `README.md` with installation instructions.

### 7.2. Interactive Commands (Advanced)
*   **Objective:** Allow users to interact with the running monitor (e.g., pause, change settings).
*   **Considerations:**
    *   [ ] This is complex for a terminal UI. Might involve `curses` or a more advanced TUI library if `plotext` doesn't support it.
    * [X] Could start with simple signal handling (e.g., a signal to toggle pause). (Implemented SIGUSR1 for pause/resume)
    * [X] Example commands: pause/resume (done), [ ] change target host, [ ] clear history.

## Phase 8: Advanced Features & Polish

### 8.1. Enhanced Alerting
*   **Objective:** More flexible and noticeable alerting mechanisms.
*   **Considerations:**
    *   [X] Configurable alert thresholds (e.g., latency > X ms for Y consecutive pings).
    *   [ ] Different alert types (e.g., visual change in graph, sound alert if possible and desired).
    *   [ ] Option for persistent alerts until acknowledged.
    *   [X] (Added for implementation) Use configured threshold in `run()` loop.
    *   [X] (Added for tests) Write unit tests for alert threshold logic.
    *   [X] (Added for docs) Document configurable alert threshold in README.

### 8.2. Historical Data Viewing/Scrolling (Advanced)
*   **Objective:** Allow users to view more than just the current screen of data points.
*   **Considerations:**
    *   [ ] This would significantly increase complexity with `plotext`. May require a different plotting approach or library.
    *   [ ] Could involve saving all data and then providing an option to generate a static plot of a larger history.

### 8.3. Formatting and Line Length (Handled by Ruff)
*   **Objective:** Ensure consistent formatting and adherence to line length.
*   **Considerations:**
    *   [X] This is now handled by `ruff format` (integrated into pre-commit) and the `line-length = 88` setting in `pyproject.toml` for `ruff`. The previous flake8-specific E501 issues are superseded by ruff's formatter.

This roadmap provides a comprehensive list of potential future enhancements.
Priorities can be adjusted based on user feedback and development resources.
