"""Tests for Modal Workflow TaskToolSet."""
import pytest
import asyncio
from pathlib import Path

# Direct imports to test each component
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestConversationState:
    """Test ConversationState dataclass."""
    
    def test_initial_state(self):
        from pantheon.toolsets.task.task_state import ConversationState
        state = ConversationState()
        
        assert state.active_task is None
        assert state.created_artifacts == []
        assert state.tools_since_boundary == 0
        assert state.current_step == 0
        
    def test_on_task_boundary(self):
        from pantheon.toolsets.task.task_state import ConversationState
        state = ConversationState()
        
        state.on_task_boundary("Test Task", "PLANNING", "Looking for files", "Started.")
        
        assert state.active_task is not None
        assert state.active_task.name == "Test Task"
        assert state.active_task.mode == "PLANNING"
        assert state.tools_since_boundary == 0
        
    def test_on_tool_call(self):
        from pantheon.toolsets.task.task_state import ConversationState
        state = ConversationState()
        
        state.on_tool_call(3)
        assert state.tools_since_boundary == 3
        assert state.current_step == 3
        
        state.on_tool_call(2)
        assert state.tools_since_boundary == 5
        assert state.current_step == 5
        
    def test_on_artifact_created(self):
        from pantheon.toolsets.task.task_state import ConversationState
        state = ConversationState()
        
        state.on_artifact_created("/path/to/task.md")
        assert "/path/to/task.md" in state.created_artifacts
        assert state.artifact_last_access["/path/to/task.md"] == 0
        
    def test_on_notify_user(self):
        from pantheon.toolsets.task.task_state import ConversationState
        state = ConversationState()
        
        state.on_task_boundary("Test", "PLANNING", "Status", "Summary")
        state.on_notify_user(["/path/to/plan.md"])
        
        assert state.active_task is None
        assert state.pending_review_paths == ["/path/to/plan.md"]


class TestEphemeralMessage:
    """Test ephemeral message generation."""
    
    def test_no_artifacts_no_task(self):
        from pantheon.toolsets.task.task_state import ConversationState
        from pantheon.toolsets.task.ephemeral import generate_ephemeral_message
        
        state = ConversationState()
        msg = generate_ephemeral_message(state, ".pantheon/brain/test")
        
        assert "<EPHEMERAL_MESSAGE>" in msg
        assert "<artifact_reminder>" in msg
        assert "<no_active_task_reminder>" in msg
        assert "You have not yet created any artifacts" in msg
        
    def test_with_task(self):
        from pantheon.toolsets.task.task_state import ConversationState
        from pantheon.toolsets.task.ephemeral import generate_ephemeral_message
        
        state = ConversationState()
        state.on_task_boundary("Test Task", "EXECUTION", "Building", "Completed design.")
        
        msg = generate_ephemeral_message(state, ".pantheon/brain/test")
        
        assert "<active_task_reminder>" in msg
        assert "Test Task" in msg
        assert "EXECUTION" in msg
        assert "<no_active_task_reminder>" not in msg
        
    def test_stale_artifact_reminder(self):
        from pantheon.toolsets.task.task_state import ConversationState
        from pantheon.toolsets.task.ephemeral import generate_ephemeral_message
        
        state = ConversationState()
        state.on_artifact_created("/path/to/old.md")
        state.on_tool_call(15)  # Make it stale (> 10 steps)
        
        msg = generate_ephemeral_message(state, ".pantheon/brain/test")
        
        assert "<artifact_file_reminder>" in msg
        assert "/path/to/old.md" in msg


class TestTaskToolSet:
    """Test TaskToolSet integration."""
    
    @pytest.mark.asyncio
    async def test_task_boundary_tool(self):
        from pantheon.toolsets.task.task_toolset import TaskToolSet
        
        ts = TaskToolSet()
        result = await ts.task_boundary(
            TaskName="Test",
            Mode="PLANNING",
            TaskSummary="Testing",
            TaskStatus="Running test",
            PredictedTaskSize=5
        )
        
        assert result["success"] is True
        assert result["mode"] == "PLANNING"
        assert ts.state.active_task.name == "Test"
        
    @pytest.mark.asyncio
    async def test_same_substitution(self):
        from pantheon.toolsets.task.task_toolset import TaskToolSet
        
        ts = TaskToolSet()
        await ts.task_boundary("Initial", "PLANNING", "Summary", "Status", 5)
        
        result = await ts.task_boundary("%SAME%", "%SAME%", "New summary", "%SAME%", 3)
        
        assert result["task"] == "Initial"
        assert result["mode"] == "PLANNING"
        
    @pytest.mark.asyncio
    async def test_notify_user_interrupt(self):
        from pantheon.toolsets.task.task_toolset import TaskToolSet
        
        ts = TaskToolSet()
        result = await ts.notify_user(
            PathsToReview=["/path/to/plan.md"],
            BlockedOnUser=True,
            Message="Please review",
            ConfidenceJustification="All No",
            ConfidenceScore=0.9
        )
        
        assert result["success"] is True
        assert result["interrupt"] is True
        
    def test_get_ephemeral_prompt(self):
        from pantheon.toolsets.task.task_toolset import TaskToolSet
        
        ts = TaskToolSet()
        eu = ts.get_ephemeral_prompt({"client_id": "test123"})
        
        assert eu["role"] == "user"
        assert "<EPHEMERAL_MESSAGE>" in eu["content"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
