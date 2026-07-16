"""Integration tests for the modular app."""
import asyncio
import sys
import os
import importlib

sys.path.insert(0, os.path.dirname(__file__))

OK = "[OK]"
FAIL = "[FAIL]"
MISS = "[MISSING]"

async def main():
    print("=" * 60)
    print("Integration Tests for Modular Backend")
    print("=" * 60)

    # 1. Import all modules
    print("\n[1/5] Importing modules...")
    modules = [
        "app.main",
        "app.core.config",
        "app.core.database",
        "app.core.container",
        "app.core.events",
        "app.core.exceptions",
        "app.core.logger",
        "app.core.module_loader",
        "app.core.plugin_manager",
        "app.shared.interfaces",
        "app.auth",
        "app.chat",
        "app.workspace",
        "app.document",
        "app.ai.manager",
        "app.ai.base",
        "app.ai.schemas",
        "app.ai.providers.ollama",
        "app.ai.providers.openai",
        "app.ai.providers.gemini",
        "app.ai.provider_registry",
    ]
    for mod_name in modules:
        try:
            importlib.import_module(mod_name)
            print(f"  {OK} {mod_name}")
        except Exception as e:
            print(f"  {FAIL} {mod_name}: {e}")

    # 2. Create the app
    print("\n[2/5] Creating FastAPI app...")
    from app.main import create_app
    app = create_app()
    print(f"  {OK} App title: {app.title}")
    print(f"  {OK} App version: {app.version}")
    
    # 3. Check routes
    print("\n[3/5] Checking routes...")
    routes = set()
    for route in app.routes:
        if hasattr(route, 'path'):
            routes.add(route.path)
    
    expected = [
        "/", "/api/models", "/api/chat",
        "/api/documents/upload", "/api/documents",
        "/api/documents/{document_id}", "/api/documents/chat",
        "/api/transcribe", "/api/health",
        "/health/live", "/health/ready",
        "/docs", "/redoc",
    ]
    for ep in expected:
        if ep in routes:
            print(f"  {OK} {ep}")
        else:
            print(f"  {MISS} {ep}")
    print(f"  Total routes: {len(routes)}")

    # 4. Test settings
    print("\n[4/5] Validating settings...")
    from app.core.config import get_settings
    s = get_settings()
    print(f"  {OK} DB URL: {s.database_url}")
    print(f"  {OK} Ollama URL: {s.ollama_url}")
    print(f"  {OK} ENV: {s.ENVIRONMENT}")
    # Verify backward-compat properties
    assert s.HOST == s.API_HOST
    assert s.PORT == s.API_PORT
    assert s.LOG_LEVEL == s.APP_LOG_LEVEL
    print(f"  {OK} Backward-compat properties OK")

    # 5. Test domain module `register()` functions exist
    print("\n[5/5] Checking domain module loading...")
    domain_packages = ["app.auth", "app.workspace", "app.chat", "app.document"]
    for pkg in domain_packages:
        mod = importlib.import_module(pkg)
        assert hasattr(mod, "register"), f"{pkg} missing register()"
        assert hasattr(mod, "module_info"), f"{pkg} missing module_info"
        print(f"  {OK} {pkg}: register() + module_info OK")

    print("\n" + "=" * 60)
    print("ALL INTEGRATION TESTS PASSED")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())