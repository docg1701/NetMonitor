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
PLOT_FAILURE_MARKER_Y_BASE = 0 # Y-value for placing failure 'X' markers

PING_MIN_TIMEOUT_S = 1  # Minimum timeout for the ping command itself
SUBPROCESS_MIN_TIMEOUT_S_BASE = 2.0 # Base for subprocess.run timeout
SUBPROCESS_TIMEOUT_S_ADDITIVE = 1.0 # Added to ping interval for subprocess

EXIT_CODE_SUCCESS = 0
EXIT_CODE_ERROR = 1


# --- Configuration Constants ---
MAX_DATA_POINTS = 200  # Max data points before old ones are removed
CONSECUTIVE_FAILURES_ALERT_THRESHOLD = 3  # Ping failures for "connection lost"
STATUS_MESSAGE_RESERVED_LINES = 3  # Lines for status messages

# --- Global Configuration Variables ---
DEFAULT_HOST = "1.1.1.1"
DEFAULT_PING_INTERVAL_SECONDS = 1.0
DEFAULT_GRAPH_Y_MAX = 200.0  # Default Y-axis max for graph (ms)
DEFAULT_Y_TICKS = 6  # Desired number of Y-axis ticks

# --- Global State Variables ---
latency_plot_values = []  # Y-values for graph (0 for failures)
latency_history_real_values = []  # Actual latencies (None for failures)
consecutive_ping_failures = 0
connection_status_message = ""
total_monitoring_time_seconds = 0


def measure_latency(host_to_ping: str) -> float | None:
    """
    Measures latency to a specific host using the Linux 'ping' command.
    Returns latency in ms or None if ping fails or output cannot be parsed.
    """
    # Ping timeout (-W) is in seconds.
    ping_timeout_val = str(max(PING_MIN_TIMEOUT_S, int(DEFAULT_PING_INTERVAL_SECONDS)))
    # subprocess.run timeout should be slightly larger than ping's timeout.
    subprocess_timeout = max(
        SUBPROCESS_MIN_TIMEOUT_S_BASE,
        DEFAULT_PING_INTERVAL_SECONDS + SUBPROCESS_TIMEOUT_S_ADDITIVE
    )

    try:
        # Linux specific ping: -c 1 (one packet), -W <timeout>
        command = ["ping", "-c", "1", "-W", ping_timeout_val, host_to_ping]

        proc = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=subprocess_timeout,
            check=False,
        )

        if proc.returncode == 0:  # Ping successful
            output = proc.stdout
            # Standard Linux ping output
            match = re.search(r"time=([0-9\.]+)\s*ms", output, re.IGNORECASE)
            if match:
                return float(match.group(1))
            # Successful response but no time found (unlikely for Linux ping)
            return None
        else:
            # Ping failed (host unknown, network unreachable, or -W timeout)
            return None
    except subprocess.TimeoutExpired:  # subprocess.run() itself timed out
        return None
    except FileNotFoundError:
        # Critical error caught by main loop's exception handler
        msg = (
            "CRITICAL ERROR: 'ping' command not found. "
            "Please ensure it is installed and in your PATH.\n"
        )
        sys.stdout.write(msg)
        raise
    except Exception:  # Other unexpected errors during ping execution
        return None


def update_display_and_status():
    """Repositions cursor, redraws graph and status information."""
    # Access global state for reading; modifications to lists are done carefully
    # global connection_status_message, consecutive_ping_failures (modified in main)
    # global latency_plot_values, latency_history_real_values (modified in main)
    # global total_monitoring_time_seconds (modified in main)

    sys.stdout.write(ANSI_CURSOR_HOME)

    # Print status message, occupying fixed lines for stable layout
    status_lines_printed = 0
    if connection_status_message:
        message_to_display = [connection_status_message]
        if connection_status_message.startswith("!!!") or \
           connection_status_message.startswith("INFO:"):
            message_to_display.append("-" * len(connection_status_message))

        for line_text in message_to_display:
            if status_lines_printed < STATUS_MESSAGE_RESERVED_LINES:
                sys.stdout.write(line_text + "\n")
                status_lines_printed += 1
            else:
                break

    for _ in range(STATUS_MESSAGE_RESERVED_LINES - status_lines_printed):
        sys.stdout.write("\n")  # Fill remaining reserved lines

    sys.stdout.write("\n")  # Blank line between status and graph

    x_axis_plot_indices = list(range(len(latency_plot_values)))

    if not latency_plot_values:
        sys.stdout.write("Waiting for first ping data...\n")
    else:
        pltx.clt()  # Clear plotext terminal (canvas settings)
        pltx.cld()  # Clear previous plotext plot data
        try:
            terminal_cols, terminal_lines = os.get_terminal_size()
            # Estimate overhead: status, title/axes, stats, etc.
            overhead_lines = STATUS_MESSAGE_RESERVED_LINES + PLOT_ESTIMATED_OVERHEAD_LINES
            plot_height = max(PLOT_MIN_HEIGHT_LINES, terminal_lines - overhead_lines)
            plot_width = max(PLOT_MIN_WIDTH_CHARS, terminal_cols - 2)

            if plot_height < PLOT_MIN_HEIGHT_LINES or plot_width < PLOT_MIN_WIDTH_CHARS:
                # This f-string was F541, now it is a regular string
                # as plot_width and plot_height are not used.
                warn_msg = (
                    "WARNING: Calculated plot area is too small. Graph "
                    "might not display well.\n"
                )
                sys.stdout.write(warn_msg)

            pltx.plot_size(plot_width, plot_height)
            pltx.title("Real-time Internet Latency")
            pltx.ylabel("(ms)")

            # Set Y-axis limits: 0 to a calculated upper bound
            max_y_data_current = 0
            if latency_plot_values:  # Check if there are plot values
                valid_latencies = [
                    val for val in latency_plot_values if val is not None and val > 0
                ]
                if valid_latencies:
                    max_y_data_current = max(valid_latencies)

            # Y-axis upper limit: greater of configured max or current max data
            y_lim_upper_cand = max_y_data_current * 1.1 \
                if max_y_data_current > 0 else DEFAULT_GRAPH_Y_MAX
            y_lim_upper = max(DEFAULT_GRAPH_Y_MAX, y_lim_upper_cand)

            if y_lim_upper < PLOT_MIN_Y_LIM_UPPER:
                y_lim_upper = PLOT_MIN_Y_LIM_UPPER  # Ensure a minimum sensible Y range
            pltx.ylim(0, y_lim_upper)

            # Attempt to set a specific number of Y-ticks
            if DEFAULT_Y_TICKS > 1:
                try:
                    pltx.yticks(DEFAULT_Y_TICKS)
                except TypeError:
                    # Fallback for yticks(int) TypeError
                    if y_lim_upper > 0:
                        step = y_lim_upper / (DEFAULT_Y_TICKS - 1)
                        ticks_list = sorted(
                            list(set([round(i * step) for i in range(DEFAULT_Y_TICKS)]))
                        )
                        if ticks_list:
                            pltx.yticks(ticks_list)
                    elif DEFAULT_Y_TICKS > 1:  # y_lim_upper is 0
                        pltx.yticks([0, 1])
                except Exception as e_ytick:
                    sys.stdout.write(
                        f"WARNING: Could not set custom y-axis ticks: {e_ytick}\n"
                    )

            pltx.canvas_color("black")
            pltx.axes_color("gray")
            pltx.ticks_color("dark_gray")

            # Plot main latency line (0 for failures for scaling)
            pltx.plot(
                x_axis_plot_indices, latency_plot_values,
                marker="braille", color="cyan"
            )

            # Identify and plot 'X' for actual failures (history has None)
            x_failure_indices = []
            for i, real_latency_val in enumerate(latency_history_real_values):
                if real_latency_val is None:
                    if i < len(x_axis_plot_indices):
                        x_failure_indices.append(x_axis_plot_indices[i])

            if x_failure_indices:
                y_values_for_failures = [PLOT_FAILURE_MARKER_Y_BASE] * len(
                    x_failure_indices
                )
                pltx.scatter(
                    x_failure_indices, y_values_for_failures,
                    marker="x", color="red"
                )

            # If no data plotted, draw empty frame for title/axes
            no_plot_data = (not latency_plot_values or
                            all(val == 0 for val in latency_plot_values))
            if no_plot_data and not x_failure_indices:
                pltx.plot([], [])

            pltx.xticks([], [])  # Hide X-axis numeric ticks and labels
            pltx.xlabel("(Press Ctrl+C to Exit)")
            pltx.show()  # Display the constructed plot
        except Exception as e_plot:
            sys.stdout.write(ANSI_CLEAR_FROM_CURSOR_TO_END)  # Clear potentially garbled plot
            sys.stdout.write(f"ERROR during plotext rendering: {e_plot}\n")

    # --- Statistics Section ---
    stats_lines = [
        "\n--- Statistics ---",
        f"Monitoring Host: {DEFAULT_HOST}",
        f"Ping Interval: {DEFAULT_PING_INTERVAL_SECONDS:.1f}s",
        f"Graph Y-Max Ref: {DEFAULT_GRAPH_Y_MAX:.0f}ms",
    ]
    if latency_history_real_values:
        last_real_ping_value = latency_history_real_values[-1]
        if last_real_ping_value is not None:
            stats_lines.append(f"Current Latency: {last_real_ping_value:.2f} ms")
        else:
            stats_lines.append("Current Latency: PING FAILED")

        valid_latencies_for_stats = [
            val for val in latency_history_real_values if val is not None
        ]
        if valid_latencies_for_stats:
            avg_lat = sum(valid_latencies_for_stats) / len(valid_latencies_for_stats)
            stats_lines.append(f"Average (valid pings): {avg_lat:.2f} ms")
            min_lat = min(valid_latencies_for_stats)
            stats_lines.append(f"Minimum (valid pings): {min_lat:.2f} ms")
            max_lat = max(valid_latencies_for_stats)
            stats_lines.append(f"Maximum (valid pings): {max_lat:.2f} ms")
        else:  # If all pings in history were failures
            stats_lines.append("Average (valid pings): N/A")
            stats_lines.append("Minimum (valid pings): N/A")
            stats_lines.append("Maximum (valid pings): N/A")

    # Format and add total monitoring time
    h = int(total_monitoring_time_seconds // 3600)
    m = int((total_monitoring_time_seconds % 3600) // 60)
    s = int(total_monitoring_time_seconds % 60)
    time_fmt = ""
    if h > 0:
        time_fmt += f"{h}h "
    if m > 0 or h > 0:
        time_fmt += f"{m}m "
    time_fmt += f"{s}s"
    stats_lines.append(f"Monitoring Time: {time_fmt.strip()}")

    stats_lines.append(f"Consecutive Failures: {consecutive_ping_failures}")
    stats_lines.append("--------------------")
    sys.stdout.write("\n".join(stats_lines) + "\n")

    sys.stdout.write(ANSI_CLEAR_FROM_CURSOR_TO_END)
    sys.stdout.flush()


def main():
    """Parses arguments, and runs the main monitoring loop."""
    # These are module-level and modified by command-line args
    global DEFAULT_HOST, DEFAULT_PING_INTERVAL_SECONDS
    global DEFAULT_GRAPH_Y_MAX, DEFAULT_Y_TICKS
    # These are module-level state variables modified during the loop
    global connection_status_message, consecutive_ping_failures
    global total_monitoring_time_seconds
    # latency_plot_values and latency_history_real_values are global lists
    # modified in place (append/pop), so 'global' is not strictly needed
    # in this function for them if they are not reassigned.

    parser = argparse.ArgumentParser(
        description=(
            "Monitors internet latency to a host and displays a "
            "real-time graph (Linux only)."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "host",
        type=str,
        nargs="?",
        default=DEFAULT_HOST,
        help="The host or IP address to ping.",
    )
    parser.add_argument(
        "-i",
        "--interval",
        type=float,
        default=DEFAULT_PING_INTERVAL_SECONDS,
        help="Interval between pings in seconds (e.g., 0.5, 1, 10).",
    )
    parser.add_argument(
        "--ymax",
        type=float,
        default=DEFAULT_GRAPH_Y_MAX,
        help="Reference maximum Y-axis value for the graph (ms).",
    )
    parser.add_argument(
        "--yticks",
        type=int,
        default=DEFAULT_Y_TICKS,
        help="Desired approximate number of Y-axis ticks.",
    )
    args = parser.parse_args()

    DEFAULT_HOST = args.host
    DEFAULT_PING_INTERVAL_SECONDS = args.interval
    DEFAULT_GRAPH_Y_MAX = args.ymax
    DEFAULT_Y_TICKS = args.yticks

    if DEFAULT_PING_INTERVAL_SECONDS <= 0:
        err_msg = (
            f"Error: Ping interval ({DEFAULT_PING_INTERVAL_SECONDS}s) "
            "must be greater than zero."
        )
        print(err_msg)
        sys.exit(EXIT_CODE_ERROR)
    if DEFAULT_GRAPH_Y_MAX <= 0:
        err_msg = (
            f"Error: Graph Y-max ({DEFAULT_GRAPH_Y_MAX}ms) "
            "must be greater than zero."
        )
        print(err_msg)
        sys.exit(EXIT_CODE_ERROR)
    if DEFAULT_Y_TICKS < 2:
        err_msg = (
            f"Error: Number of Y-axis ticks ({DEFAULT_Y_TICKS}) "
            "must be at least 2."
        )
        print(err_msg)
        sys.exit(EXIT_CODE_ERROR)

    sys.stdout.write(ANSI_HIDE_CURSOR)
    sys.stdout.flush()
    original_terminal_settings = None
    try:
        original_terminal_settings = termios.tcgetattr(sys.stdin.fileno())
    except Exception:  # pylint: disable=broad-except
        # Fails if not in a real terminal (e.g., output piped to file)
        pass

    try:
        while True:
            current_latency_real = measure_latency(DEFAULT_HOST)
            total_monitoring_time_seconds += DEFAULT_PING_INTERVAL_SECONDS

            if current_latency_real is None:
                consecutive_ping_failures += 1
                threshold = CONSECUTIVE_FAILURES_ALERT_THRESHOLD
                if consecutive_ping_failures >= threshold and \
                   not connection_status_message.startswith("!!!"):
                    connection_status_message = (
                        f"!!! ALERT: Connection to {DEFAULT_HOST} LOST "
                        f"({consecutive_ping_failures} failures) !!!")
                elif 0 < consecutive_ping_failures < threshold and \
                     not connection_status_message.startswith("!!!"):
                    connection_status_message = (
                        f"Warning: Ping to {DEFAULT_HOST} failed "
                        f"({consecutive_ping_failures}x)")
            else:  # Ping successful
                threshold = CONSECUTIVE_FAILURES_ALERT_THRESHOLD
                if consecutive_ping_failures >= threshold:
                    connection_status_message = (
                        f"INFO: Connection to {DEFAULT_HOST} RESTORED after "
                        f"{consecutive_ping_failures} failure(s)!")
                elif consecutive_ping_failures > 0:
                    connection_status_message = (
                        f"INFO: Ping to {DEFAULT_HOST} normalized after "
                        f"{consecutive_ping_failures} failure(s).")
                elif connection_status_message.startswith("INFO:"):
                    connection_status_message = ""
                consecutive_ping_failures = 0

            if len(latency_history_real_values) >= MAX_DATA_POINTS:
                latency_history_real_values.pop(0)
            latency_history_real_values.append(current_latency_real)

            if len(latency_plot_values) >= MAX_DATA_POINTS:
                latency_plot_values.pop(0)
            # Plot line uses 0 for failures for plotext auto-scale
            plot_val = current_latency_real if current_latency_real is not None else 0
            latency_plot_values.append(plot_val)

            update_display_and_status()
            time.sleep(DEFAULT_PING_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")
    except Exception as e_main:
        print(f"\nAn unexpected or critical error occurred: {e_main}")
        if not isinstance(e_main, FileNotFoundError):
            import traceback
            traceback.print_exc()
    finally:
        sys.stdout.write(ANSI_SHOW_CURSOR)
        sys.stdout.flush()
        if original_terminal_settings:
            try:
                termios.tcsetattr(
                    sys.stdin.fileno(),
                    termios.TCSADRAIN,
                    original_terminal_settings)
            except Exception:  # pylint: disable=broad-except
                pass

        exit_code = EXIT_CODE_SUCCESS
        current_exception = sys.exc_info()[1]
        if isinstance(current_exception, KeyboardInterrupt):
            pass  # Normal exit
        elif current_exception is not None:
            exit_code = EXIT_CODE_ERROR  # Unhandled exception
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
