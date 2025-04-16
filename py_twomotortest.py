#!/usr/bin/env python3
"""
Raspberry Pi ODrive Two Motor Control Script
Controls two motors connected to ODrive using keyboard input over terminal/SSH.

Key controls:
1 - Left motor forward
2 - Left motor backward
3 - Right motor forward
4 - Right motor backward
w - Both motors forward
s - Both motors backward
a - Right motor forward
d - Left motor forward
q - Left motor backward, right motor forward
e - Right motor backward, left motor forward
x - Stop all motors
Esc - Quit the program
"""

import sys
import time
import odrive
import threading
import termios
import tty
import signal
import select

# Configuration parameters
LEFT_MOTOR_INDEX = 0   # Left motor index (usually 0)
RIGHT_MOTOR_INDEX = 1  # Right motor index (usually 1)
VELOCITY = 1           # Fixed velocity value
AXIS_STATE_CLOSED_LOOP_CONTROL = 8  # ODrive closed loop control state

# Global variables
running = True
current_key = None
key_lock = threading.Lock()

def find_odrive():
    """Find and connect to ODrive."""
    print("Looking for ODrive...")
    try:
        odrv = odrive.find_any()
        print(f"Found ODrive: {odrv.serial_number}")
        return odrv
    except Exception as e:
        print(f"Failed to find ODrive: {str(e)}")
        sys.exit(1)

def setup_motor(odrv, motor_index):
    """Setup a motor for velocity control."""
    try:
        # Get the axis object based on motor index
        axis = getattr(odrv, f"axis{motor_index}")
        
        # Set the control mode to velocity control
        axis.controller.config.control_mode = 2  # Velocity control
        
        # Set the axis state to closed loop control
        axis.requested_state = AXIS_STATE_CLOSED_LOOP_CONTROL
        time.sleep(0.5)  # Give time for state change
        
        print(f"Motor on axis{motor_index} is ready for control")
        return axis
    except Exception as e:
        print(f"Failed to setup motor on axis{motor_index}: {str(e)}")
        sys.exit(1)

def set_motor_velocity(axis, velocity):
    """Set the motor velocity."""
    try:
        axis.controller.input_vel = velocity
    except Exception as e:
        print(f"Failed to set velocity: {str(e)}")

def stop_motor(axis):
    """Stop the motor."""
    try:
        set_motor_velocity(axis, 0)
    except Exception as e:
        print(f"Failed to stop motor: {str(e)}")

def stop_all_motors(left_axis, right_axis):
    """Stop both motors."""
    stop_motor(left_axis)
    stop_motor(right_axis)
    print("All motors stopped")

def getch_non_blocking():
    """Non-blocking key detection that works over SSH."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        # Short timeout for responsive detection
        rlist, _, _ = select.select([sys.stdin], [], [], 0.5)
        if rlist:
            char = sys.stdin.read(1)
            if char == '\x03':  # Ctrl+C
                raise KeyboardInterrupt
            if char == '\x1b':  # ESC character
                return 'esc'
            return char
        else:
            return None
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def handle_motor_control(key, left_axis, right_axis):
    """Handle motor control based on key input."""
    # Display the key being processed
    key_name = {
        '1': "Left motor forward",
        '2': "Left motor backward",
        '3': "Right motor forward", 
        '4': "Right motor backward",
        'w': "Both motors forward",
        's': "Both motors backward",
        'a': "Right motor forward",
        'd': "Left motor forward",
        'q': "Left motor backward, right motor forward",
        'e': "Right motor backward, left motor forward",
        'x': "Stop all motors",
        'esc': "Quit program"
    }.get(key, "Unknown key")
    
    print(f"Command: {key_name}")
    
    # Control motors based on key
    if key == '1':  # Left motor forward
        set_motor_velocity(left_axis, VELOCITY)
    elif key == '2':  # Left motor backward
        set_motor_velocity(left_axis, -VELOCITY)
    elif key == '3':  # Right motor forward
        set_motor_velocity(right_axis, VELOCITY)
    elif key == '4':  # Right motor backward
        set_motor_velocity(right_axis, -VELOCITY)
    elif key == 'w':  # Both motors forward
        set_motor_velocity(left_axis, VELOCITY)
        set_motor_velocity(right_axis, VELOCITY)
    elif key == 's':  # Both motors backward
        set_motor_velocity(left_axis, -VELOCITY)
        set_motor_velocity(right_axis, -VELOCITY)
    elif key == 'a':  # Right motor forward (turn left)
        set_motor_velocity(right_axis, VELOCITY)
        set_motor_velocity(left_axis, 0)
    elif key == 'd':  # Left motor forward (turn right)
        set_motor_velocity(left_axis, VELOCITY)
        set_motor_velocity(right_axis, 0)
    elif key == 'q':  # Left motor backward, right motor forward (rotate left)
        set_motor_velocity(left_axis, -VELOCITY)
        set_motor_velocity(right_axis, VELOCITY)
    elif key == 'e':  # Right motor backward, left motor forward (rotate right)
        set_motor_velocity(right_axis, -VELOCITY)
        set_motor_velocity(left_axis, VELOCITY)
    elif key == 'x':  # Stop all motors
        stop_all_motors(left_axis, right_axis)
    elif key == 'esc':  # Quit
        return False
    
    return True

def key_monitor_thread(left_axis, right_axis):
    """Thread to monitor key presses and control the motors."""
    global running, current_key
    
    while running:
        key = getch_non_blocking()
        
        with key_lock:
            # If a key is detected
            if key is not None:
                # If it's a different key than before
                if key != current_key:
                    current_key = key
                    
                    # Handle the key press
                    if not handle_motor_control(key, left_axis, right_axis):
                        running = False
                        break
            # If no key is detected
            else:
                # Consider it a release immediately
                if current_key is not None:
                    print("Keys released, stopping all motors")
                    stop_all_motors(left_axis, right_axis)
                    current_key = None
                
        time.sleep(0.05)  # Small delay to prevent CPU overload

def signal_handler(sig, frame):
    """Handle Ctrl+C."""
    global running
    print("\nCtrl+C detected. Exiting gracefully...")
    running = False

def main():
    print("ODrive Two Motor Control System")
    print("------------------------------")
    print("Key controls:")
    print("1 - Left motor forward")
    print("2 - Left motor backward")
    print("3 - Right motor forward")
    print("4 - Right motor backward")
    print("w - Both motors forward")
    print("s - Both motors backward")
    print("a - Right motor forward")
    print("d - Left motor forward")
    print("q - Left motor backward, right motor forward")
    print("e - Right motor backward, left motor forward")
    print("x - Stop all motors")
    print("ESC - Quit the program")
    print("------------------------------")
    
    # Find and connect to ODrive
    odrv = find_odrive()
    
    # Setup both motors
    left_axis = setup_motor(odrv, LEFT_MOTOR_INDEX)
    right_axis = setup_motor(odrv, RIGHT_MOTOR_INDEX)
    
    # Register the signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    # Start the key monitoring thread
    monitor = threading.Thread(target=key_monitor_thread, args=(left_axis, right_axis))
    monitor.daemon = True
    monitor.start()
    
    # Main thread just waits for the program to end
    try:
        while running:
            time.sleep(0.1)
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        stop_all_motors(left_axis, right_axis)
        # Give the motors time to stop
        time.sleep(0.5)
        print("Program terminated.")

if __name__ == "__main__":
    main()
