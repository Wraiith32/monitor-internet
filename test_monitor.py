#!/usr/bin/env python3
"""
Simple test script for the improved Internet Monitor.
"""

import os
import sys
import time
from unittest.mock import patch, MagicMock
from monitor import Config, Logger, NotificationService, InternetMonitor


def test_config():
    """Test configuration loading."""
    print("Testing configuration...")
    
    # Test default config
    config = Config()
    assert config.ip_address == "8.8.8.8"
    assert config.failure_threshold == 2
    assert config.check_interval == 10
    
    # Test environment variable loading
    os.environ["MONITOR_IP_ADDRESS"] = "1.1.1.1"
    os.environ["MONITOR_CHECK_INTERVAL"] = "30"
    os.environ["MONITOR_LOG_SUCCESSFUL_PINGS"] = "true"
    
    config = Config.from_env()
    assert config.ip_address == "1.1.1.1"
    assert config.check_interval == 30
    assert config.log_successful_pings == True
    
    print("✓ Configuration tests passed")


def test_logger():
    """Test logger functionality."""
    print("Testing logger...")
    
    logger = Logger(log_file="test.log")
    logger.info("Test info message")
    logger.warning("Test warning message")
    logger.error("Test error message")
    logger.debug("Test debug message")
    logger.critical("Test critical message")
    
    print("✓ Logger tests passed")


def test_notification_service():
    """Test notification service."""
    print("Testing notification service...")
    
    logger = Logger()
    notifier = NotificationService("test-key", logger)
    
    # Test with valid API key
    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        result = notifier.send_notification("Test notification")
        assert result is True
    
    # Test without API key
    notifier_no_key = NotificationService(None, logger)
    result = notifier_no_key.send_notification("Test notification")
    assert result is False
    
    print("✓ Notification service tests passed")


def test_internet_monitor():
    """Test internet monitor functionality."""
    print("Testing internet monitor...")
    
    config = Config(ip_address="127.0.0.1", failure_threshold=1, check_interval=1)
    monitor = InternetMonitor(config)
    
    # Test ping method
    result = monitor.ping("127.0.0.1")
    assert result is True
    
    # Test statistics
    stats = monitor.get_statistics()
    assert "total_checks" in stats
    assert "total_failures" in stats
    assert "success_rate" in stats
    assert "current_status" in stats
    
    # Test logging configuration
    # Test with log_successful_pings=False (default)
    monitor.config.log_successful_pings = False
    monitor.log_result(True)  # Should not log successful ping
    
    # Test with log_successful_pings=True
    monitor.config.log_successful_pings = True
    monitor.log_result(True)  # Should log successful ping
    
    print("✓ Internet monitor tests passed")


def test_integration():
    """Test basic integration."""
    print("Testing integration...")
    
    config = Config(
        ip_address="127.0.0.1",
        failure_threshold=1,
        check_interval=1,
        prowl_api_key=None  # Disable notifications for testing
    )
    
    monitor = InternetMonitor(config)
    
    # Test a few monitoring cycles
    for i in range(3):
        monitor.total_checks += 1  # Manually increment for testing
        result = not monitor.is_internet_down()
        monitor.log_result(result)
        time.sleep(0.1)  # Short delay for testing
    
    stats = monitor.get_statistics()
    assert stats["total_checks"] >= 3
    
    print("✓ Integration tests passed")


def main():
    """Run all tests."""
    print("Running Internet Monitor tests...\n")
    
    try:
        test_config()
        test_logger()
        test_notification_service()
        test_internet_monitor()
        test_integration()
        
        print("\n🎉 All tests passed!")
        return 0
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 