import time
import os
import subprocess
import re
import plotext as pltx  # For plotting in the terminal
import sys
import argparse
import termios  # POSIX-specific module for terminal I/O control
import logging
import platform  # For OS detection
import configparser  # For reading configuration file
import csv  # For CSV logging
from datetime import datetime  # For timestamping CSV entries
import socket # For resolving IP address for CSV logging
# Note: 'os' is imported near the top of the file already

# --- ANSI Escape Codes ---
ANSI_CURSOR_HOME = "\033[H"
ANSI_CLEAR_FROM_CURSOR_TO_END = "\033[J"
ANSI_HIDE_CURSOR = "\033[?25l"
ANSI_SHOW_CURSOR = "\033[?25h"

# --- Application Specific Constants ---
PLOT_ESTIMATED_OVERHEAD_LINES = 15
PLOT_MIN_HEIGHT_LINES = 5
PLOT_MIN_WIDTH_CHARS = 20
PLOT_MIN_Y_LIM_UPPER = 10.0  # Minimum Y-axis upper limit for the graph
PLOT_FAILURE_MARKER_Y_BASE = 0  # Y-value for placing failure 'X' markers

PING_MIN_TIMEOUT_S = 1  # Minimum timeout for the ping command itself
SUBPROCESS_MIN_TIMEOUT_S_BASE = 2.0  # Base for subprocess.run timeout
SUBPROCESS_TIMEOUT_S_ADDITIVE = 1.0  # Added to ping interval for subprocess

EXIT_CODE_SUCCESS = 0
EXIT_CODE_ERROR = 1

# --- Configuration Constants ---
# These are accessed by the NetworkMonitor class constructor
MAX_DATA_POINTS = 200
CONSECUTIVE_FAILURES_ALERT_THRESHOLD = 3
STATUS_MESSAGE_RESERVED_LINES = 3

CONFIG_FILE_NAME = "monitor_config.ini"


# Default values for command-line arguments
DEFAULT_HOST_ARG = "1.1.1.1"
DEFAULT_PING_INTERVAL_SECONDS_ARG = 1.0
DEFAULT_GRAPH_Y_MAX_ARG = 200.0
DEFAULT_Y_TICKS_ARG = 6


class NetworkMonitor:
    """
    Monitors network latency to a specified host by sending ICMP pings
    at regular intervals. Displays a real-time updating graph of latency
    in the terminal using plotext and provides statistics.
    """

    def __init__(self, args: argparse.Namespace):
        """
        Initializes the NetworkMonitor instance.

        Args:
            args (argparse.Namespace): Parsed command-line arguments.
                Expected attributes: host, interval, ymax, yticks.
        """
        # Configuration from command line arguments
        self.host: str = args.host
        self.ping_interval: float = args.interval
        self.graph_y_max: float = args.ymax
        self.y_ticks: int = args.yticks

        # Configuration constants
        self.max_data_points: int = MAX_DATA_POINTS
        self.consecutive_failures_threshold: int = CONSECUTIVE_FAILURES_ALERT_THRESHOLD
        self.status_message_reserved_lines: int = STATUS_MESSAGE_RESERVED_LINES

        # State variables
        self.latency_plot_values: list[float] = []
        self.latency_history_real_values: list[float | None] = []
        self.consecutive_ping_failures: int = 0
        self.connection_status_message: str = ""
        self.total_monitoring_time_seconds: float = 0.0
        self.original_terminal_settings = None
        self.current_os: str = ""  # Will be set before logger
        self.config_file_settings: dict = {}  # For settings from INI file
        self.output_file_path: str | None = None # For CSV logging
        self.output_file_handle = None # File handle for CSV
        self.csv_writer = None # CSV writer object
        self.resolved_ip: str | None = None # Resolved IP of the host for logging

        # Determine OS type first, as it might influence other setups
        self.current_os = platform.system().lower()

        # Setup logger
        logger_name = f"{__name__}.{self.__class__.__name__}"
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.INFO)

        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
        )
        handler.setFormatter(formatter)

        if not self.logger.handlers:
            self.logger.addHandler(handler)
        self.logger.propagate = False

        self.logger.info(f"Detected OS: {self.current_os}")

        # Initialize config_file_settings before determining final settings
        self.config_file_settings: dict = {}
        self._load_config_from_file()

        # Determine final settings with precedence: CLI > Config File > Defaults
        self._determine_effective_settings(args)

        # Platform-specific ping command attributes
        self.ping_cmd_parts: list[str] = []
        self.ping_regex: re.Pattern[str]
        self.ping_timeout_is_ms: bool = False

        if self.current_os == "windows":
            # For Windows: ping -n 1 -w <timeout_ms> <host>
            # Timeout is in milliseconds.
            self.ping_cmd_parts = ["ping", "-n", "1", "-w"]
            # Regex for Windows might be like: "Average = Xms", or "Minimum = Xms, Maximum = Yms, Average = Zms"
            # A common pattern for individual time is "time=XXms" or "Reply from ... time<XXms"
            # This regex aims for "time=Xms" or "time<Xms" or "Time: Xms" etc.
            self.ping_regex = re.compile(r"time(?:<|=)(\d+)\s*ms", re.IGNORECASE)
            self.ping_timeout_is_ms = True
        elif self.current_os == "darwin":  # macOS
            # For macOS: ping -c 1 -t <timeout_s> <host>
            # Timeout is in seconds.
            self.ping_cmd_parts = ["ping", "-c", "1", "-t"]
            self.ping_regex = re.compile(r"time=([0-9\.]+)\s*ms", re.IGNORECASE)
            self.ping_timeout_is_ms = False
        else:  # Default to Linux
            # For Linux: ping -c 1 -W <timeout_s> <host>
            # Timeout is in seconds (-W for Linux, -t for macOS uses same unit)
            self.ping_cmd_parts = ["ping", "-c", "1", "-W"]
            self.ping_regex = re.compile(r"time=([0-9\.]+)\s*ms", re.IGNORECASE)
            self.ping_timeout_is_ms = False

    @staticmethod
    def _convert_setting(
        value_str: str | None,
        target_type_func,
        setting_name: str,
        logger: logging.Logger,
    ):
        """
        Attempts to convert a string value to a target type.
        Logs a warning and returns None if conversion fails.
        """
        if value_str is None:
            return None
        try:
            return target_type_func(value_str)
        except ValueError:
            logger.warning(
                f"Invalid value '{value_str}' for '{setting_name}' in config "
                "file. It will be ignored."
            )
            return None

    def _determine_effective_settings(self, cli_args: argparse.Namespace):
        """
        Determines the final settings based on precedence:
        CLI > Config File > Script Defaults.
        Updates self.host, self.ping_interval, self.graph_y_max, self.y_ticks.
        """
        # Start with ultimate script defaults
        final_host = DEFAULT_HOST_ARG
        final_interval = DEFAULT_PING_INTERVAL_SECONDS_ARG
        final_ymax = DEFAULT_GRAPH_Y_MAX_ARG
        final_yticks = DEFAULT_Y_TICKS_ARG
        final_output_file = None # Default to no output file

        # 1. Apply Config File Settings (if they exist and are valid)
        cfg_host = self.config_file_settings.get("host")
        if cfg_host is not None:
            final_host = cfg_host
            self.logger.info(f"Using 'host' from config file: {final_host}")

        cfg_interval_str = self.config_file_settings.get("interval")
        if cfg_interval_str is not None:
            converted_interval = NetworkMonitor._convert_setting(
                cfg_interval_str, float, "interval", self.logger
            )
            if converted_interval is not None:
                final_interval = converted_interval
                self.logger.info(f"Using 'interval' from config file: {final_interval}")

        cfg_ymax_str = self.config_file_settings.get("ymax")
        if cfg_ymax_str is not None:
            converted_ymax = NetworkMonitor._convert_setting(
                cfg_ymax_str, float, "ymax", self.logger
            )
            if converted_ymax is not None:
                final_ymax = converted_ymax
                self.logger.info(f"Using 'ymax' from config file: {final_ymax}")

        cfg_yticks_str = self.config_file_settings.get("yticks")
        if cfg_yticks_str is not None:
            converted_yticks = NetworkMonitor._convert_setting(
                cfg_yticks_str, int, "yticks", self.logger
            )
            if converted_yticks is not None:
                final_yticks = converted_yticks
                self.logger.info(f"Using 'yticks' from config file: {final_yticks}")

        cfg_output_file = self.config_file_settings.get("output_file")
        if cfg_output_file is not None and cfg_output_file.strip(): # Ensure not empty string
            final_output_file = cfg_output_file.strip()
            self.logger.info(f"Using 'output_file' from config file: {final_output_file}")

        # 2. Apply CLI arguments (these override config and defaults if specified by user)
        # Check if CLI arg is different from its argparse-defined default.
        # If so, the user explicitly set it.
        if cli_args.host != DEFAULT_HOST_ARG:
            final_host = cli_args.host
            self.logger.info(f"CLI 'host' ({final_host}) overrides other settings.")
        if cli_args.interval != DEFAULT_PING_INTERVAL_SECONDS_ARG:
            final_interval = cli_args.interval
            self.logger.info(
                f"CLI 'interval' ({final_interval}) overrides other settings."
            )
        if cli_args.ymax != DEFAULT_GRAPH_Y_MAX_ARG:
            final_ymax = cli_args.ymax
            self.logger.info(f"CLI 'ymax' ({final_ymax}) overrides other settings.")
        if cli_args.yticks != DEFAULT_Y_TICKS_ARG:
            final_yticks = cli_args.yticks
            self.logger.info(f"CLI 'yticks' ({final_yticks}) overrides other settings.")

        # For output_file, its argparse default is None.
        # So, if cli_args.output_file is not None, the user specified it.
        if cli_args.output_file is not None:
            final_output_file = cli_args.output_file
            self.logger.info(
                f"CLI 'output_file' ({final_output_file}) overrides other settings."
            )

        # Set the final effective settings on the instance
        self.host = final_host
        self.ping_interval = final_interval
        self.graph_y_max = final_ymax
        self.y_ticks = final_yticks
        self.output_file_path = final_output_file

        # Log final effective settings
        self.logger.info(f"Effective host: {self.host}")
        self.logger.info(f"Effective interval: {self.ping_interval}s")
        self.logger.info(f"Effective graph Y-max: {self.graph_y_max}ms")
        self.logger.info(f"Effective Y-axis ticks: {self.y_ticks}")
        self.logger.info(f"Effective output file: {self.output_file_path}")


        # Final validation of effective settings
        if self.ping_interval <= 0:
            raise ValueError(
                f"Effective ping interval ({self.ping_interval}s) must be greater than zero."
            )
        if self.graph_y_max <= 0:
            raise ValueError(
                f"Effective graph Y-max ({self.graph_y_max}ms) must be greater than zero."
            )
        if self.y_ticks < 2:
            raise ValueError(
                f"Effective number of Y-axis ticks ({self.y_ticks}) must be at least 2."
            )

        # Setup CSV file logging if path is provided
        if self.output_file_path:
            self.logger.info(f"Logging ping data to CSV: {self.output_file_path}")
            try:
                self.resolved_ip = socket.gethostbyname(self.host)
            except socket.gaierror:
                self.logger.warning(
                    f"Could not resolve IP for host '{self.host}'. "
                    "IP field in CSV will be blank."
                )
                self.resolved_ip = "" # Use empty string for CSV if resolution fails

            file_exists = os.path.exists(self.output_file_path)
            is_empty_file = file_exists and os.path.getsize(self.output_file_path) == 0

            try:
                # Open in append mode, create if not exists
                self.output_file_handle = open(
                    self.output_file_path, 'a', newline='', encoding='utf-8'
                )
                self.csv_writer = csv.writer(self.output_file_handle)

                if not file_exists or is_empty_file:
                    # Write header only if file is new or was empty
                    self.csv_writer.writerow([
                        "Timestamp", "MonitoredHost", "ResolvedIP",
                        "LatencyMS", "IsSuccess"
                    ])
                    self.output_file_handle.flush() # Ensure header is written immediately
            except IOError as e:
                self.logger.error(
                    f"Error opening or writing header to CSV file "
                    f"'{self.output_file_path}': {e}. CSV logging will be disabled."
                )
                # Ensure these are None if setup fails
                if self.output_file_handle:
                    self.output_file_handle.close()
                self.output_file_handle = None
                self.csv_writer = None
                self.output_file_path = None # Disable further attempts

    def _load_config_from_file(self):
        """
        Reads settings from an INI configuration file if it exists.
        Populates self.config_file_settings with found raw string values.
        """
        config = configparser.ConfigParser()
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
        except NameError:
            script_dir = os.getcwd()
            self.logger.info(
                f"'__file__' not defined, looking for {CONFIG_FILE_NAME} in CWD: {script_dir}"
            )

        config_file_path = os.path.join(script_dir, CONFIG_FILE_NAME)

        # self.config_file_settings is initialized in __init__
        if os.path.exists(config_file_path):
            try:
                read_ok = config.read(config_file_path)
                if (
                    not read_ok
                ):  # File was empty or otherwise unreadable by configparser
                    self.logger.warning(
                        f"Could not parse '{config_file_path}', though it exists."
                    )
                    return

                if "MonitorSettings" in config:
                    self.logger.info(
                        f"Configuration file '{config_file_path}' loaded and "
                        "[MonitorSettings] section found."
                    )
                    settings_map = {
                        "host": config.get("MonitorSettings", "host", fallback=None),
                        "interval": config.get(
                            "MonitorSettings", "interval", fallback=None
                        ),
                        "ymax": config.get("MonitorSettings", "ymax", fallback=None),
                        "yticks": config.get(
                            "MonitorSettings", "yticks", fallback=None
                        ),
                        "output_file": config.get(
                            "MonitorSettings", "output_file", fallback=None
                        ),
                    }
                    for key, value in settings_map.items():
                        if value is not None:
                            self.config_file_settings[key] = value
                else:
                    self.logger.info(
                        f"Configuration file '{config_file_path}' loaded, but "
                        "[MonitorSettings] section not found."
                    )
            except configparser.Error as e:
                self.logger.error(
                    f"Error parsing configuration file '{config_file_path}': {e}"
                )
        else:
            self.logger.info(
                f"Configuration file '{config_file_path}' not found. "
                "Using defaults/CLI arguments."
            )

    def _measure_latency(self) -> float | None:
        """
        Measures latency to the configured host using the system's ping command,
        adapting command and output parsing based on the detected OS.

        Returns:
            float | None: Latency in milliseconds (ms) if successful,
                          None if ping fails or output cannot be parsed.

        Raises:
            FileNotFoundError: If the 'ping' command is not found.
        """
        if self.ping_timeout_is_ms:
            # Windows expects timeout in milliseconds
            timeout_val_for_cmd = str(
                max(int(PING_MIN_TIMEOUT_S * 1000), int(self.ping_interval * 1000))
            )
        else:
            # Linux/macOS expect timeout in seconds
            timeout_val_for_cmd = str(max(PING_MIN_TIMEOUT_S, int(self.ping_interval)))

        # Ensure subprocess timeout is always in seconds and slightly larger
        subprocess_timeout = max(
            SUBPROCESS_MIN_TIMEOUT_S_BASE,
            self.ping_interval + SUBPROCESS_TIMEOUT_S_ADDITIVE,
        )

        command = self.ping_cmd_parts + [timeout_val_for_cmd, self.host]

        try:
            proc = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=subprocess_timeout,
                check=False,  # Don't raise exception for non-zero return codes
            )
            if proc.returncode == 0:  # Successful ping
                output = proc.stdout
                match = self.ping_regex.search(output)
                if match:
                    # Group 1 should be the latency value
                    return float(match.group(1))
                self.logger.warning(
                    f"Ping to {self.host} successful, but regex did not find time in output."
                )
                return None  # Should be unlikely for standard ping
            else:  # Ping command failed (e.g., host unknown, timeout)
                self.logger.debug(
                    f"Ping failed with return code {proc.returncode}: {proc.stderr}"
                )
                return None
        except subprocess.TimeoutExpired:
            self.logger.warning(f"Ping to {self.host} timed out (subprocess).")
            return None
        except FileNotFoundError:
            msg = (
                "CRITICAL ERROR: 'ping' command not found. "
                "Please ensure it is installed and in your PATH."
            )
            self.logger.critical(msg)
            raise  # Re-raise to be caught by the main run loop's exception handler
        except Exception as e:
            self.logger.error(
                f"Unexpected error in _measure_latency: {e}", exc_info=True
            )
            return None

    def _clear_screen_and_position_cursor(self):
        """Clears screen (from cursor down) and positions cursor at home."""
        sys.stdout.write(ANSI_CURSOR_HOME)
        # Using CLS (clear screen from cursor to end) instead of full clear
        # to potentially reduce flicker with logging to stdout.
        # sys.stdout.write(ANSI_CLEAR_FROM_CURSOR_TO_END)

    def _display_status_message(self):
        """
        Displays the current connection status message at the top of the screen,
        occupying a fixed number of lines.
        """
        status_lines_printed = 0
        if self.connection_status_message:
            message_to_display = [self.connection_status_message]
            # Add a separator line for alerts or info messages for emphasis
            if self.connection_status_message.startswith(
                "!!!"
            ) or self.connection_status_message.startswith("INFO:"):
                message_to_display.append("-" * len(self.connection_status_message))

            for line_text in message_to_display:
                if status_lines_printed < self.status_message_reserved_lines:
                    sys.stdout.write(line_text + "\n")
                    status_lines_printed += 1
                else:
                    break  # Don't exceed reserved lines

        # Fill any remaining reserved lines to ensure stable layout
        for _ in range(self.status_message_reserved_lines - status_lines_printed):
            sys.stdout.write("\n")
        sys.stdout.write("\n")  # Extra blank line after status message area

    def _prepare_plot_area(self) -> tuple[int, int] | None:
        """
        Gets terminal size, calculates plot height and width.

        Returns:
            tuple[int, int] | None: (plot_height, plot_width) if successful,
                                     None otherwise.
        """
        try:
            terminal_cols, terminal_lines = os.get_terminal_size()
            # Calculate overhead based on lines reserved for status and other elements
            overhead = (
                self.status_message_reserved_lines + PLOT_ESTIMATED_OVERHEAD_LINES
            )
            plot_height = max(PLOT_MIN_HEIGHT_LINES, terminal_lines - overhead)
            plot_width = max(
                PLOT_MIN_WIDTH_CHARS, terminal_cols - 2
            )  # Small margin for borders

            if plot_height < PLOT_MIN_HEIGHT_LINES or plot_width < PLOT_MIN_WIDTH_CHARS:
                warn_msg = (
                    "Calculated plot area is too small. "
                    "Graph might not display well."
                )
                self.logger.warning(warn_msg)
            return plot_height, plot_width
        except OSError as e:  # os.get_terminal_size() can raise OSError
            self.logger.error(f"Error getting terminal size: {e}")
            return None

    def _configure_plot_axes_and_labels(self, plot_width: int, plot_height: int):
        """
        Configures plotext plot: size, title, labels, Y-axis limits, and Y-ticks.

        Args:
            plot_width (int): The calculated width for the plot.
            plot_height (int): The calculated height for the plot.
        """
        pltx.plot_size(plot_width, plot_height)
        pltx.title("Real-time Internet Latency")
        pltx.ylabel("(ms)")  # Latency in milliseconds

        max_y_data_current = 0
        if self.latency_plot_values:
            # Consider only valid, positive latencies for max Y calculation
            valid_latencies = [
                val for val in self.latency_plot_values if val is not None and val > 0
            ]
            if valid_latencies:
                max_y_data_current = max(valid_latencies)

        # Determine Y-axis upper limit
        y_lim_upper_cand = (
            max_y_data_current * 1.1
            if max_y_data_current > 0
            else self.graph_y_max  # Use default if no data or all zeros
        )
        y_lim_upper = max(self.graph_y_max, y_lim_upper_cand)

        # Ensure a minimum sensible Y range
        if y_lim_upper < PLOT_MIN_Y_LIM_UPPER:
            y_lim_upper = PLOT_MIN_Y_LIM_UPPER
        pltx.ylim(0, y_lim_upper)

        # Attempt to set a specific number of Y-ticks for better readability
        if self.y_ticks > 1:
            try:
                pltx.yticks(self.y_ticks)
            except TypeError:  # plotext might raise TypeError for certain tick counts
                # Fallback: calculate ticks manually if yticks(int) fails
                if y_lim_upper > 0:
                    step = y_lim_upper / (self.y_ticks - 1)
                    ticks_list = sorted(
                        list(set([round(i * step) for i in range(self.y_ticks)]))
                    )
                    if ticks_list:
                        pltx.yticks(ticks_list)
                elif self.y_ticks > 1:  # y_lim_upper is 0, provide minimal ticks
                    pltx.yticks([0, 1])
            except Exception as e_ytick:  # Catch any other yticks error
                warning_text = "Could not set custom y-axis ticks"
                self.logger.warning(f"{warning_text}: {e_ytick}")

        pltx.canvas_color("black")
        pltx.axes_color("gray")
        pltx.ticks_color("dark_gray")

    def _plot_latency_series(self, x_axis_plot_indices: list[int]) -> list[int]:
        """
        Plots the main latency data and failure markers on the configured plot.

        Args:
            x_axis_plot_indices (list[int]): X-axis indices for plotting.

        Returns:
            list[int]: A list of X-axis indices where failures occurred.
        """
        # Plot the primary latency data (cyan line).
        # self.latency_plot_values contains actual latency values or 0 for failures.
        # Using 0 for failures helps plotext scale the Y-axis to include zero,
        # ensuring a consistent baseline, especially if early pings fail or are high.
        pltx.plot(
            x_axis_plot_indices,
            self.latency_plot_values,
            marker="braille",  # Use braille characters for a denser line
            color="cyan",
        )

        # Identify and mark actual ping failures.
        x_failure_indices = []
        # self.latency_history_real_values stores actual latency or None for failures.
        # Iterate through this list to find where None (a failure) is recorded.
        for i, real_latency_val in enumerate(self.latency_history_real_values):
            if real_latency_val is None:
                # Ensure index is valid for x_axis_plot_indices before appending
                if i < len(x_axis_plot_indices):
                    x_failure_indices.append(x_axis_plot_indices[i])

        if x_failure_indices:
            # For each identified failure, plot a red 'X' marker.
            # These markers are plotted at PLOT_FAILURE_MARKER_Y_BASE (usually 0),
            # placing them along the X-axis.
            y_values_for_failures = [PLOT_FAILURE_MARKER_Y_BASE] * len(
                x_failure_indices
            )
            pltx.scatter(
                x_failure_indices,
                y_values_for_failures,
                marker="x",
                color="red",
            )
        return x_failure_indices

    def _render_plot(self, x_failure_indices: list[int]):
        """
        Handles final plot rendering, including empty plot scenarios.

        Args:
            x_failure_indices (list[int]): List of X-indices where failures occurred.
                                           Used to determine if any data (even failures)
                                           was plotted.
        """
        no_plot_data = not self.latency_plot_values or all(
            val == 0 for val in self.latency_plot_values
        )
        # If no data (neither success nor failure markers) was plotted,
        # draw an empty frame to show title/axes.
        if no_plot_data and not x_failure_indices:
            pltx.plot([], [])

        pltx.xticks([], [])  # Hide X-axis numeric ticks and labels for simplicity
        pltx.xlabel("(Press Ctrl+C to Exit)")
        pltx.show()  # Display the constructed plot

    def _calculate_average_latency(self) -> float | None:
        """
        Calculates the average latency from stored historical real values.

        Returns:
            float | None: The average latency, or None if no valid data.
        """
        valid_latencies = [
            val for val in self.latency_history_real_values if val is not None
        ]
        if not valid_latencies:
            return None
        return sum(valid_latencies) / len(valid_latencies)

    def _calculate_min_latency(self) -> float | None:
        """
        Calculates the minimum latency from stored historical real values.

        Returns:
            float | None: The minimum latency, or None if no valid data.
        """
        valid_latencies = [
            val for val in self.latency_history_real_values if val is not None
        ]
        if not valid_latencies:
            return None
        return min(valid_latencies)

    def _calculate_max_latency(self) -> float | None:
        """
        Calculates the maximum latency from stored historical real values.

        Returns:
            float | None: The maximum latency, or None if no valid data.
        """
        valid_latencies = [
            val for val in self.latency_history_real_values if val is not None
        ]
        if not valid_latencies:
            return None
        return max(valid_latencies)

    def _display_statistics(self):
        """Formats and prints current monitoring statistics to stdout."""
        stats_lines = [
            "\n--- Statistics ---",
            f"Monitoring Host: {self.host}",
            f"Ping Interval: {self.ping_interval:.1f}s",
            f"Graph Y-Max Ref: {self.graph_y_max:.0f}ms",
        ]
        if self.latency_history_real_values:
            last_real_ping = self.latency_history_real_values[-1]
            if last_real_ping is not None:
                stats_lines.append(f"Current Latency: {last_real_ping:.2f} ms")
            else:
                stats_lines.append("Current Latency: PING FAILED")

            # Use helper methods for statistics
            avg_lat = self._calculate_average_latency()
            min_val = self._calculate_min_latency()
            max_val = self._calculate_max_latency()

            if avg_lat is not None:
                stats_lines.append(f"Average (valid pings): {avg_lat:.2f} ms")
            else:
                stats_lines.append("Average (valid pings): N/A")

            if min_val is not None:
                stats_lines.append(f"Minimum (valid pings): {min_val:.2f} ms")
            else:
                stats_lines.append("Minimum (valid pings): N/A")

            if max_val is not None:
                stats_lines.append(f"Maximum (valid pings): {max_val:.2f} ms")
            else:
                stats_lines.append("Maximum (valid pings): N/A")
        else:  # No history yet
            stats_lines.append("Current Latency: PING FAILED")
            stats_lines.append("Average (valid pings): N/A")
            stats_lines.append("Minimum (valid pings): N/A")
            stats_lines.append("Maximum (valid pings): N/A")

        # Format total monitoring time
        h = int(self.total_monitoring_time_seconds // 3600)
        m = int((self.total_monitoring_time_seconds % 3600) // 60)
        s = int(self.total_monitoring_time_seconds % 60)
        time_fmt = ""
        if h > 0:
            time_fmt += f"{h}h "
        if m > 0 or h > 0:  # Ensure minutes show if hours are present
            time_fmt += f"{m}m "
        time_fmt += f"{s}s"
        stats_lines.append(f"Monitoring Time: {time_fmt.strip()}")
        stats_lines.append(f"Consecutive Failures: {self.consecutive_ping_failures}")
        stats_lines.append("--------------------")
        # Print all statistics directly to stdout
        sys.stdout.write("\n".join(stats_lines) + "\n")
        # Clear any part of a previous, longer stats display
        sys.stdout.write(ANSI_CLEAR_FROM_CURSOR_TO_END)
        sys.stdout.flush()

    def _update_display_and_status(self):
        """Orchestrates updating the display with status, plot, and statistics."""
        self._clear_screen_and_position_cursor()
        self._display_status_message()

        if not self.latency_plot_values:
            waiting_msg = "Waiting for first ping data..."
            sys.stdout.write(waiting_msg + "\n")  # Keep direct user feedback
            self.logger.info(waiting_msg)
            # Display statistics even if there's no plot data yet
            self._display_statistics()
            return

        pltx.clt()  # Clear plotext terminal (canvas settings)
        pltx.cld()  # Clear previous plotext plot data

        plot_area_dims = self._prepare_plot_area()
        if plot_area_dims is None:
            self.logger.error("Plot area dimensions could not be prepared.")
            # If plot area can't be prepared, still show stats
            self._display_statistics()
            return

        plot_height, plot_width = plot_area_dims
        self._configure_plot_axes_and_labels(plot_width, plot_height)

        x_axis_plot_indices = list(range(len(self.latency_plot_values)))
        try:
            x_failure_indices = self._plot_latency_series(x_axis_plot_indices)
            self._render_plot(x_failure_indices)
        except Exception as e_plot:
            # Clear potentially garbled plot area before printing error
            sys.stdout.write(ANSI_CLEAR_FROM_CURSOR_TO_END)
            self.logger.error(f"Error during plotext rendering: {e_plot}")

        self._display_statistics()

    def _setup_terminal(self):
        """Hides the cursor and saves original terminal settings (if not on Windows)."""
        sys.stdout.write(ANSI_HIDE_CURSOR)
        sys.stdout.flush()
        if self.current_os != "windows":
            try:
                # termios module is POSIX-specific
                self.original_terminal_settings = termios.tcgetattr(sys.stdin.fileno())
            except Exception as e:  # pylint: disable=broad-except
                # If not in a real terminal (e.g. piped output), tcgetattr can fail.
                self.logger.warning(
                    f"Could not get termios settings: {e}. Terminal restoration might not work."
                )
                self.original_terminal_settings = None
        else:
            self.logger.info(
                "Skipping termios-based terminal settings capture on Windows."
            )
            self.original_terminal_settings = None  # Ensure it's None on Windows

    def _restore_terminal(self):
        """Restores the cursor and original terminal settings (if not on Windows and settings were saved)."""
        sys.stdout.write(ANSI_SHOW_CURSOR)
        sys.stdout.flush()
        if self.current_os != "windows" and self.original_terminal_settings is not None:
            try:
                termios.tcsetattr(
                    sys.stdin.fileno(),
                    termios.TCSADRAIN,  # Wait for output to drain before changing settings
                    self.original_terminal_settings,
                )
            except Exception as e:  # pylint: disable=broad-except
                self.logger.warning(f"Could not restore termios settings: {e}.")
        elif self.current_os == "windows":
            self.logger.info(
                "Skipping termios-based terminal settings restoration on Windows."
            )

    def run(self):
        """Runs the main monitoring loop."""
        self._setup_terminal()
        exit_code = EXIT_CODE_SUCCESS
        try:
            while True:
                current_latency_real = self._measure_latency()
                self.total_monitoring_time_seconds += self.ping_interval

                # Update connection status message and failure counter
                if current_latency_real is None:
                    self.consecutive_ping_failures += 1
                    # threshold = self.consecutive_failures_threshold # BUG: This was a local variable
                    # Check if alert threshold is met and not already alerting
                    if (
                        self.consecutive_ping_failures
                        >= self.consecutive_failures_threshold
                        and not self.connection_status_message.startswith("!!!")
                    ):
                        self.connection_status_message = (
                            f"!!! ALERT: Connection to {self.host} LOST "
                            f"({self.consecutive_ping_failures} failures) !!!"
                        )
                        self.logger.warning(self.connection_status_message)
                    # Softer warning for initial failures below threshold
                    elif (
                        0
                        < self.consecutive_ping_failures
                        < self.consecutive_failures_threshold
                        and not self.connection_status_message.startswith("!!!")
                    ):
                        self.connection_status_message = (
                            f"Warning: Ping to {self.host} failed "
                            f"({self.consecutive_ping_failures}x)"
                        )
                        self.logger.warning(self.connection_status_message)
                else:  # Ping successful
                    # If connection was previously lost, log restoration
                    if (
                        self.consecutive_ping_failures
                        >= self.consecutive_failures_threshold
                    ):
                        self.connection_status_message = (
                            f"INFO: Connection to {self.host} RESTORED "
                            f"after {self.consecutive_ping_failures} "
                            "failure(s)!"
                        )
                        self.logger.info(self.connection_status_message)
                    elif (
                        self.consecutive_ping_failures > 0
                    ):  # If there were some prior failures before recovery
                        self.connection_status_message = (
                            f"INFO: Ping to {self.host} normalized "
                            f"after {self.consecutive_ping_failures} failure(s)."
                        )
                        self.logger.info(self.connection_status_message)
                    elif self.connection_status_message.startswith("INFO:"):
                        # Clear "INFO:" message after one display cycle
                        self.connection_status_message = ""
                    self.consecutive_ping_failures = 0

                # FUTURE: Consider a DataPoint class/namedtuple to store
                # (timestamp, real_latency, plot_latency) to unify data handling.

                # Log to CSV if enabled
                if self.csv_writer:
                    timestamp = datetime.now().isoformat()
                    is_success = current_latency_real is not None
                    latency_ms_for_csv = current_latency_real if is_success else ''
                    row_data = [
                        timestamp,
                        self.host,
                        self.resolved_ip if self.resolved_ip else '',
                        latency_ms_for_csv,
                        is_success
                    ]
                    try:
                        self.csv_writer.writerow(row_data)
                        if self.output_file_handle: # Should exist if csv_writer exists
                            self.output_file_handle.flush()
                    except IOError as e:
                        self.logger.error(f"Error writing to CSV file: {e}. Disabling further CSV logging.")
                        if self.output_file_handle:
                            self.output_file_handle.close()
                        self.csv_writer = None
                        self.output_file_handle = None
                        self.output_file_path = None # To prevent re-opening

                # Update data for history (accurate values for stats)
                if len(self.latency_history_real_values) >= self.max_data_points:
                    self.latency_history_real_values.pop(0)
                self.latency_history_real_values.append(current_latency_real)

                # Update data for plotting (0 for failures for y-axis scaling)
                if len(self.latency_plot_values) >= self.max_data_points:
                    self.latency_plot_values.pop(0)
                plot_val = (
                    current_latency_real if current_latency_real is not None else 0
                )
                self.latency_plot_values.append(plot_val)

                self._update_display_and_status()
                time.sleep(self.ping_interval)

        except KeyboardInterrupt:
            # Keep direct print for this user-initiated action
            print("\nMonitoring stopped by user.")
        except Exception:  # Catch-all for any other unexpected error
            self.logger.exception(
                "An unexpected or critical error occurred in run loop"
            )
            exit_code = EXIT_CODE_ERROR
        finally:
            self._restore_terminal()
            # Determine final exit code based on whether an unhandled exception
            # (other than KeyboardInterrupt) occurred.
            current_exception = sys.exc_info()[1]
            if (
                not isinstance(current_exception, KeyboardInterrupt)
                and current_exception is not None
            ):
                exit_code = EXIT_CODE_ERROR
            sys.exit(exit_code)


def main():
    """Parses arguments, creates a NetworkMonitor instance, and runs it."""
    desc = (
        "Monitors internet latency to a host and displays a "
        "real-time graph (Linux only)."
    )
    parser = argparse.ArgumentParser(
        description=desc,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "host",
        type=str,
        nargs="?",
        default=DEFAULT_HOST_ARG,
        help="The host or IP address to ping.",
    )
    parser.add_argument(
        "-i",
        "--interval",
        type=float,
        default=DEFAULT_PING_INTERVAL_SECONDS_ARG,
        help="Interval between pings in seconds (e.g., 0.5, 1, 10).",
    )
    parser.add_argument(
        "--ymax",
        type=float,
        default=DEFAULT_GRAPH_Y_MAX_ARG,
        help="Reference maximum Y-axis value for the graph (ms).",
    )
    parser.add_argument(
        "--yticks",
        type=int,
        default=DEFAULT_Y_TICKS_ARG,
        help="Desired approximate number of Y-axis ticks.",
    )
    parser.add_argument(
        '-o', '--output-file',
        type=str,
        default=None, # Default to no output file
        help='Path to CSV file for logging latency data.'
    )
    args = parser.parse_args()

    # Create and run the monitor
    try:
        monitor = NetworkMonitor(args)
        monitor.run()
    except ValueError as e:
        sys.stderr.write(f"Configuration Error: {e}\n")
        sys.exit(EXIT_CODE_ERROR)


if __name__ == "__main__":
    main()
