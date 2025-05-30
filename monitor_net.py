import time
import os
import subprocess
import re
import plotext as pltx  # For plotting in the terminal
import sys
import argparse
import termios  # POSIX-specific module for terminal I/O control

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


# Default values for command-line arguments
DEFAULT_HOST_ARG = "1.1.1.1"
DEFAULT_PING_INTERVAL_SECONDS_ARG = 1.0
DEFAULT_GRAPH_Y_MAX_ARG = 200.0
DEFAULT_Y_TICKS_ARG = 6


class NetworkMonitor:
    def __init__(self, args):
        # Configuration from command line arguments
        self.host = args.host
        self.ping_interval = args.interval
        self.graph_y_max = args.ymax
        self.y_ticks = args.yticks

        # Configuration constants
        self.max_data_points = MAX_DATA_POINTS
        self.consecutive_failures_threshold = (
            CONSECUTIVE_FAILURES_ALERT_THRESHOLD
        )
        self.status_message_reserved_lines = STATUS_MESSAGE_RESERVED_LINES

        # State variables
        self.latency_plot_values = []
        self.latency_history_real_values = []
        self.consecutive_ping_failures = 0
        self.connection_status_message = ""
        self.total_monitoring_time_seconds = 0
        self.original_terminal_settings = None

    def _measure_latency(self) -> float | None:
        """
        Measures latency to self.host using the Linux 'ping' command.
        Returns latency in ms or None if ping fails or output cannot be parsed.
        """
        ping_timeout_val = str(
            max(PING_MIN_TIMEOUT_S, int(self.ping_interval))
        )
        subprocess_timeout = max(
            SUBPROCESS_MIN_TIMEOUT_S_BASE,
            self.ping_interval + SUBPROCESS_TIMEOUT_S_ADDITIVE,
        )

        try:
            command = ["ping", "-c", "1", "-W", ping_timeout_val, self.host]
            proc = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=subprocess_timeout,
                check=False,
            )
            if proc.returncode == 0:
                output = proc.stdout
                # Standard Linux ping output for time
                match = re.search(
                    r"time=([0-9\.]+)\s*ms", output, re.IGNORECASE
                )
                if match:
                    return float(match.group(1))
                return None
            else:
                return None
        except subprocess.TimeoutExpired:
            return None
        except FileNotFoundError:
            msg = (
                "CRITICAL ERROR: 'ping' command not found. "
                "Please ensure it is installed and in your PATH.\n"
            )
            sys.stdout.write(msg)
            raise
        except Exception:
            return None

    def _clear_screen_and_position_cursor(self):
        """Clears screen and positions cursor at home."""
        sys.stdout.write(ANSI_CURSOR_HOME)

    def _display_status_message(self):
        """Displays the current connection status message."""
        status_lines_printed = 0
        if self.connection_status_message:
            message_to_display = [self.connection_status_message]
            if self.connection_status_message.startswith(
                "!!!"
            ) or self.connection_status_message.startswith("INFO:"):
                message_to_display.append(
                    "-" * len(self.connection_status_message)
                )

            for line_text in message_to_display:
                if status_lines_printed < self.status_message_reserved_lines:
                    sys.stdout.write(line_text + "\n")
                    status_lines_printed += 1
                else:
                    break
        for _ in range(
            self.status_message_reserved_lines - status_lines_printed
        ):
            sys.stdout.write("\n")
        sys.stdout.write("\n")  # Blank line after status message

    def _prepare_plot_area(self) -> tuple[int, int] | None:
        """
        Gets terminal size, calculates and returns plot_height, plot_width.
        Returns None if terminal size cannot be determined or is too small.
        """
        try:
            terminal_cols, terminal_lines = os.get_terminal_size()
            overhead = (
                self.status_message_reserved_lines +
                PLOT_ESTIMATED_OVERHEAD_LINES
            )
            plot_height = max(PLOT_MIN_HEIGHT_LINES,
                              terminal_lines - overhead)
            plot_width = max(PLOT_MIN_WIDTH_CHARS, terminal_cols - 2)

            if (plot_height < PLOT_MIN_HEIGHT_LINES or
                    plot_width < PLOT_MIN_WIDTH_CHARS):
                warn_msg = (
                    "WARNING: Calculated plot area is too small. "
                    "Graph might not display well.\n"
                )
                sys.stdout.write(warn_msg)
            return plot_height, plot_width
        except OSError as e:
            sys.stdout.write(f"Error getting terminal size: {e}\n")
            return None

    def _configure_plot_axes_and_labels(self, plot_width: int,
                                       plot_height: int):
        """Configures plot title, labels, Y-axis limits, and Y-ticks."""
        pltx.plot_size(plot_width, plot_height)
        pltx.title("Real-time Internet Latency")
        pltx.ylabel("(ms)")

        max_y_data_current = 0
        if self.latency_plot_values:
            valid_latencies = [
                val for val in self.latency_plot_values
                if val is not None and val > 0
            ]
            if valid_latencies:
                max_y_data_current = max(valid_latencies)

        y_lim_upper_cand = (
            max_y_data_current * 1.1 if max_y_data_current > 0
            else self.graph_y_max
        )
        y_lim_upper = max(self.graph_y_max, y_lim_upper_cand)

        if y_lim_upper < PLOT_MIN_Y_LIM_UPPER:
            y_lim_upper = PLOT_MIN_Y_LIM_UPPER
        pltx.ylim(0, y_lim_upper)

        if self.y_ticks > 1:
            try:
                pltx.yticks(self.y_ticks)
            except TypeError:
                # Fallback for yticks(int) TypeError
                if y_lim_upper > 0:
                    step = y_lim_upper / (self.y_ticks - 1)
                    # Corrected E128: align with opening parenthesis or use hanging indent
                    ticks_list = sorted(list(set(
                        [round(i * step) for i in range(self.y_ticks)]
                    )))
                    if ticks_list:
                        pltx.yticks(ticks_list)
                elif self.y_ticks > 1:  # y_lim_upper is 0
                    pltx.yticks([0, 1])
            except Exception as e_ytick:
                warning_text = "WARNING: Could not set custom y-axis ticks"
                sys.stdout.write(f"{warning_text}: {e_ytick}\n")

        pltx.canvas_color("black")
        pltx.axes_color("gray")
        pltx.ticks_color("dark_gray")

    def _plot_latency_series(self,
                             x_axis_plot_indices: list[int]) -> list[int]:
        """Plots main latency line and failure markers. Returns X indices of failures."""
        pltx.plot(
            x_axis_plot_indices,
            self.latency_plot_values,
            marker="braille",
            color="cyan",
        )
        x_failure_indices = []
        for i, real_latency_val in enumerate(self.latency_history_real_values):
            if real_latency_val is None:
                # Ensure index is valid
                if i < len(x_axis_plot_indices):
                    x_failure_indices.append(x_axis_plot_indices[i])
        if x_failure_indices:
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
        """Handles empty plot scenarios and shows the plot."""
        no_plot_data = not self.latency_plot_values or all(
            val == 0 for val in self.latency_plot_values
        )
        # Draw empty frame if no data at all and no failures marked
        if no_plot_data and not x_failure_indices:
            pltx.plot([], [])

        pltx.xticks([], [])  # Hide X-axis numeric ticks and labels
        pltx.xlabel("(Press Ctrl+C to Exit)")
        pltx.show()

    def _display_statistics(self):
        """Formats and prints all statistical information."""
        stats_lines = [
            "\n--- Statistics ---",
            f"Monitoring Host: {self.host}",
            f"Ping Interval: {self.ping_interval:.1f}s",
            f"Graph Y-Max Ref: {self.graph_y_max:.0f}ms",
        ]
        if self.latency_history_real_values:
            last_real_ping = self.latency_history_real_values[-1]
            if last_real_ping is not None:
                stats_lines.append(
                    f"Current Latency: {last_real_ping:.2f} ms")
            else:
                stats_lines.append("Current Latency: PING FAILED")

            valid_latencies = [
                val for val in self.latency_history_real_values if val is not None
            ]
            if valid_latencies:
                avg_lat = sum(valid_latencies) / len(valid_latencies)
                stats_lines.append(f"Average (valid pings): {avg_lat:.2f} ms")
                min_val = min(valid_latencies)
                stats_lines.append(
                    f"Minimum (valid pings): {min_val:.2f} ms")
                max_val = max(valid_latencies)
                stats_lines.append(
                    f"Maximum (valid pings): {max_val:.2f} ms")
            else:
                stats_lines.append("Average (valid pings): N/A")
                stats_lines.append("Minimum (valid pings): N/A")
                stats_lines.append("Maximum (valid pings): N/A")

        h = int(self.total_monitoring_time_seconds // 3600)
        m = int((self.total_monitoring_time_seconds % 3600) // 60)
        s = int(self.total_monitoring_time_seconds % 60)
        time_fmt = ""
        if h > 0:
            time_fmt += f"{h}h "
        if m > 0 or h > 0:
            time_fmt += f"{m}m "
        time_fmt += f"{s}s"
        stats_lines.append(f"Monitoring Time: {time_fmt.strip()}")
        stats_lines.append(
            f"Consecutive Failures: {self.consecutive_ping_failures}"
        )
        stats_lines.append("--------------------")
        sys.stdout.write("\n".join(stats_lines) + "\n")
        sys.stdout.write(ANSI_CLEAR_FROM_CURSOR_TO_END)
        sys.stdout.flush()

    def _update_display_and_status(self):
        """Orchestrates updating the display with status, plot, and statistics."""
        self._clear_screen_and_position_cursor()
        self._display_status_message()

        if not self.latency_plot_values:
            sys.stdout.write("Waiting for first ping data...\n")
            # Display statistics even if there's no plot data yet
            self._display_statistics()
            return

        pltx.clt()  # Clear plotext terminal (canvas settings)
        pltx.cld()  # Clear previous plotext plot data

        plot_area_dims = self._prepare_plot_area()
        if plot_area_dims is None:
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
            # Clear potentially garbled plot area before printing message
            sys.stdout.write(ANSI_CLEAR_FROM_CURSOR_TO_END)
            sys.stdout.write(f"ERROR during plotext rendering: {e_plot}\n")

        self._display_statistics()

    def _setup_terminal(self):
        sys.stdout.write(ANSI_HIDE_CURSOR)
        sys.stdout.flush()
        try:
            self.original_terminal_settings = termios.tcgetattr(
                sys.stdin.fileno()
            )
        except Exception:  # pylint: disable=broad-except
            pass  # Fails if not in a real terminal

    def _restore_terminal(self):
        sys.stdout.write(ANSI_SHOW_CURSOR)
        sys.stdout.flush()
        if self.original_terminal_settings:
            try:
                termios.tcsetattr(
                    sys.stdin.fileno(),
                    termios.TCSADRAIN,
                    self.original_terminal_settings,
                )
            except Exception:  # pylint: disable=broad-except
                pass

    def run(self):
        self._setup_terminal()
        exit_code = EXIT_CODE_SUCCESS
        try:
            while True:
                current_latency_real = self._measure_latency()
                self.total_monitoring_time_seconds += self.ping_interval

                if current_latency_real is None:
                    self.consecutive_ping_failures += 1
                    threshold = self.consecutive_failures_threshold
                    if (self.consecutive_ping_failures >= threshold and
                            not self.connection_status_message.startswith("!!!")):
                        self.connection_status_message = (
                            f"!!! ALERT: Connection to {self.host} LOST "
                            f"({self.consecutive_ping_failures} failures) !!!"
                        )
                    elif (0 < self.consecutive_ping_failures < threshold and
                            not self.connection_status_message.startswith("!!!")):
                        self.connection_status_message = (
                            f"Warning: Ping to {self.host} failed "
                            f"({self.consecutive_ping_failures}x)"
                        )
                else:  # Ping successful
                    threshold = self.consecutive_failures_threshold
                    if self.consecutive_ping_failures >= threshold:
                        self.connection_status_message = (
                            f"INFO: Connection to {self.host} RESTORED "
                            f"after {self.consecutive_ping_failures} "
                            "failure(s)!"
                        )
                    elif self.consecutive_ping_failures > 0:
                        self.connection_status_message = (
                            f"INFO: Ping to {self.host} normalized "
                            f"after {self.consecutive_ping_failures} failure(s)."
                        )
                    elif self.connection_status_message.startswith("INFO:"):
                        self.connection_status_message = ""
                    self.consecutive_ping_failures = 0

                if len(self.latency_history_real_values) >= self.max_data_points:
                    self.latency_history_real_values.pop(0)
                self.latency_history_real_values.append(current_latency_real)

                if len(self.latency_plot_values) >= self.max_data_points:
                    self.latency_plot_values.pop(0)
                plot_val = (current_latency_real
                            if current_latency_real is not None else 0)
                self.latency_plot_values.append(plot_val)

                self._update_display_and_status()
                time.sleep(self.ping_interval)

        except KeyboardInterrupt:
            print("\nMonitoring stopped by user.")
        except Exception as e_main:
            print(f"\nAn unexpected or critical error occurred: {e_main}")
            if not isinstance(e_main, FileNotFoundError):
                import traceback
                traceback.print_exc()
            # Ensure error code for other exceptions.
            exit_code = EXIT_CODE_ERROR
        finally:
            self._restore_terminal()
            # Determine final exit code
            current_exception = sys.exc_info()[1]
            if (not isinstance(current_exception, KeyboardInterrupt) and
                    current_exception is not None):
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
    args = parser.parse_args()

    if args.interval <= 0:
        err_msg = (
            f"Error: Ping interval ({args.interval}s) must be "
            "greater than zero."
        )
        print(err_msg)
        sys.exit(EXIT_CODE_ERROR)
    if args.ymax <= 0:
        err_msg = (
            f"Error: Graph Y-max ({args.ymax}ms) must be greater "
            "than zero."
        )
        print(err_msg)
        sys.exit(EXIT_CODE_ERROR)
    if args.yticks < 2:
        err_msg = (
            f"Error: Number of Y-axis ticks ({args.yticks}) must be "
            "at least 2."
        )
        print(err_msg)
        sys.exit(EXIT_CODE_ERROR)

    monitor = NetworkMonitor(args)
    monitor.run()


if __name__ == "__main__":
    main()
