import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import os
import logging
from monitor import InternetMonitor, NotificationService, Logger

class TestInternetMonitor(unittest.TestCase):

    @patch.dict(os.environ, {"PROWL_API_KEY": "dummy_api_key"})
    @patch('os.system')
    def test_ping_success(self, mock_os_system):
        # Simulate a successful ping
        mock_os_system.return_value = 0
        monitor = InternetMonitor(ip_address="8.8.8.8")
        self.assertTrue(monitor.ping())

    @patch.dict(os.environ, {"PROWL_API_KEY": "dummy_api_key"})
    @patch('os.system')
    def test_ping_failure(self, mock_os_system):
        # Simulate a failed ping
        mock_os_system.return_value = 1
        monitor = InternetMonitor(ip_address="8.8.8.8")
        self.assertFalse(monitor.ping())

    @patch.dict(os.environ, {"PROWL_API_KEY": "dummy_api_key"})
    @patch('os.system')
    def test_is_internet_down_with_no_failures(self, mock_os_system):
        # Simulate successful pings, so internet is not down
        mock_os_system.return_value = 0
        monitor = InternetMonitor(ip_address="8.8.8.8", failure_threshold=2)
        self.assertFalse(monitor.is_internet_down())

    @patch.dict(os.environ, {"PROWL_API_KEY": "dummy_api_key"})
    @patch('os.system')
    def test_is_internet_down_with_failures(self, mock_os_system):
        # Simulate failed pings, so internet is down
        mock_os_system.return_value = 1
        monitor = InternetMonitor(ip_address="8.8.8.8", failure_threshold=2)
        self.assertTrue(monitor.is_internet_down())

    @patch.dict(os.environ, {"PROWL_API_KEY": "dummy_api_key"})
    @patch('monitor.NotificationService.send_notification')
    def test_handle_outage(self, mock_send_notification):
        # Simulate internet outage and verify messages are queued correctly
        monitor = InternetMonitor(ip_address="8.8.8.8")
        outage_time = datetime.now()
        
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = outage_time
            monitor.handle_outage()

        self.assertEqual(len(monitor.message_queue), 1)
        self.assertIn("Internet connection lost!", monitor.message_queue[0])
        self.assertIn(outage_time.strftime("%Y-%m-%d %H:%M:%S"), monitor.message_queue[0])

    @patch.dict(os.environ, {"PROWL_API_KEY": "dummy_api_key"})
    @patch('monitor.NotificationService.send_notification')
    def test_handle_recovery(self, mock_send_notification):
        # Simulate internet recovery and verify messages are queued and sent correctly
        monitor = InternetMonitor(ip_address="8.8.8.8")
        outage_start_time = datetime.now() - timedelta(minutes=5)  # Set outage start time to 5 minutes ago
        monitor.outage_start_time = outage_start_time

        recovery_time = datetime.now()

        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = recovery_time
            monitor.handle_recovery()

        self.assertEqual(mock_send_notification.call_count, 1)

        sent_message = mock_send_notification.call_args[0][0]
        self.assertIn("Internet connection restored!", sent_message)
        self.assertIn(str(timedelta(minutes=5)), sent_message)

    @patch.dict(os.environ, {"PROWL_API_KEY": "dummy_api_key"})
    @patch('monitor.NotificationService.send_notification')
    def test_send_queued_messages(self, mock_send_notification):
        # Test that queued messages are sent properly when connection is restored
        monitor = InternetMonitor(ip_address="8.8.8.8")
        monitor.queue_message("Test message 1")
        monitor.queue_message("Test message 2")

        monitor.send_queued_messages()

        self.assertEqual(mock_send_notification.call_count, 2)  # Two messages should be sent
        mock_send_notification.assert_any_call("Test message 1")
        mock_send_notification.assert_any_call("Test message 2")
        self.assertEqual(len(monitor.message_queue), 0)  # Queue should be empty after sending

    @patch.dict(os.environ, {"PROWL_API_KEY": "dummy_api_key"})
    @patch('requests.post')
    def test_notification_service_success(self, mock_post):
        # Simulate a successful notification sending
        mock_post.return_value.status_code = 200
        service = NotificationService(api_key="dummy_api_key")
        service.send_notification("Test message")

        self.assertEqual(mock_post.call_count, 1)
        self.assertIn("Test message", mock_post.call_args[1]['data']['description'])

    @patch.dict(os.environ, {"PROWL_API_KEY": "dummy_api_key"})
    @patch('requests.post')
    def test_notification_service_failure(self, mock_post):
        # Simulate a failed notification sending
        mock_post.return_value.status_code = 500
        service = NotificationService(api_key="dummy_api_key")
        service.send_notification("Test message")

        self.assertEqual(mock_post.call_count, 1)
        self.assertIn("Test message", mock_post.call_args[1]['data']['description'])

    def test_logger_setup(self):
        # Verify that the logger is properly configured
        logger = Logger()
        self.assertTrue(logger.logger.hasHandlers())  # Logger should have handlers attached
        self.assertEqual(logger.logger.level, logging.INFO)

if __name__ == '__main__':
    unittest.main()
