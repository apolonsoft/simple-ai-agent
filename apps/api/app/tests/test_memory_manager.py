# app/tests/test_memory_manager.py
import datetime
import uuid

from app.models.chat import ChatMessageModel
from app.services.memory_manager import DEFAULT_SYSTEM_PROMPT, MemoryManager


def test_memory_manager_builds_default_context():
    manager = MemoryManager(window_size=5)
    context = manager.build_context(
        history=[],
        new_user_message="Hello AI!",
    )

    assert len(context) == 2
    assert context[0].role == "system"
    assert context[0].content == DEFAULT_SYSTEM_PROMPT
    assert context[1].role == "user"
    assert context[1].content == "Hello AI!"


def test_memory_manager_custom_system_prompt():
    manager = MemoryManager(window_size=5)
    custom_prompt = "You are a Python programming mentor."
    context = manager.build_context(
        history=[],
        new_user_message="Teach me decorators.",
        custom_system_prompt=custom_prompt,
    )

    assert context[0].role == "system"
    assert context[0].content == custom_prompt


def test_memory_manager_sliding_window_trims_oldest():
    manager = MemoryManager(window_size=4)
    session_id = uuid.uuid4()
    now = datetime.datetime.now(datetime.timezone.utc)

    # 6 historical messages (turn 1, 2, 3)
    history = [
        ChatMessageModel(
            id=uuid.uuid4(),
            session_id=session_id,
            role="user",
            content="Turn 1 User",
            created_at=now,
        ),
        ChatMessageModel(
            id=uuid.uuid4(),
            session_id=session_id,
            role="assistant",
            content="Turn 1 Bot",
            created_at=now,
        ),
        ChatMessageModel(
            id=uuid.uuid4(),
            session_id=session_id,
            role="user",
            content="Turn 2 User",
            created_at=now,
        ),
        ChatMessageModel(
            id=uuid.uuid4(),
            session_id=session_id,
            role="assistant",
            content="Turn 2 Bot",
            created_at=now,
        ),
        ChatMessageModel(
            id=uuid.uuid4(),
            session_id=session_id,
            role="user",
            content="Turn 3 User",
            created_at=now,
        ),
        ChatMessageModel(
            id=uuid.uuid4(),
            session_id=session_id,
            role="assistant",
            content="Turn 3 Bot",
            created_at=now,
        ),
    ]

    context = manager.build_context(history=history, new_user_message="Turn 4 User")

    # Result should be: System (1) + Last 4 history turns (Turns 2 & 3) + New User (Turn 4) = 6 messages
    assert len(context) == 6
    assert context[0].role == "system"
    # Oldest turns (Turn 1 User and Turn 1 Bot) must have been dropped
    assert context[1].content == "Turn 2 User"
    assert context[2].content == "Turn 2 Bot"
    assert context[3].content == "Turn 3 User"
    assert context[4].content == "Turn 3 Bot"
    assert context[5].content == "Turn 4 User"
