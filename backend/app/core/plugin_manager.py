"""
Plugin Manager.

Provides the foundation for the Phase 11 Plugin Marketplace.
Manages plugin discovery, installation, lifecycle, and MCP server integration.
Implementation details deferred to Phase 11, with only the interface
and scaffolding built in Phase 0.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from datetime import datetime, timezone

from app.core.logger import get_logger

logger = get_logger("app.core.plugin_manager")


class PluginType(Enum):
    """Types of plugins supported by the system."""
    MCP_SERVER = "mcp_server"
    PROMPT_TEMPLATE = "prompt_template"
    AI_PROVIDER = "ai_provider"
    TOOL = "tool"
    UI_WIDGET = "ui_widget"
    WORKFLOW_NODE = "workflow_node"
    STORAGE_BACKEND = "storage_backend"
    AUTH_PROVIDER = "auth_provider"


class PluginStatus(Enum):
    DISABLED = "disabled"
    ENABLED = "enabled"
    ERROR = "error"
    INCOMPATIBLE = "incompatible"


@dataclass
class PluginManifest:
    """Plugin manifest file structure."""
    id: str
    name: str
    version: str
    plugin_type: PluginType
    description: str = ""
    author: str = ""
    license: str = ""
    homepage: str = ""
    min_app_version: str = "0.1.0"
    dependencies: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    entrypoint: str = ""
    mcp_config: Optional[Dict[str, Any]] = None


@dataclass
class Plugin:
    """Runtime representation of an installed plugin."""
    manifest: PluginManifest
    status: PluginStatus = PluginStatus.DISABLED
    installed_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    config: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.manifest.id,
            "name": self.manifest.name,
            "version": self.manifest.version,
            "type": self.manifest.plugin_type.value,
            "description": self.manifest.description,
            "author": self.manifest.author,
            "license": self.manifest.license,
            "status": self.status.value,
            "installed_at": self.installed_at,
            "updated_at": self.updated_at,
            "config": self.config,
        }


class PluginInterface(ABC):
    """Interface that all plugins must implement."""

    @abstractmethod
    def initialize(self, plugin_manager: PluginManager) -> None:
        """Initialize the plugin with access to the plugin manager."""
        ...

    @abstractmethod
    def get_manifest(self) -> PluginManifest:
        """Return the plugin's manifest."""
        ...

    @abstractmethod
    def on_enable(self) -> None:
        """Called when the plugin is enabled."""
        ...

    @abstractmethod
    def on_disable(self) -> None:
        """Called when the plugin is disabled."""
        ...


class PluginManager:
    """Manages plugin lifecycle.

    Phase 0: Interface and scaffolding only.
    Phase 11: Full implementation with marketplace support.

    Usage:
        plugin_manager = PluginManager()
        plugin_manager.discover_plugins()
        plugin_manager.enable_plugin("plugin-id")
        plugin_manager.disable_plugin("plugin-id")
    """

    def __init__(self):
        self._plugins: Dict[str, Plugin] = {}
        self._plugin_instances: Dict[str, PluginInterface] = {}
        self._mcp_configs: Dict[str, Dict[str, Any]] = {}

    def register_plugin(self, plugin_instance: PluginInterface) -> str:
        """Register a plugin instance.

        Args:
            plugin_instance: Plugin implementing PluginInterface.

        Returns:
            Plugin ID string.
        """
        manifest = plugin_instance.get_manifest()
        plugin = Plugin(manifest=manifest)
        self._plugins[manifest.id] = plugin
        self._plugin_instances[manifest.id] = plugin_instance

        # Store MCP configuration if provided
        if manifest.mcp_config:
            self._mcp_configs[manifest.id] = manifest.mcp_config

        logger.info(f"Plugin registered: {manifest.name} v{manifest.version}")
        return manifest.id

    def unregister_plugin(self, plugin_id: str) -> bool:
        """Unregister a plugin.

        Args:
            plugin_id: The plugin's unique identifier.

        Returns:
            True if successfully unregistered.
        """
        if plugin_id not in self._plugins:
            logger.warning(f"Plugin not found: {plugin_id}")
            return False

        # Disable first if enabled
        if self._plugins[plugin_id].status == PluginStatus.ENABLED:
            self.disable_plugin(plugin_id)

        del self._plugins[plugin_id]
        self._plugin_instances.pop(plugin_id, None)
        self._mcp_configs.pop(plugin_id, None)

        logger.info(f"Plugin unregistered: {plugin_id}")
        return True

    def enable_plugin(self, plugin_id: str) -> bool:
        """Enable a plugin.

        Args:
            plugin_id: The plugin's unique identifier.

        Returns:
            True if successfully enabled.
        """
        if plugin_id not in self._plugins:
            logger.warning(f"Plugin not found: {plugin_id}")
            return False

        plugin = self._plugins[plugin_id]
        instance = self._plugin_instances.get(plugin_id)

        try:
            if instance:
                instance.on_enable()
            plugin.status = PluginStatus.ENABLED
            plugin.updated_at = datetime.now(timezone.utc).isoformat()
            logger.info(f"Plugin enabled: {plugin_id}")
            return True
        except Exception as e:
            plugin.status = PluginStatus.ERROR
            logger.error(f"Failed to enable plugin {plugin_id}: {e}")
            return False

    def disable_plugin(self, plugin_id: str) -> bool:
        """Disable a plugin.

        Args:
            plugin_id: The plugin's unique identifier.

        Returns:
            True if successfully disabled.
        """
        if plugin_id not in self._plugins:
            logger.warning(f"Plugin not found: {plugin_id}")
            return False

        plugin = self._plugins[plugin_id]
        instance = self._plugin_instances.get(plugin_id)

        try:
            if instance:
                instance.on_disable()
            plugin.status = PluginStatus.DISABLED
            plugin.updated_at = datetime.now(timezone.utc).isoformat()
            logger.info(f"Plugin disabled: {plugin_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to disable plugin {plugin_id}: {e}")
            return False

    def get_plugin(self, plugin_id: str) -> Optional[Plugin]:
        """Get plugin information."""
        return self._plugins.get(plugin_id)

    def get_all_plugins(self) -> List[Plugin]:
        """Get all registered plugins."""
        return list(self._plugins.values())

    def get_plugins_by_type(self, plugin_type: PluginType) -> List[Plugin]:
        """Get all plugins of a specific type."""
        return [
            p for p in self._plugins.values()
            if p.manifest.plugin_type == plugin_type
        ]

    def get_mcp_configs(self) -> Dict[str, Dict[str, Any]]:
        """Get all MCP server configurations from plugins."""
        return dict(self._mcp_configs)

    def discover_plugins(self, plugin_dir: str) -> None:
        """Discover plugins in a directory.

        Phase 0: Stub implementation.
        Phase 11: Full directory scanning and manifest parsing.

        Args:
            plugin_dir: Directory to scan for plugins.
        """
        logger.info(f"Plugin discovery from {plugin_dir} (stub)")
        # TODO: Phase 11 implementation