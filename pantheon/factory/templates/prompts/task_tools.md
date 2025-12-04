---
id: task_tools
name: Task Tools
description: Task tracking tools usage guide
---

## Task Tracking Tools

**Workflow**:
1. `create_task(title, description, initial_todos=["Step 1", "Step 2", ...])` - Returns todos with IDs
2. `manage_task(update_todos=[...], add_todos=[...], remove_todos=[...])`
   - `update_todos`: `[{"id": "todo_id", "status": "in_progress/completed"}]` - Change todo status
   - `add_todos`: `["New step"]` - Add todos
   - `remove_todos`: `["todo_id"]` - Remove todos
3. `list_tasks()` - Get detailed tasks
4. `complete_task()` - Mark entire task as done

**Todo states**: pending → in_progress → completed

**Best practices**:
- Update todo status, don't add completion todos
- Report execution details in messages, not in todos
