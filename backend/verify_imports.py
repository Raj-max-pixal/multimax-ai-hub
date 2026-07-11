"""Quick sanity check that all module imports work correctly."""
import sys
sys.path.insert(0, '.')

try:
    from app.core.container import Container
    from app.core.events import EventBus
    from app.core.config import AppConfig
    from app.core.logger import setup_logger, get_logger
    from app.core.database import DatabaseManager, get_session
    from app.core.exceptions import (
        AppException,
        NotFoundError,
        ValidationError,
        ConfigurationError,
        DatabaseError,
        AuthenticationError,
        AuthorizationError,
    )
    from app.core.module_loader import ModuleLoader
    from app.core.plugin_manager import PluginManager
    from app.shared.interfaces import (
        BaseRepository,
        BaseService,
    )
    from app.workspace.models import (
        Workspace,
        Project,
        WorkspaceMember,
        ProjectSettings,
    )
    from app.workspace.service import WorkspaceService
    from app.workspace.api import router as workspace_router
    print("✅ All imports successful!")
    sys.exit(0)
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)