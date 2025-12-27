# Specifications

> Technical details and hardware information

## Device Overview

Waycore is a portable field computer designed for outdoor use. Specifications may vary by model.

## Hardware

### Display
| Specification | Details |
|---------------|---------|
| Type | LCD/OLED (varies by model) |
| Resolution | Model-dependent |
| Touch | Capacitive touchscreen |
| Visibility | Daylight readable |

### Processor
| Specification | Details |
|---------------|---------|
| Architecture | ARM-based |
| Cores | 4 (typical) |
| RAM | 2-4 GB (typical) |

### Storage
| Specification | Details |
|---------------|---------|
| Type | eMMC/SD |
| Capacity | 16-64 GB (typical) |
| Expandable | Model-dependent |

### Battery
| Specification | Details |
|---------------|---------|
| Type | Lithium-ion |
| Capacity | Model-dependent |
| Charging | USB-C |
| Runtime | 6-12 hours typical |

## Sensors

### GPS
| Specification | Details |
|---------------|---------|
| Type | GNSS receiver |
| Systems | GPS, GLONASS (model-dependent) |
| Accuracy | ±5-15m horizontal |
| Cold start | ~30 seconds typical |
| Hot start | ~5 seconds typical |

### Compass
| Specification | Details |
|---------------|---------|
| Type | 3-axis magnetometer |
| Accuracy | ±2-5° (calibrated) |
| Resolution | 0.1° |

### Altimeter
| Specification | Details |
|---------------|---------|
| Type | Barometric |
| Range | -500m to 9000m |
| Resolution | 0.1m |
| Accuracy | ±10-30m (GPS), ±1m (calibrated barometric) |

### Temperature
| Specification | Details |
|---------------|---------|
| Range | -40°C to +85°C |
| Accuracy | ±1°C |
| Note | May be affected by device heat |

### Other Sensors
- **Accelerometer**: 3-axis, for orientation
- **Gyroscope**: Model-dependent
- **Light sensor**: For auto-brightness (some models)

## Connectivity

### Wireless
| Type | Details |
|------|---------|
| WiFi | 802.11 b/g/n (2.4GHz) |
| Bluetooth | 4.0+ (model-dependent) |

### Ports
| Type | Details |
|------|---------|
| USB-C | Charging, data transfer |
| Expansion | Model-dependent (module port) |

### Radio (Meshtastic)
| Specification | Details |
|---------------|---------|
| Frequency | 868/915 MHz (region-dependent) |
| Range | 2-10+ miles line-of-sight |
| Protocol | LoRa/Meshtastic |

## Environmental

### Operating Conditions
| Specification | Range |
|---------------|-------|
| Temperature | -20°C to +45°C |
| Humidity | 0-95% non-condensing |

### Storage Conditions
| Specification | Range |
|---------------|-------|
| Temperature | -30°C to +60°C |
| Humidity | 0-95% non-condensing |

### Durability
| Specification | Rating |
|---------------|--------|
| Water resistance | Model-dependent (IPX4-IPX7) |
| Drop resistance | Designed for field use |
| Dust resistance | Model-dependent (IP5X-IP6X) |

## Software

### Operating System
| Specification | Details |
|---------------|---------|
| Base | Linux-based |
| UI | Qt/QML |
| Updates | OTA when connected |

### AI Model
| Specification | Details |
|---------------|---------|
| Type | Local language model |
| Size | ~2GB |
| Capabilities | Text, vision (model-dependent) |
| Processing | On-device only |

## Power

### Charging
| Specification | Details |
|---------------|---------|
| Input | USB-C, 5V/2A minimum |
| Charge time | 2-3 hours (typical) |
| Fast charging | Model-dependent |

### Power Consumption
| Mode | Consumption |
|------|-------------|
| Idle (screen off) | Low |
| Active use | Moderate |
| GPS + radio | Higher |
| Charging | Pauses during heavy use |

## Dimensions

Varies by model. Check your specific model documentation for exact dimensions and weight.

## Compliance

- FCC (USA)
- CE (Europe)
- Region-specific radio regulations

## Related

- [Battery](../features/battery.md) - Power management
- [Sensors](../features/sensors.md) - Sensor details
- [Troubleshooting](./troubleshooting.md) - Hardware issues
