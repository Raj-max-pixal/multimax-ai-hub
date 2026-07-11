"""
Module Loader.

Provides dynamic discovery and loading of domain modules.
Each module is a self-contained subpackage with its own models,
services, and API routes. Modules register themselves with the
application via a standard interface.
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil
from typing import Any, Dict, List, Optional, Set, Type

from app.core.logger import get_logger

logger = get_logger("app.core.module_loader")


class ModuleInfo:
    """Metadata about a registered module."""

    def __init__(
        self,
        name: str,
        package: str,
        description: str = "",
        version: str = "0.1.0",
        dependencies: List[str] = None,
        enabled: bool = True,
    ):
        self.name = name
        self.package = package
        self.description = description
        self.version = version
        self.dependencies = dependencies or []
        self.enabled = enabled

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "package": self.package,
            "description": self.description,
            "version": self.version,
            "dependencies": self.dependencies,
            "enabled": self.enabled,
        }


class ModuleInterface:
    """Interface that all domain modules must implement.

    Each module must define a 'module_info' attribute and a 'register' function.
    """

    module_info: ModuleInfo

    @staticmethod
    def register(app: Any, container: Any) -> None:
        """Register the module with the FastAPI application and DI container.

        Args:
            app: FastAPI application instance.
            container: DI container instance.
        """
        raise NotImplementedError("Modules must implement register()")


class ModuleLoader:
    """Discovers and loads domain modules.

    Usage:
        loader = ModuleLoader()
        loader.discover("app.modules")
        loader.load_all(app, container)
    """

    def __init__(self):
        self._modules: Dict[str, ModuleInfo] = {}
        self._loaded: Set[str] = set()
        self._failed: Dict[str, str] = {}

    def discover(self, base_package: str) -> List[ModuleInfo]:
        """Discover available modules in a package.

        Scans the base_package for subpackages that inherit from ModuleInterface.

        Args:
            base_package: Dot-notation package path (e.g., 'app.modules').

        Returns:
            List of discovered module information.
        """
        discovered: List[ModuleInfo] = []

        try:
            package = importlib.import_module(base_package)
            package_path = getattr(package, "__path__", [])

            for finder, name, is_pkg in pkgutil.iter_modules(package_path):
                if not is_pkg:
                    continue

                full_name = f"{base_package}.{name}"
                try:
                    module = importlib.import_module(full_name)

                    # Check if module has ModuleInterface
                    if hasattr(module, "module_info"):
                        info = module.module_info
                        self._modules[info.name] = info
                        discovered.append(info)
                        logger.info(f"Discovered module: {info.name} ({full_name})")

                except Exception as e:
                    logger.warning(f"Failed to load module {full_name}: {e}")
                    self._failed[full_name] = str(e)

        except ImportError as e:
            logger.warning(f"Could not discover modules in {base_package}: {e}")

        return discovered

    def load_module(self, module_name: str, app: Any, container: Any) -> bool:
        """Load and register a specific module.

        Args:
            module_name: Name of the module (from ModuleInfo.name).
            app: FastAPI application instance.
            container: DI container instance.

        Returns:
            True if module loaded successfully, False otherwise.
        """
        if module_name in self._loaded:
            logger.warning(f"Module already loaded: {module_name}")
            return True

        info = self._modules.get(module_name)
        if not info:
            logger.error(f"Module not found: {module_name}")
            return False

        try:
            module = importlib.import_module(info.package)
            if hasattr(module, "register"):
                module.register(app, container)
                self._loaded.add(module_name)
                logger.info(f"Loaded module: {module_name}")
                return True
            else:
                logger.error(f"Module {module_name} has no register() function")
                return False

        except Exception as e:
            logger.error(f"Failed to load module {module_name}: {e}")
            self._failed[module_name] = str(e)
            return False

    def load_all(self, app: Any, container: Any) -> Dict[str, bool]:
        """Load all discovered modules.

        Args:
            app: FastAPI application instance.
            container: DI container instance.

        Returns:
            Dict mapping module names to load success status.
        """
        results: Dict[str, bool] = {}
        for name in self._modules:
            results[name] = self.load_module(name, app, container)
        return results

    def get_module(self, name: str) -> Optional[ModuleInfo]:
        """Get information about a module."""
        return self._modules.get(name)

    def get_all_modules(self) -> List[ModuleInfo]:
        """Get all discovered modules."""
        return list(self._modules.values())

    def enable_module(self, name: str) -> bool:
        """Enable a module."""
        if name in self._modules:
            self._modules[name].enabled = True
            return True
        return False

    def disable_module(self, name: str) -> bool:
        """Disable a module."""
        if name in self._modules:
            self._modules[name].enabled = False
            return True
        return False