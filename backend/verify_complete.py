"""Verify chat database layer is complete and app starts without errors."""
import sys
sys.path.insert(0, '.')

def test_imports():
    """Test all new modules can be imported."""
    print("Testing imports...")
    
    # Chat models
    from app.chat.models import ChatSession, Message, Attachment
    print("  ✓ Chat models imported")
    
    # Verify model attributes
    assert hasattr(ChatSession, 'workspace'), "ChatSession missing workspace relationship"
    assert hasattr(ChatSession, 'messages'), "ChatSession missing messages relationship"
    assert hasattr(Message, 'session'), "Message missing session relationship"
    assert hasattr(Message, 'attachments'), "Message missing attachments relationship"
    assert hasattr(Attachment, 'message'), "Attachment missing message relationship"
    print("  ✓ All model relationships verified")
    
    # Chat repositories
    from app.chat.repositories import ChatSessionRepository, MessageRepository, AttachmentRepository
    print("  ✓ Chat repositories imported")
    
    # Chat module
    from app.chat import __init__  # noqa
    print("  ✓ Chat module loaded")
    
    print("\n✓ All imports successful\n")

def test_app_creation():
    """Test FastAPI app can be created."""
    print("Testing app creation...")
    from app.main import create_app
    app = create_app()
    
    # Verify app has expected configuration
    assert app.title is not None, "App title missing"
    print(f"  ✓ App created: {app.title}")
    
    # Count routes (should have existing Phase 0 routes)
    routes = [r.path for r in app.routes]
    print(f"  ✓ {len(routes)} routes registered")
    
    # Verify no chat API routes were accidentally added (Step 1 constraint)
    chat_routes = [r for r in routes if 'chat' in r.lower()]
    assert len(chat_routes) == 0, f"Chat routes should not exist yet, found: {chat_routes}"
    print(f"  ✓ No chat API routes (Step 1 constraint maintained)")
    
    print("\n✓ App creation successful\n")


if __name__ == "__main__":
    print("=" * 50)
    print("Chat Database Layer - Final Verification")
    print("=" * 50)
    
    test_imports()
    test_app_creation()
    
