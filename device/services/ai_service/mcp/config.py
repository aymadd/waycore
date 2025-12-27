"""Configuration for MCP servers."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server."""

    name: str
    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] | None = None
    description: str = ""
    enabled: bool = True
    timeout_seconds: float = 10.0
    requires_confirmation: list[str] = field(default_factory=list)


def load_mcp_config(config_path: Path | str) -> list[MCPServerConfig]:
    """Load MCP server configurations from YAML file.

    Args:
        config_path: Path to the mcp_servers.yaml file.

    Returns:
        List of MCPServerConfig objects for enabled servers.
    """
    config_path = Path(config_path)
    if not config_path.exists():
        logger.warning(f"MCP config file not found: {config_path}")
        return []

    try:
        with open(config_path) as f:
            data = yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load MCP config: {e}")
        return []

    servers: list[MCPServerConfig] = []
    server_configs = data.get("servers", {})

    for name, config in server_configs.items():
        if not isinstance(config, dict):
            logger.warning(f"Invalid config for server {name}, skipping")
            continue

        if not config.get("enabled", True):
            logger.debug(f"Server {name} is disabled, skipping")
            continue

        try:
            server = MCPServerConfig(
                name=name,
                command=config.get("command", "python"),
                args=config.get("args", []),
                env=config.get("env"),
                description=config.get("description", ""),
                enabled=config.get("enabled", True),
                timeout_seconds=float(config.get("timeout_seconds", 10.0)),
                requires_confirmation=config.get("requires_confirmation", []),
            )
            servers.append(server)
            logger.debug(f"Loaded MCP server config: {name}")
        except Exception as e:
            logger.error(f"Failed to parse config for server {name}: {e}")

    return servers


def get_default_configs() -> list[MCPServerConfig]:
    """Get default MCP server configurations.

    Returns:
        List of default MCPServerConfig objects.
    """
    return [
        MCPServerConfig(
            name="sensors",
            command="python",
            args=["-m", "device.services.ai_service.mcp_servers.sensors"],
            description="Device sensor data access",
            timeout_seconds=5.0,
        ),
        MCPServerConfig(
            name="actions",
            command="python",
            args=["-m", "device.services.ai_service.mcp_servers.actions"],
            description="Device actions (notes, messages, etc.)",
            timeout_seconds=10.0,
            requires_confirmation=[
                "send_mesh_message",
                "factory_reset",
                "delete_note",
                "clear_conversation",
            ],
        ),
    ]
