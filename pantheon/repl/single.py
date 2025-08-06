import asyncio
import sys
import time
import json
from datetime import datetime
import os
from pathlib import Path

from rich.console import Console
from rich.prompt import Prompt
from rich.text import Text
from rich.live import Live
from rich.spinner import Spinner
from rich.columns import Columns
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax

# Simple readline support for history
try:
    import readline
    import atexit
    READLINE_AVAILABLE = True
except ImportError:
    READLINE_AVAILABLE = False

from ..agent import Agent
from ..remote.agent import RemoteAgent
from ..utils.misc import print_agent_message, print_agent, print_banner, print_agent_message_modern_style


class Repl:
    """REPL for a single agent.

    Args:
        agent: The agent to use for the REPL.
    """
    def __init__(self, agent: Agent | RemoteAgent):
        self.agent = agent
        self.console = Console()
        self.current_task = None
        self.tool_calls_active = False
        self.session_start = datetime.now()
        self.message_count = 0
        
        # Token statistics
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.current_input_tokens = 0
        self.current_output_tokens = 0
        
        # Setup history file
        self.history_file = Path.home() / ".pantheon_history"
        self.command_history = []
        self.history_index = -1
        
        # Setup input system
        self._setup_input_system()
        self._load_history()

    async def print_greeting(self):
        await print_banner(self.console)
        self.console.print(
            "[bold]Welcome to the Pantheon REPL![/bold]\n" +
            "Single-cell genomics analysis assistant\n"
        )
        
        # Agent info in a compact format
        self.console.print("[bold]Current agent:[/bold]")
        agent_info = f"  - [bright_blue]{self.agent.name}[/bright_blue]"
        if hasattr(self.agent, 'models') and self.agent.models:
            model = self.agent.models[0] if isinstance(self.agent.models, list) else self.agent.models
            agent_info += f" [dim]•[/dim] [yellow]{model}[/yellow]"
        self.console.print(agent_info)
        self.console.print("[dim]Type your message, 'exit' to quit, or 'help' for commands[/dim]")
        if READLINE_AVAILABLE:
            self.console.print("[dim]Use ↑/↓ arrows for command history[/dim]")
        self.console.print()

    def print_tool_call(self, tool_name: str, args: str):
        """Print tool call in Claude Code style"""
        self.console.print(f"[dim]▶ Using {tool_name}[/dim]")
        
    def print_tool_result(self, result: str, truncate: bool = True):
        """Print tool result in a clean format"""
        if truncate and len(result) > 500:
            result = result[:500] + "..."
        
        # Try to format as JSON if possible
        try:
            parsed = json.loads(result)
            formatted_result = json.dumps(parsed, indent=2)
            self.console.print(Syntax(formatted_result, "json", theme="monokai", line_numbers=False))
        except (json.JSONDecodeError, TypeError):
            # If not JSON, print as regular text with syntax highlighting if it looks like code
            if any(keyword in result.lower() for keyword in ['def ', 'import ', 'class ', 'function', '#!/']):
                self.console.print(Syntax(result, "python", theme="monokai", line_numbers=False))
            else:
                self.console.print(f"[dim]{result}[/dim]")

    async def print_message(self):
        """Enhanced message handler with Claude Code style formatting"""
        while True:
            message = await self.agent.events_queue.get()
            
            # Skip tool calls and responses - we handle content in main loop
            if message.get("tool_calls") or message.get("role") == "tool":
                continue
                
            # Skip assistant messages - we handle them in main loop via content_buffer
            if message.get("role") == "assistant":
                continue
            
            # Only print other message types (like system messages, if any)
            print_agent_message_modern_style(
                self.agent.name, 
                message, 
                self.console,
                show_tool_details=False
            )
    
    def _setup_input_system(self):
        """Setup simple input system with readline history"""
        if READLINE_AVAILABLE:
            # Setup readline with history
            if self.history_file.exists():
                readline.read_history_file(str(self.history_file))
            atexit.register(readline.write_history_file, str(self.history_file))
            readline.set_history_length(1000)
            
            # Simple readline configuration for better user experience
            readline.parse_and_bind("tab: complete")
            readline.parse_and_bind("set completion-ignore-case on")
    
    def _load_history(self):
        """Load command history from file"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.command_history = [line.strip() for line in f.readlines()[-100:]]  # Keep last 100
            except Exception:
                self.command_history = []
    
    def _save_history(self):
        """Save command history to file"""
        try:
            with open(self.history_file, 'a', encoding='utf-8') as f:
                if self.command_history:
                    f.write(self.command_history[-1] + '\n')
        except Exception:
            pass  # Silently ignore history save errors
            
    def _add_to_history(self, command: str):
        """Add command to history"""
        command = command.strip()
        if command and (not self.command_history or self.command_history[-1] != command):
            self.command_history.append(command)
            self._save_history()
            self.history_index = len(self.command_history)
    
    def ask_user_input(self) -> str:
        """Get user input with simple Claude-style prompt"""
        try:
            return input('> ')
        except (KeyboardInterrupt, EOFError):
            raise
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count using rough approximation (4 chars ≈ 1 token)"""
        if not text:
            return 0
        # Simple estimation: ~4 characters per token for English text
        return max(1, len(text) // 4)
    
    def _format_token_count(self, count: int) -> str:
        """Format token count with appropriate units and thousand separators"""
        if count >= 1000000:
            return f"{count/1000000:.1f}M"
        elif count >= 10000:  # Use K for 10K+
            return f"{count/1000:.1f}K"
        elif count >= 1000:   # Use comma separator for 1K-10K
            return f"{count:,}"
        else:
            return str(count)
    
    def _update_token_stats(self, input_tokens: int, output_tokens: int):
        """Update token statistics"""
        self.current_input_tokens = input_tokens
        self.current_output_tokens = output_tokens
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens

    async def run(self, message: str | dict | None = None):
        # Suppress verbose logging for cleaner output
        import logging
        logging.getLogger().setLevel(logging.WARNING)
        import loguru
        loguru.logger.remove()
        loguru.logger.add(sys.stdout, level="WARNING")

        await self.print_greeting()
        print_task = asyncio.create_task(self.print_message())

        # Handle initial message if provided
        initial_message = message
        if initial_message is not None:
            self.console.print(f"> {initial_message}")
            self._add_to_history(initial_message)

        # Main message processing loop
        current_message = initial_message
        
        while True:
            # Get message (either initial message or new user input)
            if current_message is None:
                try:
                    current_message = self.ask_user_input()
                    # Skip empty messages (from ESC interruption)
                    if not current_message.strip():
                        continue
                    self._add_to_history(current_message)
                except (KeyboardInterrupt, EOFError):
                    self.console.print("\n[dim]Session interrupted[/dim]")
                    self._print_session_summary()
                    break
            
            # Handle special commands FIRST (before sending to API)
            cmd = current_message.lower().strip()
            
            if cmd in ["exit", "quit", "q", "/exit", "/quit", "/q"]:
                self._print_session_summary()
                break
            elif cmd in ["help", "/help"]:
                self._print_help()
                current_message = None  # Reset to get new input
                continue
            elif cmd in ["status", "/status"]:
                self._print_status()
                current_message = None  # Reset to get new input
                continue
            elif cmd in ["clear", "/clear"]:
                self.console.clear()
                await self.print_greeting()
                current_message = None  # Reset to get new input
                continue
            elif cmd in ["history", "/history"]:
                self._print_history()
                current_message = None  # Reset to get new input
                continue
            elif cmd in ["tokens", "/tokens"]:
                self._print_token_analysis()
                current_message = None  # Reset to get new input
                continue
            
            # If not a special command, process with agent
            start_time = time.time()
            
            # Estimate input tokens
            input_tokens = self._estimate_tokens(current_message)
            output_tokens = 0
            
            # Create live status with real-time token tracking
            content_buffer = []
            
            def process_chunk(chunk: dict):
                content = chunk.get("content")
                if content is not None:
                    content_buffer.append(content)

            # Use Live display for real-time token updates
            with Live(console=self.console, refresh_per_second=4) as live:
                def update_live_display():
                    current_output_tokens = self._estimate_tokens(''.join(content_buffer))
                    elapsed = time.time() - start_time
                    
                    # Create processing message with real-time token info
                    status_text = f"[dim]Processing... • {self._format_token_count(input_tokens)} in, {self._format_token_count(current_output_tokens)} out"
                    if elapsed > 1:
                        status_text += f" • {elapsed:.1f}s"
                    status_text += "[/dim]"
                    
                    live.update(Text.from_markup(status_text))

                try:
                    # Initial display
                    update_live_display()
                    
                    # Custom process_chunk that updates display
                    def live_process_chunk(chunk: dict):
                        process_chunk(chunk)  # Original processing
                        update_live_display()  # Update display
                    
                    await self.agent.run(
                        current_message,
                        process_chunk=live_process_chunk,
                    )
                    
                    # Final output token calculation
                    if content_buffer:
                        full_content = ''.join(content_buffer)
                        if full_content.strip():
                            output_tokens = self._estimate_tokens(full_content)
                    
                    # Update token statistics
                    self._update_token_stats(input_tokens, output_tokens)
                    self.message_count += 1
                    
                except KeyboardInterrupt:
                    live.stop()
                    self.console.print("\n[yellow]Interrupted by user[/yellow]")
                    current_message = None  # Reset to get new input
                    continue
                except Exception as e:
                    live.stop()
                    self.console.print(f"[red]Error:[/red] {str(e)}")
                    self.console.print("[dim]You can continue the conversation or type 'exit' to quit[/dim]")
            
            # Print accumulated content after processing
            if content_buffer:
                full_content = ''.join(content_buffer)
                if full_content.strip():
                    self.console.print(Markdown(full_content))
            
            self.console.print()  # Add spacing
            current_message = None  # Reset to get new input

        print_task.cancel()
    
    def _print_help(self):
        """Print available commands"""
        self.console.print("\n[bold]Commands:[/bold]")
        self.console.print("[dim]/help[/dim] - Show this help")
        self.console.print("[dim]/status[/dim] - Session info")
        self.console.print("[dim]/history[/dim] - Show command history")
        self.console.print("[dim]/tokens[/dim] - Token usage analysis")  
        self.console.print("[dim]/clear[/dim] - Clear screen")
        self.console.print("[dim]/exit[/dim] - Exit")
        self.console.print("[dim]Ctrl+C[/dim] - Interrupt/Exit")
        
        if READLINE_AVAILABLE:
            self.console.print("\n[bold]Navigation:[/bold]")
            self.console.print("[dim]↑/↓[/dim] - Browse command history")
        
        self.console.print("\n[bold]Examples:[/bold]")
        self.console.print("[dim]analyze single cell data[/dim]")
        self.console.print("[dim]run quality control[/dim]")
        self.console.print("[dim]create UMAP plot[/dim]\n")
    
    def _print_history(self):
        """Print recent command history"""
        if not self.command_history:
            self.console.print("\n[dim]No command history yet[/dim]\n")
            return
            
        self.console.print(f"\n[bold]Command History[/bold] [dim]({len(self.command_history)} commands)[/dim]")
        
        # Show last 10 commands
        recent = self.command_history[-10:]
        for i, cmd in enumerate(recent, 1):
            if len(recent) == 10 and i == 1 and len(self.command_history) > 10:
                self.console.print("[dim]...[/dim]")
            self.console.print(f"[dim]{len(self.command_history) - len(recent) + i:2d}.[/dim] {cmd}")
        self.console.print()
    
    def _print_token_analysis(self):
        """Print detailed token usage analysis"""
        total_tokens = self.total_input_tokens + self.total_output_tokens
        
        if total_tokens == 0:
            self.console.print("\n[dim]No token usage data yet[/dim]\n")
            return
        
        self.console.print(f"\n[bold]Token Analysis[/bold]")
        
        # Basic stats
        self.console.print(f"[dim]Total:[/dim] {self._format_token_count(total_tokens)} tokens")
        self.console.print(f"[dim]  • Input:[/dim] {self._format_token_count(self.total_input_tokens)} ({self.total_input_tokens/total_tokens*100:.1f}%)")
        self.console.print(f"[dim]  • Output:[/dim] {self._format_token_count(self.total_output_tokens)} ({self.total_output_tokens/total_tokens*100:.1f}%)")
        
        # Efficiency metrics
        if self.message_count > 0:
            avg_total = total_tokens / self.message_count
            avg_input = self.total_input_tokens / self.message_count
            avg_output = self.total_output_tokens / self.message_count
            
            self.console.print(f"\n[bold]Per Message Average:[/bold]")
            self.console.print(f"[dim]Total:[/dim] {self._format_token_count(int(avg_total))}")
            self.console.print(f"[dim]Input:[/dim] {self._format_token_count(int(avg_input))}")
            self.console.print(f"[dim]Output:[/dim] {self._format_token_count(int(avg_output))}")
        
        # Usage recommendations
        self.console.print(f"\n[bold]Tips:[/bold]")
        if avg_input > 1000:
            self.console.print("[dim]• Consider shorter prompts to reduce input tokens[/dim]")
        if self.total_output_tokens / max(1, self.total_input_tokens) > 3:
            self.console.print("[dim]• High output ratio - responses are verbose[/dim]")
        if self.message_count > 5 and avg_total < 100:
            self.console.print("[dim]• Efficient usage - good token management[/dim]")
        elif avg_total > 2000:
            self.console.print("[dim]• High token usage - consider optimizing prompts[/dim]")
        
        self.console.print()
        
    def _print_status(self):
        """Print current session status"""
        session_duration = datetime.now() - self.session_start
        duration_mins = int(session_duration.total_seconds() / 60)
        
        self.console.print(f"\n[bold]Session Status:[/bold]")
        self.console.print(f"[dim]• Agent:[/dim] {self.agent.name}")
        if hasattr(self.agent, 'models') and self.agent.models:
            model = self.agent.models[0] if isinstance(self.agent.models, list) else self.agent.models
            self.console.print(f"[dim]• Model:[/dim] {model}")
        self.console.print(f"[dim]Messages:[/dim] {self.message_count}")
        self.console.print(f"[dim]Duration:[/dim] {duration_mins}m")
        self.console.print(f"[dim]History:[/dim] {len(self.command_history)} commands")
        
        # Token usage statistics
        total_tokens = self.total_input_tokens + self.total_output_tokens
        if total_tokens > 0:
            self.console.print(f"[dim]Tokens:[/dim] {self._format_token_count(total_tokens)} total")
            self.console.print(f"[dim]  • Input:[/dim] {self._format_token_count(self.total_input_tokens)}")
            self.console.print(f"[dim]  • Output:[/dim] {self._format_token_count(self.total_output_tokens)}")
            
            # Show efficiency metrics
            if self.message_count > 0:
                avg_tokens_per_msg = total_tokens / self.message_count
                self.console.print(f"[dim]  • Avg/msg:[/dim] {self._format_token_count(int(avg_tokens_per_msg))}")
        
        if READLINE_AVAILABLE:
            self.console.print(f"[dim]Input:[/dim] readline (with history)")
        else:
            self.console.print(f"[dim]Input:[/dim] basic")
        self.console.print()

    def _print_session_summary(self):
        """Print a brief session summary before exit"""
        session_duration = datetime.now() - self.session_start
        duration_mins = int(session_duration.total_seconds() / 60)
        
        if self.message_count > 0:
            summary = f"Session: {self.message_count} messages in {duration_mins}m"
            total_tokens = self.total_input_tokens + self.total_output_tokens
            if total_tokens > 0:
                summary += f" • {self._format_token_count(total_tokens)} tokens"
            self.console.print(f"\n[dim]{summary}[/dim]")
        self.console.print("[dim]Goodbye![/dim]")


if __name__ == "__main__":
    agent = Agent(
        "agent",
        "You are a helpful assistant."
    )
    repl = Repl(agent)
    asyncio.run(repl.run())
