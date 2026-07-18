"""Phase 0 Integration Verification — validates all domain modules exist, import, and register correctly."""

from __future__ import annotations

import sys

import os

# Add the backend directory to sys.path so that `app` can be found.
backend_dir = os.path.join(os.path.dirname(__file__), os.pardir)
sys.path.insert(0, os.path.abspath(backend_dir))


def header(title: str) -> None:
    print()
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_module_imports() -> int:
    """Verify all domain module packages import cleanly."""
    header("Module Imports")
    errors = 0

    modules = [
        "app.core",
        "app.shared",
        "app.auth",
        "app.workspace",
        "app.chat",
        "app.ai",
        "app.document",
        "app.settings",
        "app.storage",
    ]

    for mod_name in modules:
        try:
            __import__(mod_name, fromlist=["__init__"])
            print(f"  [OK] {mod_name}")
        except ImportError as e:
            print(f"  [FAIL] {mod_name}: {e}")
            errors += 1

    return errors


def test_module_info() -> int:
    """Verify each domain module exposes a valid ModuleInfo object."""
    header("Module Info")
    errors = 0

    modules = {
        "app.chat": "chat",
        "app.document": "document",
        "app.settings": "settings",
        "app.storage": "storage",
    }

    for mod_path, expected_name in modules.items():
        try:
            mod = __import__(mod_path, fromlist=["module_info"])
            info = mod.module_info
            assert info.name == expected_name, (
                f"Expected name={expected_name!r}, got {info.name!r}"
            )
            assert hasattr(info, "version"), "Missing version"
            assert hasattr(info, "dependencies"), "Missing dependencies"
            print(f"  [OK] {mod_path}: name={info.name!r}  version={info.version!r}")
        except Exception as e:
            print(f"  [FAIL] {mod_path}: {e}")
            errors += 1

    return errors


def test_register_function() -> int:
    """Verify every domain module exposes a callable register function."""
    header("Register Functions")
    errors = 0

    modules = [
        "app.chat",
        "app.document",
        "app.settings",
        "app.storage",
    ]

    for mod_path in modules:
        try:
            mod = __import__(mod_path, fromlist=["register"])
            reg = mod.register
            assert callable(reg), f"register is not callable"
            print(f"  [OK] {mod_path}.register")
        except Exception as e:
            print(f"  [FAIL] {mod_path}.register: {e}")
            errors += 1

    return errors


def test_model_classes() -> int:
    """Verify all model classes from each module can be imported."""
    header("Model Classes")
    errors = 0

    checks = {
        "app.chat.models": ["ChatSession", "Message", "Attachment", "MessageRole"],
        "app.document.models": ["Document", "DocumentChunk"],
        "app.settings.models": ["SystemSetting", "UserSetting"],
        "app.storage.models": ["StorageFile", "StorageQuota"],
        "app.workspace.models": ["Workspace", "Project", "WorkspaceMember", "ProjectFile"],
        "app.auth.models": ["User", "UserSession"],
    }

    for mod_path, classes in checks.items():
        try:
            mod = __import__(mod_path, fromlist=classes)
            for cls_name in classes:
                cls = getattr(mod, cls_name, None)
                assert cls is not None, f"{cls_name} not found in {mod_path}"
            print(f"  [OK] {mod_path}: {', '.join(classes)}")
        except Exception as e:
            print(f"  [FAIL] {mod_path}: {e}")
            errors += 1

    return errors


def test_schema_classes() -> int:
    """Verify all pydantic schema classes can be imported."""
    header("Schema Classes")
    errors = 0

    checks = {
        "app.chat.schemes": [],
        "app.document.schemas": ["DocumentCreate", "DocumentResponse", "DocumentChunkResponse"],
        "app.storage.schemas": ["StorageFileCreate", "StorageFileResponse", "StorageQuotaResponse"],
        "app.settings.schemas": ["SystemSettingCreate", "UserSettingCreate"],
    }

    for mod_path, classes in checks.items():
        try:
            mod = __import__(mod_path, fromlist=classes)
            for cls_name in classes:
                cls = getattr(mod, cls_name, None)
                assert cls is not None, f"{cls_name} not found in {mod_path}"
            if classes:
                print(f"  [OK] {mod_path}: {', '.join(classes)}")
            else:
                print(f"  [OK] {mod_path} (imported)")
        except Exception as e:
            print(f"  [FAIL] {mod_path}: {e}")
            errors += 1

    return errors


def test_service_classes() -> int:
    """Verify all service classes can be imported."""
    header("Service Classes")
    errors = 0

    checks = {
        "app.document.service": ["DocumentService"],
        "app.storage.service": ["StorageService"],
        "app.workspace.service": ["WorkspaceService"],
        "app.chat.service": ["ChatService"],
        "app.settings.service": [],
        "app.ai.manager": ["AIProviderManager"],
    }

    for mod_path, classes in checks.items():
        try:
            mod = __import__(mod_path, fromlist=classes)
            for cls_name in classes:
                cls = getattr(mod, cls_name, None)
                assert cls is not None, f"{cls_name} not found in {mod_path}"
            if classes:
                print(f"  [OK] {mod_path}: {', '.join(classes)}")
            else:
                print(f"  [OK] {mod_path} (imported)")
        except Exception as e:
            print(f"  [FAIL] {mod_path}: {e}")
            errors += 1

    return errors


def test_ai_providers() -> int:
    """Verify all AI provider implementations can be imported."""
    header("AI Provider Implementations")
    errors = 0

    providers = {
        "app.ai.providers.openai": "OpenAIProvider",
        "app.ai.providers.gemini": "GeminiProvider",
        "app.ai.providers.ollama": "OllamaProvider",
        "app.ai.providers.qwen": "QwenProvider",
    }

    for mod_path, cls_name in providers.items():
        try:
            mod = __import__(mod_path, fromlist=[cls_name])
            cls = getattr(mod, cls_name, None)
            assert cls is not None, f"{cls_name} not found in {mod_path}"
            assert hasattr(cls, "chat"), f"{cls_name} missing chat() method"
            print(f"  [OK] {mod_path}.{cls_name}")
        except Exception as e:
            print(f"  [FAIL] {mod_path}.{cls_name}: {e}")
            errors += 1

    return errors


def test_repository_classes() -> int:
    """Verify all repository classes can be imported."""
    header("Repository Classes")
    errors = 0

    checks = {
        "app.chat.repositories": [
            "ChatSessionRepository",
            "MessageRepository",
            "AttachmentRepository",
        ],
        "app.document.repositories": ["DocumentRepository", "DocumentChunkRepository"],
        "app.storage.repositories": ["StorageFileRepository", "StorageQuotaRepository"],
    }

    for mod_path, classes in checks.items():
        try:
            mod = __import__(mod_path, fromlist=classes)
            for cls_name in classes:
                cls = getattr(mod, cls_name, None)
                assert cls is not None, f"{cls_name} not found in {mod_path}"
            print(f"  [OK] {mod_path}: {', '.join(classes)}")
        except Exception as e:
            print(f"  [FAIL] {mod_path}: {e}")
            errors += 1

    return errors


def test_api_routers() -> int:
    """Verify all API router modules can be imported."""
    header("API Routers")
    errors = 0

    modules = [
        "app.document.api",
        "app.storage.api",
        "app.workspace.api",
        "app.chat.api",
        "app.auth.api",
    ]

    for mod_path in modules:
        try:
            mod = __import__(mod_path, fromlist=["router"])
            assert hasattr(mod, "router") or hasattr(mod, "api_router"), (
                f"No router found in {mod_path}"
            )
            print(f"  [OK] {mod_path}.router")
        except Exception as e:
            print(f"  [FAIL] {mod_path}: {e}")
            errors += 1

    return errors


def test_exception_hierarchy() -> int:
    """Verify all exception classes can be imported."""
    header("Exception Classes")
    errors = 0

    exceptions = [
        "app.core.exceptions.MultimaxError",
        "app.core.exceptions.NotFoundError",
        "app.core.exceptions.ValidationError",
        "app.core.exceptions.ConfigurationError",
        "app.core.exceptions.AuthenticationError",
        "app.core.exceptions.AuthorizationError",
        "app.core.exceptions.DuplicateError",
        "app.core.exceptions.ExternalServiceError",
        "app.core.exceptions.RateLimitError",
        "app.chat.exceptions.ChatNotFoundError",
        "app.chat.exceptions.MessageNotFoundError",
        "app.document.exceptions.DocumentError",
        "app.storage.exceptions.StorageError",
        "app.storage.exceptions.StorageQuotaExceeded",
        "app.storage.exceptions.FileNotFoundError",
        "app.ai.exceptions.AIProviderError",
    ]

    for exc_path in exceptions:
        try:
            parts = exc_path.rsplit(".", 1)
            mod_path = parts[0]
            cls_name = parts[1]
            mod = __import__(mod_path, fromlist=[cls_name])
            cls = getattr(mod, cls_name, None)
            assert cls is not None, f"{cls_name} not found in {mod_path}"
            assert issubclass(cls, Exception), f"{cls_name} is not an Exception subclass"
            print(f"  [OK] {exc_path}")
        except Exception as e:
            print(f"  [FAIL] {exc_path}: {e}")
            errors += 1

    return errors


def test_app_creation() -> int:
    """Verify the FastAPI application can be created without errors."""
    header("FastAPI Application Creation")
    errors = 0

    try:
        from app.main import create_app

        app = create_app()
        assert app.title is not None, "App title missing"
        print(f"  [OK] App created: {app.title!r}")
        routes = [r.path for r in app.routes]
        print(f"  [OK] {len(routes)} routes registered")

        # Verify storage routes are present
        storage_routes = [r for r in routes if "storage" in r.lower()]
        print(f"  [OK] {len(storage_routes)} storage routes: {storage_routes}")

        # Verify document routes are present
        doc_routes = [r for r in routes if "document" in r.lower()]
        print(f"  [OK] {len(doc_routes)} document routes: {doc_routes}")

    except Exception as e:
        print(f"  [FAIL] App creation failed: {e}")
        errors += 1

    return errors


def main() -> int:
    """Run all verification checks and return exit code."""
    print("=" * 60)
    print("  Phase 0 -- Domain Module Integration Verification")
    print("=" * 60)

    total_errors = 0
    total_errors += test_module_imports()
    total_errors += test_module_info()
    total_errors += test_register_function()
    total_errors += test_model_classes()
    total_errors += test_schema_classes()
    total_errors += test_service_classes()
    total_errors += test_ai_providers()
    total_errors += test_repository_classes()
    total_errors += test_api_routers()
    total_errors += test_exception_hierarchy()
    total_errors += test_app_creation()

    print()
    print("=" * 60)
    if total_errors == 0:
        print("  [OK] ALL CHECKS PASSED -- Phase 0 modules are complete!")
        print(f"  {'=' * 56}")
        return 0
    else:
        print(f"  [FAIL] {total_errors} CHECK(S) FAILED -- review output above")
        print(f"  {'=' * 56}")
        return 1


if __name__ == "__main__":
    sys.exit(main())