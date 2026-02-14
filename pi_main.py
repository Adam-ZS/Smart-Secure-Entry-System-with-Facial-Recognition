#!/usr/bin/env python3
"""
Smart Secure Entry System - Raspberry Pi
Winter26- CEN425 - Abu Dhabi University Adam Soman, Moh Sami, Hadi Alnader, Fares Nemer, special thanks for eng. gasm, and  Dr.Mohammed fadl.
"""

from picamera2 import Picamera2
import cv2, time, socket, os, struct
from gpiozero import LED, Buzzer
import RPi.GPIO as GPIO
from datetime import datetime
import numpy as np
import pickle
import face_recognition

# ============================================
# CONFIGURATION
# ============================================
class Config:
    GATEWAY_IP = "100.127.50.12" #This is my laptop ip, which is tailscale conected(scope global tailscale0), so even if indiffrent wifi's it stays the same, and same on the pi
    GATEWAY_PORT = 9999
    
    PIR_PIN = 26
    SERVO_PIN = 17
    GREEN_LED_PIN = 6
    RED_LED_PIN = 16
    BUZZER_PIN = 23
    
    EMBEDDINGS_FILE = "users_embeddings.pkl"
    UNKNOWN_THRESHOLD = 0.45
    
    DOOR_OPEN_TIME = 2
    DOOR_CLOSED_ANGLE = 180
    DOOR_OPEN_ANGLE = 90
    
    MOTION_COOLDOWN = 1
    
    LOG_DIR = "logs"
    ENCRYPTED_LOG_DIR = "encrypted_logs"
    XOR_KEY = 0xAA

# ============================================
# HARDWARE SETUP
# ============================================
print("=" * 60)
print("Smart Secure Entry System - Raspberry Pi")
print("=" * 60)
print("[INFO] Initializing hardware...")

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(Config.PIR_PIN, GPIO.IN)
GPIO.setup(Config.SERVO_PIN, GPIO.OUT)

servo_pwm = GPIO.PWM(Config.SERVO_PIN, 50)
servo_pwm.start(0)

def set_servo_angle(angle):
    duty = 2 + (angle / 18)
    servo_pwm.ChangeDutyCycle(duty)
    time.sleep(0.3)
    servo_pwm.ChangeDutyCycle(0)

green_led = LED(Config.GREEN_LED_PIN)
red_led = LED(Config.RED_LED_PIN)
buzzer = Buzzer(Config.BUZZER_PIN)

set_servo_angle(Config.DOOR_CLOSED_ANGLE)
print(f"[INFO] Door secured at {Config.DOOR_CLOSED_ANGLE}°")

os.makedirs(Config.LOG_DIR, exist_ok=True)
os.makedirs(Config.ENCRYPTED_LOG_DIR, exist_ok=True)

# ============================================
# CAMERA SETUP
# ============================================
print("[INFO] Initializing camera...")
picam = Picamera2()
camera_config = picam.create_preview_configuration(
    main={"size": (1280, 720)},
    controls={"FrameRate": 30}
)
picam.configure(camera_config)
print("[INFO] Camera configured")

# ============================================
# FACE DATABASE
# ============================================
print("[INFO] Loading face encodings...")
known_encodings, known_names = [], []

if os.path.exists(Config.EMBEDDINGS_FILE):
    with open(Config.EMBEDDINGS_FILE, "rb") as f:
        data = pickle.load(f)
        known_encodings = data["encodings"]
        known_names = data["names"]
    print(f"[INFO] Loaded {len(known_names)} face encodings")
else:
    print("[WARNING] No face database found!")

# ============================================
# CONTROL FUNCTIONS
# ============================================
def unlock_door():
    print(f"[LOCK] Opening ({Config.DOOR_CLOSED_ANGLE}° → {Config.DOOR_OPEN_ANGLE}°)")
    set_servo_angle(Config.DOOR_OPEN_ANGLE)
    time.sleep(Config.DOOR_OPEN_TIME)
    print(f"[LOCK] Closing ({Config.DOOR_OPEN_ANGLE}° → {Config.DOOR_CLOSED_ANGLE}°)")
    set_servo_angle(Config.DOOR_CLOSED_ANGLE)

def access_granted():
    print("[STATUS]  ACCESS GRANTED")
    green_led.on()
    for _ in range(3):
        buzzer.on()
        time.sleep(0.15)
        buzzer.off()
        time.sleep(0.15)
    green_led.off()

def access_denied():
    print("[STATUS] X ACCESS DENIED")
    red_led.on()
    for _ in range(10):
        buzzer.on()
        time.sleep(0.03)
        buzzer.off()
        time.sleep(0.05)
    buzzer.off()
    red_led.off()

def recognize_face(frame):
    if len(known_encodings) == 0:
        return "Unknown", 0, None
    
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    small_frame = cv2.resize(rgb_frame, (0, 0), fx=0.25, fy=0.25)
    
    face_locations = face_recognition.face_locations(small_frame)
    face_encodings = face_recognition.face_encodings(small_frame, face_locations)
    
    if len(face_encodings) == 0:
        return None, 0, None
    
    face_encoding = face_encodings[0]
    location = face_locations[0]
    
    top, right, bottom, left = location
    location = (top * 4, right * 4, bottom * 4, left * 4)
    
    distances = face_recognition.face_distance(known_encodings, face_encoding)
    
    if len(distances) > 0:
        best_idx = np.argmin(distances)
        distance = distances[best_idx]
        
        print(f"[RECOGNITION] Best match: {known_names[best_idx]} (distance: {distance:.3f})")
        
        if distance < Config.UNKNOWN_THRESHOLD:
            return known_names[best_idx], 1.0 - distance, location
    
    return "Unknown", 0, location

# ============================================
# LOGGING
# ============================================
def encrypt_image(image_path):
    with open(image_path, "rb") as f:
        data = bytearray(f.read())
    
    encrypted = bytearray([byte ^ Config.XOR_KEY for byte in data])
    
    filename = os.path.basename(image_path)
    encrypted_path = os.path.join(Config.ENCRYPTED_LOG_DIR, f"enc_{filename}")
    
    with open(encrypted_path, "wb") as f:
        f.write(encrypted)
    
    print(f"[SECURITY] Encrypted: enc_{filename}")

def save_log(frame, name, granted):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    status = "GRANTED" if granted else "DENIED"
    filename = f"{timestamp}_{name}_{status}.jpg"
    filepath = os.path.join(Config.LOG_DIR, filename)
    
    cv2.imwrite(filepath, frame)
    encrypt_image(filepath)
    
    with open(os.path.join(Config.LOG_DIR, "access_log.txt"), "a") as f:
        f.write(f"[{datetime.now()}] {status} - {name}\n")
    
    print(f"[LOG] Saved: {filename}")

# ============================================
# NETWORK
# ============================================
sock = None

def connect_to_gateway():
    global sock
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((Config.GATEWAY_IP, Config.GATEWAY_PORT))
        print(f"[NETWORK]  Connected to gateway at {Config.GATEWAY_IP}:{Config.GATEWAY_PORT}")
    except Exception as e:
        print(f"[NETWORK] Gateway not available: {e}")
        sock = None

def send_frame_to_gateway(frame, name, granted):
    if sock is None:
        return
    
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        status = "GRANTED" if granted else "DENIED"
        metadata = f"{name}|{status}|{timestamp}"
        
        display_frame = frame.copy()
        cv2.putText(display_frame, f"{name} - {status}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0) if granted else (0, 0, 255), 2)
        cv2.putText(display_frame, timestamp, (10, 70),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        _, buffer = cv2.imencode('.jpg', display_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        frame_data = buffer.tobytes()
        
        sock.sendall(struct.pack('!I', len(metadata)))
        sock.sendall(metadata.encode())
        
        sock.sendall(struct.pack('!I', len(frame_data)))
        sock.sendall(frame_data)
        
        print(f"[NETWORK] Streamed frame to gateway ({len(frame_data)} bytes)")
        
    except Exception as e:
        print(f"[NETWORK] Stream failed: {e}")

# ============================================
# MOTION DETECTION
# ============================================
last_motion_time = 0
camera_active = False

def process_entry_attempt():
    global last_motion_time, camera_active
    
    current_time = time.time()
    
    if current_time - last_motion_time < Config.MOTION_COOLDOWN:
        return
    
    last_motion_time = current_time
    
    print("\n" + "=" * 60)
    print(f"[MOTION] Motion detected at {datetime.now().strftime('%H:%M:%S')}")
    print("[CAMERA] Activating camera...")
    
    if not camera_active:
        picam.start()
        time.sleep(1)
        camera_active = True
    
    frame = picam.capture_array()
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    
    print("[RECOGNITION] Processing face...")
    
    name, confidence, location = recognize_face(frame)
    
    if name is None:
        print("[RECOGNITION] No face detected")
        print("=" * 60)
        return
    
    if location:
        top, right, bottom, left = location
        color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
        cv2.rectangle(frame, (left, top), (right, bottom), color, 3)
        
        label = f"{name} ({confidence:.2f})" if name != "Unknown" else "Unknown"
        cv2.rectangle(frame, (left, top - 35), (right, top), color, cv2.FILLED)
        cv2.putText(frame, label, (left + 6, top - 10),
                   cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1)
    
    if name != "Unknown":
        print(f"[RECOGNITION]  Authorized: {name} (confidence: {confidence:.2f})")
        access_granted()
        unlock_door()
        save_log(frame, name, True)
        send_frame_to_gateway(frame, name, True)
    else:
        print(f"[RECOGNITION] Unauthorized: Unknown person")
        access_denied()
        save_log(frame, "Unknown", False)
        send_frame_to_gateway(frame, "Unknown", False)
    
    print("=" * 60 + "\n")
    
    print("[CAMERA] Deactivating (low-power mode)")
    picam.stop()
    camera_active = False

# ============================================
# MAIN
# ============================================
def main():
    print("\n" + "=" * 60)
    print("PROJECT: Smart Secure Entry System")
    print("MODE: Event-Triggered (PIR Motion Sensor)")
    print("=" * 60)
    print(f"Door: CLOSED at {Config.DOOR_CLOSED_ANGLE}°")
    print(f"Recognition threshold: {Config.UNKNOWN_THRESHOLD}")
    print(f"Motion cooldown: {Config.MOTION_COOLDOWN}s")
    print(f"Camera: IDLE (activates on motion)")
    print("=" * 60)
    
    connect_to_gateway()
    
    print("\n[SYSTEM] Ready - LOW POWER MODE")
    print("[SYSTEM] Waiting for motion...\n")
    
    try:
        while True:
            if GPIO.input(Config.PIR_PIN):
                process_entry_attempt()
            
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("\n[SYSTEM] Shutdown requested")
    
    finally:
        cleanup()

def cleanup():
    print("\n[CLEANUP] Shutting down...")
    
    set_servo_angle(Config.DOOR_CLOSED_ANGLE)
    print(f"[CLEANUP] Door secured at {Config.DOOR_CLOSED_ANGLE}°")
    
    if sock:
        sock.close()
        print("[CLEANUP] Network connection closed")
    
    try:
        picam.stop()
    except:
        pass
    
    green_led.close()
    red_led.close()
    buzzer.close()
    servo_pwm.stop()
    GPIO.cleanup()
    
    print("[CLEANUP] Complete. Goodbye!")

if __name__ == "__main__":
    main()
