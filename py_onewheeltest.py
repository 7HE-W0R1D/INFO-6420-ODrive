#!/usr/bin/env python3
"""
Raspberry Pi ODrive Motor Control Script (Remote Shell Compatible)
Controls a motor connected to ODrive using keyboard input over terminal/SSH.
Enter 1: Turn motor forward at fixed velocity
Enter 2: Turn motor backward at fixed velocity
Enter q: Quit the program
"""

import time
import sys
import odrive
import signal

# Configuration parameters
MOTOR_INDEX = 0  # Motor index (0 or 1)
FORWARD_VELOCITY = 1  # Fixed forward velocity
BACKWARD_VELOCITY = -1  # Fixed backward velocity
AXIS_STATE_CLOSED_LOOP_CONTROL = 8  # ODrive closed loop control state

# Current velocity
current_velocity = 0

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
    """Setup the motor for velocity control."""
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
        print(f"Failed to setup motor: {str(e)}")
        sys.exit(1)

def set_velocity(axis, velocity):
    """Set the motor velocity."""
    try:
        axis.controller.input_vel = velocity
        print(f"Velocity set to: {velocity} counts/s")
    except Exception as e:
        print(f"Failed to set velocity: {str(e)}")

def stop_motor(axis):
    """Stop the motor."""
    try:
        print("Stopping motor...")
        set_velocity(axis, 0)
        time.sleep(0.5)  # Give time for motor to stop
    except Exception as e:
        print(f"Failed to stop motor: {str(e)}")

def signal_handler(sig, frame):
    """Handle Ctrl+C."""
    print("\nCtrl+C detected. Exiting gracefully...")
    if 'axis' in globals():
        stop_motor(axis)
    sys.exit(0)

def main():
    print("ODrive Single Motor Control (Remote Shell Compatible)")
    print("----------------------------------------------------")
    print("Enter 1: Turn motor forward")
    print("Enter 2: Turn motor backward")
    print("Enter 0: Stop motor")
    print("Enter q: Quit")
    print("----------------------------------------------------")
    
    # Find and connect to ODrive
    odrv = find_odrive()
    
    # Setup the motor
    global axis
    axis = setup_motor(odrv, MOTOR_INDEX)
    
    # Register the signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    # Main control loop
    try:
        while True:
            user_input = input("Enter command (1/2/0/q): ")
            
            if user_input == '1':
                set_velocity(axis, FORWARD_VELOCITY)
            elif user_input == '2':
                set_velocity(axis, BACKWARD_VELOCITY)
            elif user_input == '0':
                set_velocity(axis, 0)
            elif user_input.lower() == 'q':
                stop_motor(axis)
                print("Exiting program...")
                break
            else:
                print("Invalid input. Please enter 1, 2, 0, or q.")
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        stop_motor(axis)

if __name__ == "__main__":
    main()
