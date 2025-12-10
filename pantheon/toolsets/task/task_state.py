"""Task state management for Modal Workflow System."""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TaskInfo:
    """Current task information."""
    name: str
    mode: str  # PLANNING | EXECUTION | VERIFICATION
    status: str
    summary: str


@dataclass
class ConversationState:
    """Workflow state tracking for ephemeral message generation.
    
    Tracks artifacts, current task, and counters for generating
    contextual ephemeral reminders injected before each LLM call.
    """
    
    # Artifact tracking
    created_artifacts: list[str] = field(default_factory=list)
    artifact_last_access: dict[str, int] = field(default_factory=dict)  # path -> step count
    
    # Task tracking
    active_task: Optional[TaskInfo] = None
    task_boundary_reason: str = "a task boundary has never been set yet"
    
    # Counter tracking
    tools_since_boundary: int = 0
    tools_since_update: int = 0
    current_step: int = 0
    
    # Conditional flags
    plan_edited_in_planning: bool = False
    pending_review_paths: list[str] = field(default_factory=list)
    
    def on_task_boundary(self, name: str, mode: str, status: str, summary: str):
        """Called when task_boundary tool is invoked."""
        self.active_task = TaskInfo(name=name, mode=mode, status=status, summary=summary)
        self.tools_since_boundary = 0
        self.tools_since_update = 0
        self.task_boundary_reason = ""
        
    def on_notify_user(self, paths: list[str]):
        """Called when notify_user tool is invoked."""
        self.pending_review_paths = paths
        self.active_task = None
        self.task_boundary_reason = "there has been a notify_user action since the last task boundary"
        
    def on_artifact_created(self, path: str):
        """Track artifact creation."""
        if path not in self.created_artifacts:
            self.created_artifacts.append(path)
        self.artifact_last_access[path] = self.current_step
        
    def on_artifact_modified(self, path: str):
        """Track artifact modification/access."""
        self.artifact_last_access[path] = self.current_step
        # Check if plan edited in PLANNING mode
        if "plan" in path and self.active_task and self.active_task.mode == "PLANNING":
            self.plan_edited_in_planning = True
            
    def on_tool_call(self, count: int = 1):
        """Update counters after tool execution."""
        self.tools_since_boundary += count
        self.tools_since_update += count
        self.current_step += count
