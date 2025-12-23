# Waycore Project Overview

## 1. Project Vision

Build a **modular, rugged, handheld field computer** inspired by Flipper Zero, but designed for **outdoors, EDC, survival, and trades/handyman use**, not networking geeks.

Core principles:

* **Communications-first** (works when phones/networks fail)
* **Modular by design** (core device + external modules)
* **On-device intelligence** (AI without cloud dependency)
* **Reliable & resilient** (SOS must work even if UI crashes)
* **Developer-friendly** (clear interfaces, mockable hardware)

The device is not a phone replacement or power tool. It is a **field gateway and control plane** that connects radios, sensors, AI, and external modules into one dependable system.

---

## 2. High-Level Architecture

The system is split into two compute domains:

```
+--------------------------------------------------+
|                MAIN BRAIN (Linux SBC)             |
|  - UI (Qt/QML)                                   |
|  - On-device AI                                  |
|  - Maps / Logs / Notes                           |
|  - TAK / CoT over IP                             |
|  - LTE / Wi-Fi networking logic                  |
|                                                  |
|     USB / Serial / IPC                           |
|                                                  |
|  LOW-POWER CONTROLLER (ESP32-S3)                 |
|  - Meshtastic (LoRa)                             |
|  - GPS                                           |
|  - Always-on sensors                             |
|  - SOS button + buzzer/LED                       |
|  - Power & battery supervision                   |
+--------------------------------------------------+
```

Why this split:

* Linux SBC excels at **UI, AI, camera, storage, networking**
* ESP32 excels at **low power, reliability, instant response**
* SOS and radios continue working even if Linux is busy or rebooting

---

## 3. Main Board Choice

### Selected Main Board

**Raspberry Pi 5**

Reasons:

* Mature ecosystem and documentation
* Excellent camera + display support
* Enough compute for MVP AI models
* Works well with Linux, Qt, Python, ONNX/TFLite

### Operating System

**Raspberry Pi OS Lite (64-bit)**

Why:

* Best hardware support for Pi (camera, GPU, touch)
* Lighter than desktop OS variants
* Easy path to later hardening (Ubuntu Server / Buildroot)

---

## 4. Low-Power Controller

### ESP32-S3 (sidecar controller)

Responsibilities:

* Runs Meshtastic (LoRa mesh)
* Reads GPS and core sensors
* Handles SOS button, buzzer, LEDs
* Enforces power rules (e.g. LTE off at low battery)
* Communicates with Pi over USB CDC or UART

This controller must remain stable and rarely change once working.

---

## 5. Communications Stack

### Supported Transports

* **LoRa (Meshtastic)** — long-range, low-power text + telemetry
* **Wi-Fi** — local UI access, TAK, phone/tablet integration
* **Bluetooth** — pairing, config, accessories
* **LTE (optional, manual)** — uplink when available
* **GPS/GNSS** — position, tracking, SOS

### TAK Integration

* Device acts as a **TAK / CoT gateway**, not a full ATAK client
* Outputs CoT over IP to:

  * local Wi-Fi (offline)
  * remote server (when LTE is enabled)

---

## 6. On-Device AI (MVP Scope)

### AI Goals

* Offline image classification (plants, mushrooms, fish)
* Simple local Q&A (rules + small models)
* Sensor anomaly detection

### What AI Is NOT (MVP)

* No ChatGPT-scale LLMs
* No continuous video analysis
* No cloud dependency

### AI Runtime

* Language: **Python**
* Frameworks: ONNX Runtime / TensorFlow Lite / OpenCV
* Input: camera images, sensor data
* Output: class labels, confidence, short explanations

AI runs on-demand to preserve battery.

---

## 7. Core Sensors (Built-In)

Low-power, high-value sensors included in the core device:

* GNSS (GPS/GLONASS/Galileo)
* 9-axis IMU (accelerometer + gyro + magnetometer)
* Barometer / altimeter
* Ambient temperature & humidity
* Ambient light sensor
* Battery fuel gauge

These support navigation, environment awareness, logging, and AI features.

---

## 8. Modularity System (Critical Design Element)

### Philosophy

* Core device stays small, reliable, and power-efficient
* Specialized or power-hungry features live in **external modules**

### Physical Interface (MVP)

* 1–2 expansion ports
* USB-C or rugged side connector
* Provides:

  * 5V, 3.3V, GND
  * UART
  * I²C
  * SPI (optional)
  * Module detect / ID pin

### Module Protocol

Each module must:

* Identify itself
* Declare power usage
* Declare capabilities
* Expose a simple data schema

Example:

```json
{
  "module_id": "TEMP_SENSOR_V1",
  "power_ma": 20,
  "capabilities": ["temperature"]
}
```

### MVP External Modules

* External battery pack (proves power negotiation)
* Sensor pod (e.g. temperature / radiation)

Future modules may include water quality, borescope camera, multimeter, wind sensor, etc.

---

## 9. User Interface

### UI Philosophy

* Control plane, not text-heavy typing
* Fast access to critical states
* Physical buttons for safety-critical actions

### Core UI Screens

* System status (radios, GPS, battery)
* Mesh / node overview
* SOS screen
* Sensor dashboard
* AI tools (image classify, Q&A)
* Module manager
* Notes / logs

### UI Technology

* **Qt/QML** frontend
* Python backend (PySide6)
* Fixed target resolution (e.g. 480×800)

---

## 10. Software Architecture

### Services (run as separate processes)

* `core-daemon` — state machine, modes, policies
* `module-manager` — module discovery and lifecycle
* `ai-service` — inference endpoints
* `ui-app` — main interface
* `comms-bridge` — Meshtastic + TAK integration

### Inter-Process Communication

* HTTP + WebSocket (MVP simplicity)
* JSON schemas for messages

### Repository Structure

```
device/
  apps/ui/
  services/
    core_daemon/
    module_manager/
    ai_service/
    comms_bridge/
  drivers/
    mock/
    real/
  proto/
  docker/
  docs/
```

---

## 11. Development Strategy (Simulation-First)

### Key Rule

Do **not** simulate Raspberry Pi OS early.

Instead:

* Develop on laptop
* Use Docker Compose
* Mock all hardware (GPS, LoRa, sensors, ESP32)
* Fix UI resolution early

### Why

* Faster iteration
* Less friction
* Hardware becomes integration work later

---

## 12. Build Phases

### Phase 1 — Software MVP (No Hardware)

* UI skeleton
* Mock ESP32 + sensors
* AI inference pipeline
* Module protocol

### Phase 2 — Bench Hardware

* Raspberry Pi 5
* USB Meshtastic device
* Camera + screen

### Phase 3 — Custom PCB (Gen-2)

* Pi compute module or SBC
* ESP32-S3
* Power system
* Expansion ports

### Phase 4 — Field Testing

* Battery life
* RF behavior
* UX under stress

---

## 13. Non-Goals (Explicitly Out of Scope for MVP)

* Power tools (drill, dremel, blower)
* Full ATAK client on device
* Large LLMs
* Continuous voice comms
* Cloud-first dependencies

---

## 14. Guiding Principle

> **This product is a modular, communications-first field computer. Everything else is a module or a later generation.**

This document defines the MVP scope and architecture. Future generations will iterate, not reinvent.
