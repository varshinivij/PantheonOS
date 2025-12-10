"""Ephemeral message generator for Modal Workflow System."""
from .task_state import ConversationState


def generate_ephemeral_message(state: ConversationState, brain_dir: str) -> str:
    """Generate EPHEMERAL_MESSAGE based on current state.
    
    Args:
        state: Current conversation state
        brain_dir: Path to the brain directory for artifacts
        
    Returns:
        XML-formatted ephemeral message content
    """
    parts = []
    
    # 1. artifact_reminder (always included)
    if state.created_artifacts:
        parts.append(f"""<artifact_reminder>
You have created the following artifacts:
{chr(10).join(state.created_artifacts)}
CRITICAL REMINDER: artifacts should be AS CONCISE AS POSSIBLE.
</artifact_reminder>""")
    else:
        parts.append(f"""<artifact_reminder>
You have not yet created any artifacts. 
Artifacts should be written to: {brain_dir}
</artifact_reminder>""")
    
    # 2. Task state reminder (mutually exclusive)
    if state.active_task:
        t = state.active_task
        parts.append(f"""<active_task_reminder>
Current task: task_name:"{t.name}" mode:{t.mode}
task_status:"{t.status}" task_summary:"{t.summary}"
Tools since last update: {state.tools_since_update}
YOUR CURRENT MODE IS: {t.mode}. Embody this mindset.
REMEMBER: user WILL NOT SEE your messages. Use notify_user to communicate.
</active_task_reminder>""")
    else:
        parts.append(f"""<no_active_task_reminder>
You are not in a task because: {state.task_boundary_reason}
For simple requests (explaining code, single-file edits), no task is needed.
For complex work, create task.md first, then call task_boundary.
Do NOT call notify_user unless requesting file review.
</no_active_task_reminder>""")
    
    # 3. Conditional reminders
    if state.active_task and state.active_task.mode == "PLANNING" and state.plan_edited_in_planning:
        parts.append("""<planning_mode_plan_edited_reminder>
You modified plan.md in PLANNING mode. Request user review via notify_user before EXECUTION.
</planning_mode_plan_edited_reminder>""")
    
    if state.pending_review_paths and not state.active_task:
        parts.append("""<requested_review_not_in_planning_mode_reminder>
You used notify_user but haven't set task_boundary since.
Either: (1) Enter PLANNING to update plan, or (2) Enter EXECUTION to implement.
</requested_review_not_in_planning_mode_reminder>""")
    
    # 4. Artifact access reminder (stale artifacts)
    STALE_THRESHOLD = 10
    stale_artifacts = [
        path for path, last_step in state.artifact_last_access.items()
        if state.current_step - last_step > STALE_THRESHOLD
    ]
    if stale_artifacts:
        artifact_lines = [
            f"- {p} (last access: {state.current_step - state.artifact_last_access[p]} steps ago)"
            for p in stale_artifacts
        ]
        parts.append(f"""<artifact_file_reminder>
You have not accessed these files recently:
{chr(10).join(artifact_lines)}
</artifact_file_reminder>""")
    
    return f"<EPHEMERAL_MESSAGE>\n{chr(10).join(parts)}\n</EPHEMERAL_MESSAGE>"
