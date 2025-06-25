#!/usr/bin/env python3

import os
import sys
import subprocess
import time
import argparse
import logging
from threading import Thread

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ai_dashboard.start')

def start_app():
    """Start the Flask web application"""
    try:
        # Import the app factory and create the app
        from AppFactory import AppFactory
        factory = AppFactory()
        app = factory.create_app()
        app.run(debug=False, host='0.0.0.0', port=5000)
    except Exception as e:
        logger.error(f"Error starting web app: {str(e)}")
        sys.exit(1)

def start_daemon():
    """Start the background daemon"""
    try:
        # Import and run the daemon
        from daemon import main as daemon_main
        daemon_main()
    except Exception as e:
        logger.error(f"Error starting daemon: {str(e)}")
        sys.exit(1)

def start_separate_process(script, name):
    """Start a script as a separate process
    
    Args:
        script (str): The script to run
        name (str): The name of the process
    """
    try:
        # Start the process
        process = subprocess.Popen(
            [sys.executable, script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        logger.info(f"Started {name} process with PID {process.pid}")
        return process
    except Exception as e:
        logger.error(f"Error starting {name} process: {str(e)}")
        return None

def main():
    """Main entry point"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Start the AI Control Dashboard')
    parser.add_argument('--no-daemon', action='store_true', help='Do not start the background daemon')
    parser.add_argument('--no-web', action='store_true', help='Do not start the web dashboard')
    parser.add_argument('--separate-processes', action='store_true', help='Run components in separate processes')
    args = parser.parse_args()
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Print banner
    print("\n" + "=" * 60)
    print("AI Control Dashboard")
    print("=" * 60)
    
    # Start the components
    if args.separate_processes:
        # Start components as separate processes
        processes = []
        
        if not args.no_web:
            web_process = start_separate_process('app.py', 'web dashboard')
            if web_process:
                processes.append(('web', web_process))
                print(f"Web dashboard started (PID: {web_process.pid})")
                print("Access the dashboard at http://localhost:5000")
        
        if not args.no_daemon:
            daemon_process = start_separate_process('daemon.py', 'background daemon')
            if daemon_process:
                processes.append(('daemon', daemon_process))
                print(f"Background daemon started (PID: {daemon_process.pid})")
        
        # Wait for processes to complete or user interrupt
        try:
            while processes:
                for name, process in processes.copy():
                    if process.poll() is not None:
                        # Process has terminated
                        stdout, stderr = process.communicate()
                        if process.returncode != 0:
                            logger.error(f"{name} process exited with code {process.returncode}")
                            if stderr:
                                logger.error(f"{name} stderr: {stderr}")
                        else:
                            logger.info(f"{name} process completed successfully")
                        processes.remove((name, process))
                
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")
            for name, process in processes:
                if process.poll() is None:
                    print(f"Terminating {name} process (PID: {process.pid})")
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
    else:
        # Start components in threads
        threads = []
        
        if not args.no_web:
            web_thread = Thread(target=start_app, name="WebApp")
            web_thread.daemon = True
            threads.append(web_thread)
            web_thread.start()
            print("Web dashboard started")
            print("Access the dashboard at http://localhost:5000")
        
        if not args.no_daemon:
            daemon_thread = Thread(target=start_daemon, name="Daemon")
            daemon_thread.daemon = True
            threads.append(daemon_thread)
            daemon_thread.start()
            print("Background daemon started")
        
        # Wait for threads to complete or user interrupt
        try:
            for thread in threads:
                thread.join()
        except KeyboardInterrupt:
            print("\nShutting down...")
            sys.exit(0)

if __name__ == '__main__':
    main()