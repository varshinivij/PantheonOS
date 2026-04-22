"""
Heartbeat Engine for PantheonOS

Periodic agent turns in the main session so the model can surface anything
that needs attention without spamming the user.

Response contract:
- If nothing needs attention, the agent replies HEARTBEAT_OK (start or end).
- If HEARTBEAT_OK appears and the remaining content is <= ackMaxChars, the
  reply is silently dropped.
- If HEARTBEAT_OK appears in the middle of a reply it is not treated specially.
- For alerts, the agent must NOT include HEARTBEAT_OK; return only alert text.

Configuration (under agents.heartbeat in settings.json):
    every       - interval string e.g. "30m", "1h", "0m" to disable (default 30m)
    model       - optional model override
    lightContext - bool; if true, only HEARTBEAT.md is passed as context
    prompt      - override default prompt body
    ackMaxChars - max chars after HEARTBEAT_OK before it's treated as an alert
    activeHours - {start: "HH:MM", end: "HH:MM", timezone: "..."}
"""

from __future__ import annotations

import asyncio
import re
from datetime import datetime, time as dt_time
from pathlib import Path
from typing import TYPE_CHECKING

from pantheon.utils.log import logger

if TYPE_CHECKING:
    from pantheon.repl.core import Repl


HEARTBEAT_OK_TOKEN = "HEARTBEAT_OK"

DEFAULT_PROMPT = (
    "Read HEARTBEAT.md if it exists (workspace context). "
    "Follow it strictly. "
    "Do not infer or repeat old tasks from prior chats. "
    "If nothing needs attention, reply HEARTBEAT_OK."
)

_INTERVAL_RE = re.compile(
    r"(?:(\d+)\s*h)?\s*(?:(\d+)\s*m)?\s*(?:(\d+)\s*s)?", re.IGNORECASE
)


def parse_interval(s: str) -> int:
    """Parse a human interval string into seconds.

    Supported formats: "30m", "1h", "1h30m", "90s", "0m", bare integer treated as minutes.
    Returns 0 if the interval is zero or unrecognised (disables heartbeat).
    """
    if not s:
        return 0
    s = str(s).strip()
    # Bare integer → minutes
    if s.isdigit():
        return int(s) * 60

    m = _INTERVAL_RE.fullmatch(s)
    if m:
        h = int(m.group(1) or 0)
        mins = int(m.group(2) or 0)
        sec = int(m.group(3) or 0)
        total = h * 3600 + mins * 60 + sec
        return total

    # Fallback: try treating as float minutes
    try:
        return int(float(s) * 60)
    except ValueError:
        logger.warning(f"[heartbeat] Cannot parse interval '{s}', disabling heartbeat")
        return 0


def _parse_hhmm(s: str) -> dt_time:
    """Parse HH:MM into a time object. '24:00' is mapped to end-of-day sentinel."""
    if s == "24:00":
        return dt_time(23, 59, 59)
    h, m = s.split(":")
    return dt_time(int(h), int(m))


def _is_within_active_hours(active_hours: dict | None) -> bool:
    """Return True if the current wall-clock time is inside the configured window."""
    if not active_hours:
        return True

    start_str = active_hours.get("start", "00:00")
    end_str = active_hours.get("end", "24:00")
    tz_str = active_hours.get("timezone")

    try:
        if tz_str and tz_str not in ("local", "user"):
            import zoneinfo
            tz = zoneinfo.ZoneInfo(tz_str)
            now = datetime.now(tz).time()
        else:
            now = datetime.now().time()

        start = _parse_hhmm(start_str)
        end = _parse_hhmm(end_str)

        if start == end:
            return False  # Zero-width window → always outside
        if start < end:
            return start <= now < end
        # Overnight window (e.g. 22:00 – 06:00)
        return now >= start or now < end
    except Exception as exc:
        logger.debug(f"[heartbeat] active_hours check failed ({exc}), treating as always-active")
        return True


# ──────────────────────────────────────────────────────────────────────────────
# HEARTBEAT.md parsing
# ──────────────────────────────────────────────────────────────────────────────

def _parse_heartbeat_md(path: Path) -> tuple[list[dict], str]:
    """Parse HEARTBEAT.md into (tasks, extra_context).

    The optional ``tasks:`` block (YAML-like list) is extracted; the rest of
    the file is returned verbatim as extra_context.

    Task dict keys: name (str), interval (int seconds), prompt (str).
    """
    if not path.exists():
        return [], ""

    text = path.read_text(encoding="utf-8")

    # Effectively empty: only blank lines / markdown headings
    if not any(
        ln.strip() and not ln.strip().startswith("#")
        for ln in text.splitlines()
    ):
        return [], ""

    tasks: list[dict] = []
    extra_lines: list[str] = []

    lines = text.splitlines()
    i = 0
    n = len(lines)

    # Find "tasks:" block
    tasks_start = None
    for idx, line in enumerate(lines):
        if line.strip() == "tasks:":
            tasks_start = idx
            break

    if tasks_start is None:
        # No tasks block — entire file is extra context
        return [], text.strip()

    # Lines before tasks: block go to extra_context as-is (rare but valid)
    extra_lines.extend(lines[:tasks_start])

    # Parse tasks block: list items start with "- name:" (may be indented)
    i = tasks_start + 1
    current_task: dict | None = None

    while i < n:
        line = lines[i]
        stripped = line.strip()

        # Blank lines inside the block are fine
        if not stripped:
            i += 1
            continue

        # New list item
        if stripped.startswith("- name:"):
            if current_task and "name" in current_task:
                tasks.append(current_task)
            current_task = {"name": stripped[len("- name:"):].strip()}
            i += 1
            continue

        # Properties of the current task (indented or plain key: value)
        if stripped.startswith("interval:"):
            if current_task is not None:
                raw = stripped[len("interval:"):].strip()
                current_task["interval"] = parse_interval(raw)
            i += 1
            continue

        if stripped.startswith("prompt:"):
            if current_task is not None:
                current_task["prompt"] = stripped[len("prompt:"):].strip().strip('"').strip("'")
            i += 1
            continue

        # A non-empty, non-task-property, non-indented line ends the block
        if not line[0].isspace() and not stripped.startswith("-"):
            break

        # Indented but unrecognised — skip
        i += 1

    if current_task and "name" in current_task:
        tasks.append(current_task)

    # Remaining lines after the tasks block → extra context
    extra_lines.extend(lines[i:])
    extra_context = "\n".join(extra_lines).strip()
    return tasks, extra_context


# ──────────────────────────────────────────────────────────────────────────────
# Response processing
# ──────────────────────────────────────────────────────────────────────────────

def process_heartbeat_response(text: str, ack_max_chars: int = 300) -> tuple[bool, str]:
    """Analyse a heartbeat response.

    Returns (is_ok, alert_text):
        is_ok=True  → the run was acknowledged; alert_text is empty
        is_ok=False → alert_text contains the alert to surface to the user
    """
    stripped = text.strip()
    if not stripped:
        return True, ""

    # HEARTBEAT_OK at start
    if stripped.startswith(HEARTBEAT_OK_TOKEN):
        remainder = stripped[len(HEARTBEAT_OK_TOKEN):].strip()
        if len(remainder) <= ack_max_chars:
            return True, ""
        # Long remainder → treat as alert (strip token from front)
        return False, remainder

    # HEARTBEAT_OK at end
    if stripped.endswith(HEARTBEAT_OK_TOKEN):
        remainder = stripped[: -len(HEARTBEAT_OK_TOKEN)].strip()
        if len(remainder) <= ack_max_chars:
            return True, ""
        return False, remainder

    # No token → this is an alert
    return False, stripped


# ──────────────────────────────────────────────────────────────────────────────
# HeartbeatEngine
# ──────────────────────────────────────────────────────────────────────────────

class HeartbeatEngine:
    """Runs periodic agent turns for the main REPL session.

    Args:
        config:  heartbeat config dict (from settings agents.heartbeat).
        repl:    The Repl instance that owns this engine.
    """

    def __init__(self, config: dict, repl: "Repl"):
        self._repl = repl
        self._config = config

        every_raw = config.get("every", "30m")
        self.interval: int = parse_interval(str(every_raw))  # seconds
        self.enabled: bool = self.interval > 0

        self.prompt: str = config.get("prompt") or DEFAULT_PROMPT
        self.ack_max_chars: int = int(config.get("ackMaxChars", 300))
        self.active_hours: dict | None = config.get("activeHours")
        self.light_context: bool = bool(config.get("lightContext", False))
        self.model: str | None = config.get("model")

        # Alert delivery target: "console" | "ui" | "none" | <channel e.g. "telegram">
        self.target: str = config.get("target", "console")
        # Optional recipient ID (Telegram chat_id, Slack channel, ...)
        self.to: str | None = config.get("to") or None

        self._task: asyncio.Task | None = None
        self._last_run: datetime | None = None
        self._next_run: datetime | None = None
        self._run_count: int = 0
        self._skip_count: int = 0

        # Per-task state: {task_name: last_run_datetime}
        self._task_state: dict[str, datetime] = {}
        self._due_tasks_this_run: list[str] = []

    # ──────────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────────

    def start(self) -> None:
        """Start the background heartbeat loop (idempotent)."""
        if not self.enabled:
            return
        if self._task and not self._task.done():
            return
        self._seed_heartbeat_md()
        self._next_run = datetime.fromtimestamp(
            asyncio.get_event_loop().time() + self.interval
        )
        self._task = asyncio.create_task(self._loop(), name="heartbeat-loop")
        logger.info(f"[heartbeat] started, interval={self.interval}s")

    def _seed_heartbeat_md(self) -> None:
        """Write the default HEARTBEAT.md to the workspace if it doesn't exist."""
        try:
            from pantheon.settings import get_settings
            workspace = get_settings().workspace
            dest = workspace / "HEARTBEAT.md"
            if dest.exists():
                return
            template = Path(__file__).parent / "factory" / "templates" / "HEARTBEAT.md"
            if template.exists():
                dest.write_text(template.read_text(encoding="utf-8"), encoding="utf-8")
                logger.info(f"[heartbeat] created {dest}")
        except Exception as exc:
            logger.debug(f"[heartbeat] could not seed HEARTBEAT.md: {exc}")

    def stop(self) -> None:
        """Cancel the heartbeat loop."""
        if self._task and not self._task.done():
            self._task.cancel()
            self._task = None
        logger.info("[heartbeat] stopped")

    def reconfigure(self, new_config: dict) -> None:
        """Update config and restart the loop with new settings."""
        was_running = self._task and not self._task.done()
        self.stop()
        self.__init__(new_config, self._repl)
        if was_running or self.enabled:
            self.start()

    async def trigger_now(self) -> None:
        """Immediately fire a heartbeat turn (manual wake)."""
        await self._run_heartbeat()

    def status(self) -> dict:
        """Return a status snapshot."""
        return {
            "enabled": self.enabled,
            "interval_seconds": self.interval,
            "interval_human": _seconds_to_human(self.interval),
            "last_run": self._last_run.isoformat() if self._last_run else None,
            "next_run": self._next_run.isoformat() if self._next_run else None,
            "run_count": self._run_count,
            "skip_count": self._skip_count,
            "active_hours": self.active_hours,
            "light_context": self.light_context,
            "target": self.target,
            "to": self.to,
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Background loop
    # ──────────────────────────────────────────────────────────────────────────

    async def _loop(self) -> None:
        _outside_hours_logged = False
        try:
            while True:
                await asyncio.sleep(self.interval)
                self._next_run = datetime.fromtimestamp(
                    asyncio.get_event_loop().time() + self.interval
                )

                if not _is_within_active_hours(self.active_hours):
                    if not _outside_hours_logged:
                        ah = self.active_hours or {}
                        logger.info(
                            f"[heartbeat] outside active hours "
                            f"({ah.get('start','?')}–{ah.get('end','?')} "
                            f"{ah.get('timezone','local')}), skipping until window"
                        )
                        _outside_hours_logged = True
                    self._skip_count += 1
                    continue

                _outside_hours_logged = False  # Re-arm for next gap

                if self._repl._is_processing:
                    logger.debug("[heartbeat] skipped — main session is busy, will retry next tick")
                    self._skip_count += 1
                    continue

                try:
                    await self._run_heartbeat()
                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    logger.warning(f"[heartbeat] run raised an exception: {exc}", exc_info=True)
        except asyncio.CancelledError:
            pass

    # ──────────────────────────────────────────────────────────────────────────
    # Single heartbeat run
    # ──────────────────────────────────────────────────────────────────────────

    async def _run_heartbeat(self) -> None:
        """Execute one heartbeat agent turn and handle the response."""
        import time as _time

        chat_id = self._repl._chat_id
        chatroom = self._repl._chatroom

        if not chat_id or not chatroom:
            logger.debug("[heartbeat] skipped — no active chat")
            return

        # Guard: don't run if chatroom is already processing this chat
        if chat_id in chatroom.threads:
            logger.debug("[heartbeat] skipped — chat already running")
            self._skip_count += 1
            return

        prompt_text = self._build_prompt()
        if prompt_text is None:
            logger.debug("[heartbeat] skipped — empty HEARTBEAT.md / no due tasks")
            return

        run_n = self._run_count + 1
        logger.info(
            f"[heartbeat] run #{run_n} starting — "
            f"chat={chat_id} interval={_seconds_to_human(self.interval)} "
            f"prompt_chars={len(prompt_text)}"
        )

        # ── Collect streamed response + usage ──────────────────────────────────
        response_chunks: list[str] = []
        # Usage is emitted as a final chunk: {"usage": {"prompt_tokens": X, ...}}
        _usage: dict = {}

        def _on_chunk(chunk: dict) -> None:
            content = chunk.get("content")
            if content:
                response_chunks.append(content)
            if "usage" in chunk:
                _usage.update(chunk["usage"])

        message = [{"role": "user", "content": prompt_text}]

        t_start = _time.monotonic()

        # Temporarily set processing flag so normal input waits
        self._repl._is_processing = True
        try:
            result = await chatroom.chat(
                chat_id=chat_id,
                message=message,
                process_chunk=_on_chunk,
            )
        finally:
            self._repl._is_processing = False

        elapsed = _time.monotonic() - t_start
        self._last_run = datetime.now()
        self._run_count += 1

        if not (result and result.get("success", True)):
            err = result.get("message", "unknown") if result else "unknown"
            logger.warning(f"[heartbeat] run #{run_n} failed — {err}")
            return

        full_response = "".join(response_chunks).strip()
        is_ok, alert_text = process_heartbeat_response(full_response, self.ack_max_chars)

        # ── Read cost from memory (set by collect_message_stats_lightweight) ──
        cost = self._read_last_turn_cost(chat_id, chatroom)

        # ── Normalise token counts ─────────────────────────────────────────────
        prompt_tok = _usage.get("prompt_tokens", 0)
        completion_tok = _usage.get("completion_tokens", 0)
        # Some providers only emit total_tokens; fall back gracefully
        total_tok = _usage.get("total_tokens") or (prompt_tok + completion_tok)

        result_label = "OK" if is_ok else f"ALERT ({len(alert_text)} chars)"
        cost_str = f"${cost:.4f}" if cost else "n/a"

        logger.info(
            f"[heartbeat] run #{run_n} complete — "
            f"in: {prompt_tok:,} tok | out: {completion_tok:,} tok | "
            f"ctx_total: {total_tok:,} tok | cost: {cost_str} | "
            f"elapsed: {elapsed:.2f}s | result: {result_label}"
        )

        if is_ok:
            logger.debug(f"[heartbeat] run #{run_n} — HEARTBEAT_OK acknowledged")
        else:
            logger.info(f"[heartbeat] run #{run_n} — surfacing alert to user")
            self._surface_alert(alert_text)

        # Advance task last-run timestamps
        self._task_state.update(
            {name: datetime.now() for name in self._due_tasks_this_run}
        )
        self._due_tasks_this_run = []

    def _read_last_turn_cost(self, chat_id: str, chatroom) -> float:
        """Read the cost of the last completed turn from chat memory."""
        try:
            memory = chatroom.memory_manager.get_memory(chat_id)
            if not memory:
                return 0.0
            msgs = memory.get_messages(execution_context_id=None, for_llm=True)
            # Find the last assistant message with metadata
            for msg in reversed(msgs):
                if msg.get("role") == "assistant" and "_metadata" in msg:
                    return float(msg["_metadata"].get("current_cost", 0.0))
        except Exception as exc:
            logger.debug(f"[heartbeat] could not read turn cost: {exc}")
        return 0.0

    # ──────────────────────────────────────────────────────────────────────────
    # Prompt construction
    # ──────────────────────────────────────────────────────────────────────────

    def _build_prompt(self) -> str | None:
        """Build the heartbeat prompt body.

        Returns None if the run should be skipped (empty file / no due tasks).
        """
        from pantheon.settings import get_settings
        workspace = get_settings().workspace

        heartbeat_md = workspace / "HEARTBEAT.md"
        tasks, extra_context = _parse_heartbeat_md(heartbeat_md)

        self._due_tasks_this_run = []

        if tasks:
            # Task mode: only include due tasks
            now = datetime.now()
            due: list[dict] = []
            for t in tasks:
                last = self._task_state.get(t["name"])
                interval = t.get("interval", 0)
                if last is None or (now - last).total_seconds() >= interval:
                    due.append(t)
            if not due:
                return None  # No tasks due

            self._due_tasks_this_run = [t["name"] for t in due]
            task_lines = "\n".join(
                f"- {t['name']}: {t.get('prompt', '')}" for t in due
            )
            parts = [f"Due tasks:\n{task_lines}"]
            if extra_context:
                parts.append(extra_context)
            return "\n\n".join(parts)

        # No tasks block — use default or custom prompt
        if heartbeat_md.exists():
            # Append file content after the prompt
            content = heartbeat_md.read_text(encoding="utf-8").strip()
            if not content or not any(
                ln.strip() and not ln.strip().startswith("#")
                for ln in content.splitlines()
            ):
                return None  # Effectively empty
            return f"{self.prompt}\n\n---\n{content}"

        return self.prompt

    # ──────────────────────────────────────────────────────────────────────────
    # Alert surfacing — routes based on self.target
    # ──────────────────────────────────────────────────────────────────────────

    def _surface_alert(self, text: str) -> None:
        """Route a heartbeat alert to the configured target(s)."""
        ts = datetime.now().strftime("%H:%M")

        if self.target == "none":
            logger.info(f"[heartbeat] alert suppressed (target=none): {text[:80]}")
            return

        logger.info(
            f"[heartbeat] alert → target={self.target}"
            + (f" to={self.to}" if self.to else "")
            + f": {text[:120]}"
        )

        # Console output (always for console + ui targets; also on external channel
        # so the user sees it locally even while the remote delivery is async)
        if self.target in ("console", "ui"):
            self._print_to_console(text, ts)

        if self.target == "ui":
            self._deliver_to_ui(text)
        elif self.target not in ("console", "none"):
            # External channel — fire-and-forget async task
            asyncio.create_task(self._deliver_to_channel(text))

    def _print_to_console(self, text: str, ts: str) -> None:
        console = (
            self._repl.output.console
            if hasattr(self._repl, "output")
            else self._repl.console
        )
        console.print(
            f"\n[bold yellow]⚡ Heartbeat alert[/bold yellow] [dim]{ts}[/dim]"
        )
        try:
            from rich.markdown import Markdown
            console.print(Markdown(text))
        except Exception:
            console.print(text)
        console.print()

    def _deliver_to_ui(self, text: str) -> None:
        """Push alert to the ChatRoom web UI via the NATS adapter."""
        try:
            chatroom = self._repl._chatroom
            chat_id = self._repl._chat_id
            if chatroom and chat_id and chatroom._nats_adapter:
                asyncio.create_task(
                    chatroom._nats_adapter.publish(
                        chat_id,
                        "heartbeat_alert",
                        {
                            "type": "heartbeat_alert",
                            "text": text,
                            "timestamp": datetime.now().isoformat(),
                        },
                    )
                )
                logger.debug("[heartbeat] alert published to UI via NATS")
            else:
                logger.debug(
                    "[heartbeat] UI delivery skipped — NATS adapter not active; "
                    "alert already printed to console"
                )
        except Exception as exc:
            logger.debug(f"[heartbeat] UI delivery failed: {exc}")

    async def _deliver_to_channel(self, text: str) -> None:
        """Send alert to an external channel using its SDK directly."""
        ch = self.target
        to = self.to
        alert_body = f"⚡ Heartbeat alert\n\n{text}"

        try:
            from pantheon.claw.config import ClawConfigStore
            cfg = ClawConfigStore().load()

            if ch == "telegram":
                from telegram import Bot
                token = (cfg.get("telegram") or {}).get("token")
                if not token:
                    logger.warning("[heartbeat] Telegram token not configured")
                    return
                if not to:
                    logger.warning(
                        "[heartbeat] Telegram target chosen but no recipient chat_id set. "
                        "Run /heartbeat on and enter your chat_id."
                    )
                    return
                await Bot(token).send_message(chat_id=to, text=alert_body)
                logger.info(f"[heartbeat] alert delivered to Telegram chat_id={to}")

            elif ch == "slack":
                from slack_sdk.web.async_client import AsyncWebClient
                bot_token = (cfg.get("slack") or {}).get("bot_token")
                if not bot_token:
                    logger.warning("[heartbeat] Slack bot_token not configured")
                    return
                if not to:
                    logger.warning(
                        "[heartbeat] Slack target chosen but no channel set. "
                        "Run /heartbeat on and enter a channel name."
                    )
                    return
                client = AsyncWebClient(token=bot_token)
                await client.chat_postMessage(channel=to, text=alert_body)
                logger.info(f"[heartbeat] alert delivered to Slack channel={to}")

            elif ch == "discord":
                logger.warning(
                    "[heartbeat] Discord outbound delivery requires a running bot instance "
                    "and is not supported for direct heartbeat alerts. "
                    "Consider using 'console' or 'ui' as your alert target instead."
                )

            else:
                logger.warning(f"[heartbeat] Unknown external target '{ch}' — alert not delivered")

        except Exception as exc:
            logger.warning(f"[heartbeat] channel delivery to {ch} failed: {exc}")


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _seconds_to_human(seconds: int) -> str:
    if seconds == 0:
        return "disabled"
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    parts = []
    if h:
        parts.append(f"{h}h")
    if m:
        parts.append(f"{m}m")
    if s:
        parts.append(f"{s}s")
    return "".join(parts) or "0s"
