from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from typing import TYPE_CHECKING, Any, Callable, TypeVar

from .interfaces.camera import ICamera
from .interfaces.gps import IGPS
from .interfaces.module_port import IModulePort
from .interfaces.power import IPowerController
from .interfaces.radio import IRadio
from .interfaces.sensor import ISensor

if TYPE_CHECKING:
    from .interfaces.mesh_network import IMeshNetwork

T = TypeVar("T")
Creator = Callable[[Mapping[str, Any]], T]


class DriverFactory:
    """
    Configuration-driven driver creation.
    Concrete drivers should register themselves at import time.
    """

    _camera_creators: MutableMapping[str, Creator[ICamera]] = {}
    _gps_creators: MutableMapping[str, Creator[IGPS]] = {}
    _radio_creators: MutableMapping[str, Creator[IRadio]] = {}
    _sensor_creators: MutableMapping[str, Creator[ISensor]] = {}
    _module_port_creators: MutableMapping[str, Creator[IModulePort]] = {}
    _power_creators: MutableMapping[str, Creator[IPowerController]] = {}
    _mesh_network_creators: MutableMapping[str, Creator[IMeshNetwork]] = {}

    # Registration
    @classmethod
    def register_camera(cls, name: str, creator: Creator[ICamera]) -> None:
        cls._camera_creators[name] = creator

    @classmethod
    def register_gps(cls, name: str, creator: Creator[IGPS]) -> None:
        cls._gps_creators[name] = creator

    @classmethod
    def register_radio(cls, name: str, creator: Creator[IRadio]) -> None:
        cls._radio_creators[name] = creator

    @classmethod
    def register_sensor(cls, name: str, creator: Creator[ISensor]) -> None:
        cls._sensor_creators[name] = creator

    @classmethod
    def register_module_port(cls, name: str, creator: Creator[IModulePort]) -> None:
        cls._module_port_creators[name] = creator

    @classmethod
    def register_power(cls, name: str, creator: Creator[IPowerController]) -> None:
        cls._power_creators[name] = creator

    @classmethod
    def register_mesh_network(cls, name: str, creator: Creator[IMeshNetwork]) -> None:
        cls._mesh_network_creators[name] = creator

    # Creation
    @classmethod
    def create_camera(cls, name: str, config: Mapping[str, Any] | None = None) -> ICamera:
        return cls._create(cls._camera_creators, name, config)

    @classmethod
    def create_gps(cls, name: str, config: Mapping[str, Any] | None = None) -> IGPS:
        return cls._create(cls._gps_creators, name, config)

    @classmethod
    def create_radio(cls, name: str, config: Mapping[str, Any] | None = None) -> IRadio:
        return cls._create(cls._radio_creators, name, config)

    @classmethod
    def create_sensor(cls, name: str, config: Mapping[str, Any] | None = None) -> ISensor:
        return cls._create(cls._sensor_creators, name, config)

    @classmethod
    def create_module_port(cls, name: str, config: Mapping[str, Any] | None = None) -> IModulePort:
        return cls._create(cls._module_port_creators, name, config)

    @classmethod
    def create_power(cls, name: str, config: Mapping[str, Any] | None = None) -> IPowerController:
        return cls._create(cls._power_creators, name, config)

    @classmethod
    def create_mesh_network(
        cls, name: str, config: Mapping[str, Any] | None = None
    ) -> IMeshNetwork:
        return cls._create(cls._mesh_network_creators, name, config)

    @staticmethod
    def _create(
        registry: Mapping[str, Creator[T]], name: str, config: Mapping[str, Any] | None
    ) -> T:
        if name not in registry:
            msg = f"Unknown driver '{name}'"
            raise KeyError(msg)
        creator = registry[name]
        return creator(config or {})
