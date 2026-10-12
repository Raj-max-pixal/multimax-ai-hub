"""Source-grounded research module."""
from app.core.module_loader import ModuleInfo
from app.research.api import router

module_info = ModuleInfo(name="research", package="app.research", dependencies=["auth"], enabled=True)


def register(app, container):
    app.include_router(router)
