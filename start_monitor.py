#!/usr/bin/env python3
"""
Startup script for Internet Monitor with interactive configuration.
"""

import os
import sys
from monitor import Config, InternetMonitor


def get_user_input(prompt, default_value):
    """Get user input with a default value."""
    user_input = input(f"{prompt} [{default_value}]: ").strip()
    return user_input if user_input else default_value


def interactive_config():
    """Get configuration interactively from user."""
    print("🌐 Internet Monitor Configuration")
    print("=" * 40)
    
    config = {}
    
    config["ip_address"] = get_user_input(
        "Target IP address to ping", 
        "8.8.8.8"
    )
    
    config["failure_threshold"] = int(get_user_input(
        "Number of consecutive failures before considering internet down", 
        "2"
    ))
    
    config["check_interval"] = int(get_user_input(
        "Interval between checks (seconds)", 
        "10"
    ))
    
    config["log_file"] = get_user_input(
        "Log file path", 
        "internet_monitor.log"
    )
    
    prowl_key = get_user_input(
        "Prowl API key (optional, press Enter to skip)", 
        ""
    )
    config["prowl_api_key"] = prowl_key if prowl_key else None
    
    config["max_retries"] = int(get_user_input(
        "Maximum retry attempts", 
        "3"
    ))
    
    config["retry_delay"] = int(get_user_input(
        "Delay between retries (seconds)", 
        "2"
    ))
    
    return Config(**config)


def load_env_config():
    """Load configuration from environment variables."""
    print("📋 Loading configuration from environment variables...")
    return Config.from_env()


def main():
    """Main entry point with interactive configuration."""
    print("🚀 Internet Monitor")
    print("=" * 20)
    
    # Check if environment variables are set
    env_vars = [
        "MONITOR_IP_ADDRESS", 
        "MONITOR_FAILURE_THRESHOLD", 
        "MONITOR_CHECK_INTERVAL"
    ]
    
    env_configured = any(os.getenv(var) for var in env_vars)
    
    if env_configured:
        print("Environment variables detected!")
        choice = input("Use environment configuration? (y/n) [y]: ").strip().lower()
        if choice in ['', 'y', 'yes']:
            config = load_env_config()
        else:
            config = interactive_config()
    else:
        print("No environment variables found.")
        choice = input("Configure interactively? (y/n) [y]: ").strip().lower()
        if choice in ['', 'y', 'yes']:
            config = interactive_config()
        else:
            print("Using default configuration...")
            config = Config()
    
    # Display final configuration
    print("\n📊 Final Configuration:")
    print(f"  Target IP: {config.ip_address}")
    print(f"  Failure Threshold: {config.failure_threshold}")
    print(f"  Check Interval: {config.check_interval}s")
    print(f"  Log File: {config.log_file}")
    print(f"  Notifications: {'Enabled' if config.prowl_api_key else 'Disabled'}")
    print(f"  Max Retries: {config.max_retries}")
    print(f"  Retry Delay: {config.retry_delay}s")
    
    # Confirm start
    print("\n" + "=" * 40)
    choice = input("Start monitoring? (y/n) [y]: ").strip().lower()
    if choice not in ['', 'y', 'yes']:
        print("Monitoring cancelled.")
        return
    
    try:
        print("\n🔍 Starting Internet Monitor...")
        print("Press Ctrl+C to stop\n")
        
        monitor = InternetMonitor(config)
        monitor.monitor()
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Monitoring stopped by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 