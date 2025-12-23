# Waycore Vision

> This document captures the **full vision space** for the device: all major ideas, capabilities, and future expansion areas. It is intentionally **broad and aspirational**, without timelines, to guide long-term design decisions while keeping the MVP grounded.

---

## 1. Product Identity

**What this is**

* A **modular, rugged, handheld field computer**
* Inspired by **Flipper Zero** (modularity + hacking friendliness)
* Tuned for **outdoors, survival, EDC, family safety, and trades/handyman use**

**What this is not**

* Not a smartphone replacement
* Not a single-purpose tool
* Not cloud-dependent

Core philosophy:

> **Communications + awareness first. Tools and sensors second. Power tools never in the core.**

---

## 2. Communication Modes (Core Pillar)

The device is designed to operate across **multiple communication layers**, degrading gracefully as infrastructure disappears.

### 2.1 Supported Communication Modes

1. **Meshtastic (LoRa mesh)**

   * Long-range, low-power text + telemetry
   * Family / group communication when networks are down
   * Device-to-device and mesh routing

2. **LTE (optional, user-controlled)**

   * Internet-first mode when available
   * Used for TAK forwarding, updates, data sync
   * Explicit ON/OFF for battery and control

3. **Wi-Fi**

   * Local UI access
   * Offline TAK/iTAK connectivity
   * Phone/tablet pairing

4. **TAK / CoT over IP**

   * Situational awareness integration
   * Gateway role (not full ATAK client)
   * Local or remote server output

5. **GPS / GNSS**

   * Position, tracking, breadcrumbing
   * Used for navigation, SOS, logging

6. **SOS / Beacon Mode**

   * Dedicated distress signaling
   * Mesh broadcast + IP escalation
   * Audible and visual locator

---

## 3. Core Features

### 3.1 Safety & Emergency

* One-button **SOS beacon**
* Loud audible alert (speaker siren)
* Flashlight strobe
* GPS position embedded in SOS messages
* Works even if main UI is unavailable

---

### 3.2 Built-In AI (On-Device)

AI is a **core differentiator**, but scoped to what is realistic and valuable offline.

#### AI Capabilities

* **Image recognition**

  * Plants, mushrooms, fish
  * Object and environment classification
* **Q&A**

  * Local knowledge base
  * Rules + small models
* **Voice (future / experimental)**

  * Wake word
  * Simple commands
  * Voice notes

AI runs **on demand**, not continuously, to preserve power.

---

### 3.3 Communication & Interaction

* Text messaging (mesh + IP)
* Preset / canned messages
* (Future) VoIP when LTE/Wi-Fi available
* Notifications via sound, vibration, and UI

---

### 3.4 Power & Sustainability

* Internal battery
* **Solar panel on back (trickle charge / extension only)**
* External battery support via module or port

---

### 3.5 Core Sensors & Utilities

Built-in, low-power sensors that support many use cases:

* Gyroscope + accelerometer (level detection, motion)
* Barometer / elevation
* Temperature sensor
* Compass (magnetometer)
* Ambient light sensor
* High-CRI flashlight

---

## 4. Applications & Software Domains

The device supports **internal apps** and **module-driven apps**.

### 4.1 Core Apps

* Notes & journaling
* Event and location logging
* Maps (offline, lightweight)
* Distance tracker
* Shooting tracker (logs, environment, repeatability)

### 4.2 Integrations

* iTAK / ATAK
* Drone control & telemetry (future, ecosystem-dependent)
* External receivers (game cameras, sensors)

---

## 5. Application & Module Domains

The platform is designed to serve multiple verticals without fragmenting the core device.

### 5.1 Domains

* Hunting & fishing
* Hiking & camping
* Tactical / preparedness
* EDC & family communications
* Geeks, makers & handyman

Each domain is enabled primarily through **software + external modules**, not core hardware changes.

---

## 6. External Modules (Expansion Ecosystem)

External modules attach via a defined module port and protocol.

### 6.1 Environmental & Safety Modules

* Water quality check
* Radiation (Geiger) sensor
* Wind sensor
* UV light module
* Moisture sensors

### 6.2 Measurement & Inspection Modules

* Laser distance meter
* Micrometer
* Voltage & amp meter
* RFID / NFC reader-writer
* External wired camera (borescope)

### 6.3 Outdoor & Niche Modules

* Fishing sonar receiver
* Drone receiver
* Wireless sensor receiver (game cams, fishing line sensors, pagers)
* Extended touchscreen display
* External battery module

### 6.4 Experimental / Low-Priority Modules

* Fire starter
* Hand warmer
* Blower

(These are explicitly **not** part of the core and may remain experimental.)

---

## 7. Physical Controls & Hardware Features

Physical controls are critical for reliability and safety.

### 7.1 Buttons & Controls

* Dedicated SOS button
* Flashlight button
* Screen power toggle
* Volume control
* Comms mode switch

### 7.2 Ports & Interfaces

* Module port(s)
* Main charging port (USB-C)
* External antenna port(s)
* Optional antenna switch (internal/external)

### 7.3 I/O Hardware

* Speakers
* Microphone
* Camera (initially for computer vision)

---

## 8. Design Constraints & Guardrails

Explicit constraints to keep the platform viable:

* Core device must remain usable without modules
* No high-power motors in the core device
* No cloud dependency for critical functions
* Battery life prioritized over raw performance
* Modular features must not compromise reliability

---

## 9. Long-Term Direction (Without Timelines)

* Gen-1: Communications-first, modular foundation
* Gen-2: Better AI efficiency, more mature module ecosystem
* Gen-3+: Optional consolidation, specialized variants

The roadmap is **evolutionary**, not revolutionary. Each generation builds on the same core philosophy.

---

## 10. Guiding Principle

> **This device is a resilient, modular field platform. Communications and awareness are the spine; tools and sensors are replaceable limbs.**

This document captures the full idea space to guide design decisions and avoid scope drift while still enabling long-term ambition.
