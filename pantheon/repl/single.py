import asyncio
import sys
import time
import json
from datetime import datetime

from rich.console import Console
from rich.prompt import Prompt
from rich.text import Text
from rich.live import Live
from rich.spinner import Spinner
from rich.columns import Columns
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax

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
            print_agent_message_modern_style(
                self.agent.name, 
                message, 
                self.console,
                show_tool_details=False
            )

    async def run(self, message: str | dict | None = None):
        # Suppress verbose logging for cleaner output
        import logging
        logging.getLogger().setLevel(logging.WARNING)
        import loguru
        loguru.logger.remove()
        loguru.logger.add(sys.stdout, level="WARNING")

        await self.print_greeting()
        print_task = asyncio.create_task(self.print_message())

        def ask_user():
            return Prompt.ask("[bright_white]❯[/bright_white]")

        # Handle initial message
        if message is None:
            message = ask_user()
            if message.lower().strip() in ["exit", "quit", "q"]:
                return
        else:
            self.console.print(f"[bright_white]❯[/bright_white] {message}")

        while True:
            # Start processing indicator
            start_time = time.time()
            
            # Create a subtle processing indicator
            with self.console.status("[dim]Processing...[/dim]", spinner="dots"):
                content_buffer = []
                
                def process_chunk(chunk: dict):
                    content = chunk.get("content")
                    if content is not None:
                        content_buffer.append(content)

                try:
                    await self.agent.run(
                        message,
                        process_chunk=process_chunk,
                    )
                    
                    # Print accumulated content if any
                    if content_buffer:
                        full_content = ''.join(content_buffer)
                        if full_content.strip():
                            self.console.print(Markdown(full_content))
                    
                    self.message_count += 1
                    
                except KeyboardInterrupt:
                    self.console.print("\n[yellow]Interrupted by user[/yellow]")
                    continue
                except Exception as e:
                    self.console.print(f"[red]Error:[/red] {str(e)}")
                    self.console.print("[dim]You can continue the conversation or type 'exit' to quit[/dim]")
                
                # Show processing time for long operations
                elapsed = time.time() - start_time
                if elapsed > 3:  # Only show if took more than 3 seconds
                    self.console.print(f"[dim]({elapsed:.1f}s)[/dim]")
            
            self.console.print()  # Add spacing
            
            # Get next user input
            try:
                message = ask_user()
                
                # Handle special commands
                if message.lower().strip() in ["exit", "quit", "q"]:
                    self._print_session_summary()
                    break
                elif message.lower().strip() == "help":
                    self._print_help()
                    continue
                elif message.lower().strip() == "status":
                    self._print_status()
                    continue
                elif message.lower().strip() == "clear":
                    self.console.clear()
                    await self.print_greeting()
                    continue
                    
            except (KeyboardInterrupt, EOFError):
                self.console.print("\n[dim]Session interrupted[/dim]")
                self._print_session_summary()
                break

        print_task.cancel()
    
    def _print_help(self):
        """Print available commands"""
        self.console.print("\n[bold]Available commands:[/bold]")
        self.console.print("[dim]• exit, quit, q[/dim] - Exit the application")
        self.console.print("[dim]• help[/dim] - Show this help message")
        self.console.print("[dim]• status[/dim] - Show session information")  
        self.console.print("[dim]• clear[/dim] - Clear screen and reset")
        self.console.print("[dim]• Ctrl+C[/dim] - Interrupt current operation\n")
        
    def _print_status(self):
        """Print current session status"""
        session_duration = datetime.now() - self.session_start
        duration_mins = int(session_duration.total_seconds() / 60)
        
        self.console.print(f"\n[bold]Session Status:[/bold]")
        self.console.print(f"[dim]• Agent:[/dim] {self.agent.name}")
        if hasattr(self.agent, 'models') and self.agent.models:
            model = self.agent.models[0] if isinstance(self.agent.models, list) else self.agent.models
            self.console.print(f"[dim]• Model:[/dim] {model}")
        self.console.print(f"[dim]• Messages:[/dim] {self.message_count}")
        self.console.print(f"[dim]• Duration:[/dim] {duration_mins}m\n")

    def _print_session_summary(self):
        """Print a brief session summary before exit"""
        session_duration = datetime.now() - self.session_start
        duration_mins = int(session_duration.total_seconds() / 60)
        
        if self.message_count > 0:
            self.console.print(f"\n[dim]Session summary: {self.message_count} messages in {duration_mins}m[/dim]")
        self.console.print("[dim]Goodbye![/dim]")


if __name__ == "__main__":
    agent = Agent(
        "agent",
        "You are a helpful assistant."
    )
    repl = Repl(agent)
    asyncio.run(repl.run())
