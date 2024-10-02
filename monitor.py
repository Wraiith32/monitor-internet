import os
import time
from datetime import datetime
import requests

# Define the IP address to ping and log file location
ip_address = "8.8.8.8"
log_file = "ping_log.txt"
prowl_api_key = os.getenv("PROWL_API_KEY")  # Get the API key from the environment variable
queued_message = None

if prowl_api_key is None:
    raise ValueError("Prowl API key is not set. Please set the PROWL_API_KEY environment variable.")

def send_prowl_notification(message):
    url = "https://api.prowlapp.com/publicapi/add"
    payload = {
        "apikey": prowl_api_key,
        "application": "Internet Monitor",
        "event": "Internet Status",
        "description": message,
        "priority": 1  # Prowl priority (-2 to 2); 1 is default
    }
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print("Notification sent successfully!")
        else:
            print(f"Failed to send notification: {response.status_code}")
    except Exception as e:
        print(f"Error sending notification: {e}")

def ping():
    # Send the ping command (Windows uses -n 1 instead of -c 1)
    response = os.system(f"ping -n 1 {ip_address} > nul")
    return response == 0  # True if ping is successful

def log_result(result):
    # Get the current date and time
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Create the log entry
    log_entry = f"{current_time} - {'Connected' if result else 'Disconnected'} - pinging {ip_address}\n"
    # Write the log entry to the file
    with open(log_file, "a") as file:
        file.write(log_entry)

def queue_message(message):
    """ Store only one message in the queue """
    global queued_message
    queued_message = message
    print(f"Queued message: {message}")

def send_queued_message():
    """ Send the stored message (if any) when the internet is restored """
    global queued_message
    if queued_message:
        send_prowl_notification(queued_message)
        queued_message = None  # Clear the queued message after sending

def main():
    was_connected = True  # Track the previous status

    while True:
        # Ping the IP address and log the result
        result = ping()
        log_result(result)

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not result and was_connected:
            # If the internet was connected previously and is now disconnected, send a notification
            queue_message("Internet connection lost! - " + current_time)
            was_connected = False
        elif result and not was_connected:
            # If the internet is back online, update the status and notify
            send_queued_message()
            queue_message("Internet connection restored! - " + current_time)
            was_connected = True

        # Wait for a while before the next check (e.g., 5 minutes)
        time.sleep(10)

if __name__ == "__main__":
    main()
