import pytest
import subprocess
import logging
import argparse
from unittest.mock import MagicMock, call
import sys
import os
import time # For mocking time.sleep
# import platform as pf # Not needed here, mocked in fixture

# Add the parent directory to sys.path to allow direct import of monitor_net
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from monitor_net import (
    NetworkMonitor, DEFAULT_HOST_ARG,
    DEFAULT_PING_INTERVAL_SECONDS_ARG, DEFAULT_GRAPH_Y_MAX_ARG,
    DEFAULT_Y_TICKS_ARG, main, EXIT_CODE_ERROR, PING_MIN_TIMEOUT_S
)

# Custom exception to break the run loop in tests
class TestLoopIntegrationExit(Exception):
    pass

@pytest.fixture
def mock_default_args(mocker):
    """Provides a MagicMock for argparse.Namespace with default values."""
    mock_args = mocker.MagicMock(spec=argparse.Namespace)
    mock_args.host = DEFAULT_HOST_ARG
    mock_args.interval = DEFAULT_PING_INTERVAL_SECONDS_ARG
    mock_args.ymax = DEFAULT_GRAPH_Y_MAX_ARG
    mock_args.yticks = DEFAULT_Y_TICKS_ARG
    return mock_args

@pytest.fixture
def monitor_instance_base(mock_default_args, mocker):
    """Basic NetworkMonitor instance with a fully mocked logger for most tests."""
    monitor = NetworkMonitor(mock_default_args)
    # Replace the real logger with a MagicMock that has mock methods
    monitor.logger = mocker.MagicMock(spec=logging.Logger)
    # Ensure individual log methods are also mocks if not automatically by spec
    for level in ['info', 'warning', 'error', 'critical', 'exception', 'debug']:
        setattr(monitor.logger, level, mocker.MagicMock())
    return monitor

@pytest.fixture
def monitor_instance_os(request, mocker, mock_default_args):
    """
    Parameterized fixture to create a NetworkMonitor instance simulating
    different OS environments by mocking platform.system().
    """
    os_name_to_return = request.param
    # Mock platform.system() *before* NetworkMonitor is instantiated
    mocker.patch('monitor_net.platform.system', return_value=os_name_to_return) # Patch in monitor_net's context

    monitor = NetworkMonitor(mock_default_args)
    # Replace the real logger with a MagicMock as in monitor_instance_base
    monitor.logger = mocker.MagicMock(spec=logging.Logger)
    for level in ['info', 'warning', 'error', 'critical', 'exception', 'debug']:
        setattr(monitor.logger, level, mocker.MagicMock())
    # Store the os_name with the instance for easy access/assertion in tests
    monitor.TEST_OS_NAME = os_name_to_return.lower()
    return monitor

# --- Tests for _measure_latency (OS-agnostic for some error cases) ---

def test_measure_latency_subprocess_timeout(monitor_instance_base, mocker):
    """Test subprocess.TimeoutExpired returns None (OS-agnostic part)."""
    mock_subprocess_run = mocker.patch(
        'subprocess.run',
        side_effect=subprocess.TimeoutExpired(cmd="ping", timeout=5)
    )
    result = monitor_instance_base._measure_latency()
    assert result is None
    mock_subprocess_run.assert_called_once()
    monitor_instance_base.logger.warning.assert_called_with(
        f"Ping to {monitor_instance_base.host} timed out (subprocess)."
    )

def test_measure_latency_file_not_found(monitor_instance_base, mocker):
    """Test FileNotFoundError for ping command re-raises (OS-agnostic part)."""
    mock_subprocess_run = mocker.patch(
        'subprocess.run',
        side_effect=FileNotFoundError("ping command not found")
    )
    with pytest.raises(FileNotFoundError):
        monitor_instance_base._measure_latency()
    mock_subprocess_run.assert_called_once()
    monitor_instance_base.logger.critical.assert_called_once_with(
        "CRITICAL ERROR: 'ping' command not found. "
        "Please ensure it is installed and in your PATH."
    )

# --- OS-Specific Tests for _measure_latency ---

OS_PARAMS_SUCCESS = [
    ("Linux", "time=10.5 ms", 10.5, ["ping", "-c", "1", "-W"]),
    ("Darwin", "time=12.34 ms", 12.34, ["ping", "-c", "1", "-t"]),
    ("Windows", "Reply from 1.2.3.4: bytes=32 time=15ms TTL=118", 15.0, ["ping", "-n", "1", "-w"]),
    ("Windows", "Reply from 1.2.3.4: bytes=32 time<1ms TTL=118", 1.0, ["ping", "-n", "1", "-w"]),
]

@pytest.mark.parametrize("monitor_instance_os, os_specific_stdout, expected_latency, cmd_start",
                         OS_PARAMS_SUCCESS,
                         indirect=["monitor_instance_os"])
def test_measure_latency_success_os_specific(monitor_instance_os, mocker, os_specific_stdout, expected_latency, cmd_start):
    """Test successful ping parsing for different OS."""
    mock_proc_result = MagicMock()
    mock_proc_result.returncode = 0
    mock_proc_result.stdout = os_specific_stdout
    mock_subprocess_run = mocker.patch('subprocess.run', return_value=mock_proc_result)

    result = monitor_instance_os._measure_latency()
    assert result == expected_latency, f"Failed for OS {monitor_instance_os.TEST_OS_NAME}"

    called_command = mock_subprocess_run.call_args[0][0]
    assert called_command[0:len(cmd_start)] == cmd_start
    assert called_command[-1] == monitor_instance_os.host

    if monitor_instance_os.TEST_OS_NAME == "windows":
        expected_timeout_str = str(max(int(PING_MIN_TIMEOUT_S * 1000),
                                       int(monitor_instance_os.ping_interval * 1000)))
        assert called_command[-2] == expected_timeout_str
    else:
        expected_timeout_str = str(max(PING_MIN_TIMEOUT_S,
                                       int(monitor_instance_os.ping_interval)))
        assert called_command[-2] == expected_timeout_str


OS_PARAMS_FAILURE = ["Linux", "Darwin", "Windows"]

@pytest.mark.parametrize("monitor_instance_os", OS_PARAMS_FAILURE, indirect=True)
def test_measure_latency_failure_os_specific(monitor_instance_os, mocker):
    """Test ping failure (non-zero return code) for different OS."""
    mock_proc_result = MagicMock()
    mock_proc_result.returncode = 1
    mock_proc_result.stdout = "Request timed out." if monitor_instance_os.TEST_OS_NAME == "windows" else ""
    mock_proc_result.stderr = "General failure." if monitor_instance_os.TEST_OS_NAME == "windows" else "ping: unknown host"
    mock_subprocess_run = mocker.patch('subprocess.run', return_value=mock_proc_result)

    result = monitor_instance_os._measure_latency()
    assert result is None
    mock_subprocess_run.assert_called_once()
    called_command = mock_subprocess_run.call_args[0][0]
    if monitor_instance_os.TEST_OS_NAME == "windows":
        assert called_command[0:3] == ["ping", "-n", "1"]
        assert called_command[3] == "-w"
    elif monitor_instance_os.TEST_OS_NAME == "darwin":
        assert called_command[0:3] == ["ping", "-c", "1"]
        assert called_command[3] == "-t"
    else:
        assert called_command[0:3] == ["ping", "-c", "1"]
        assert called_command[3] == "-W"


@pytest.mark.parametrize("monitor_instance_os", ["Linux", "Windows", "Darwin"], indirect=True)
def test_measure_latency_success_no_time_in_output_os_specific(monitor_instance_os, mocker):
    """Test successful ping but no 'time=' in output returns None (OS specific check)."""
    mock_proc_result = MagicMock()
    mock_proc_result.returncode = 0
    mock_proc_result.stdout = "some other output without time information"
    mocker.patch('subprocess.run', return_value=mock_proc_result)

    result = monitor_instance_os._measure_latency()
    assert result is None
    monitor_instance_os.logger.warning.assert_called_with(
        f"Ping to {monitor_instance_os.host} successful, but regex did not find time in output."
    )


# --- Tests for Statistical Calculation Methods (using monitor_instance_base) ---

def test_calculate_average_latency_empty(monitor_instance_base):
    monitor_instance_base.latency_history_real_values = []
    assert monitor_instance_base._calculate_average_latency() is None

def test_calculate_average_latency_all_none(monitor_instance_base):
    monitor_instance_base.latency_history_real_values = [None, None, None]
    assert monitor_instance_base._calculate_average_latency() is None

def test_calculate_average_latency_single_value(monitor_instance_base):
    monitor_instance_base.latency_history_real_values = [10.0]
    assert monitor_instance_base._calculate_average_latency() == 10.0

def test_calculate_average_latency_multiple_values(monitor_instance_base):
    monitor_instance_base.latency_history_real_values = [10.0, 20.0, 30.0]
    assert monitor_instance_base._calculate_average_latency() == 20.0

def test_calculate_average_latency_with_nones(monitor_instance_base):
    monitor_instance_base.latency_history_real_values = [10.0, None, 20.0, None, 30.0]
    assert monitor_instance_base._calculate_average_latency() == 20.0


def test_calculate_min_latency_empty(monitor_instance_base):
    monitor_instance_base.latency_history_real_values = []
    assert monitor_instance_base._calculate_min_latency() is None

def test_calculate_min_latency_all_none(monitor_instance_base):
    monitor_instance_base.latency_history_real_values = [None, None, None]
    assert monitor_instance_base._calculate_min_latency() is None

def test_calculate_min_latency_single_value(monitor_instance_base):
    monitor_instance_base.latency_history_real_values = [15.5]
    assert monitor_instance_base._calculate_min_latency() == 15.5

def test_calculate_min_latency_multiple_values(monitor_instance_base):
    monitor_instance_base.latency_history_real_values = [20.0, 10.0, 30.0]
    assert monitor_instance_base._calculate_min_latency() == 10.0

def test_calculate_min_latency_with_nones(monitor_instance_base):
    monitor_instance_base.latency_history_real_values = [20.0, None, 10.0, None, 30.0]
    assert monitor_instance_base._calculate_min_latency() == 10.0


def test_calculate_max_latency_empty(monitor_instance_base):
    monitor_instance_base.latency_history_real_values = []
    assert monitor_instance_base._calculate_max_latency() is None

def test_calculate_max_latency_all_none(monitor_instance_base):
    monitor_instance_base.latency_history_real_values = [None, None, None]
    assert monitor_instance_base._calculate_max_latency() is None

def test_calculate_max_latency_single_value(monitor_instance_base):
    monitor_instance_base.latency_history_real_values = [25.0]
    assert monitor_instance_base._calculate_max_latency() == 25.0

def test_calculate_max_latency_multiple_values(monitor_instance_base):
    monitor_instance_base.latency_history_real_values = [10.0, 30.0, 20.0]
    assert monitor_instance_base._calculate_max_latency() == 30.0

def test_calculate_max_latency_with_nones(monitor_instance_base):
    monitor_instance_base.latency_history_real_values = [10.0, None, 30.0, None, 20.0]
    assert monitor_instance_base._calculate_max_latency() == 30.0

# --- Tests for main() Argument Parsing and Validation ---

def test_main_default_args(mocker, mock_default_args):
    mocker.patch('sys.argv', ['monitor_net.py'])
    mock_monitor_class = mocker.patch('monitor_net.NetworkMonitor')
    mock_sys_exit = mocker.patch('sys.exit')

    main()

    mock_monitor_class.assert_called_once()
    call_args_list = mock_monitor_class.call_args_list
    args_passed_to_constructor = call_args_list[0][0][0]

    assert args_passed_to_constructor.host == DEFAULT_HOST_ARG
    assert args_passed_to_constructor.interval == DEFAULT_PING_INTERVAL_SECONDS_ARG
    assert args_passed_to_constructor.ymax == DEFAULT_GRAPH_Y_MAX_ARG
    assert args_passed_to_constructor.yticks == DEFAULT_Y_TICKS_ARG
    mock_sys_exit.assert_not_called()

def test_main_custom_args(mocker):
    custom_args_list = [
        'monitor_net.py', 'testhost.com',
        '-i', '0.7',
        '--ymax', '180',
        '--yticks', '4'
    ]
    mocker.patch('sys.argv', custom_args_list)
    mock_monitor_class = mocker.patch('monitor_net.NetworkMonitor')
    mocker.patch('sys.exit')

    main()

    mock_monitor_class.assert_called_once()
    call_args_list = mock_monitor_class.call_args_list
    args_passed_to_constructor = call_args_list[0][0][0]
    assert args_passed_to_constructor.host == 'testhost.com'
    assert args_passed_to_constructor.interval == 0.7
    assert args_passed_to_constructor.ymax == 180.0
    assert args_passed_to_constructor.yticks == 4

def test_main_invalid_interval(mocker):
    mocker.patch('sys.argv', ['monitor_net.py', '--interval', '0'])
    mock_monitor_class = mocker.patch('monitor_net.NetworkMonitor')
    mock_sys_exit = mocker.patch('sys.exit', side_effect=SystemExit)
    mocker.patch('builtins.print')

    with pytest.raises(SystemExit):
        main()

    mock_sys_exit.assert_called_once_with(EXIT_CODE_ERROR)
    mock_monitor_class.assert_not_called()

def test_main_invalid_ymax(mocker):
    mocker.patch('sys.argv', ['monitor_net.py', '--ymax', '-50'])
    mock_monitor_class = mocker.patch('monitor_net.NetworkMonitor')
    mock_sys_exit = mocker.patch('sys.exit', side_effect=SystemExit)
    mocker.patch('builtins.print')

    with pytest.raises(SystemExit):
        main()

    mock_sys_exit.assert_called_once_with(EXIT_CODE_ERROR)
    mock_monitor_class.assert_not_called()

def test_main_invalid_yticks(mocker):
    mocker.patch('sys.argv', ['monitor_net.py', '--yticks', '1'])
    mock_monitor_class = mocker.patch('monitor_net.NetworkMonitor')
    mock_sys_exit = mocker.patch('sys.exit', side_effect=SystemExit)
    mocker.patch('builtins.print')

    with pytest.raises(SystemExit):
        main()

    mock_sys_exit.assert_called_once_with(EXIT_CODE_ERROR)
    mock_monitor_class.assert_not_called()

# --- Integration Test for run() method (using monitor_instance_base) ---

class TestLoopIntegrationExit(Exception): # Defined for this test
    pass

def test_network_monitor_run_loop_basic_iterations(monitor_instance_base, mocker):
    latency_values_for_test = [10.0, 15.0]
    num_expected_data_points = len(latency_values_for_test)

    mock_measure_latency = mocker.patch.object(monitor_instance_base, '_measure_latency', autospec=True)

    side_effect_sequence = latency_values_for_test + [TestLoopIntegrationExit("Simulated loop break")]
    mock_measure_latency.side_effect = side_effect_sequence

    mock_update_display = mocker.patch.object(monitor_instance_base, '_update_display_and_status', autospec=True)
    mock_setup_terminal = mocker.patch.object(monitor_instance_base, '_setup_terminal', autospec=True)
    mock_restore_terminal = mocker.patch.object(monitor_instance_base, '_restore_terminal', autospec=True)
    mock_time_sleep = mocker.patch('time.sleep', autospec=True)
    mock_sys_exit = mocker.patch('sys.exit', side_effect=SystemExit)

    logged_exception_details = []
    def capture_exception_details_with_exc_info(msg, *args, **kwargs):
        exc_type, exc_value, _ = sys.exc_info()
        detail = {
            "msg": msg,
            "type": str(exc_type) if exc_type else "None",
            "value": str(exc_value) if exc_value else "None",
            "exc_obj": exc_value
        }
        logged_exception_details.append(detail)

    monitor_instance_base.logger.exception = MagicMock(
        side_effect=capture_exception_details_with_exc_info
    )

    with pytest.raises(SystemExit):
        monitor_instance_base.run()

    mock_setup_terminal.assert_called_once()
    mock_restore_terminal.assert_called_once()
    mock_sys_exit.assert_called_once_with(EXIT_CODE_ERROR)
    monitor_instance_base.logger.exception.assert_called_once()

    print(f"DEBUG_AGENT: Captured exception details by logger: {logged_exception_details}")

    assert len(logged_exception_details) == 1
    assert logged_exception_details[0]["msg"] == "An unexpected or critical error occurred in run loop"
    assert isinstance(logged_exception_details[0]["exc_obj"], TestLoopIntegrationExit)
    assert str(logged_exception_details[0]["exc_obj"]) == "Simulated loop break"

    expected_measure_latency_calls = num_expected_data_points + 1
    assert mock_measure_latency.call_count == expected_measure_latency_calls

    assert mock_update_display.call_count == num_expected_data_points

    assert mock_time_sleep.call_count == num_expected_data_points
    expected_sleep_calls = [call(monitor_instance_base.ping_interval)] * num_expected_data_points
    if num_expected_data_points > 0 :
        mock_time_sleep.assert_has_calls(expected_sleep_calls)

    expected_history_real = latency_values_for_test
    expected_plot_values = [val if val is not None else 0.0 for val in latency_values_for_test]

    assert monitor_instance_base.latency_history_real_values == expected_history_real
    assert monitor_instance_base.latency_plot_values == expected_plot_values
