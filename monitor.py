import os
import time
import sys
from datetime import datetime
from typing import Optional, List
import requests
import logging
from logging.handlers import TimedRotatingFileHandler
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    """Configuration class for the internet monitor."""
    ip_address: str = "8.8.8.8"
    failure_threshold: int = 2
    check_interval: int = 10
    log_file: str = "internet_monitor.log"
    prowl_api_key: Optional[str] = None
    max_retries: int = 3
    retry_delay: int = 2
    log_successful_pings: bool = False

    @classmethod
    def from_env(cls) -> 'Config':
        """Create configuration from environment variables."""
        return cls(
            ip_address=os.getenv("MONITOR_IP_ADDRESS", "8.8.8.8"),
            failure_threshold=int(os.getenv("MONITOR_FAILURE_THRESHOLD", "2")),
            check_interval=int(os.getenv("MONITOR_CHECK_INTERVAL", "10")),
            log_file=os.getenv("MONITOR_LOG_FILE", "internet_monitor.log"),
            prowl_api_key=os.getenv("PROWL_API_KEY"),
            max_retries=int(os.getenv("MONITOR_MAX_RETRIES", "3")),
            retry_delay=int(os.getenv("MONITOR_RETRY_DELAY", "2")),
            log_successful_pings=os.getenv("MONITOR_LOG_SUCCESSFUL_PINGS", "false").lower() == "true"
        )


class Logger:
    """Enhanced logging class with better configuration and error handling."""
    
    def __init__(self, log_file: str = "internet_monitor.log", log_level: str = "INFO"):
        self.logger = logging.getLogger("InternetMonitor")
        
        # Set log level
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        self.logger.setLevel(level_map.get(log_level.upper(), logging.INFO))

        # Prevent duplicate handlers
        if self.logger.hasHandlers():
            return

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # File handler with rotation
        try:
            file_handler = TimedRotatingFileHandler(
                log_file, 
                when="midnight", 
                interval=1, 
                backupCount=7
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        except Exception as e:
            print(f"Warning: Could not create file handler: {e}")

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def info(self, message: str) -> None:
        """Log info message."""
        self.logger.info(message)

    def warning(self, message: str) -> None:
        """Log warning message."""
        self.logger.warning(message)

    def error(self, message: str) -> None:
        """Log error message."""
        self.logger.error(message)

    def debug(self, message: str) -> None:
        """Log debug message."""
        self.logger.debug(message)

    def critical(self, message: str) -> None:
        """Log critical message."""
        self.logger.critical(message)


class NotificationService:
    """Service for sending notifications via Prowl API."""
    
    def __init__(self, api_key: Optional[str], logger: Logger):
        self.api_key = api_key
        self.logger = logger
        self.base_url = "https://api.prowlapp.com/publicapi/add"
        
        if not self.api_key:
            self.logger.warning("Prowl API key is not set. Notifications will be disabled.")

    def send_notification(self, message: str, priority: int = 1) -> bool:
        """
        Send notification via Prowl API.
        
        Args:
            message: The message to send
            priority: Prowl priority (-2 to 2)
            
        Returns:
            bool: True if notification was sent successfully
        """
        if not self.api_key:
            self.logger.warning("Cannot send notification: API key not configured")
            return False

        payload = {
            "apikey": self.api_key,
            "application": "Internet Monitor",
            "event": "Internet Status",
            "description": message,
            "priority": max(-2, min(2, priority))  # Clamp priority between -2 and 2
        }
        
        try:
            response = requests.post(self.base_url, data=payload, timeout=10)
            if response.status_code == 200:
                self.logger.info("Notification sent successfully!")
                return True
            else:
                self.logger.warning(f"Failed to send notification: HTTP {response.status_code}")
                return False
        except requests.exceptions.Timeout:
            self.logger.error("Notification request timed out")
            return False
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error sending notification: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error sending notification: {e}")
            return False


class InternetMonitor:
    """Main internet monitoring class with enhanced functionality."""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = Logger(config.log_file)
        self.notifier = NotificationService(config.prowl_api_key, self.logger)
        
        # State tracking
        self.message_queue: List[str] = []
        self.outage_start_time: Optional[datetime] = None
        self.was_connected = True
        self.consecutive_failures = 0
        self.total_checks = 0
        self.total_failures = 0

    def ping(self, target: str) -> bool:
        """
        Ping a target IP address.
        
        Args:
            target: IP address to ping
            
        Returns:
            bool: True if ping is successful
        """
        try:
            # Use platform-appropriate ping command
            if sys.platform.startswith('win'):
                response = os.system(f"ping -n 1 {target} > nul 2>&1")
            else:
                response = os.system(f"ping -c 1 {target} > /dev/null 2>&1")
            
            return response == 0
        except Exception as e:
            self.logger.error(f"Error during ping: {e}")
            return False

    def is_internet_down(self) -> bool:
        """
        Check if internet is down by performing multiple ping attempts.
        
        Returns:
            bool: True if internet is down
        """
        consecutive_failures = 0
        
        for attempt in range(self.config.failure_threshold):
            self.logger.debug(f"Ping attempt {attempt + 1}/{self.config.failure_threshold}")
            
            if not self.ping(self.config.ip_address):
                consecutive_failures += 1
                self.logger.info(f'Consecutive failure {consecutive_failures}/{self.config.failure_threshold}')
                
                if attempt < self.config.failure_threshold - 1:
                    time.sleep(self.config.retry_delay)
            else:
                return False
        
        self.logger.critical(f"Threshold breached - internet down after {consecutive_failures} consecutive failures")
        return True

    def log_result(self, result: bool) -> None:
        """Log the current connection status."""
        if result and not self.config.log_successful_pings:
            # Don't log successful pings unless configured to do so
            return
            
        status = "Connected" if result else "Disconnected"
        self.logger.info(f"{status} - pinging {self.config.ip_address}")

    def queue_message(self, message: str) -> None:
        """Add message to notification queue."""
        self.message_queue.append(message)
        self.logger.info(f"Queued message: {message}")

    def send_queued_messages(self) -> None:
        """Send all queued messages."""
        while self.message_queue:
            message = self.message_queue.pop(0)
            self.notifier.send_notification(message)

    def get_outage_duration(self) -> Optional[str]:
        """Get the duration of the current outage."""
        if self.outage_start_time:
            outage_end_time = datetime.now()
            duration = outage_end_time - self.outage_start_time
            return str(duration)
        return None

    def handle_outage(self) -> None:
        """Handle internet outage event."""
        self.outage_start_time = datetime.now()
        current_time = self.outage_start_time.strftime("%Y-%m-%d %H:%M:%S")
        self.queue_message(f"Internet connection lost! - {current_time}")

    def handle_recovery(self) -> None:
        """Handle internet recovery event."""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        outage_duration = self.get_outage_duration()

        if outage_duration:
            self.queue_message(
                f"Internet connection restored! - {current_time} - "
                f"outage duration: {outage_duration}"
            )
        else:
            self.queue_message(f"Internet connection restored! - {current_time}")

        self.send_queued_messages()
        self.outage_start_time = None

    def get_statistics(self) -> dict:
        """Get monitoring statistics."""
        return {
            "total_checks": self.total_checks,
            "total_failures": self.total_failures,
            "success_rate": ((self.total_checks - self.total_failures) / self.total_checks * 100) if self.total_checks > 0 else 0,
            "current_status": "Connected" if self.was_connected else "Disconnected"
        }

    def monitor(self) -> None:
        """Main monitoring loop."""
        self.logger.info(f"Starting internet monitoring for {self.config.ip_address}")
        self.logger.info(f"Check interval: {self.config.check_interval}s, Failure threshold: {self.config.failure_threshold}")
        self.logger.info(f"Log successful pings: {self.config.log_successful_pings}")
        
        try:
            while True:
                self.total_checks += 1
                result = not self.is_internet_down()
                
                if not result:
                    self.total_failures += 1
                
                self.log_result(result)

                if not result and self.was_connected:
                    self.handle_outage()
                    self.was_connected = False
                elif result and not self.was_connected:
                    self.handle_recovery()
                    self.was_connected = True

                # Log statistics every 100 checks
                if self.total_checks % 100 == 0:
                    stats = self.get_statistics()
                    self.logger.info(f"Statistics: {json.dumps(stats, indent=2)}")

                time.sleep(self.config.check_interval)
                
        except KeyboardInterrupt:
            self.logger.info("Monitoring stopped by user")
            stats = self.get_statistics()
            self.logger.info(f"Final statistics: {json.dumps(stats, indent=2)}")
        except Exception as e:
            self.logger.error(f"Unexpected error in monitoring loop: {e}")
            raise


def main():
    """Main entry point."""
    try:
        config = Config.from_env()
        internet_monitor = InternetMonitor(config)
        internet_monitor.monitor()
    except Exception as e:
        print(f"Failed to start internet monitor: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()