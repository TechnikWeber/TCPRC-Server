import socket
import json
import board
import busio
from adafruit_pca9685 import PCA9685

# Initialisiere I2C und PCA9685
i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c)
pca.frequency = 50

# Pulsbereich für Servos
SERVO_MIN = 500  # us
SERVO_MAX = 2500  # us
PWM_FREQUENCY = 60  # Hz
PWM_PERIOD = 1000000 / PWM_FREQUENCY  # in us

def pulse_width_to_duty_cycle(pulse_us):
    duty_cycle = int((pulse_us / PWM_PERIOD) * 65535)
    return max(0, min(65535, duty_cycle))

def map_value(value, from_min, from_max, to_min, to_max):
    return (value - from_min) * (to_max - to_min) / (from_max - from_min) + to_min

def set_servo_pulse(channel, pulse):
    duty_cycle = pulse_width_to_duty_cycle(pulse)
    pca.channels[channel].duty_cycle = duty_cycle

def handle_input(data):
    # Map Stick-Values (Assuming 1000-2000 range for sticks)
    left_x = map_value(data['LeftStickX'], 1000, 2000, SERVO_MIN, SERVO_MAX)
    left_y = map_value(data['LeftStickY'], 1000, 2000, SERVO_MIN, SERVO_MAX)
    right_x = map_value(data['RightStickX'], 1000, 2000, SERVO_MIN, SERVO_MAX)
    right_y = map_value(data['RightStickY'], 1000, 2000, SERVO_MIN, SERVO_MAX)

    # Set Stick-controlled servos
    set_servo_pulse(0, left_x)
    set_servo_pulse(1, left_y)
    set_servo_pulse(2, right_x)
    set_servo_pulse(3, right_y)

    # CH5State -> Servo 4
    set_servo_pulse(4, SERVO_MAX if data['CH5State'] else SERVO_MIN)

    # CH6State -> Servo 5
    set_servo_pulse(5, SERVO_MAX if data['CH6State'] else SERVO_MIN)

def start_server(host='192.168.178.38', port=65535):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((host, port))
        server_socket.listen(1)
        print(f"Server listening on {host}:{port}")

        conn, addr = server_socket.accept()
        print(f"Connection from {addr}")

        with conn:
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                try:
                    json_data = json.loads(data.decode())
                    handle_input(json_data)
                except json.JSONDecodeError:
                    print("Invalid JSON received")

if __name__ == "__main__":
    try:
        start_server()
    except KeyboardInterrupt:
        print("Server stopped")
