from __future__ import annotations

from device.libs.schemas.module import (
    ModuleCapability,
    ModuleCommand,
    ModuleData,
    ModuleDiscovered,
    ModuleRemoved,
    ModuleRemovedReason,
    ModuleStatus,
)


def test_module_discovered_valid() -> None:
    msg = ModuleDiscovered(
        source="module-manager",
        module_id="mod-123",
        module_type="sensor-pack",
        hardware_version="1.0",
        firmware_version="1.2.3",
        capabilities=[ModuleCapability.sensor, ModuleCapability.power],
        power_draw_ma=250,
        metadata={"ports": [1, 2]},
    )
    assert ModuleCapability.sensor in msg.capabilities
    assert msg.power_draw_ma == 250


def test_module_removed_valid() -> None:
    msg = ModuleRemoved(
        source="module-manager", module_id="mod-123", reason=ModuleRemovedReason.timeout
    )
    assert msg.reason is ModuleRemovedReason.timeout


def test_module_status_valid() -> None:
    status = ModuleStatus(
        source="module-manager",
        module_id="mod-123",
        connected=True,
        healthy=True,
        data={"temp": 22.1},
    )
    assert status.connected is True
    assert status.data["temp"] == 22.1


def test_module_data_valid() -> None:
    data = ModuleData(
        source="module-manager",
        module_id="mod-123",
        data_type="sample",
        value={"x": 1},
    )
    assert data.data_type == "sample"


def test_module_command_valid() -> None:
    cmd = ModuleCommand(source="ui", module_id="mod-123", command="set_rate", parameters={"hz": 5})
    assert cmd.command == "set_rate"
    assert cmd.parameters["hz"] == 5
