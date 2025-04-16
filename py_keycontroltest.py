#!/usr/bin/env python3
"""
Minimal keyboard control example with game-like controls over SSH
Press and hold 1: Simulates turning motor forward
Press and hold 2: Simulates turning motor backward
Release key: Simulates motor stopping
Press q: Quit the program
"""

import sys
import time
import threading
import termios
import tty
import signal
import select

# Global variables
running = True
current_key = None
key_lock = threading.Lock()

def getch_non_blocking():
    """Non-blocking key detection that works over SSH."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        rlist, _, _ = select.select([sys.stdin], [], [], 0.5)
        if rlist:
            char = sys.stdin.read(1)
            if char == '\x03':  # Ctrl+C
                raise KeyboardInterrupt
            return char
        else:
            return None
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def key_monitor_thread():
    """Thread to monitor key presses and simulate motor control."""
    global running, current_key
    
    while running:
        key = getch_non_blocking()
        
        with key_lock:
            # If a new key is pressed, update the current key
            if key is not None:
                if key != current_key:
                    current_key = key
                    
                    if key == '1':
                        print("ACTION: Moving forward")
                    elif key == '2':
                        print("ACTION: Moving backward")
                    elif key.lower() == 'q':
                        print("\nQuitting program...")
                        running = False
                    else:
                        # Any other key stops the motor
                        print("ACTION: Stopping (other key pressed)")
            # If no key is pressed, stop the motor (simulating key release)
            else:
                if current_key in ['1', '2']:
                    print("ACTION: Stopping (key released)")
                current_key = None
                
        time.sleep(0.05)  # Small delay to prevent CPU overload

def signal_handler(sig, frame):
    """Handle Ctrl+C."""
    global running
    print("\nCtrl+C detected. Exiting gracefully...")
    running = False

def main():
    print("Minimal Keyboard Control Example")
    print("--------------------------------")
    print("Press and hold 1: Simulates moving forward")
    print("Press and hold 2: Simulates moving backward")
    print("Release key: Simulates stopping")
    print("Press q: Quit")
    print("--------------------------------")
    
    # Register the signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    # Start the key monitoring thread
    monitor = threading.Thread(target=key_monitor_thread)
    monitor.daemon = True
    monitor.start()
    
    # Main thread just waits for the program to end
    try:
        while running:
            time.sleep(0.1)
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        print("Program terminated.")

if __name__ == "__main__":
    main()
