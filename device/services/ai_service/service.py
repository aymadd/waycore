from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any, Callable

from device.libs.common.base_service import BaseService
from device.libs.database.ai import AIDatabase
from device.libs.messaging.bus import MessageBus
from device.libs.schemas.ai import AIInferenceRequest

from .agent import AgentController
from .engine import run_inference
from .mcp import MCPManager, load_mcp_config
from .preprocessing import PreprocessingError, preprocess_for_inference
from .safety import add_safety_warning

logger = logging.getLogger(__name__)

# Database path
AI_DB_PATH = os.getenv("AI_DB_PATH", "/app/data/ai.sqlite3")

# Model storage path
MODEL_DIR = Path(os.getenv("WAYCORE_MODEL_PATH", "/opt/waycore/models"))
REGISTRY_FILE = MODEL_DIR / "registry.json"

# Knowledge base path
RAG_DATA_DIR = Path(os.getenv("RAG_DATA_DIR", "/app/data/outdoor"))

# MCP configuration
MCP_CONFIG_PATH = Path(__file__).parent / "config" / "mcp_servers.yaml"
MCP_ENABLED = os.getenv("MCP_ENABLED", "true").lower() == "true"


def _get_knowledge_base_info() -> dict[str, Any]:
    """Get information about the installed knowledge base."""
    info: dict[str, Any] = {
        "installed": False,
        "version": None,
        "db_size_mb": 0,
        "idx_size_mb": 0,
    }

    db_path = RAG_DATA_DIR / "knowledge.db"
    idx_path = RAG_DATA_DIR / "knowledge.idx"
    version_file = RAG_DATA_DIR / ".version"
    manifest_file = RAG_DATA_DIR / "manifest.json"

    if db_path.exists() and idx_path.exists():
        info["installed"] = True
        info["db_size_mb"] = round(db_path.stat().st_size / (1024 * 1024), 2)
        info["idx_size_mb"] = round(idx_path.stat().st_size / (1024 * 1024), 2)

        # Try to get version
        if version_file.exists():
            info["version"] = version_file.read_text().strip()
        elif manifest_file.exists():
            try:
                with open(manifest_file) as f:
                    manifest = json.load(f)
                info["version"] = manifest.get("version")
                info["entry_count"] = manifest.get("entry_count")
            except Exception:
                pass

    return info


class AIService(BaseService):
    def __init__(self, config: dict[str, Any], bus: MessageBus | None = None) -> None:
        super().__init__(config, bus)
        self._healthy = False
        self._unsubscribe: Callable[[], None] | None = None
        self._idle_sleep_s = float(config.get("idle_sleep_seconds", 0.1))
        self._response_source = str(config.get("response_source", "ai-service"))
        self._db: AIDatabase | None = None
        self._mcp: MCPManager | None = None
        self._agent: AgentController | None = None

    @property
    def response_source(self) -> str:
        return self._response_source

    @property
    def db(self) -> AIDatabase | None:
        return self._db

    @property
    def mcp(self) -> MCPManager | None:
        """Get the MCP manager for tool access."""
        return self._mcp

    @property
    def agent(self) -> AgentController | None:
        """Get the agent controller for agentic AI capabilities."""
        return self._agent

    async def _setup(self) -> None:
        # Initialize database
        self._db = AIDatabase(AI_DB_PATH)
        await self._db.open()

        # Log knowledge base status
        kb_info = _get_knowledge_base_info()
        if kb_info["installed"]:
            version = kb_info.get("version", "unknown")
            db_mb = kb_info.get("db_size_mb", 0)
            idx_mb = kb_info.get("idx_size_mb", 0)
            logger.info(f"Knowledge base: v{version} (db: {db_mb}MB, idx: {idx_mb}MB)")
        else:
            logger.warning("Knowledge base not found at %s", RAG_DATA_DIR)

        # Scan and register models on startup
        await self._sync_models_to_db()

        # Initialize MCP infrastructure for agentic AI
        if MCP_ENABLED:
            await self._setup_mcp()

        self._healthy = True
        if self.bus:
            self._unsubscribe = self.bus.subscribe("ai/inference/request", self._on_request)

    async def _setup_mcp(self) -> None:
        """Initialize MCP servers and agent controller."""
        logger.info("Initializing MCP infrastructure...")

        # Create MCP manager
        self._mcp = MCPManager()

        # Load server configurations
        if MCP_CONFIG_PATH.exists():
            configs = load_mcp_config(MCP_CONFIG_PATH)
            logger.info(f"Loaded {len(configs)} MCP server configurations")
        else:
            logger.warning(f"MCP config not found at {MCP_CONFIG_PATH}, using defaults")
            from .mcp.config import get_default_configs

            configs = get_default_configs()

        # Connect to MCP servers
        connected = await self._mcp.connect_all(configs)
        logger.info(f"Connected to {connected} MCP servers")

        # Get LLM runner for agent
        from .models.runtime import registry as model_registry

        phi3_runner = model_registry.get("phi3-mini")

        # Create agent controller with LLM functions
        generate_with_tools = getattr(phi3_runner, "generate_with_tools", None)
        generate_final_response = getattr(phi3_runner, "generate_final_response", None)

        if phi3_runner and generate_with_tools and generate_final_response:
            self._agent = AgentController(
                mcp_manager=self._mcp,
                llm_generate=generate_with_tools,
                llm_final_response=generate_final_response,
            )
            logger.info("Agent controller initialized with LLM support")
        else:
            self._agent = AgentController(mcp_manager=self._mcp)
            logger.warning("Agent controller initialized without LLM support")

        # Log available tools
        tools = self._mcp.list_tools()
        logger.info(f"MCP ready with {len(tools)} tools available")

    async def _sync_models_to_db(self) -> None:
        """Scan model directory and sync to database on startup."""
        if not self._db:
            return

        # Load or create registry
        registry: dict[str, Any] = {}
        if REGISTRY_FILE.exists():
            try:
                with open(REGISTRY_FILE) as f:
                    registry = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load model registry: {e}")
                registry = {"models": {}, "active": {"language": None, "vision": None}}

        models = registry.get("models", {})

        # Scan language models (GGUF)
        lang_dir = MODEL_DIR / "language"
        if lang_dir.exists():
            for model_file in lang_dir.glob("*.gguf"):
                model_id = model_file.stem.replace(".", "-").lower()
                if model_id not in models:
                    size_mb = round(model_file.stat().st_size / (1024 * 1024), 1)
                    models[model_id] = {
                        "id": model_id,
                        "type": "language",
                        "name": model_file.stem,
                        "format": "gguf",
                        "path": str(model_file),
                        "size_mb": size_mb,
                    }
                    logger.info(f"Detected language model: {model_id} ({size_mb} MB)")

        # Scan vision models (TFLite)
        vision_dir = MODEL_DIR / "vision"
        if vision_dir.exists():
            for model_file in vision_dir.glob("*.tflite"):
                model_id = model_file.stem.replace(".", "-").replace("_", "-").lower()
                if model_id not in models:
                    size_mb = round(model_file.stat().st_size / (1024 * 1024), 1)
                    models[model_id] = {
                        "id": model_id,
                        "type": "vision",
                        "name": model_file.stem,
                        "format": "tflite",
                        "path": str(model_file),
                        "size_mb": size_mb,
                    }
                    logger.info(f"Detected vision model: {model_id} ({size_mb} MB)")

        # Update registry
        registry["models"] = models

        # Set default active models if none set
        if not registry.get("active", {}).get("language"):
            for mid, info in models.items():
                if info.get("type") == "language":
                    registry.setdefault("active", {})["language"] = mid
                    break

        if not registry.get("active", {}).get("vision"):
            for mid, info in models.items():
                if info.get("type") == "vision":
                    registry.setdefault("active", {})["vision"] = mid
                    break

        # Save registry
        REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(REGISTRY_FILE, "w") as f:
            json.dump(registry, f, indent=2)

        # Sync to database
        for model_id, info in models.items():
            try:
                await self._db.add_model(
                    model_id=model_id,
                    model_type=info.get("type", "unknown"),
                    name=info.get("name", model_id),
                    fmt=info.get("format", "unknown"),
                    path=info.get("path", ""),
                    size_mb=info.get("size_mb", 0),
                )
                # Set active status
                active = registry.get("active", {})
                if active.get(info.get("type")) == model_id:
                    await self._db.set_model_active(model_id, info.get("type", "unknown"))
            except Exception as e:
                logger.warning(f"Failed to sync model {model_id} to database: {e}")

        logger.info(f"Synced {len(models)} models to database")

    async def _run(self) -> None:
        # Event-driven; idle loop to allow graceful stop
        while not self.should_stop():
            await asyncio.sleep(self._idle_sleep_s)

    async def _cleanup(self) -> None:
        self._healthy = False
        if self._unsubscribe:
            try:
                self._unsubscribe()
            finally:
                self._unsubscribe = None

        # Close MCP connections
        if self._mcp:
            try:
                await self._mcp.close_all()
                logger.info("MCP servers closed")
            except Exception as e:
                logger.error(f"Error closing MCP servers: {e}")
            self._mcp = None
            self._agent = None

        if self._db:
            await self._db.close()

    def is_healthy(self) -> bool:
        return self._healthy

    def _on_request(self, topic: str, payload: bytes) -> None:
        # Parse, preprocess, run inference, publish response (fire-and-forget)
        if not self.bus:
            return
        bus = self.bus
        try:
            req = AIInferenceRequest.model_validate_json(payload.decode("utf-8"))
        except Exception:
            # Ignore malformed requests
            return

        async def _process() -> None:
            try:
                pre = preprocess_for_inference(req)
                resp = run_inference(req, pre, response_source=self._response_source)

                # Add safety warnings for critical topics
                if resp.success and resp.results:
                    query_text = req.prompt if hasattr(req, "prompt") else ""
                    for result in resp.results:
                        if hasattr(result, "text") and result.text:
                            result.text = add_safety_warning(result.text, query_text)

            except PreprocessingError as exc:
                from device.libs.schemas.ai import AIInferenceResponse

                # Return a structured failure response when preprocessing fails
                resp = AIInferenceResponse(
                    source=self._response_source,
                    request_id=req.msg_id,
                    inference_type=req.inference_type,
                    model_id=req.model_id,
                    results=[],
                    processing_time_ms=0,
                    success=False,
                    error_message=str(exc),
                )
            assert bus is not None
            await bus.publish("ai/inference/response", resp.model_dump_json())

        asyncio.create_task(_process())
