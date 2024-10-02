import os
import time
from datetime import datetime
import requests

# Define the IP address to ping and log file location
ip_address = "8.8.8.8"
log_file = "ping_log.txt"
prowl_api_key = os.getenv("PROWL_API_KEY")  # Get the API key from the environment variable
message_queue = [] # store message when internet goes down

outage_start_time = None

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

def is_internet_down(failure_threshold=2):
    consecutive_failures = 0
    for _ in range(failure_threshold):
        if not ping():
            consecutive_failures += 1
            print(f"consecutive failure {consecutive_failures}")
            time.sleep(2)
        else:
            return False

    print("threshold breached - internet down")        
    return True

def log_result(result):
    # Get the current date and time
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Create the log entry
    log_entry = f"{current_time} - {'Connected' if result else 'Disconnected'} - pinging {ip_address}\n"
    # Write the log entry to the file
    with open(log_file, "a") as file:
        file.write(log_entry)

def queue_message(message):
    message_queue.append(message)
    print(f"Queued message: {message}")

def send_queued_message():
    """ send all queued messages when the internet is restored """
    while message_queue:
        message = message_queue.pop(0)
        send_prowl_notification(message)

def get_outage_duration():
    global outage_start_time
    if outage_start_time:
        outage_end_time = datetime.now()
        duration = outage_end_time - outage_start_time
        return str(duration)
    
    return None

def main():
    global outage_start_time
    was_connected = True  # Track the previous status

    while True:
        # Ping the IP address and log the result
        result = not is_internet_down()
        log_result(result)

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not result and was_connected:
            handle_outage()
            was_connected = False

        elif result and not was_connected:
            handle_recovery()
            was_connected = True

        # Wait for a while before the next check (e.g., 5 minutes)
        time.sleep(10)

def handle_outage():
    global outage_start_time
    outage_start_time = datetime.now()
    current_time = outage_start_time.strftime("%Y-%m-%d %H:%M:%S")
    queue_message("Internet connection lost! - " + current_time)

def handle_recovery():
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    outage_duration = get_outage_duration()
    
    if outage_duration:
        queue_message("Internet connection restored! - " + current_time + " - outage duration = " + outage_duration)
    else:
        queue_message("Internet connection restored! - " + current_time)
    
    send_queued_message()
    

if __name__ == "__main__":
    main()
