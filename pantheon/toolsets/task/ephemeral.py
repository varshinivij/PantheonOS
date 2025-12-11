"""Ephemeral message generator for Modal Workflow System."""
import os
from .task_state import ConversationState, ArtifactRoles


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
    
    # 3. Plan artifact modified in plan phase reminder (semantic check)
    if state.active_task and state.active_task.is_plan_phase:
        if state.has_plan_artifacts_modified():
            plan_files = state.get_modified_artifacts_by_role("plan")
            files_str = ", ".join(os.path.basename(p) for p in plan_files)
            parts.append(f"""<plan_artifact_modified_reminder>
You modified plan artifact(s): {files_str} in {state.active_task.mode} mode.
Request user review via notify_user before proceeding to execution/analysis.
</plan_artifact_modified_reminder>""")
    
    # 4. General artifact modification reminder (non-plan phases)
    if state.active_task and not state.active_task.is_plan_phase:
        all_modified = state.get_all_modified_artifacts()
        if all_modified:
            parts.append(f"""<artifacts_modified_reminder>
You have modified {len(all_modified)} artifact(s) in this task.
Consider updating them as you progress.
</artifacts_modified_reminder>""")
    
    # 5. Pending review reminder (after notify_user, not in task)
    if state.pending_review_paths and not state.active_task:
        parts.append("""<requested_review_not_in_task_reminder>
You used notify_user but haven't set task_boundary since.
Either: (1) Enter planning mode to update plan, or (2) Enter execution mode to implement.
</requested_review_not_in_task_reminder>""")
    
    # 6. Artifact access reminder (stale artifacts)
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
