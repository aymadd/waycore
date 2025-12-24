# Resource and Power Analysis

## Purpose

This document analyzes resource requirements (CPU, RAM, storage) and power consumption for the Waycore device to determine realistic hardware specifications and battery life expectations.

---

## Hardware Baseline: Raspberry Pi 5

### Available Resources

**CPU**:
- Quad-core ARM Cortex-A76 @ 2.4GHz
- ARMv8.2-A architecture
- 64-bit
- ~4-5x faster than Pi 4

**RAM Options**:
- 4GB LPDDR4X-4267
- 8GB LPDDR4X-4267

**Storage**:
- MicroSD card (user-provided)
- Typical: 64GB to 256GB

**Power**:
- 5V via USB-C
- Recommended: 5V/5A (25W) power supply
- Actual consumption: 3-8W typical, 12W peak

**Connectivity**:
- Dual-band 802.11ac Wi-Fi
- Bluetooth 5.0 / BLE
- 2× USB 3.0, 2× USB 2.0
- 2× micro-HDMI (won't use for field device)

---

## Software Resource Requirements

### Memory (RAM) Analysis

#### Operating System Baseline

**Raspberry Pi OS Lite (64-bit)**:
- Base OS: ~400MB
- System services: ~200MB
- **Total OS overhead**: ~600MB

#### Docker Infrastructure

**Docker Engine**:
- Docker daemon: ~100MB
- containerd: ~50MB
- **Total**: ~150MB

**Mosquitto (MQTT Broker)**:
- Memory: ~10-20MB
- Lightweight, efficient

#### Backend Services (Containers)

**Core Daemon**:
- Python runtime: ~30MB
- Service code: ~20MB
- SQLite database: ~10MB
- **Total**: ~60MB

**Module Manager**:
- Python runtime: ~30MB
- Service code: ~15MB
- **Total**: ~45MB

**AI Service**:
- Python runtime: ~50MB
- ONNX Runtime: ~30MB
- TFLite Runtime: ~20MB
- Vision model loaded: ~50MB
- Language model (Phi-3 Mini 4-bit): ~2,300MB
- Context buffer: ~500MB
- **Total idle**: ~100MB
- **Total with LLM loaded**: ~2,950MB

**Comms Bridge**:
- Python runtime: ~30MB
- Radio drivers: ~20MB
- **Total**: ~50MB

**Data Logger**:
- Python runtime: ~30MB
- Service code: ~15MB
- SQLite connections: ~20MB
- **Total**: ~65MB

**Total Backend Services**:
- Without AI model loaded: ~370MB
- With AI model loaded: ~3,220MB

#### UI Application

**Qt/QML Application**:
- Qt runtime libraries: ~100MB
- QML engine: ~50MB
- PySide6: ~50MB
- Application code: ~30MB
- Texture cache: ~50MB
- **Total**: ~280MB

#### Total Memory Usage

**Scenario 1: Idle (No AI loaded)**:
```
OS:                 600 MB
Docker:             150 MB
MQTT:                20 MB
Backend Services:   370 MB
UI:                 280 MB
Buffer:             200 MB
─────────────────────────
TOTAL:            1,620 MB (~1.6 GB)
```

**Scenario 2: AI Active (LLM loaded)**:
```
OS:                 600 MB
Docker:             150 MB
MQTT:                20 MB
Backend Services:   370 MB
AI Service (LLM):  2,950 MB
UI:                 280 MB
Buffer:             100 MB
─────────────────────────
TOTAL:            4,470 MB (~4.5 GB)
```

**Scenario 3: Peak (AI + image processing)**:
```
OS:                 600 MB
Docker:             150 MB
MQTT:                20 MB
Backend Services:   370 MB
AI Service (LLM):  2,950 MB
Image buffer:       400 MB (temp)
UI:                 280 MB
Buffer:              50 MB
─────────────────────────
TOTAL:            4,820 MB (~4.8 GB)
```

**Conclusion**: **4GB RAM is TIGHT but workable**. 8GB recommended for comfort.

**Recommendation**:
- **MVP/Budget**: 4GB Pi 5 (requires careful memory management)
- **Production**: 8GB Pi 5 (recommended, more headroom)

---

### Storage Analysis

#### Operating System

**Raspberry Pi OS Lite**:
- Base system: ~1.5GB
- System updates buffer: ~500MB
- **Total**: ~2GB

#### Docker Images

**Service Images** (optimized):
- Base Python Alpine images: ~150MB each
- Service code: ~20MB each
- Total for 5 services: ~850MB

**UI Image**:
- Ubuntu base with Qt6: ~400MB
- Application code: ~50MB
- **Total**: ~450MB

**Total Docker Images**: ~1,300MB

#### AI Models

**Vision Models**:
- MobileNetV3: 5MB
- Fine-tuned plant classifier: 10MB
- Fine-tuned animal classifier: 10MB
- **Total**: ~25MB

**Language Models**:
- Phi-3 Mini 4k (4-bit GGUF): 2,300MB
- Backup TinyLlama (4-bit): 800MB
- **Total**: ~3,100MB

**Total AI Models**: ~3,125MB

#### Application Data

**Databases**:
- system.db: 50MB (grows slowly)
- app_data.db: 200MB (conversations, waypoints)
- logs.db: 500MB (rotating, max size)
- **Total**: ~750MB

**User Data**:
- Photos (temporary): 200MB
- Map tiles (cached): 500MB
- Field guides: 100MB
- **Total**: ~800MB

#### Total Storage Requirement

**Minimum Installation**:
```
OS:               2,000 MB
Docker images:    1,300 MB
AI models:        3,125 MB
Application data:   750 MB
User data:          800 MB
System overhead:  1,000 MB
───────────────────────
TOTAL:            8,975 MB (~9 GB)
```

**Recommended with headroom**:
```
Base install:      9 GB
Growth buffer:    16 GB (logs, photos, data)
Map tiles:        10 GB (offline maps for region)
Updates:           5 GB (system + app updates)
───────────────────────
TOTAL:           ~40 GB
```

**Recommendation**:
- **Minimum**: 32GB SD card (tight)
- **Recommended**: 64GB SD card
- **Ideal**: 128GB SD card (lots of map tiles, photos)

**SD Card Requirements**:
- Class 10 minimum
- UHS-I (U1) or better
- A1/A2 application class preferred
- Reliable brand (Samsung, SanDisk)

---

### CPU Usage Analysis

#### Idle State

**OS and Background Services**: ~5-10% CPU (1 core)

**Services Idle**:
- Core Daemon: ~1-2% (periodic checks)
- Module Manager: ~1-2% (port scanning)
- MQTT broker: ~1%
- Others: ~1% each
- **Total**: ~10-15% CPU

**UI Idle**: ~5-10% (refresh, animations)

**Total Idle**: ~20-35% CPU (0.5-0.9 cores busy)

#### Active Operations

**GPS Reading**: ~2-5% (1 read/sec)

**LoRa Message**: ~5-10% (send/receive)

**Image Classification** (MobileNetV3):
- Preprocessing: ~20% for 0.1s
- Inference: ~80% for 0.2s
- Postprocessing: ~10% for 0.05s
- **Total**: Spike to 80-100% for ~0.35s

**LLM Inference** (Phi-3 Mini):
- Token generation: ~100% (all cores)
- Speed: ~5-8 tokens/sec
- Duration: Depends on response length
- Example: 100 tokens = 12-20 seconds at 100% CPU

**Two-Stage Pipeline** (Image + LLM):
- Image classification: 0.35s at 80-100%
- LLM generation: 12-20s at 100%
- **Total**: ~13-20 seconds of high CPU

#### Peak Usage Scenarios

**Scenario 1: Taking Photo + AI Classification**:
- Camera capture: 0.5s at 40%
- Image preprocessing: 0.1s at 80%
- Classification: 0.3s at 100%
- **Total**: ~1s, peak 100%

**Scenario 2: Chat Query (text only)**:
- Input processing: <0.1s at 20%
- LLM inference: 10-15s at 100%
- **Total**: ~10-15s at 100%

**Scenario 3: "What is this?" (Image + Chat)**:
- Classification: 0.35s at 100%
- LLM inference: 12-20s at 100%
- **Total**: ~13-20s at 100%

**CPU Thermal Considerations**:
- Pi 5 can sustain 100% CPU load
- Needs heatsink (passive OK, active better)
- Throttles at 80°C (shouldn't reach in normal use)
- Field temperature: -10°C to 50°C ambient

**Recommendation**: Pi 5's quad-core is **adequate** but will be busy during AI operations. This is acceptable for on-demand AI use.

---

## Power Consumption Analysis

### Raspberry Pi 5 Power Draw

**Base Measurements** (from official specs and testing):

**Idle** (no peripherals):
- Headless: ~2.5-3W
- With HDMI: ~3-3.5W

**Typical Load**:
- Light use: ~4-5W
- Moderate load: ~6-8W

**Peak Load**:
- CPU stress: ~10-12W
- All peripherals active: ~12-15W

### Waycore Configuration Power Draw

#### Scenario 1: Idle/Sleep

**Components Active**:
- Pi 5 (minimal): 2.5W
- Display (dim): 0.5W
- ESP32-S3: 0.2W
- GPS (periodic): 0.1W (averaged)
- LoRa (receive): 0.05W
- Sensors: 0.05W

**Total**: ~3.4W

#### Scenario 2: Active Use (No AI)

**Components Active**:
- Pi 5 (light load): 4W
- Display (bright): 1W
- ESP32-S3: 0.3W
- GPS (continuous): 0.3W
- LoRa (active): 0.1W
- Sensors: 0.1W

**Total**: ~5.8W

#### Scenario 3: AI Image Classification

**Components Active**:
- Pi 5 (high load): 8W (spike)
- Display: 1W
- ESP32-S3: 0.3W
- Camera (active): 0.5W
- GPS: 0.3W
- LoRa: 0.1W

**Total**: ~10.2W (for ~1 second)

#### Scenario 4: AI Chat (LLM)

**Components Active**:
- Pi 5 (max load): 12W
- Display: 1W
- ESP32-S3: 0.3W
- GPS: 0.3W
- LoRa: 0.1W

**Total**: ~13.7W (for 10-20 seconds per response)

#### Scenario 5: Full Load (Image + Chat)

**Components Active**:
- Pi 5 (max load): 12W
- Display: 1W
- Camera: 0.5W (briefly)
- ESP32-S3: 0.3W
- GPS: 0.3W
- LoRa: 0.1W

**Total**: ~14.2W (for ~15-20 seconds)

### Power Budget by Component

| Component | Idle | Active | Peak | Notes |
|-----------|------|--------|------|-------|
| Raspberry Pi 5 | 2.5W | 4-8W | 12W | Main compute |
| Display (5") | 0.5W | 1W | 1.5W | Backlight |
| ESP32-S3 | 0.2W | 0.3W | 0.5W | Always-on controller |
| GPS Module | 0.1W | 0.3W | 0.5W | Acquisition phase |
| LoRa Radio | 0.05W | 0.1W | 1.5W | Transmit spikes |
| Wi-Fi (Pi 5) | 0.2W | 0.5W | 1.5W | When enabled |
| LTE Modem | 0W | 2W | 3W | Optional, manual enable |
| Camera | 0W | 0.5W | 0.8W | When active |
| Sensors | 0.05W | 0.1W | 0.2W | Continuous |
| External Modules | 0W | 0-1W | varies | User dependent |

---

## Battery Life Calculations

### Battery Options

**Option 1: Internal Li-Ion (Recommended)**
- Capacity: 10,000 mAh @ 3.7V = 37 Wh
- With boost converter to 5V: ~7,000 mAh @ 5V = 35 Wh (95% efficient)

**Option 2: Larger Internal**
- Capacity: 20,000 mAh @ 3.7V = 74 Wh
- At 5V: ~14,000 mAh @ 5V = 70 Wh

**Option 3: External USB Battery Pack**
- Capacity: 20,000-50,000 mAh @ 3.7V
- At 5V: varies by model and efficiency

**For calculations, assume 10,000 mAh @ 5V = 50 Wh internal battery**

### Battery Life Scenarios

#### Scenario 1: Idle/Standby

**Power Draw**: 3.4W
**Battery**: 50 Wh
**Runtime**: 50 Wh / 3.4W = **14.7 hours**

**Usage Pattern**:
- Display dimmed
- GPS periodic (every 30s)
- LoRa listening
- No active operations

#### Scenario 2: Light Field Use

**Power Profile** (hourly average):
- Idle (80% of time): 3.4W × 0.8 = 2.72W
- Active (15% of time): 5.8W × 0.15 = 0.87W
- AI (5% of time): 10W × 0.05 = 0.5W
- **Average**: 4.09W

**Battery**: 50 Wh
**Runtime**: 50 Wh / 4.09W = **12.2 hours**

**Usage Pattern**:
- Occasional map viewing
- Few messages sent/received
- 2-3 AI queries per hour
- GPS tracking enabled

#### Scenario 3: Moderate Use

**Power Profile** (hourly average):
- Idle (60% of time): 3.4W × 0.6 = 2.04W
- Active (25% of time): 5.8W × 0.25 = 1.45W
- AI (15% of time): 10W × 0.15 = 1.5W
- **Average**: 4.99W

**Battery**: 50 Wh
**Runtime**: 50 Wh / 4.99W = **10 hours**

**Usage Pattern**:
- Active navigation
- Regular messaging
- 5-8 AI queries per hour
- Continuous GPS tracking

#### Scenario 4: Heavy Use (Chat Session)

**Power Profile**:
- Continuous AI chat: 13.7W
- Some idle between messages: 10W average

**Battery**: 50 Wh
**Runtime**: 50 Wh / 10W = **5 hours**

**Usage Pattern**:
- Extended AI chat session
- Continuous screen on
- Multiple image classifications
- Active messaging

#### Scenario 5: Worst Case (All Features)

**Power Profile**:
- Max load: 14.2W sustained

**Battery**: 50 Wh
**Runtime**: 50 Wh / 14.2W = **3.5 hours**

**Usage Pattern**:
- Continuous AI use
- Screen always bright
- GPS tracking
- Active messaging
- All radios enabled

### Real-World Battery Life Estimates

**With 10,000 mAh internal battery**:

| Use Case | Expected Runtime | Confidence |
|----------|------------------|------------|
| Standby | 12-15 hours | High |
| Light field use | 10-12 hours | High |
| Moderate use | 8-10 hours | Medium |
| Heavy AI use | 5-7 hours | Medium |
| Continuous AI | 3-5 hours | Low (unrealistic) |

**With 20,000 mAh battery** (double capacity):
- Double all runtime estimates above

**With external battery pack** (additional):
- Add proportional runtime
- 20,000 mAh pack adds ~10 hours moderate use

### Battery Life Optimization Strategies

#### Software Optimizations

**Low Power Mode** (< 20% battery):
- Disable Wi-Fi and LTE
- Reduce GPS update rate (5 min intervals)
- Dim display to minimum
- Disable non-essential modules
- Unload AI models from memory
- **Expected savings**: 30-40% power reduction

**Ultra Low Power Mode** (< 10% battery):
- All above, plus:
- LoRa only (essential comms)
- Display off (wake on button)
- GPS only on demand
- Core services only
- **Expected savings**: 50-60% power reduction

**Adaptive Brightness**:
- Auto-dim after 30 seconds idle
- Ambient light sensor adjustment
- **Savings**: ~0.5W (15% in active use)

**AI Model Unloading**:
- Unload LLM when not in use (after 5 min)
- Keep vision model loaded (small)
- **Savings**: ~1W when AI idle

#### Hardware Optimizations

**Display**:
- Use e-ink or low-power LCD
- OLED for dark UI (black pixels = off)
- **Potential savings**: 0.5-1W

**LTE Management**:
- Manual enable only
- Auto-disable after timeout
- **Savings**: 2-3W when disabled

**CPU Scaling**:
- Dynamic frequency scaling
- Idle cores when possible
- **Savings**: 1-2W at idle

### Solar Charging Integration

**Solar Panel Option** (5W panel on back):
- Output: 5V @ 1A max (5W)
- Realistic outdoor: 3-4W average
- Extends runtime: ~6-8 hours of moderate use
- Not primary power, extends battery

**Use Case**:
- Trickle charge during day
- Extend multi-day missions
- Emergency backup

---

## Thermal Management

### Operating Temperature Range

**Specifications**:
- Pi 5: 0°C to 50°C (recommended)
- Battery: -20°C to 60°C (discharge), 0°C to 45°C (charge)
- Display: -10°C to 60°C
- **Target range**: -10°C to 50°C

### Thermal Design

**Heat Generation**:
- Pi 5: Up to 10W (12W peak)
- Concentrated in SoC

**Cooling Solution**:
- **Passive heatsink**: Adequate for most use
- **Small fan**: Optional, 0.5W, for sustained AI use
- **Thermal pad**: To enclosure for heat dissipation

**Thermal Throttling**:
- Pi 5 throttles at 80°C
- Should not reach in normal use
- During AI inference: May reach 70-75°C
- Acceptable for short bursts

**Cold Weather Considerations**:
- Battery performance degrades < 0°C
- Display may slow response < -10°C
- Keep device in inside pocket when not in use

---

## Recommendations

### Hardware Configuration

**Recommended Core System**:
- **Pi 5**: 8GB RAM (4GB workable but tight)
- **Storage**: 64GB SD card (Class 10, A1)
- **Battery**: 10,000-15,000 mAh internal
- **Display**: 5" 800×480 IPS LCD
- **Cooling**: Passive heatsink + thermal pad

**Optional Additions**:
- Small fan for heavy AI users
- Larger battery (20,000 mAh) for extended missions
- Solar panel (5W) for multi-day use
- External battery pack connector

### Software Configuration

**Memory Management**:
- Implement aggressive swap for 4GB systems
- Lazy-load AI models
- Unload LLM after timeout
- Monitor and warn on low memory

**Power Management**:
- Implement low power modes
- Auto-dim display
- Manage radio states
- CPU frequency scaling
- Unload unused services

**Storage Management**:
- Log rotation (max 500MB)
- Periodic database vacuum
- Clear cached map tiles (LRU)
- Warn at 80% capacity

### Battery Sizing Recommendation

**For MVP/Testing**:
- 10,000 mAh internal: Adequate for testing
- External pack optional

**For Production**:
- 15,000 mAh internal: Good balance
- 20,000 mAh: Ideal for heavy users
- External pack connector: For extended missions

**Target Battery Life** (realistic):
- Light use: 12+ hours
- Moderate use: 8-10 hours
- Heavy use: 6-8 hours

These targets are **achievable** with the recommended configuration and power management strategies.

---

## Cost Implications

### Hardware Costs (Approximate)

**Core Components**:
- Raspberry Pi 5 (8GB): $80
- 64GB SD card: $15
- 5" IPS display: $40
- 15,000 mAh battery: $25
- ESP32-S3: $8
- LoRa module: $15
- GPS module: $20
- Case/enclosure: $30
- **Subtotal**: ~$233

**Optional**:
- Solar panel (5W): $15
- Active cooling fan: $5
- Larger battery: +$15
- External modules: $20-50 each

**Total BOM**: ~$250-300 (without external modules)

### Trade-offs

**4GB vs 8GB Pi 5**:
- Cost difference: $0 (same price now)
- Recommendation: Always choose 8GB

**Battery Size**:
- 10,000 mAh: -$8, -2 hours runtime
- 15,000 mAh: baseline
- 20,000 mAh: +$8, +5 hours runtime

**Display**:
- Lower resolution: -$15, worse UX
- e-ink: +$20, better battery, slower refresh
- OLED: +$30, better contrast, better battery (dark UI)

---

## Performance vs Power Trade-offs

### AI Model Choices

**Phi-3 Mini vs TinyLlama**:
- Phi-3: Better capability, 13W for 15-20s
- TinyLlama: Faster, 10W for 5-8s, less capable
- **Recommendation**: Phi-3 for quality, allow battery hit

**Vision Model Size**:
- MobileNetV3: 5MB, fast, 0.3s
- EfficientNet-Lite: 15MB, slower, 0.5s, more accurate
- **Recommendation**: MobileNetV3 for speed/battery

### Radio Management

**Always On** vs **On Demand**:
- LoRa: Always on (minimal power)
- Wi-Fi: On demand only (2-3W savings)
- LTE: Manual enable (2-3W savings)
- **Recommendation**: LoRa always, others on demand

### Display Strategy

**Always On** vs **Auto-dim**:
- Always on: 1W constant
- Auto-dim: 0.5W average (50% savings)
- **Recommendation**: Aggressive auto-dim

---

## Testing and Validation

### Power Measurement

**Tools Needed**:
- USB power meter (inline)
- Data logging (continuous monitoring)
- Thermal camera (optional)

**Test Scenarios**:
1. Measure idle power
2. Measure active use power
3. Measure AI inference power
4. Measure with all radios active
5. Record battery drain over time

**Acceptance Criteria**:
- Idle: < 4W
- Active: < 7W (without AI)
- AI inference: < 15W peak
- Battery life: > 8 hours moderate use

### Thermal Testing

**Test Scenarios**:
1. Sustained AI inference (20 min)
2. High ambient temperature (40°C)
3. Low ambient temperature (-10°C)
4. Check for throttling

**Acceptance Criteria**:
- No throttling in normal use
- SoC temp < 80°C
- Enclosure surface < 45°C (touch safe)

### Battery Testing

**Test Scenarios**:
1. Full discharge cycle
2. Discharge curves at different loads
3. Temperature effects on capacity
4. Charging time and efficiency

**Acceptance Criteria**:
- Meets rated capacity (±10%)
- Consistent discharge behavior
- Safe temperature range maintained

---

## Summary

### Resource Requirements

**RAM**:
- Minimum: 4GB (tight, requires management)
- Recommended: 8GB (comfortable headroom)

**Storage**:
- Minimum: 32GB (tight)
- Recommended: 64GB (adequate)
- Ideal: 128GB (maps + photos)

**CPU**:
- Pi 5 quad-core adequate
- Expect 100% load during AI
- Thermal management needed

### Power Consumption

**Typical**: 4-6W (idle to light use)
**Peak**: 14W (AI inference)
**Average**: 5-8W (realistic field use)

### Battery Life (10,000 mAh internal)

**Realistic Expectations**:
- Standby: 12-15 hours
- Light use: 10-12 hours
- Moderate use: 8-10 hours
- Heavy use: 6-8 hours

**With 15,000 mAh** (recommended):
- Add 50% to all estimates above

### Feasibility

**Conclusion**: The Waycore device is **feasible** with the proposed hardware configuration. The Pi 5 provides adequate compute for the workload, and battery life targets are **achievable** with proper power management.

**Key Success Factors**:
1. Efficient power management software
2. Lazy-loading AI models
3. Aggressive display management
4. Proper thermal design
5. Quality battery cells
6. User education on power modes

The device can provide a **full day of field use** (8-10 hours) with moderate usage patterns, which is acceptable for the target use cases.
