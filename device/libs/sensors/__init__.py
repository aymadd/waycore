"""
Sensor registry and discovery system.

This module provides a dynamic sensor registration system that allows:
- Automatic sensor discovery on startup
- Mock sensors for development
- Real hardware sensors for production
- Future extensibility for external modules
"""

from .registry import SensorRegistry, SensorType, get_registry, initialize_sensors

__all__ = ["SensorRegistry", "SensorType", "get_registry", "initialize_sensors"]
