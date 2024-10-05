import os
import time
from datetime import datetime
import requests # type: ignore
import logging
from logging.handlers import TimedRotatingFileHandler

class Logger:
    def __init__(self, log_file="internet_monitor.log"):
        self.logger = logging.getLogger("InternetMonitor")
        self.logger.setLevel(logging.INFO)

        if not self.logger.hasHandlers():
            handler = TimedRotatingFileHandler(log_file, when="midnight", interval=1)
            handler.suffix = "%Y-%m-%d"
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            self.logger.addHandler(handler)

            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

class NotificationService:
    def __init__(self, api_key):
        self.api_key = api_key
        if not self.api_key:
            raise ValueError("Prowl API key is not set. Please set the PROWL_API_KEY environment variable.")
        self.logger = Logger().logger

    def send_notification(self, message):
        url = "https://api.prowlapp.com/publicapi/add"
        payload = {
            "apikey": self.api_key,
            "application": "Internet Monitor",
            "event": "Internet Status",
            "description": message,
            "priority": 1  # Prowl priority (-2 to 2); 1 is default
        }
        try:
            response = requests.post(url, data=payload)
            if response.status_code == 200:
                self.logger.info("Notification sent successfully!")
            else:
                self.logger.warning(f"Failed to send notification: {response.status_code}")
        except Exception as e:
            self.logger.error(f"Error sending notification: {e}")

class InternetMonitor:
    def __init__(self, ip_address, failure_threshold=2):
        self.ip_address = ip_address
        self.failure_threshold = failure_threshold
        self.message_queue = []
        self.outage_start_time = None
        self.was_connected = True
        self.logger = Logger().logger
        self.notifier = NotificationService(os.getenv("PROWL_API_KEY"))

    def ping(self):
        response = os.system(f"ping -n 1 {self.ip_address} > nul")
        return response == 0  # True if ping is successful

    def is_internet_down(self):
        consecutive_failures = 0
        for _ in range(self.failure_threshold):
            if not self.ping():
                consecutive_failures += 1
                self.logger.info(f'consecutive failure {consecutive_failures}')
                time.sleep(2)
            else:
                return False
            
        self.logger.info("Threshold breached - internet down")
        return True
    
    def log_result(self, result):
        log_entry = f"{'Connected' if result else 'Disconnected'} - pinging {ip_address}"
        self.logger.info(log_entry)

    def queue_message(self, message):
        self.message_queue.append(message)
        self.logger.info(f"Queued message: {message}")        

    def send_queued_messages(self):
        while self.message_queue:
            message = self.message_queue.pop(0)
            self.notifier.send_notification(message)

    def get_outage_duration(self):
        if self.outage_start_time:
            outage_end_time = datetime.now()
            duration = outage_end_time - self.outage_start_time
            return str(duration)
        
        return None
    
    def handle_outage(self):
        self.outage_start_time = datetime.now()
        current_time = self.outage_start_time.strftime("%Y-%m-%d %H:%M:%S")
        self.queue_message("Internet connection lost! - " + current_time)

    def handle_recovery(self):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        outage_duration = self.get_outage_duration()

        if outage_duration:
            self.queue_message("Internet connection restored! - " + current_time + " - outage duration = " + outage_duration)
        else:
            self.queue_message("Internet connection restored! - " + current_time)

        self.send_queued_messages()

    def monitor(self, check_interval=10):
        while True:
            result = not self.is_internet_down()
            self.log_result(result)

            if not result and self.was_connected:
                self.handle_outage()
                self.was_connected = False

            elif result and not self.was_connected:
                self.handle_recovery()
                self.was_connected = True

            time.sleep(check_interval)
        
if __name__ == "__main__":
    ip_address = "8.8.8.8"
    internet_monitor = InternetMonitor(ip_address)
    internet_monitor.monitor()