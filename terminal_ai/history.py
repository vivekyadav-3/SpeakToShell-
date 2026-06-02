import json
import datetime
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()

class HistoryManager:
    def __init__(self):
        self.history_path = Path.home() / ".terminal_ai_history.json"
        
    def _read_history(self) -> list:
        """Reads and parses history file."""
        if not self.history_path.exists():
            return []
        try:
            with open(self.history_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _write_history(self, history: list):
        """Writes history back to the file."""
        try:
            with open(self.history_path, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not save history: {e}[/yellow]")

    def add(self, query: str, command: str, status: str):
        """
        Adds a command execution to history.
        status should be 'Executed', 'Aborted', or 'Failed'.
        """
        history = self._read_history()
        entry = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "query": query,
            "command": command,
            "status": status
        }
        history.append(entry)
        # Cap history at 100 entries to prevent oversized files
        if len(history) > 100:
            history = history[-100:]
        self._write_history(history)

    def list_history(self, limit: int = 15):
        """Prints a beautifully formatted history table using Rich."""
        history = self._read_history()
        if not history:
            console.print("[bold yellow]No command history found.[/bold yellow]")
            return

        table = Table(title="TerminalAI Command History", show_lines=True)
        table.add_column("ID", justify="center", style="cyan", no_wrap=True)
        table.add_column("Time", justify="center", style="magenta", no_wrap=True)
        table.add_column("Query (Natural Language)", style="green")
        table.add_column("Shell Command", style="bold white")
        table.add_column("Status", justify="center")

        # Show the most recent commands up to limit
        recent_history = history[-limit:]
        
        for idx, entry in enumerate(recent_history, 1):
            status = entry.get("status", "Unknown")
            if status == "Executed":
                status_formatted = "[bold green]Executed[/bold green]"
            elif status == "Aborted":
                status_formatted = "[bold yellow]Aborted[/bold yellow]"
            else:
                status_formatted = f"[red]{status}[/red]"
                
            table.add_row(
                str(idx),
                entry.get("timestamp", ""),
                entry.get("query", ""),
                entry.get("command", ""),
                status_formatted
            )

        console.print(table)
        
    def clear(self):
        """Clears all command history."""
        if self.history_path.exists():
            try:
                self.history_path.unlink()
                console.print("[bold green]Command history cleared successfully.[/bold green]")
            except Exception as e:
                console.print(f"[bold red]Error clearing history: {e}[/bold red]")
        else:
            console.print("[yellow]No history file exists to clear.[/yellow]")
