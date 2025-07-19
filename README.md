# Internet Monitor

A robust Python-based internet connectivity monitoring tool that tracks internet availability and sends notifications when outages occur or when connectivity is restored.

## Features

- **Real-time monitoring**: Continuously monitors internet connectivity by pinging a configurable target
- **Configurable thresholds**: Set custom failure thresholds to avoid false positives
- **Cross-platform support**: Works on Windows, macOS, and Linux
- **Enhanced logging**: Comprehensive logging with rotation and multiple output formats
- **Notification system**: Send alerts via Prowl API when outages occur or connectivity is restored
- **Statistics tracking**: Monitor success rates and connection statistics
- **Graceful error handling**: Robust error handling with detailed logging
- **Environment-based configuration**: Easy configuration through environment variables

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd monitor-internet
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

Or if using Pipenv:
```bash
pipenv install
```

## Configuration

The application can be configured using environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `MONITOR_IP_ADDRESS` | `8.8.8.8` | IP address to ping for connectivity checks |
| `MONITOR_FAILURE_THRESHOLD` | `2` | Number of consecutive failures before considering internet down |
| `MONITOR_CHECK_INTERVAL` | `10` | Interval between checks in seconds |
| `MONITOR_LOG_FILE` | `internet_monitor.log` | Path to the log file |
| `PROWL_API_KEY` | `None` | Prowl API key for notifications (optional) |
| `MONITOR_MAX_RETRIES` | `3` | Maximum number of retry attempts |
| `MONITOR_RETRY_DELAY` | `2` | Delay between retry attempts in seconds |

### Setting up Prowl Notifications

1. Get a Prowl API key from [prowlapp.com](https://prowlapp.com)
2. Set the environment variable:
```bash
export PROWL_API_KEY="your-api-key-here"
```

## Usage

### Basic Usage

Run the monitor with default settings:
```bash
python monitor.py
```

### With Custom Configuration

Set environment variables and run:
```bash
export MONITOR_IP_ADDRESS="1.1.1.1"
export MONITOR_CHECK_INTERVAL="30"
export PROWL_API_KEY="your-key"
python monitor.py
```

### Windows PowerShell

```powershell
$env:MONITOR_IP_ADDRESS="1.1.1.1"
$env:MONITOR_CHECK_INTERVAL="30"
$env:PROWL_API_KEY="your-key"
python monitor.py
```

## Output

The application provides:

1. **Console output**: Real-time status updates and statistics
2. **Log file**: Detailed logs with rotation (daily rotation, 7-day retention)
3. **Notifications**: Push notifications via Prowl when status changes

### Sample Output

```
2024-01-15 10:30:00,123 - InternetMonitor - INFO - Starting internet monitoring for 8.8.8.8
2024-01-15 10:30:00,124 - InternetMonitor - INFO - Check interval: 10s, Failure threshold: 2
2024-01-15 10:30:00,125 - InternetMonitor - INFO - Connected - pinging 8.8.8.8
2024-01-15 10:30:10,126 - InternetMonitor - INFO - Connected - pinging 8.8.8.8
2024-01-15 10:30:20,127 - InternetMonitor - INFO - Consecutive failure 1/2
2024-01-15 10:30:22,128 - InternetMonitor - INFO - Consecutive failure 2/2
2024-01-15 10:30:22,129 - InternetMonitor - CRITICAL - Threshold breached - internet down after 2 consecutive failures
2024-01-15 10:30:22,130 - InternetMonitor - INFO - Disconnected - pinging 8.8.8.8
2024-01-15 10:30:22,131 - InternetMonitor - INFO - Queued message: Internet connection lost! - 2024-01-15 10:30:22
2024-01-15 10:30:22,132 - InternetMonitor - INFO - Notification sent successfully!
```

## Statistics

The application tracks and reports statistics every 100 checks:

```json
{
  "total_checks": 100,
  "total_failures": 5,
  "success_rate": 95.0,
  "current_status": "Connected"
}
```

## Error Handling

The application includes comprehensive error handling:

- **Network errors**: Graceful handling of network timeouts and connection issues
- **API errors**: Proper error handling for notification service failures
- **File system errors**: Safe handling of log file creation and rotation
- **Platform differences**: Automatic detection and use of appropriate ping commands

## Logging

Logs are written to both console and file with the following features:

- **Log rotation**: Daily rotation with 7-day retention
- **Multiple levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Structured format**: Timestamp, logger name, level, and message
- **Error recovery**: Continues operation even if file logging fails

## Development

### Running Tests

```bash
python monitor_tests.py
```

### Code Structure

- `Config`: Configuration management using dataclasses
- `Logger`: Enhanced logging with rotation and error handling
- `NotificationService`: Prowl API integration for notifications
- `InternetMonitor`: Main monitoring logic with statistics tracking

### Adding New Features

The modular design makes it easy to extend:

1. Add new configuration options to the `Config` class
2. Implement new notification services by extending the notification system
3. Add new monitoring methods by extending the `InternetMonitor` class

## Troubleshooting

### Common Issues

1. **Permission denied for log file**: Ensure write permissions in the log directory
2. **Prowl notifications not working**: Verify API key and internet connectivity
3. **High CPU usage**: Increase check interval to reduce system load
4. **False positives**: Increase failure threshold for more stable networks

### Debug Mode

Enable debug logging by modifying the Logger initialization:
```python
logger = Logger(log_file="debug.log", log_level="DEBUG")
```

## License

[Add your license information here]

## Contributing

[Add contribution guidelines here]

