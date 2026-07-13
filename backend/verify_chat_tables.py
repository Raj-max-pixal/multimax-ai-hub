"""
Verification script for Chat Database tables and model integrity.
Run this after implementing Phase 1 Step 1 to confirm everything is working.
"""

import sys
import asyncio
import sqlite3
from pathlib import Path

# Ensure backend is on the path
sys.path.insert(0, str(Path(__file__).parent))


async def verify_database():
    """Verify that all chat tables were created and models are correct."""
    from app.core.config import get_settings
    from app.core.database import DatabaseManager

    settings = get_settings()
    db = DatabaseManager(settings)

    print("=" * 60)
    print("Chat Database Verification")
    print("=" * 60)

    # Initialize database
    await db.initialize()
    await db.create_all()
    print("\n[✓] Database initialized and tables created")

    # Verify tables exist
    db_path = Path(__file__).parent.parent / "data" / "multimax.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tables = [row[0] for row in cursor.fetchall()]
    print(f"\n[✓] All tables in database: {tables}")

    expected_chat_tables = {"chat_sessions", "messages", "attachments"}
    for table in expected_chat_tables:
        assert table in tables, f"Missing table: {table}"
        print(f"    - {table}: FOUND")

    # Verify table schemas
    print("\n--- Chat Sessions Schema ---")
    cursor = conn.execute("PRAGMA table_info(chat_sessions)")
    for col in cursor.fetchall():
        print(f"  {col[1]:25s} {col[2]:15s} nullable={not col[3]} default={col[4]}")

    print("\n--- Messages Schema ---")
    cursor = conn.execute("PRAGMA table_info(messages)")
    for col in cursor.fetchall():
        print(f"  {col[1]:25s} {col[2]:15s} nullable={not col[3]} default={col[4]}")

    print("\n--- Attachments Schema ---")
    cursor = conn.execute("PRAGMA table_info(attachments)")
    for col in cursor.fetchall():
        print(f"  {col[1]:25s} {col[2]:15s} nullable={not col[3]} default={col[4]}")

    conn.close()

    # Verify relationships
    from app.chat.models import ChatSession, Message, Attachment, MessageRole
    from app.workspace.models import Workspace

    assert hasattr(ChatSession, "messages")
    assert hasattr(ChatSession, "workspace")
    assert hasattr(Message, "session")
    assert hasattr(Message, "attachments")
    assert hasattr(Attachment, "message")

    rel = Workspace.__mapper__.relationships.get("chat_sessions")
    assert rel is not None

    print("\n[✓] All bidirectional relationships verified")

    # Verify soft delete
    assert hasattr(ChatSession, "deleted_at")
    print("[✓] Soft delete field (deleted_at) present on ChatSession")

    await db.close()

    print("\n" + "=" * 60)
    print("ALL VERIFICATIONS PASSED")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = asyncio.run(verify_database())
    sys.exit(0 if success else 1)