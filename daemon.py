#!/usr/bin/env python3

import os
import time
import logging
import sys
from config.ConfigManager import ConfigManager
from services.KeyRotator import KeyRotator
from services.ProviderSwitcher import ProviderSwitcher
from services.DaemonMonitor import DaemonMonitor
from utils.Logger import setup_logger

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Configure logging
logger = setup_logger('ai_dashboard.daemon', 'logs/daemon.log')

def main():
    """Main entry point for the daemon"""
    try:
        logger.info("Starting AI Dashboard Daemon")
        
        # Initialize components
        config_manager = ConfigManager('config.json')
        key_rotator = KeyRotator(config_manager)
        provider_switcher = ProviderSwitcher(config_manager)
        
        # Create and start the daemon monitor
        daemon = DaemonMonitor(config_manager, key_rotator, provider_switcher)
        daemon.start()
        
        # Keep the main thread alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Daemon stopped by user")
        if 'daemon' in locals():
            daemon.stop()
        
    except Exception as e:
        logger.error(f"Error in daemon main: {str(e)}")
        if 'daemon' in locals():
            daemon.stop()
    
if __name__ == '__main__':
    main()