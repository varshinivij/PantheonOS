"""
/heartbeat slash command handler + interactive setup wizard.

Usage:
    /heartbeat               — show current status
    /heartbeat on [interval] — open setup wizard (optionally specify interval)
    /heartbeat off           — disable
    /heartbeat now           — fire immediately
    /heartbeat config        — dump full config

Natural language aliases (detected by match_command):
    "develop heartbeat", "enable heartbeat", "start heartbeat",
    "setup heartbeat", "turn on heartbeat", "configure heartbeat"

Wizard flow (triggered by /heartbeat on or NL enable):
    1. Ask where alerts should be sent (console / web UI / <channel> / silent)
    2. If external channel chosen → ask for recipient ID
    3. Finalise: reconfigure engine and confirm
"""

from __future__ import annotations

import asyncio
from pantheon.repl.handlers.base import CommandHandler


_NL_ACTION_WORDS = {
    "develop", "enable", "start", "setup", "set up",
    "configure", "turn on", "activate", "create",
    "disable", "turn off", "deactivate", "stop",
}


class HeartbeatCommandHandler(CommandHandler):

    def match_command(self, command: str) -> bool:
        cmd = command.strip().lower()
        if cmd == "/heartbeat" or cmd.startswith("/heartbeat "):
            return True
        if "heartbeat" in cmd:
            for word in _NL_ACTION_WORDS:
                if word in cmd:
                    return True
        return False

    async def handle_command(self, command: str) -> str | None:
        engine = getattr(self.parent, "_heartbeat_engine", None)
        cmd = command.strip()
        cmd_lower = cmd.lower()

        # ── Natural language ──────────────────────────────────────────────────
        if not cmd_lower.startswith("/heartbeat"):
            await self._handle_natural_language(cmd_lower, engine)
            return None

        # ── Parse subcommand ──────────────────────────────────────────────────
        parts = cmd.split(None, 2)
        subcommand = parts[1].lower() if len(parts) > 1 else ""
        arg = parts[2].strip() if len(parts) > 2 else ""

        if subcommand in ("", "status"):
            self._print_status(engine)
        elif subcommand == "on":
            await self._cmd_on(engine, arg, raw_cmd=arg)
        elif subcommand in ("off", "0m"):
            await self._cmd_off(engine)
        elif subcommand == "now":
            await self._cmd_now(engine)
        elif subcommand == "config":
            self._print_config(engine)
        else:
            self.console.print(f"[yellow]Unknown subcommand:[/yellow] {subcommand}")
            self._print_help()

        return None

    # ──────────────────────────────────────────────────────────────────────────
    # /heartbeat on → wizard entry point
    # ──────────────────────────────────────────────────────────────────────────

    async def _cmd_on(self, engine, interval_arg: str, raw_cmd: str = "") -> None:
        from pantheon.heartbeat import parse_interval
        interval = parse_interval(interval_arg) if interval_arg else (
            engine.interval if (engine and engine.interval) else 1800
        )
        preset_target = self._extract_preset_target(raw_cmd or interval_arg)
        await self._start_wizard(engine, interval, preset_target=preset_target)

    def _extract_preset_target(self, text: str) -> str | None:
        """Return a target key if the user already named one in their command."""
        t = text.lower()
        # Check all known target keys and common aliases
        _aliases: dict[str, str] = {
            "console": "console",
            "terminal": "console",
            "repl": "console",
            "web": "ui",
            "web ui": "ui",
            "webui": "ui",
            "browser": "ui",
            "ui": "ui",
            "silent": "none",
            "quiet": "none",
            "none": "none",
            "nowhere": "none",
            "no notification": "none",
            "telegram": "telegram",
            "slack": "slack",
            "discord": "discord",
            "wechat": "wechat",
            "feishu": "feishu",
            "qq": "qq",
            "imessage": "imessage",
        }
        for phrase, key in _aliases.items():
            if phrase in t:
                return key
        return None

    async def _start_wizard(self, engine, interval: int, preset_target: str | None = None) -> None:
        """Print the target-selection menu and set _pending_heartbeat_setup.

        If *preset_target* is already known (user specified it in the command),
        skip the menu and go straight to the next required step.
        """
        from pantheon.heartbeat import _seconds_to_human
        options = self._build_target_options()

        # ── Target already specified — skip the menu ───────────────────────────
        if preset_target is not None:
            # Normalise: make sure it's one of the valid keys
            valid_keys = {o["key"] for o in options}
            if preset_target in valid_keys:
                if preset_target not in ("console", "ui", "none"):
                    # External channel — still need a recipient ID
                    self.console.print(
                        f"\n[dim]Recipient ID for [bold]{preset_target.capitalize()}[/bold] "
                        f"(e.g. Telegram chat_id, Slack #channel-name).\n"
                        f"Press Enter to skip:[/dim]"
                    )
                    self.parent._pending_heartbeat_setup = {
                        "stage": "to",
                        "interval": interval,
                        "target": preset_target,
                        "options": options,
                    }
                else:
                    await self._finalise_wizard(interval, preset_target, to=None)
                return

        self.console.print()
        self.console.print(
            f"[bold]Setting up heartbeat[/bold]  "
            f"[dim]interval: {_seconds_to_human(interval)}[/dim]"
        )
        self.console.print()
        self.console.print("Where should alerts be sent?\n")
        for i, opt in enumerate(options, 1):
            self.console.print(
                f"  [cyan][{i}][/cyan] [bold]{opt['label']}[/bold]  "
                f"[dim]{opt['description']}[/dim]"
            )
        self.console.print()
        self.console.print("[dim]Enter a number or name (e.g. 1, telegram):[/dim]")

        self.parent._pending_heartbeat_setup = {
            "stage": "target",
            "interval": interval,
            "options": options,
        }

    def _build_target_options(self) -> list[dict]:
        """Build the list of available alert targets."""
        options: list[dict] = [
            {
                "key": "console",
                "label": "Console only",
                "description": "Print alerts in the REPL terminal",
            },
            {
                "key": "ui",
                "label": "Web UI",
                "description": "Show in the ChatRoom browser interface",
            },
        ]

        # Discover configured external channels
        try:
            from pantheon.claw.manager import _channel_configured
            from pantheon.claw.config import ClawConfigStore, IMPLEMENTED_CHANNELS
            cfg = ClawConfigStore().load()
            for ch in IMPLEMENTED_CHANNELS:
                if _channel_configured(ch, cfg):
                    options.append({
                        "key": ch,
                        "label": ch.capitalize(),
                        "description": f"Send via {ch.capitalize()} bot",
                    })
        except Exception:
            pass  # claw not available

        options.append({
            "key": "none",
            "label": "Silent",
            "description": "Run heartbeat turns but suppress all alert delivery",
        })
        return options

    # ──────────────────────────────────────────────────────────────────────────
    # Wizard step handler (called by Repl._handle_heartbeat_wizard_input)
    # ──────────────────────────────────────────────────────────────────────────

    async def handle_wizard_input(self, message: str) -> None:
        """Process one wizard-step answer from the user."""
        state = self.parent._pending_heartbeat_setup
        if state is None:
            return

        stage = state["stage"]

        if stage == "target":
            await self._wizard_handle_target(state, message)
        elif stage == "to":
            to_val = message.strip() or None
            await self._finalise_wizard(state["interval"], state["target"], to=to_val)

    async def _wizard_handle_target(self, state: dict, message: str) -> None:
        options = state["options"]
        choice = message.strip().lower()

        # Accept a number or a key/label name
        target_key: str | None = None
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                target_key = options[idx]["key"]
        else:
            for opt in options:
                if choice in (opt["key"], opt["label"].lower()):
                    target_key = opt["key"]
                    break

        if target_key is None:
            self.console.print(
                f"[yellow]'{message.strip()}' is not a valid choice.[/yellow] "
                "Enter a number or name from the list above."
            )
            return  # keep pending state, ask again

        # External channel targets need a recipient ID
        if target_key not in ("console", "ui", "none"):
            state["target"] = target_key
            state["stage"] = "to"
            self.console.print(
                f"\n[dim]Recipient ID for [bold]{target_key.capitalize()}[/bold] "
                f"(e.g. Telegram chat_id, Slack #channel-name).\n"
                f"Press Enter to skip (you can set this later with /heartbeat config):[/dim]"
            )
            return

        await self._finalise_wizard(state["interval"], target_key, to=None)

    async def _finalise_wizard(self, interval: int, target: str, to: str | None) -> None:
        """Commit config, reconfigure the engine, print confirmation."""
        from pantheon.heartbeat import _seconds_to_human

        # Clear pending state first
        self.parent._pending_heartbeat_setup = None

        engine = getattr(self.parent, "_heartbeat_engine", None)
        if engine is None:
            # Engine was never started (every=0m in settings). Bootstrap it now.
            try:
                from pantheon.heartbeat import HeartbeatEngine
                engine = HeartbeatEngine({}, self.parent)
                self.parent._heartbeat_engine = engine
            except Exception as exc:
                self.console.print(f"[red]Could not create heartbeat engine:[/red] {exc}")
                return

        cfg = dict(engine._config)
        cfg["every"] = (
            f"{interval // 60}m" if interval % 60 == 0 else f"{interval}s"
        )
        cfg["target"] = target
        if to:
            cfg["to"] = to
        else:
            cfg.pop("to", None)

        engine.reconfigure(cfg)

        _target_labels = {
            "console": "REPL console",
            "ui":      "Web UI",
            "none":    "silent (no delivery)",
        }
        target_label = _target_labels.get(target, target.capitalize())

        self.console.print(
            f"\n[green]✓[/green] Heartbeat active — "
            f"every [bold]{_seconds_to_human(interval)}[/bold], "
            f"alerts → [bold]{target_label}[/bold]"
        )
        if to:
            self.console.print(f"  [dim]Recipient: {to}[/dim]")
        self.console.print(
            "  [dim]Reply HEARTBEAT_OK when nothing needs attention.[/dim]\n"
        )

    # ──────────────────────────────────────────────────────────────────────────
    # Other subcommands
    # ──────────────────────────────────────────────────────────────────────────

    async def _cmd_off(self, engine) -> None:
        # Cancel any active wizard first
        self.parent._pending_heartbeat_setup = None
        if engine is None:
            self.console.print("[dim]Heartbeat not running.[/dim]")
            return
        cfg = dict(engine._config)
        cfg["every"] = "0m"
        engine.reconfigure(cfg)
        self.console.print("[green]✓[/green] Heartbeat [bold]disabled[/bold]")
        self.console.print()

    async def _cmd_now(self, engine) -> None:
        if engine is None:
            self.console.print("[yellow]Heartbeat engine not available.[/yellow]")
            return
        chat_id = getattr(self.parent, "_chat_id", None)
        if not chat_id:
            self.console.print("[yellow]No active chat. Start chatting first.[/yellow]")
            return
        self.console.print("[dim]⚡ Firing heartbeat now...[/dim]")
        try:
            await engine.trigger_now()
        except Exception as exc:
            self.console.print(f"[red]Heartbeat run failed:[/red] {exc}")

    def _print_status(self, engine) -> None:
        if engine is None:
            self.console.print("[dim]Heartbeat engine not initialised.[/dim]")
            self._print_help()
            return

        s = engine.status()
        enabled_str = "[green]enabled[/green]" if s["enabled"] else "[red]disabled[/red]"

        self.console.print()
        self.console.print(
            f"  [bold]Heartbeat[/bold]  {enabled_str}  "
            f"[dim]every {s['interval_human']}[/dim]"
        )
        self.console.print()

        _target_labels = {
            "console": "REPL console",
            "ui":      "Web UI",
            "none":    "silent",
        }
        target = s.get("target", "console")
        target_label = _target_labels.get(target, target.capitalize())
        to = s.get("to")
        self.console.print(
            f"  Alerts:     [bold]{target_label}[/bold]"
            + (f"  [dim]→ {to}[/dim]" if to else "")
        )

        if s["last_run"]:
            self.console.print(f"  Last run:   [dim]{s['last_run']}[/dim]")
        if s["next_run"] and s["enabled"]:
            self.console.print(f"  Next run:   [dim]{s['next_run']}[/dim]")
        if s["run_count"] or s["skip_count"]:
            self.console.print(
                f"  Runs: [green]{s['run_count']}[/green]   "
                f"Skipped: [yellow]{s['skip_count']}[/yellow]"
            )
        if s["active_hours"]:
            ah = s["active_hours"]
            self.console.print(
                f"  Active:     {ah.get('start', '?')}–{ah.get('end', '?')}  "
                f"{ah.get('timezone', 'local')}"
            )
        self.console.print()

    def _print_config(self, engine) -> None:
        if engine is None:
            self.console.print("[dim]Heartbeat engine not initialised.[/dim]")
            return
        import json
        self.console.print()
        self.console.print("[bold]Heartbeat config:[/bold]")
        self.console.print(json.dumps(engine._config, indent=2, default=str))
        self.console.print()

    def _print_help(self) -> None:
        self.console.print()
        self.console.print("[bold]Usage:[/bold]")
        self.console.print("  [cyan]/heartbeat[/cyan]              — show status")
        self.console.print("  [cyan]/heartbeat on [interval][/cyan] — setup wizard  (e.g. 30m, 1h)")
        self.console.print("  [cyan]/heartbeat off[/cyan]           — disable")
        self.console.print("  [cyan]/heartbeat now[/cyan]           — fire immediately")
        self.console.print("  [cyan]/heartbeat config[/cyan]        — show full config")
        self.console.print()
        self.console.print(
            "[dim]Or set [bold]agents.heartbeat[/bold] in .pantheon/settings.json[/dim]"
        )
        self.console.print()

    # ──────────────────────────────────────────────────────────────────────────
    # Natural language routing
    # ──────────────────────────────────────────────────────────────────────────

    async def _handle_natural_language(self, cmd_lower: str, engine) -> None:
        disable_words = {"disable", "turn off", "deactivate", "stop", "off"}
        now_words = {"now", "immediately", "trigger", "fire", "wake"}
        status_words = {"status", "check", "show", "what"}

        if any(w in cmd_lower for w in disable_words):
            await self._cmd_off(engine)
            return
        if any(w in cmd_lower for w in now_words):
            await self._cmd_now(engine)
            return
        if any(w in cmd_lower for w in status_words):
            self._print_status(engine)
            return

        # Extract an optional inline interval
        import re
        m = re.search(r"\b(\d+\s*(?:h|m|s)(?:our|in|econd)?s?\b)", cmd_lower)
        await self._cmd_on(engine, m.group(1) if m else "", raw_cmd=cmd_lower)
