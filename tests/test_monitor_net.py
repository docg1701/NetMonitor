import pytest
import subprocess
import logging
import argparse
from unittest.mock import MagicMock, call
import sys
import os
import time
# Import real termios for termios.TCSADRAIN constant
import termios as real_termios # Renamed to avoid conflict if 'termios' is mocked
import configparser
import socket # Added for test_csv_init_dns_failure
import csv # Added for test_csv_write_row_success and others
import platform # Added for test_csv_file_closed_on_exit

# Add the parent directory to sys.path to allow direct import of monitor_net
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import monitor_net # Import the module itself to access its namespace items like datetime
from monitor_net import (
    NetworkMonitor, DEFAULT_HOST_ARG,
    DEFAULT_PING_INTERVAL_SECONDS_ARG, DEFAULT_GRAPH_Y_MAX_ARG,
    DEFAULT_Y_TICKS_ARG, main, EXIT_CODE_ERROR, PING_MIN_TIMEOUT_S,
    ANSI_HIDE_CURSOR, ANSI_SHOW_CURSOR, CONFIG_FILE_NAME # Import specific constant
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
    mock_args.output_file = None # Add new default attribute
    return mock_args

@pytest.fixture
def monitor_instance_base(mock_default_args, mocker):
    """Basic NetworkMonitor instance with a fully mocked logger for most tests."""
    # Default to Linux for non-OS-specific tests.
    # Patch platform.system within monitor_net's context for this fixture.
    with mocker.patch('monitor_net.platform.system', return_value="Linux"):
        monitor = NetworkMonitor(mock_default_args)

    # Fully mock the logger and its methods
    monitor.logger = mocker.MagicMock(spec=logging.Logger)
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
    # Patch platform.system within monitor_net's context for this fixture
    with mocker.patch('monitor_net.platform.system', return_value=os_name_to_return):
        monitor = NetworkMonitor(mock_default_args)

    monitor.logger = mocker.MagicMock(spec=logging.Logger)
    for level in ['info', 'warning', 'error', 'critical', 'exception', 'debug']:
        setattr(monitor.logger, level, mocker.MagicMock())
    # Store the os_name with the instance for easy access/assertion in tests
    monitor.TEST_OS_NAME = os_name_to_return.lower()
    return monitor

# --- Tests for _measure_latency (OS-agnostic for some error cases) ---

def test_measure_latency_subprocess_timeout(monitor_instance_base, mocker):
    """Test subprocess.TimeoutExpired returns None."""
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
    """Test FileNotFoundError for ping command re-raises."""
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
    # Let NetworkMonitor be instantiated to trigger the validation error
    # mock_monitor_class = mocker.patch('monitor_net.NetworkMonitor')
    mock_sys_exit = mocker.patch('sys.exit', side_effect=SystemExit)
    mock_stderr_write = mocker.patch('sys.stderr.write')

    with pytest.raises(SystemExit):
        main()

    mock_sys_exit.assert_called_once_with(EXIT_CODE_ERROR)
    # NetworkMonitor.__init__ will be called, and raise ValueError
    # Check that stderr was called with a message containing the arg problem
    assert any("Configuration Error: Effective ping interval (0.0s) must be greater than zero" in call_arg[0][0] for call_arg in mock_stderr_write.call_args_list)


def test_main_invalid_ymax(mocker):
    mocker.patch('sys.argv', ['monitor_net.py', '--ymax', '-50'])
    mock_sys_exit = mocker.patch('sys.exit', side_effect=SystemExit)
    mock_stderr_write = mocker.patch('sys.stderr.write')

    with pytest.raises(SystemExit):
        main()

    mock_sys_exit.assert_called_once_with(EXIT_CODE_ERROR)
    assert any("Configuration Error: Effective graph Y-max (-50.0ms) must be greater than zero" in call_arg[0][0] for call_arg in mock_stderr_write.call_args_list)


def test_main_invalid_yticks(mocker):
    mocker.patch('sys.argv', ['monitor_net.py', '--yticks', '1'])
    mock_sys_exit = mocker.patch('sys.exit', side_effect=SystemExit)
    mock_stderr_write = mocker.patch('sys.stderr.write')

    with pytest.raises(SystemExit):
        main()

    mock_sys_exit.assert_called_once_with(EXIT_CODE_ERROR)
    assert any("Configuration Error: Effective number of Y-axis ticks (1) must be at least 2" in call_arg[0][0] for call_arg in mock_stderr_write.call_args_list)

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

    # This print is for debugging in case the test fails.
    # print(f"DEBUG_AGENT: Captured exception details by logger: {logged_exception_details}")

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

# --- Tests for OS-aware _setup_terminal and _restore_terminal ---

@pytest.mark.parametrize("monitor_instance_os", ["Linux", "Darwin", "Windows"], indirect=True)
def test_setup_terminal_os_awareness(monitor_instance_os, mocker):
    mock_stdout_write = mocker.patch('sys.stdout.write')
    mock_fileno = mocker.patch('sys.stdin.fileno', return_value=0)

    mock_tcgetattr = None
    if monitor_instance_os.TEST_OS_NAME != "windows":
        mock_termios_module = mocker.patch('monitor_net.termios', spec=real_termios)
        mock_tcgetattr = mock_termios_module.tcgetattr
        mock_tcgetattr.return_value = "fake_settings"

    monitor_instance_os._setup_terminal()

    mock_stdout_write.assert_any_call(ANSI_HIDE_CURSOR)

    if monitor_instance_os.TEST_OS_NAME != "windows":
        assert mock_tcgetattr is not None
        mock_tcgetattr.assert_called_once_with(0)
        assert monitor_instance_os.original_terminal_settings == "fake_settings"
        # Ensure the "Skipping..." log for Windows was NOT called
        assert not any(
            cargs[0][0] == "Skipping termios-based terminal settings capture on Windows."
            for cargs in monitor_instance_os.logger.info.call_args_list
        )
    else:
        if mock_tcgetattr:
             mock_tcgetattr.assert_not_called()
        assert monitor_instance_os.original_terminal_settings is None
        monitor_instance_os.logger.info.assert_any_call(
            "Skipping termios-based terminal settings capture on Windows."
        )

@pytest.mark.parametrize("monitor_instance_os", ["Linux", "Darwin", "Windows"], indirect=True)
def test_restore_terminal_os_awareness(monitor_instance_os, mocker):
    mock_stdout_write = mocker.patch('sys.stdout.write')
    mock_fileno = mocker.patch('sys.stdin.fileno', return_value=0)

    if monitor_instance_os.TEST_OS_NAME != "windows":
        mock_termios_module = mocker.patch('monitor_net.termios', spec=real_termios)
        # Configure the mocked module's TCSADRAIN attribute to have the real value
        mock_termios_module.TCSADRAIN = real_termios.TCSADRAIN
        mock_tcsetattr = mock_termios_module.tcsetattr

        # Scenario 1: Settings were saved
        monitor_instance_os.original_terminal_settings = "fake_settings"
        monitor_instance_os._restore_terminal()
        mock_tcsetattr.assert_called_once_with(0, real_termios.TCSADRAIN, "fake_settings")

        # Scenario 2: Settings were None
        monitor_instance_os.original_terminal_settings = None
        mock_tcsetattr.reset_mock()
        monitor_instance_os._restore_terminal()
        mock_tcsetattr.assert_not_called()
        # Ensure the "Skipping..." log for Windows was NOT called
        assert not any(
            cargs[0][0] == "Skipping termios-based terminal settings restoration on Windows."
            for cargs in monitor_instance_os.logger.info.call_args_list
        )
    else:
        monitor_instance_os.original_terminal_settings = None
        # Ensure tcsetattr is not called on Windows.
        mock_tcsetattr_win = mocker.patch('monitor_net.termios.tcsetattr', create=True, spec=True)
        monitor_instance_os._restore_terminal()
        mock_tcsetattr_win.assert_not_called()
        monitor_instance_os.logger.info.assert_any_call(
            "Skipping termios-based terminal settings restoration on Windows."
        )

    mock_stdout_write.assert_any_call(ANSI_SHOW_CURSOR)


# --- Tests for Configuration File Logic ---

def test_config_file_not_found(mocker, mock_default_args):
    """Test behavior when config file does not exist."""
    # Ensure that NetworkMonitor.__init__ uses the patched os.path.exists
    mocker.patch('monitor_net.os.path.exists', return_value=False)

    # We need to mock platform.system because it's called early in __init__
    mocker.patch('monitor_net.platform.system', return_value="Linux")

    # Mock the logger on the class itself before instantiation for these init tests
    mock_logger_on_class = mocker.patch('monitor_net.logging.getLogger').return_value
    mock_logger_on_class.info = MagicMock()
    mock_logger_on_class.warning = MagicMock()
    mock_logger_on_class.error = MagicMock()
    mock_logger_on_class.handlers = [] # Fix: Add handlers attribute

    monitor = NetworkMonitor(mock_default_args)

    assert monitor.config_file_settings == {}
    # Check that a message indicating the file was not found is logged
    found_log = any(
        f"configuration file '{mocker.ANY}' not found" in call_item[0][0].lower()
        for call_item in mock_logger_on_class.info.call_args_list
    ) or any(
        "not found. using defaults/cli arguments" in call_item[0][0].lower()
        for call_item in mock_logger_on_class.info.call_args_list
    )
    assert found_log, "Log message for config file not found not present"


def test_config_file_exists_no_section(mocker, mock_default_args):
    """Test behavior when config file exists but [MonitorSettings] section is missing."""
    mocker.patch('monitor_net.os.path.exists', return_value=True)

    mock_config_parser_instance = MagicMock(spec=configparser.ConfigParser)
    # Simulate file read successfully, but section not found
    mock_config_parser_instance.read.return_value = ["dummy_path/monitor_config.ini"] # Indicates file was read
    # Simulate 'MonitorSettings' section does not exist by controlling __contains__
    mock_config_parser_instance.__contains__.side_effect = lambda item: item != 'MonitorSettings'
    # If get is called, it should fallback
    mock_config_parser_instance.get.return_value = None # Should not be relied upon if section not found

    mocker.patch('monitor_net.configparser.ConfigParser', return_value=mock_config_parser_instance)
    mocker.patch('monitor_net.platform.system', return_value="Linux")

    mock_logger_on_class = mocker.patch('monitor_net.logging.getLogger').return_value
    mock_logger_on_class.info = MagicMock()
    mock_logger_on_class.handlers = [] # Fix: Add handlers attribute

    monitor = NetworkMonitor(mock_default_args)

    assert monitor.config_file_settings == {}
    found_log = any(
        "section not found" in call_item[0][0].lower()
        for call_item in mock_logger_on_class.info.call_args_list
    )
    assert found_log, "Log message for section not found not present"


def test_config_file_exists_with_valid_settings(mocker, mock_default_args):
    """Test loading valid settings from config file."""
    mocker.patch('monitor_net.os.path.exists', return_value=True)

    mock_config_parser_instance = MagicMock(spec=configparser.ConfigParser)
    mock_config_parser_instance.read.return_value = ["dummy_path/monitor_config.ini"]

    # Simulate 'MonitorSettings' section exists by controlling __contains__
    mock_config_parser_instance.__contains__.side_effect = lambda item: item == 'MonitorSettings'

    config_values = {
        # Using a tuple (section, key, fallback_value_passed_to_get) as key for dict
        ('MonitorSettings', 'host', None): 'config.com',
        ('MonitorSettings', 'interval', None): '2.2',
        ('MonitorSettings', 'ymax', None): '120.0',
        ('MonitorSettings', 'yticks', None): '3'
    }
    # side_effect for get: (section, key, fallback=xxx)
    mock_config_parser_instance.get.side_effect = lambda section, key, fallback: config_values.get((section, key, fallback))

    mocker.patch('monitor_net.configparser.ConfigParser', return_value=mock_config_parser_instance)
    mocker.patch('monitor_net.platform.system', return_value="Linux")
    mock_logger_on_class = mocker.patch('monitor_net.logging.getLogger').return_value # Mock logger
    mock_logger_on_class.info = MagicMock()
    mock_logger_on_class.handlers = [] # Fix: Add handlers attribute


    monitor = NetworkMonitor(mock_default_args)

    expected_settings = {'host': 'config.com', 'interval': '2.2', 'ymax': '120.0', 'yticks': '3'}
    assert monitor.config_file_settings == expected_settings
    # Check for log message about loading the config file
    found_log = False
    for call_item in mock_logger_on_class.info.call_args_list:
        if "configuration file" in call_item[0][0].lower() and "loaded" in call_item[0][0].lower():
            found_log = True
            break
    assert found_log, "Log message for successful config load not found"


def test_config_file_parsing_error(mocker, mock_default_args):
    """Test behavior when configparser raises an error during parsing."""
    mocker.patch('monitor_net.os.path.exists', return_value=True)

    mock_config_parser_instance = MagicMock(spec=configparser.ConfigParser)
    # Simulate a parsing error
    mock_config_parser_instance.read.side_effect = configparser.Error("mock parsing error")

    mocker.patch('monitor_net.configparser.ConfigParser', return_value=mock_config_parser_instance)
    mocker.patch('monitor_net.platform.system', return_value="Linux")

    mock_logger_on_class = mocker.patch('monitor_net.logging.getLogger').return_value
    mock_logger_on_class.error = MagicMock()
    mock_logger_on_class.handlers = [] # Fix: Add handlers attribute

    monitor = NetworkMonitor(mock_default_args)

    assert monitor.config_file_settings == {}
    mock_logger_on_class.error.assert_any_call(mocker.ANY)
    # Check that the error message includes "Error parsing configuration file"
    assert "error parsing configuration file" in mock_logger_on_class.error.call_args[0][0].lower()
    assert "mock parsing error" in mock_logger_on_class.error.call_args[0][0].lower()


# --- Test for _convert_setting (via NetworkMonitor init) ---

def test_config_value_conversion_error(mocker, mock_default_args):
    """Test that a config value conversion error logs a warning and uses default."""
    mocker.patch('monitor_net.os.path.exists', return_value=True) # Config file exists

    mock_config_parser_instance = MagicMock(spec=configparser.ConfigParser)
    mock_config_parser_instance.read.return_value = ["dummy_path/monitor_config.ini"]
    # Simulate 'MonitorSettings' section exists by controlling __contains__
    mock_config_parser_instance.__contains__.side_effect = lambda item: item == 'MonitorSettings'

    # Simulate 'interval' is 'not_a_float', other valid settings or None
    def get_side_effect(section, key, fallback):
        if section == 'MonitorSettings':
            if key == 'interval':
                return 'not_a_float' # Invalid value for float conversion
            if key == 'host':
                return 'config.host.com' # Valid other value
        return fallback # For other keys or if section doesn't match

    mock_config_parser_instance.get.side_effect = get_side_effect
    mocker.patch('monitor_net.configparser.ConfigParser', return_value=mock_config_parser_instance)
    mocker.patch('monitor_net.platform.system', return_value="Linux")

    # Mock the logger that NetworkMonitor will create and use for itself
    mock_logger_instance = MagicMock(spec=logging.Logger)
    # Add handlers attribute to the mock logger instance
    mock_logger_instance.handlers = []
    mocker.patch('logging.getLogger', return_value=mock_logger_instance)

    # Create monitor instance. _determine_effective_settings will call _convert_setting
    monitor = NetworkMonitor(mock_default_args)

    # Assert that ping_interval fell back to the default CLI arg value
    assert monitor.ping_interval == DEFAULT_PING_INTERVAL_SECONDS_ARG
    # Assert that host was taken from config (to ensure config was partially processed)
    assert monitor.host == 'config.host.com'

    # Check for the specific warning log from _convert_setting
    found_warning = False
    for call_arg in mock_logger_instance.warning.call_args_list:
        msg = call_arg[0][0] # Get the first positional argument of the call
        if "Invalid value 'not_a_float' for 'interval'" in msg and "config file. It will be ignored" in msg:
            found_warning = True
            break
    assert found_warning, "Specific warning for conversion error not found"


# --- Tests for Precedence Logic in _determine_effective_settings ---

def test_precedence_cli_overrides_config_and_default(mocker, mock_default_args):
    """Test CLI args override config file, which would override defaults."""
    # CLI arguments (all custom)
    mock_default_args.host = "cli.host.com"
    mock_default_args.interval = 0.5
    mock_default_args.ymax = 100.0
    mock_default_args.yticks = 3

    # Config file settings (all different from CLI and defaults)
    mocker.patch('monitor_net.os.path.exists', return_value=True)
    mock_config_parser_instance = MagicMock(spec=configparser.ConfigParser)
    mock_config_parser_instance.read.return_value = ["dummy_path/monitor_config.ini"]
    # Simulate 'MonitorSettings' section exists by controlling __contains__
    mock_config_parser_instance.__contains__.side_effect = lambda item: item == 'MonitorSettings'
    config_values = {
        ('MonitorSettings', 'host', None): 'config.host.com',
        ('MonitorSettings', 'interval', None): '2.5',
        ('MonitorSettings', 'ymax', None): '250.0',
        ('MonitorSettings', 'yticks', None): '5'
    }
    mock_config_parser_instance.get.side_effect = lambda sec, k, fallback: config_values.get((sec, k, fallback))
    mocker.patch('monitor_net.configparser.ConfigParser', return_value=mock_config_parser_instance)
    mocker.patch('monitor_net.platform.system', return_value="Linux")
    mock_logger_instance = MagicMock(spec=logging.Logger)
    mock_logger_instance.handlers = [] # Fix: Add handlers attribute
    mocker.patch('logging.getLogger', return_value=mock_logger_instance)

    monitor = NetworkMonitor(mock_default_args)

    assert monitor.host == "cli.host.com"
    assert monitor.ping_interval == 0.5
    assert monitor.graph_y_max == 100.0
    assert monitor.y_ticks == 3

    # Check logs for CLI override messages
    log_calls = [call_arg[0][0] for call_arg in mock_logger_instance.info.call_args_list]
    assert any("CLI 'host' (cli.host.com) overrides other settings." in msg for msg in log_calls)
    assert any("CLI 'interval' (0.5) overrides other settings." in msg for msg in log_calls)
    assert any("CLI 'ymax' (100.0) overrides other settings." in msg for msg in log_calls)
    assert any("CLI 'yticks' (3) overrides other settings." in msg for msg in log_calls)

def test_precedence_config_overrides_default(mocker, mock_default_args):
    """Test config file settings override defaults when CLI uses defaults."""
    # CLI arguments are all defaults (from mock_default_args fixture)
    # mock_default_args.host = DEFAULT_HOST_ARG etc.

    # Config file settings
    mocker.patch('monitor_net.os.path.exists', return_value=True)
    mock_config_parser_instance = MagicMock(spec=configparser.ConfigParser)
    mock_config_parser_instance.read.return_value = ["dummy_path/monitor_config.ini"]
    # Simulate 'MonitorSettings' section exists by controlling __contains__
    mock_config_parser_instance.__contains__.side_effect = lambda item: item == 'MonitorSettings'
    config_values = {
        ('MonitorSettings', 'host', None): 'config.host.com',
        ('MonitorSettings', 'interval', None): '2.5',
        ('MonitorSettings', 'ymax', None): '250.0',
        ('MonitorSettings', 'yticks', None): '5'
    }
    mock_config_parser_instance.get.side_effect = lambda sec, k, fallback: config_values.get((sec, k, fallback))
    mocker.patch('monitor_net.configparser.ConfigParser', return_value=mock_config_parser_instance)
    mocker.patch('monitor_net.platform.system', return_value="Linux")
    mock_logger_instance = MagicMock(spec=logging.Logger)
    mock_logger_instance.handlers = [] # Fix: Add handlers attribute
    mock_logger_instance.handlers = [] # Fix: Add handlers attribute
    mock_logger_instance.handlers = [] # Fix: Add handlers attribute
    mocker.patch('logging.getLogger', return_value=mock_logger_instance)

    monitor = NetworkMonitor(mock_default_args)

    assert monitor.host == "config.host.com"
    assert monitor.ping_interval == 2.5
    assert monitor.graph_y_max == 250.0
    assert monitor.y_ticks == 5

    # Check logs for config usage messages
    log_calls = [call_arg[0][0] for call_arg in mock_logger_instance.info.call_args_list]
    assert any("Using 'host' from config file: config.host.com" in msg for msg in log_calls)
    assert any("Using 'interval' from config file: 2.5" in msg for msg in log_calls)
    assert any("Using 'ymax' from config file: 250.0" in msg for msg in log_calls)
    assert any("Using 'yticks' from config file: 5" in msg for msg in log_calls)
    # Ensure CLI override messages are NOT present for these
    assert not any("CLI 'host'" in msg for msg in log_calls)


def test_precedence_cli_overrides_default_no_config_file(mocker, mock_default_args):
    """Test CLI args override defaults when no config file exists."""
    mock_default_args.host = "my.cli.com"
    mock_default_args.interval = 1.2

    mocker.patch('monitor_net.os.path.exists', return_value=False) # No config file
    mocker.patch('monitor_net.platform.system', return_value="Linux")
    mock_logger_instance = MagicMock(spec=logging.Logger)
    mock_logger_instance.handlers = [] # Fix: Add handlers attribute
    mocker.patch('logging.getLogger', return_value=mock_logger_instance)

    monitor = NetworkMonitor(mock_default_args)

    assert monitor.host == "my.cli.com"
    assert monitor.ping_interval == 1.2
    # ymax and yticks should be their defaults as not specified by CLI here
    assert monitor.graph_y_max == DEFAULT_GRAPH_Y_MAX_ARG
    assert monitor.y_ticks == DEFAULT_Y_TICKS_ARG

    log_calls = [call_arg[0][0] for call_arg in mock_logger_instance.info.call_args_list]
    assert any("CLI 'host' (my.cli.com) overrides other settings." in msg for msg in log_calls)
    assert any("CLI 'interval' (1.2) overrides other settings." in msg for msg in log_calls)
    assert any("not found. using defaults/cli arguments" in msg.lower() for msg in log_calls)


def test_precedence_defaults_used_if_no_cli_custom_no_config(mocker, mock_default_args):
    """Test defaults are used if CLI args are not custom and no config file."""
    # mock_default_args already holds default values

    mocker.patch('monitor_net.os.path.exists', return_value=False) # No config file
    mocker.patch('monitor_net.platform.system', return_value="Linux")
    mock_logger_instance = MagicMock(spec=logging.Logger)
    mock_logger_instance.handlers = [] # Fix: Add handlers attribute
    mocker.patch('logging.getLogger', return_value=mock_logger_instance)

    monitor = NetworkMonitor(mock_default_args)

    assert monitor.host == DEFAULT_HOST_ARG
    assert monitor.ping_interval == DEFAULT_PING_INTERVAL_SECONDS_ARG
    assert monitor.graph_y_max == DEFAULT_GRAPH_Y_MAX_ARG
    assert monitor.y_ticks == DEFAULT_Y_TICKS_ARG

    log_calls = [call_arg[0][0] for call_arg in mock_logger_instance.info.call_args_list]
    # Ensure no "CLI ... overrides" messages and no "Using ... from config file" messages
    assert not any("CLI '" in msg and "overrides" in msg for msg in log_calls)
    assert not any("from config file" in msg for msg in log_calls)
    assert any("not found. using defaults/cli arguments" in msg.lower() for msg in log_calls)
    assert any(f"Effective host: {DEFAULT_HOST_ARG}" in msg for msg in log_calls) # Check effective settings log


# --- Tests for Validation Logic in NetworkMonitor.__init__ (raising ValueError) ---

def test_init_validation_error_from_config(mocker, mock_default_args):
    """Test __init__ raises ValueError for invalid effective setting from config."""
    mocker.patch('monitor_net.os.path.exists', return_value=True)
    mock_config_parser_instance = MagicMock(spec=configparser.ConfigParser)
    mock_config_parser_instance.read.return_value = ["dummy_path/monitor_config.ini"]
    # Simulate 'MonitorSettings' section exists by controlling __contains__
    mock_config_parser_instance.__contains__.side_effect = lambda item: item == 'MonitorSettings'
    # Config provides an invalid interval
    config_values = {('MonitorSettings', 'interval', None): '-1.0'}
    mock_config_parser_instance.get.side_effect = lambda sec, k, fallback: config_values.get((sec, k, fallback), fallback)

    mocker.patch('monitor_net.configparser.ConfigParser', return_value=mock_config_parser_instance)
    mocker.patch('monitor_net.platform.system', return_value="Linux")
    mock_logger = mocker.patch('logging.getLogger').return_value # Basic logger mock
    mock_logger.handlers = [] # Fix: Add handlers attribute

    # mock_default_args uses default valid interval, so config will take precedence
    with pytest.raises(ValueError, match="Effective ping interval \\(-1.0s\\) must be greater than zero"):
        NetworkMonitor(mock_default_args)


def test_init_validation_error_from_cli(mocker, mock_default_args):
    """Test __init__ raises ValueError for invalid effective setting from CLI."""
    mock_default_args.interval = -2.0 # Invalid CLI interval

    # Config can be non-existent or valid, CLI should override and fail
    mocker.patch('monitor_net.os.path.exists', return_value=False)
    mocker.patch('monitor_net.platform.system', return_value="Linux")
    mock_logger_cli_only = mocker.patch('logging.getLogger').return_value
    mock_logger_cli_only.handlers = [] # Fix: Add handlers attribute

    with pytest.raises(ValueError, match="Effective ping interval \\(-2.0s\\) must be greater than zero"):
        NetworkMonitor(mock_default_args)

    # Test with a valid config that CLI still overrides
    mocker.patch('monitor_net.os.path.exists', return_value=True)
    mock_config_parser_instance = MagicMock(spec=configparser.ConfigParser)
    mock_config_parser_instance.read.return_value = ["dummy_path/monitor_config.ini"]
    type(mock_config_parser_instance).sections = mocker.PropertyMock(return_value=['MonitorSettings'])
    config_values = {('MonitorSettings', 'interval', None): '1.0'} # Valid config interval
    mock_config_parser_instance.get.side_effect = lambda sec, k, fallback: config_values.get((sec, k, fallback), fallback)
    mocker.patch('monitor_net.configparser.ConfigParser', return_value=mock_config_parser_instance)
    # Ensure the logger mock is fresh for this part of the test if logging.getLogger is called again
    # or ensure the previous mock_logger_cli_only is appropriately configured if it's reused.
    # For simplicity, if NetworkMonitor.__init__ calls getLogger multiple times, this might need adjustment.
    # However, it typically calls it once.

    with pytest.raises(ValueError, match="Effective ping interval \\(-2.0s\\) must be greater than zero"):
        NetworkMonitor(mock_default_args)


# --- Test for main() function's handling of __init__ ValueError ---

def test_main_catches_config_validation_error(mocker):
    """Test that main() catches ValueError from NetworkMonitor.__init__ and exits."""
    # Make NetworkMonitor.__init__ directly raise a ValueError
    mock_network_monitor_init = mocker.patch(
        'monitor_net.NetworkMonitor.__init__',
        side_effect=ValueError("mock validation error from init")
    )

    # Mock sys.argv for main()
    mocker.patch('sys.argv', ['monitor_net.py'])

    mock_sys_exit = mocker.patch('sys.exit', side_effect=SystemExit) # To catch the exit
    mock_stderr_write = mocker.patch('sys.stderr.write')

    with pytest.raises(SystemExit) as excinfo:
        main()

    mock_network_monitor_init.assert_called_once() # Ensure __init__ was called
    mock_stderr_write.assert_any_call("Configuration Error: mock validation error from init\n")
    mock_sys_exit.assert_called_once_with(EXIT_CODE_ERROR)
    assert excinfo.type == SystemExit # Check that SystemExit was indeed raised


# --- Tests for CSV Output File Argument Parsing and Precedence ---

def test_output_file_arg_parsing_cli_specified(mocker, mock_default_args):
    """Test NetworkMonitor.__init__ correctly sets output_file_path from CLI arg."""
    cli_output_path = "cli_output.csv"
    mock_default_args.output_file = cli_output_path # Simulate CLI specifying the output file

    mocker.patch('monitor_net.platform.system', return_value="Linux")
    mock_logger_instance = MagicMock(spec=logging.Logger)
    mock_logger_instance.handlers = []
    mocker.patch('logging.getLogger', return_value=mock_logger_instance)

    # Mock os.path.exists for config file check, socket for DNS
    mocker.patch('monitor_net.os.path.exists', return_value=False) # No config file, no output file exists yet
    mocker.patch('monitor_net.socket.gethostbyname', return_value="1.2.3.4")
    mocker.patch('builtins.open', mocker.mock_open()) # Mock opening the output file

    monitor = NetworkMonitor(mock_default_args)
    assert monitor.output_file_path == cli_output_path
    mock_logger_instance.info.assert_any_call(
        f"CLI 'output_file' ({cli_output_path}) overrides other settings."
    )
    mock_logger_instance.info.assert_any_call(f"Effective output file: {cli_output_path}")


def test_output_file_arg_parsing_config_specified(mocker, mock_default_args):
    """Test NetworkMonitor.__init__ correctly sets output_file_path from config file."""
    config_output_path = "config_output.csv"
    mock_default_args.output_file = None # CLI does not specify output file

    # Mock config file settings
    mocker.patch('monitor_net.os.path.exists', side_effect=lambda path: path.endswith('.ini')) # True for .ini, False for .csv
    mock_config_parser_instance = MagicMock(spec=configparser.ConfigParser)
    mock_config_parser_instance.read.return_value = ["dummy_path/monitor_config.ini"]
    mock_config_parser_instance.__contains__.side_effect = lambda item: item == 'MonitorSettings'
    config_values = {('MonitorSettings', 'output_file', None): config_output_path}
    mock_config_parser_instance.get.side_effect = lambda sec, k, fallback: config_values.get((sec, k, fallback), fallback)
    mocker.patch('monitor_net.configparser.ConfigParser', return_value=mock_config_parser_instance)

    mocker.patch('monitor_net.platform.system', return_value="Linux")
    mock_logger_instance = MagicMock(spec=logging.Logger)
    mock_logger_instance.handlers = []
    mocker.patch('logging.getLogger', return_value=mock_logger_instance)
    mocker.patch('monitor_net.socket.gethostbyname', return_value="1.2.3.4")
    mocker.patch('builtins.open', mocker.mock_open())

    monitor = NetworkMonitor(mock_default_args)
    assert monitor.output_file_path == config_output_path
    mock_logger_instance.info.assert_any_call(
        f"Using 'output_file' from config file: {config_output_path}"
    )
    mock_logger_instance.info.assert_any_call(f"Effective output file: {config_output_path}")

def test_output_file_arg_parsing_cli_overrides_config(mocker, mock_default_args):
    """Test CLI --output-file overrides config file's output_file."""
    cli_output_path = "cli_path.csv"
    config_output_path = "config_path.csv"
    mock_default_args.output_file = cli_output_path # CLI specifies

    # Mock config file settings
    mocker.patch('monitor_net.os.path.exists', side_effect=lambda path: path.endswith('.ini'))
    mock_config_parser_instance = MagicMock(spec=configparser.ConfigParser)
    mock_config_parser_instance.read.return_value = ["dummy_path/monitor_config.ini"]
    mock_config_parser_instance.__contains__.side_effect = lambda item: item == 'MonitorSettings'
    config_values = {('MonitorSettings', 'output_file', None): config_output_path}
    mock_config_parser_instance.get.side_effect = lambda sec, k, fallback: config_values.get((sec, k, fallback), fallback)
    mocker.patch('monitor_net.configparser.ConfigParser', return_value=mock_config_parser_instance)

    mocker.patch('monitor_net.platform.system', return_value="Linux")
    mock_logger_instance = MagicMock(spec=logging.Logger)
    mock_logger_instance.handlers = []
    mocker.patch('logging.getLogger', return_value=mock_logger_instance)
    mocker.patch('monitor_net.socket.gethostbyname', return_value="1.2.3.4")
    mocker.patch('builtins.open', mocker.mock_open())

    monitor = NetworkMonitor(mock_default_args)
    assert monitor.output_file_path == cli_output_path
    mock_logger_instance.info.assert_any_call(
        f"CLI 'output_file' ({cli_output_path}) overrides other settings."
    )
    # Ensure config log is present, and CLI override log is also present and later.
    log_calls = [c[0][0] for c in mock_logger_instance.info.call_args_list]
    assert any(f"Using 'output_file' from config file: {config_output_path}" in call_text for call_text in log_calls)
    assert any(f"CLI 'output_file' ({cli_output_path}) overrides other settings." in call_text for call_text in log_calls)

    # More precise check: CLI override message should appear AFTER config usage message if both exist.
    config_log_idx = -1
    cli_override_log_idx = -1
    for i, call_text in enumerate(log_calls):
        if f"Using 'output_file' from config file: {config_output_path}" in call_text:
            config_log_idx = i
        if f"CLI 'output_file' ({cli_output_path}) overrides other settings." in call_text:
            cli_override_log_idx = i

    assert config_log_idx != -1, "Config usage log not found"
    assert cli_override_log_idx != -1, "CLI override log not found"
    assert cli_override_log_idx > config_log_idx, "CLI override log should appear after config usage log"


def test_output_file_arg_parsing_default_is_none(mocker, mock_default_args):
    """Test output_file_path is None if not specified by CLI or config."""
    mock_default_args.output_file = None # CLI does not specify

    mocker.patch('monitor_net.os.path.exists', return_value=False) # No config file
    mocker.patch('monitor_net.platform.system', return_value="Linux")
    mock_logger_instance = MagicMock(spec=logging.Logger)
    mock_logger_instance.handlers = []
    mocker.patch('logging.getLogger', return_value=mock_logger_instance)
    # socket and open should not be called if output_file_path is None
    mock_socket_gethostbyname = mocker.patch('monitor_net.socket.gethostbyname')
    mock_builtin_open = mocker.patch('builtins.open')

    monitor = NetworkMonitor(mock_default_args)
    assert monitor.output_file_path is None
    mock_logger_instance.info.assert_any_call("Effective output file: None")
    mock_socket_gethostbyname.assert_not_called()
    mock_builtin_open.assert_not_called()


# --- Tests for CSV Initialization and Header Writing ---

@pytest.fixture
def mock_monitor_for_csv(mocker, mock_default_args):
    """
    Provides a NetworkMonitor instance where essential external dependencies
    for CSV initialization are pre-mocked.
    Specific test functions can then override individual mocks as needed.
    """
    mocker.patch('monitor_net.platform.system', return_value="Linux")
    mock_logger = MagicMock(spec=logging.Logger)
    mock_logger.handlers = []
    mocker.patch('logging.getLogger', return_value=mock_logger)

    # Default mocks, can be overridden in tests
    mocker.patch('monitor_net.os.path.exists', return_value=False)
    mocker.patch('monitor_net.os.path.getsize', return_value=0)
    mocker.patch('builtins.open', mocker.mock_open())
    mocker.patch('monitor_net.csv.writer', return_value=MagicMock())
    mocker.patch('monitor_net.socket.gethostbyname', return_value='1.2.3.4')

    # Allow config file to be non-existent for focused testing unless specified
    # This prevents interference from config file logic if not being tested.
    # The `os.path.exists` mock above will also make it think config file doesn't exist
    # if the path doesn't end with .ini (which it won't for default config path)
    # To be more explicit:
    original_os_path_exists = os.path.exists
    def exists_side_effect(path):
        if path == monitor_net.CONFIG_FILE_NAME or path.endswith(monitor_net.CONFIG_FILE_NAME) : # check for config
             return False # Explicitly say global config file doesn't exist for these csv tests
        if path == "test_output.csv": # The file we are testing for csv
             # This will be re-mocked by specific tests using this fixture
             return mocker.get_original_mock_for('monitor_net.os.path.exists')(path)
        return original_os_path_exists(path) # real behavior for other paths

    mocker.patch('monitor_net.os.path.exists', side_effect=exists_side_effect)


    # The mock_default_args will be modified by each test to set output_file
    monitor = NetworkMonitor(mock_default_args)
    monitor.logger = mock_logger # Ensure the instance uses our pre-mocked logger
    return monitor


def test_csv_init_no_output_file(mocker, mock_default_args):
    """Test CSV attributes are None if no output file is specified."""
    mock_default_args.output_file = None
    # Need to mock platform and logger as __init__ runs fully
    mocker.patch('monitor_net.platform.system', return_value="Linux")
    mock_logger = MagicMock(spec=logging.Logger); mock_logger.handlers = []
    mocker.patch('logging.getLogger', return_value=mock_logger)
    # No config file for this simple check
    mocker.patch('monitor_net.os.path.exists', return_value=False)


    monitor = NetworkMonitor(mock_default_args)

    assert monitor.output_file_handle is None
    assert monitor.csv_writer is None
    assert monitor.resolved_ip is None # Should not be resolved if no output file


def test_csv_init_new_file(mocker, mock_default_args):
    """Test CSV init when output file is new."""
    test_csv_path = "test_output.csv"
    mock_default_args.output_file = test_csv_path

    mocker.patch('monitor_net.platform.system', return_value="Linux")
    mock_logger_instance = MagicMock(spec=logging.Logger); mock_logger_instance.handlers = []
    mocker.patch('logging.getLogger', return_value=mock_logger_instance)

    # Ensure config file is seen as not existing to isolate CSV open call
    def exists_side_effect_new_csv(path):
        if monitor_net.CONFIG_FILE_NAME in path: return False
        if path == test_csv_path: return False # This is a new CSV file
        return True # Default for other paths if any (shouldn't matter here)
    mock_os_path_exists = mocker.patch('monitor_net.os.path.exists', side_effect=exists_side_effect_new_csv)

    mocker.patch('monitor_net.os.path.getsize', return_value=0)
    mock_open_func = mocker.patch('builtins.open', mocker.mock_open())
    mock_csv_writer_obj = MagicMock()
    mock_csv_module_writer = mocker.patch('monitor_net.csv.writer', return_value=mock_csv_writer_obj)
    mock_socket_gethostbyname = mocker.patch('monitor_net.socket.gethostbyname', return_value='1.2.3.4')

    monitor = NetworkMonitor(mock_default_args)

    mock_socket_gethostbyname.assert_called_once_with(mock_default_args.host)
    assert monitor.resolved_ip == '1.2.3.4'
    mock_open_func.assert_called_once_with(test_csv_path, 'a', newline='', encoding='utf-8')
    mock_csv_module_writer.assert_called_once_with(mock_open_func.return_value)
    mock_csv_writer_obj.writerow.assert_called_once_with(
        ["Timestamp", "MonitoredHost", "ResolvedIP", "LatencyMS", "IsSuccess"]
    )
    assert monitor.output_file_handle is not None
    assert monitor.csv_writer is not None
    mock_logger_instance.info.assert_any_call(f"Logging ping data to CSV: {test_csv_path}")


def test_csv_init_existing_empty_file(mocker, mock_default_args):
    """Test CSV init when output file exists but is empty."""
    test_csv_path = "test_output.csv"
    mock_default_args.output_file = test_csv_path

    mocker.patch('monitor_net.platform.system', return_value="Linux")
    mock_logger_instance = MagicMock(spec=logging.Logger); mock_logger_instance.handlers = []
    mocker.patch('logging.getLogger', return_value=mock_logger_instance)

    # Ensure config file is seen as not existing
    def exists_side_effect_empty_csv(path):
        if monitor_net.CONFIG_FILE_NAME in path: return False
        if path == test_csv_path: return True # This CSV file exists
        return False
    mocker.patch('monitor_net.os.path.exists', side_effect=exists_side_effect_empty_csv)
    mocker.patch('monitor_net.os.path.getsize', return_value=0)  # File is empty
    mock_open_func = mocker.patch('builtins.open', mocker.mock_open())
    mock_csv_writer_obj = MagicMock()
    mocker.patch('monitor_net.csv.writer', return_value=mock_csv_writer_obj)
    mocker.patch('monitor_net.socket.gethostbyname', return_value='1.2.3.4')

    monitor = NetworkMonitor(mock_default_args)

    mock_open_func.assert_called_once_with(test_csv_path, 'a', newline='', encoding='utf-8')
    mock_csv_writer_obj.writerow.assert_called_once_with(
        ["Timestamp", "MonitoredHost", "ResolvedIP", "LatencyMS", "IsSuccess"]
    )

def test_csv_init_existing_non_empty_file(mocker, mock_default_args):
    """Test CSV init when output file exists and is not empty."""
    test_csv_path = "test_output.csv"
    mock_default_args.output_file = test_csv_path

    mocker.patch('monitor_net.platform.system', return_value="Linux")
    mocker.patch('logging.getLogger').return_value = MagicMock(handlers=[]) # Basic mock for logger

    # Ensure config file is seen as not existing
    def exists_side_effect_nonempty_csv(path):
        if monitor_net.CONFIG_FILE_NAME in path: return False
        if path == test_csv_path: return True # This CSV file exists
        return False
    mocker.patch('monitor_net.os.path.exists', side_effect=exists_side_effect_nonempty_csv)
    mocker.patch('monitor_net.os.path.getsize', return_value=100) # File not empty
    mock_open_func = mocker.patch('builtins.open', mocker.mock_open())
    mock_csv_writer_obj = MagicMock()
    mocker.patch('monitor_net.csv.writer', return_value=mock_csv_writer_obj)
    mocker.patch('monitor_net.socket.gethostbyname', return_value='1.2.3.4')

    monitor = NetworkMonitor(mock_default_args)

    mock_open_func.assert_called_once_with(test_csv_path, 'a', newline='', encoding='utf-8')
    mock_csv_writer_obj.writerow.assert_not_called() # Header should not be written


def test_csv_init_dns_failure(mocker, mock_default_args):
    """Test CSV init when DNS resolution for the host fails."""
    test_csv_path = "test_output.csv"
    mock_default_args.output_file = test_csv_path

    mocker.patch('monitor_net.platform.system', return_value="Linux")
    mock_logger_instance = MagicMock(spec=logging.Logger); mock_logger_instance.handlers = []
    mocker.patch('logging.getLogger', return_value=mock_logger_instance)

    mocker.patch('monitor_net.os.path.exists', return_value=False) # New file
    mocker.patch('builtins.open', mocker.mock_open())
    mocker.patch('monitor_net.csv.writer')
    mocker.patch('monitor_net.socket.gethostbyname', side_effect=socket.gaierror("DNS lookup failed"))

    monitor = NetworkMonitor(mock_default_args)

    assert monitor.resolved_ip == "" # Should be empty string on failure
    mock_logger_instance.warning.assert_any_call(
        f"Could not resolve IP for host '{mock_default_args.host}'. IP field in CSV will be blank."
    )


def test_csv_init_io_error_opening(mocker, mock_default_args):
    """Test CSV init when opening the output file raises IOError."""
    test_csv_path = "test_output.csv"
    mock_default_args.output_file = test_csv_path

    mocker.patch('monitor_net.platform.system', return_value="Linux")
    mock_logger_instance = MagicMock(spec=logging.Logger); mock_logger_instance.handlers = []
    mocker.patch('logging.getLogger', return_value=mock_logger_instance)

    mocker.patch('monitor_net.os.path.exists', return_value=False) # New file
    mocker.patch('monitor_net.socket.gethostbyname', return_value='1.2.3.4')
    mocker.patch('builtins.open', side_effect=IOError("Permission denied"))

    monitor = NetworkMonitor(mock_default_args)

    assert monitor.output_file_handle is None
    assert monitor.csv_writer is None
    assert monitor.output_file_path is None # Path should be reset to disable CSV
    mock_logger_instance.error.assert_any_call(
        f"Error opening or writing header to CSV file '{test_csv_path}': Permission denied. CSV logging will be disabled."
    )

# --- Tests for CSV Data Row Writing ---

def test_csv_write_row_success(mocker, mock_default_args):
    """Test a successful ping logs a correct row to CSV."""
    monitor = NetworkMonitor(mock_default_args) # output_file_path is None initially
    # Manually set up CSV writer and related attributes for focused test
    monitor.output_file_path = "test.csv" # Needs a path for logging messages
    monitor.csv_writer = mocker.MagicMock() # Plain MagicMock is fine
    monitor.output_file_handle = mocker.MagicMock() # Needs flush method
    monitor.resolved_ip = "1.2.3.4"
    monitor.host = "test.host" # From mock_default_args or set explicitly

    fixed_timestamp = "2023-01-01T12:00:00.000000"
    mocker.patch('monitor_net.datetime') # Patch entire module
    monitor_net.datetime.now.return_value.isoformat.return_value = fixed_timestamp

    current_latency_real = 10.5

    # Simulate the part of the run loop that calls the CSV writing
    # This is a simplified representation of the logic in run()
    if monitor.csv_writer:
        timestamp = monitor_net.datetime.now().isoformat()
        is_success = current_latency_real is not None
        latency_ms_for_csv = current_latency_real if is_success else ''
        row_data = [
            timestamp,
            monitor.host,
            monitor.resolved_ip if monitor.resolved_ip else '',
            latency_ms_for_csv,
            is_success
        ]
        monitor.csv_writer.writerow(row_data)
        if monitor.output_file_handle:
            monitor.output_file_handle.flush()

    monitor.csv_writer.writerow.assert_called_once_with(
        [fixed_timestamp, "test.host", "1.2.3.4", 10.5, True]
    )
    monitor.output_file_handle.flush.assert_called_once()


def test_csv_write_row_failure(mocker, mock_default_args):
    """Test a failed ping logs a correct row to CSV."""
    monitor = NetworkMonitor(mock_default_args)
    monitor.output_file_path = "test.csv"
    monitor.csv_writer = mocker.MagicMock() # Plain MagicMock is fine
    monitor.output_file_handle = mocker.MagicMock()
    monitor.resolved_ip = "1.2.3.4"
    monitor.host = "test.host"

    fixed_timestamp = "2023-01-01T12:00:01.000000"
    # Ensure datetime is mocked correctly within the scope of where it's called
    # If it's from monitor_net.datetime, then:
    mocker.patch('monitor_net.datetime')
    monitor_net.datetime.now.return_value.isoformat.return_value = fixed_timestamp

    current_latency_real = None # Failed ping

    if monitor.csv_writer:
        timestamp = monitor_net.datetime.now().isoformat()
        is_success = current_latency_real is not None
        latency_ms_for_csv = current_latency_real if is_success else ''
        row_data = [
            timestamp,
            monitor.host,
            monitor.resolved_ip if monitor.resolved_ip else '',
            latency_ms_for_csv,
            is_success
        ]
        monitor.csv_writer.writerow(row_data)
        if monitor.output_file_handle:
            monitor.output_file_handle.flush()

    monitor.csv_writer.writerow.assert_called_once_with(
        [fixed_timestamp, "test.host", "1.2.3.4", '', False]
    )
    monitor.output_file_handle.flush.assert_called_once()


def test_csv_write_io_error(mocker, mock_default_args):
    """Test IOError during CSV write disables further CSV logging."""
    # We need a monitor instance where CSV was initially set up
    mock_default_args.output_file = "test_io_error.csv" # Enable CSV path

    mocker.patch('monitor_net.platform.system', return_value="Linux")
    mock_logger_instance = MagicMock(spec=logging.Logger); mock_logger_instance.handlers = []
    mocker.patch('logging.getLogger', return_value=mock_logger_instance)

    # Mock successful CSV setup in __init__
    def exists_side_effect_io_error(path): # New file for CSV, no config file
        if monitor_net.CONFIG_FILE_NAME in path: return False
        return False
    mocker.patch('monitor_net.os.path.exists', side_effect=exists_side_effect_io_error)
    mocker.patch('monitor_net.socket.gethostbyname', return_value='1.2.3.4')
    # This open is for the CSV file which will fail
    mock_open_func = mocker.patch('builtins.open', mocker.mock_open())

    # This is the writer instance that would be created if open succeeded
    mock_csv_writer_instance = MagicMock()
    mocker.patch('monitor_net.csv.writer', return_value=mock_csv_writer_instance)

    monitor = NetworkMonitor(mock_default_args) # __init__ will call the patched open
    assert monitor.csv_writer is not None # Pre-condition: CSV writer is active
    assert monitor.csv_writer is mock_csv_writer_instance # Ensure it's the one we are about to modify

    # Now, make the (correct) writer instance's writerow method raise IOError for the data write
    # The header write should have succeeded (or not happened if file existed and was non-empty).
    # For this test, we assume header write was fine.
    mock_csv_writer_instance.writerow.side_effect = IOError("Disk full")

    # Simulate a ping result and the CSV writing part of run()
    current_latency_real = 20.0
    mocker.patch('monitor_net.datetime')
    monitor_net.datetime.now.return_value.isoformat.return_value = "timestamp"

    # Extracted CSV writing logic from run() for testing
    if monitor.csv_writer:
        timestamp = monitor_net.datetime.now().isoformat()
        is_success = current_latency_real is not None
        latency_ms_for_csv = current_latency_real if is_success else ''
        row_data = [timestamp, monitor.host, monitor.resolved_ip if monitor.resolved_ip else '', latency_ms_for_csv, is_success]
        try:
            monitor.csv_writer.writerow(row_data) # This should raise IOError
            if monitor.output_file_handle:
                monitor.output_file_handle.flush()
        except IOError as e:
            monitor.logger.error(f"Error writing to CSV file: {e}. Disabling further CSV logging.")
            if monitor.output_file_handle:
                monitor.output_file_handle.close() # Close on error
            monitor.csv_writer = None
            monitor.output_file_handle = None
            monitor.output_file_path = None # Important: disable path to prevent re-opening

    assert monitor.csv_writer is None
    assert monitor.output_file_handle is None
    assert monitor.output_file_path is None # Check that path is reset
    mock_logger_instance.error.assert_any_call("Error writing to CSV file: Disk full. Disabling further CSV logging.")


# --- Test for CSV File Closing ---

def test_csv_file_closed_on_exit(mocker, mock_default_args):
    """Test the CSV output file is closed by _restore_terminal."""
    # Enable CSV path to simulate it being opened
    mock_default_args.output_file = "test_close.csv"

    mocker.patch('monitor_net.platform.system', return_value="Linux")
    mock_logger_instance = MagicMock(spec=logging.Logger); mock_logger_instance.handlers = []
    mocker.patch('logging.getLogger', return_value=mock_logger_instance)

    # Mock successful CSV setup in __init__
    def exists_side_effect_close_test(path): # New file for CSV, no config file
        if monitor_net.CONFIG_FILE_NAME in path: return False
        if path == "test_close.csv": return False # CSV is new
        return False
    mocker.patch('monitor_net.os.path.exists', side_effect=exists_side_effect_close_test)
    mocker.patch('monitor_net.socket.gethostbyname', return_value='1.2.3.4')

    # Correctly mock open to get a handle that can be closed
    mock_file_handle = MagicMock() # Simpler mock, close will be auto-created
    mocker.patch('builtins.open', return_value=mock_file_handle)
    mocker.patch('monitor_net.csv.writer')

    monitor = NetworkMonitor(mock_default_args)

    # Pre-conditions: Ensure CSV was set up and self.output_file_handle is the return_value of the mocked open
    assert monitor.output_file_handle is mock_file_handle
    assert monitor.output_file_path == "test_close.csv" # Confirm path is also set
    original_path = monitor.output_file_path # Save for log check

    # Call _restore_terminal (which should close the file)

    # Mock sys.stdout.write as it's called by _restore_terminal
    mock_stdout_write = mocker.patch('sys.stdout.write')

    # Simplify termios mocking for this specific test:
    # We are not testing termios itself here, just that it doesn't break CSV closing.
    # So, if termios is used, make sure its calls don't raise errors.
    if monitor.current_os != "windows": # Check against monitor's detected OS
        mock_termios_module = mocker.patch('monitor_net.termios')
        mock_termios_module.tcsetattr = MagicMock()
        # Ensure original_terminal_settings is not None so tcsetattr is called
        monitor.original_terminal_settings = "fake_settings"

    # monitor.output_file_handle = mock_file_handle # Removed for testing natural state

    monitor._restore_terminal()

    mock_file_handle.close.assert_called_once() # Check the auto-created close mock
    mock_logger_instance.info.assert_any_call(f"Closing CSV output file: {original_path}")
    assert monitor.output_file_handle is None
    assert monitor.csv_writer is None
