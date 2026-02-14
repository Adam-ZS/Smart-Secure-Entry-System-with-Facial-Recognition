# 🔐 Smart Secure Entry System with Facial Recognition

[![Project Status](https://img.shields.io/badge/Status-Complete-success)]()
[![Raspberry Pi](https://img.shields.io/badge/Platform-Raspberry%20Pi%205-red)]()
[![Python](https://img.shields.io/badge/Python-3.11+-blue)]()
[![OpenCV](https://img.shields.io/badge/OpenCV-4.13.0-green)]()
[![License](https://img.shields.io/badge/License-Academic-yellow)]()

**IoT Course Project - Abu Dhabi University**  
*Authors: Adam Soman, Mohammed Sami, Fares Nimer, Hadi Alnader*

---

## 📋 Table of Contents
- [Overview](#-overview)
- [Features](#-features)
- [System Architecture](#-system-architecture)
- [Hardware Requirements](#-hardware-requirements)
- [Installation](#-installation)
- [Usage](#-usage)
- [Demo](#-demo)
- [Performance](#-performance)
- [Team](#-team-contributions)

---

## 🎯 Overview

An **IoT-based contactless door entry system** that leverages facial recognition technology for automated access control. The system employs edge computing on a Raspberry Pi 5, PIR motion sensors for energy efficiency, and secure VPN communication for remote monitoring.

### Key Highlights
- 🔋 **68% Energy Savings** through motion-triggered activation
- 🔒 **95.2% Recognition Accuracy** with 0.45 distance threshold
- ⚡ **2.1s Average Response Time** from detection to door unlock
- 🛡️ **Privacy-First Design** with local edge processing (no cloud)
- 🌐 **Secure VPN Communication** via Tailscale/WireGuard

---

## ✨ Features

- ✅ **Motion-Triggered Activation**: PIR sensor triggers camera only when needed
- ✅ **Real-Time Facial Recognition**: OpenCV + dlib-based deep learning
- ✅ **Automated Door Lock**: Servo motor control (180° closed / 90° open)
- ✅ **Visual/Audio Feedback**: Green/Red LEDs + buzzer confirmation
- ✅ **Security Logging**: XOR-encrypted image logs with timestamps
- ✅ **Gateway Monitoring**: Flask web dashboard for real-time access logs
- ✅ **Network Streaming**: TCP/IP communication over Tailscale VPN

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Raspberry Pi 5                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Pi Camera v2 │  │  PIR Sensor  │  │ Servo Motor  │ │
│  │    (CSI)     │  │   GPIO 26    │  │   GPIO 17    │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  Green LED   │  │   Red LED    │  │    Buzzer    │ │
│  │   GPIO 6     │  │   GPIO 16    │  │   GPIO 23    │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
                           │
                    [Tailscale VPN]
                           │
              ┌─────────────────────────┐
              │   Gateway PC (Kali)     │
              │  Flask Dashboard :5000  │
              └─────────────────────────┘
```

---

## 🛠️ Hardware Requirements

| Component | Model | GPIO | Cost (AED) |
|-----------|-------|------|------------|
| Microcontroller | Raspberry Pi 5 | - | 200 |
| Camera | Pi Camera v2 (8MP) | CSI | 80 |
| Motion Sensor | HC-SR501 PIR | 26 | 15 |
| Servo Motor | SG90 (0-180°) | 17 | 20 |
| Green LED | 5mm | 6 | 2 |
| Red LED | 5mm | 16 | 2 |
| Buzzer | Active | 23 | 5 |
| Misc | Wires, Breadboard, PSU | - | 80 |
| **TOTAL** | | | **~450 AED** |

---

## 📦 Installation

### 1. System Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
pip3 install --break-system-packages picamera2 opencv-python face-recognition RPi.GPIO gpiozero
```

### 2. Hardware Assembly
Connect components according to GPIO assignments:
- PIR Sensor → GPIO 26
- Servo Motor → GPIO 17 (PWM)
- Green LED → GPIO 6
- Red LED → GPIO 16
- Buzzer → GPIO 23
- Pi Camera → CSI Port

### 3. Dataset Preparation
```bash
# Create dataset structure
mkdir -p dataset/{user1,user2,user3}

# Capture 10-20 images per user in their folder
# Then generate encodings:
python3 encode_faces.py
```

### 4. Network Configuration
```bash
# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up

# Update Gateway IP in pi_main.py
GATEWAY_IP = "YOUR_KALI_TAILSCALE_IP"
```

---

## 🚀 Usage

### Start Gateway (on Kali PC):
```bash
python3 kali_gateway.py
```
Dashboard: `http://localhost:5000`

### Start System (on Raspberry Pi):
```bash
python3 pi_main.py
```

### System Operation:
1. **Motion Detected** → Camera activates
2. **Face Captured** → Recognition processing
3. **Match Found** ✅ → Green LED + 3 beeps → Door unlocks 2s
4. **No Match** ❌ → Red LED + long beep → Door locked
5. **Log Saved** → Encrypted image + timestamp
6. **Stream to Gateway** → Real-time monitoring

---

## 🎬 Demo

### 📺 Video Demonstration
**[Watch Full Demo on YouTube](https://youtu.be/CiPJNbaYFqo)**

Showcases:
- Hardware assembly
- Authorized access with door unlock
- Unauthorized access denial
- Gateway web interface
- Encrypted log storage

---

## 📊 Performance

### Recognition Metrics
- **Accuracy**: 95.2%
- **FAR**: 2.1%
- **FRR**: 2.7%
- **Threshold**: 0.45

### Response Time
- Camera Activation: 1.0s
- Recognition: 0.8s
- Door Actuation: 0.3s
- **Total: 2.1s**

### Energy Efficiency
- IDLE: 1.2W
- Active: 4.8W
- **Savings: 68%**

---

## 👥 Team Contributions

**Adam Soman** (1089101)
- Hardware research & assembly
- Wiring & integration
- Testing & security

**Mohammed Sami** (1088429)
- Dataset preparation
- Face recognition pipeline
- Documentation

**Fares Nimer** (1090380)
- Dataset preparation
- Face recognition pipeline
- Security implementation

**Hadi Alnader** (1088510)
- Network configuration (Tailscale)
- Gateway server (Flask)
- Hardware wiring

---

## 🎓 Acknowledgments

**Abu Dhabi University**  
Internet of Things: Applications & Networking

Special thanks to:
- **Dr. Mohamed Fadl** - Course Instructor
- **Eng. Gasm Elbary Elkhair** - Course Coordinator

---

## 📄 Project Files

- `pi_main.py` - Main Raspberry Pi control script
- `kali_gateway.py` - Flask gateway server
- `encode_faces.py` - Face encoding generator
- `decrypt_logs.py` - Log decryption utility

---

##  Done by

- **Adam ZS**
- **Mohammed Sami**
- **Fares Nimer**
- **Hadi Alnader**

---

<div align="center">

**Built with ❤️ by Cyber26 Team ADU | February 2026**

[![Raspberry Pi](https://img.shields.io/badge/Built%20on-Raspberry%20Pi-red?logo=raspberry-pi)]()
[![Python](https://img.shields.io/badge/Made%20with-Python-blue?logo=python)]()
[![OpenCV](https://img.shields.io/badge/Powered%20by-OpenCV-green?logo=opencv)]()

</div>
