"""Tests for MCP configuration loading."""

from __future__ import annotations

import tempfile

from device.services.ai_service.mcp.config import (
    MCPServerConfig,
    get_default_configs,
    load_mcp_config,
)


class TestMCPServerConfig:
    """Tests for MCPServerConfig dataclass."""

    def test_basic_config(self) -> None:
        """Test basic configuration creation."""
        config = MCPServerConfig(
            name="test-server",
            command="python",
            args=["-m", "test.module"],
        )
        assert config.name == "test-server"
        assert config.command == "python"
        assert config.args == ["-m", "test.module"]
        assert config.enabled is True
        assert config.timeout_seconds == 10.0
        assert config.requires_confirmation == []

    def test_full_config(self) -> None:
        """Test configuration with all fields."""
        config = MCPServerConfig(
            name="actions",
            command="python",
            args=["-m", "mcp_servers.actions"],
            env={"DEBUG": "1"},
            description="Device actions",
            enabled=True,
            timeout_seconds=15.0,
            requires_confirmation=["delete_note", "factory_reset"],
        )
        assert config.name == "actions"
        assert config.env == {"DEBUG": "1"}
        assert config.description == "Device actions"
        assert config.timeout_seconds == 15.0
        assert "delete_note" in config.requires_confirmation


class TestLoadMCPConfig:
    """Tests for load_mcp_config function."""

    def test_load_valid_config(self) -> None:
        """Test loading a valid configuration file."""
        config_content = """
servers:
  sensors:
    command: "python"
    args: ["-m", "mcp_servers.sensors"]
    description: "Sensor access"
    enabled: true
    timeout_seconds: 5

  actions:
    command: "python"
    args: ["-m", "mcp_servers.actions"]
    enabled: true
    timeout_seconds: 10
    requires_confirmation:
      - send_message
      - delete_note
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_content)
            f.flush()

            configs = load_mcp_config(f.name)

        assert len(configs) == 2

        sensors = next(c for c in configs if c.name == "sensors")
        assert sensors.timeout_seconds == 5.0
        assert sensors.requires_confirmation == []

        actions = next(c for c in configs if c.name == "actions")
        assert actions.timeout_seconds == 10.0
        assert "send_message" in actions.requires_confirmation

    def test_load_with_disabled_server(self) -> None:
        """Test that disabled servers are not loaded."""
        config_content = """
servers:
  enabled_server:
    command: "python"
    args: []
    enabled: true

  disabled_server:
    command: "python"
    args: []
    enabled: false
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_content)
            f.flush()

            configs = load_mcp_config(f.name)

        assert len(configs) == 1
        assert configs[0].name == "enabled_server"

    def test_load_nonexistent_file(self) -> None:
        """Test loading from nonexistent file returns empty list."""
        configs = load_mcp_config("/nonexistent/path/config.yaml")
        assert configs == []

    def test_load_empty_servers(self) -> None:
        """Test loading config with no servers."""
        config_content = """
servers: {}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_content)
            f.flush()

            configs = load_mcp_config(f.name)

        assert configs == []


class TestGetDefaultConfigs:
    """Tests for get_default_configs function."""

    def test_default_configs_exist(self) -> None:
        """Test that default configs are provided."""
        configs = get_default_configs()
        assert len(configs) >= 2

    def test_default_configs_have_sensors(self) -> None:
        """Test that sensors server is in defaults."""
        configs = get_default_configs()
        sensor_configs = [c for c in configs if c.name == "sensors"]
        assert len(sensor_configs) == 1
        assert sensor_configs[0].timeout_seconds == 5.0

    def test_default_configs_have_actions(self) -> None:
        """Test that actions server is in defaults."""
        configs = get_default_configs()
        action_configs = [c for c in configs if c.name == "actions"]
        assert len(action_configs) == 1
        assert len(action_configs[0].requires_confirmation) > 0
