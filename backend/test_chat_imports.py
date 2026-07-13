"""Quick verification that chat module imports work correctly."""
import sys

sys.path.insert(0, ".")

try:
    from app.chat.models import ChatSession, Message, Attachment, MessageRole
    print("[OK] Models imported successfully")
except Exception as e:
    print(f"[FAIL] Models: {e}")
    sys.exit(1)

try:
    from app.chat.repositories import ChatSessionRepository, MessageRepository, AttachmentRepository
    print("[OK] Repositories imported successfully")
except Exception as e:
    print(f"[FAIL] Repositories: {e}")
    sys.exit(1)

try:
    from app.chat.schemas import (
        CreateChatSessionRequest,
        ChatSessionResponse,
        CreateMessageRequest,
        MessageResponse,
        ChatSessionListResponse,
        MessageListResponse,
        RenameChatSessionRequest,
        CreateAttachmentRequest,
        AttachmentResponse,
    )
    print("[OK] Schemas imported successfully")
except Exception as e:
    print(f"[FAIL] Schemas: {e}")
    sys.exit(1)

try:
    from app.chat import module_info, register
    print("[OK] __init__ exports imported successfully")
except Exception as e:
    print(f"[FAIL] __init__: {e}")
    sys.exit(1)

try:
    # Test the FastAPI app factory can import the module registration
    from app.main import create_app
    print("[OK] App factory imported successfully")
except Exception as e:
    print(f"[WARN] App factory import (expected if services fail): {e}")

print()
print("All chat module imports verified successfully!")