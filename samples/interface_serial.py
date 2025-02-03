"""
Demonstration of a simple RS232 serial communication interface using PySerial.
"""

COMMAND: str = 'Hello, World\n'

import time

import serial

# Configure the serial connection
ser = serial.Serial(
    port='COM5',        # Replace with port
    baudrate=9600,      # Set the baud rate
    timeout=1,          # Timeout in seconds
    bytesize=serial.EIGHTBITS,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE
)

try:
    # Open the port
    if not ser.is_open:
        ser.open()

    print("Port is open:", ser.is_open)

    # Send data
    ser.write(b'Hello RS232\n')
    time.sleep(1)

    # Read data
    if ser.in_waiting > 0:
        response = ser.read(ser.in_waiting).decode('utf-8')
        print("Received:", response)

    # Write data to the serial device
    ser.write(COMMAND.encode('utf-8'))
    print(f"Sent: {COMMAND.strip()}")

    # Read a line of response from the device
    response = ser.readline().decode('utf-8').strip()
    print(f"Received: {response}")

except serial.SerialException as e:
    print(f"Error: {e}")

finally:
    # Close the port
    ser.close()
    print("Port is closed:", not ser.is_open)
