import sys
import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from terminal_ai.config import detect_os_and_shell, Config
from terminal_ai.nvidia_client import NvidiaClient
from terminal_ai.executor import scan_danger, execute_command
from terminal_ai.history import HistoryManager

app = typer.Typer(
    name="TerminalAI",
    help="AI-Powered CLI tool to translate natural language queries to shell commands with safety checks.",
    add_completion=False
)
console = Console()
history_manager = HistoryManager()

def get_single_keypress() -> str:
    """
    Reads a single keypress from the user without requiring them to press Enter.
    Falls back gracefully to readline if environment does not support raw terminal access
    or if standard input is redirected (non-TTY).
    """
    try:
        # If input is redirected (e.g., in testing pipelines or background tasks), read from sys.stdin
        if not sys.stdin.isatty():
            ch = sys.stdin.read(1)
            if not ch:  # EOF
                return ""
            return ch.strip().lower()

        if sys.platform == "win32":
            import msvcrt
            ch = msvcrt.getch()
            # Handle Ctrl+C (which generates binary \x03)
            if ch == b'\x03':
                raise KeyboardInterrupt()
            # Ignore arrow keys/special prefixes
            if ch in (b'\x00', b'\xe0'):
                msvcrt.getch()
                return ""
            return ch.decode("utf-8", errors="ignore").lower()
        else:
            import tty
            import termios
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                ch = sys.stdin.read(1)
                # Handle Ctrl+C
                if ch == '\x03':
                    raise KeyboardInterrupt()
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            return ch.lower()
    except KeyboardInterrupt:
        raise
    except Exception:
        # Graceful fallback to standard prompt
        try:
            ans = input().strip().lower()
            return ans[0] if ans else ""
        except (KeyboardInterrupt, EOFError):
            raise KeyboardInterrupt()

def try_copy_to_clipboard(command: str) -> bool:
    """
    Copies the command to the clipboard using pyperclip.
    Handles cross-platform failures gracefully.
    """
    try:
        import pyperclip
        pyperclip.copy(command)
        return True
    except Exception as e:
        console.print(f"[yellow]⚠️  Could not copy to clipboard: {e}[/yellow]")
        return False

def run_configuration_flow():
    """
    Guides the user through an interactive setup flow to save credentials to ~/.terminal_ai.env.
    """
    console.print(Panel(
        "[bold cyan]Welcome to the TerminalAI Interactive Setup Guide 🤖[/bold cyan]\n\n"
        "We will securely save your NVIDIA NIM credentials to your user home folder:\n"
        "[bold white]~/.terminal_ai.env[/bold white]",
        title="TerminalAI Setup",
        border_style="cyan"
    ))
    
    console.print("[bold green]👉 Step 1: NVIDIA API Key[/bold green]")
    console.print("Sign up and get a free key with credits from: [underline blue]https://build.nvidia.com[/underline blue]")
    api_key = ""
    while not api_key:
        try:
            api_key = input("Enter your Nvidia API Key: ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Setup cancelled.[/yellow]")
            raise typer.Exit()
        if not api_key:
            console.print("[red]API Key cannot be empty. Please enter a key or press Ctrl+C to cancel.[/red]")
            continue
        if not api_key.startswith("nvapi-"):
            console.print("[yellow]⚠️  Warning: Key does not start with 'nvapi-'. Please verify.[/yellow]")
            try:
                override = input("Save this key anyway? [y/N]: ").strip().lower()
            except (KeyboardInterrupt, EOFError):
                console.print("\n[yellow]Setup cancelled.[/yellow]")
                raise typer.Exit()
            if override != 'y':
                api_key = ""
                
    console.print("\n[bold green]👉 Step 2: Choose default model[/bold green]")
    console.print("[1] meta/llama-3.1-70b-instruct (Recommended - Balanced)")
    console.print("[2] meta/llama-3.1-405b-instruct (Extreme precision - Slower)")
    console.print("[3] Custom model identifier")
    
    try:
        choice = input("Select option [1-3] (Default: 1): ").strip()
    except (KeyboardInterrupt, EOFError):
        console.print("\n[yellow]Setup cancelled.[/yellow]")
        raise typer.Exit()
        
    if choice == "2":
        model = "meta/llama-3.1-405b-instruct"
    elif choice == "3":
        try:
            model = input("Enter custom model identifier: ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Setup cancelled.[/yellow]")
            raise typer.Exit()
        if not model:
            model = "meta/llama-3.1-70b-instruct"
    else:
        model = "meta/llama-3.1-70b-instruct"

    try:
        Config.save_config(api_key, model)
        console.print(Panel(
            "[bold green]✓ Configuration written successfully![/bold green]\n\n"
            f"- Model: [white]{model}[/white]\n"
            "- Config Location: [white]~/.terminal_ai.env[/white]\n\n"
            "All systems ready! Run your first command now:\n"
            "[bold cyan]ai \"list directories in current folder\"[/bold cyan]",
            title="Setup Successful",
            border_style="green",
            padding=(1, 2)
        ))
    except Exception as e:
        console.print(f"[bold red]Failed to save configuration:[/bold red] {e}")
        raise typer.Exit(code=1)

@app.command()
def main(
    query: str = typer.Argument(None, help="The plain English description of the command you want to run"),
    explain: str = typer.Option(None, "--explain", "-e", help="Explain a specific command string"),
    history: bool = typer.Option(False, "--history", "-his", help="Display command execution history"),
    clear_history: bool = typer.Option(False, "--clear-history", help="Clear command execution history"),
    configure: bool = typer.Option(False, "--configure", help="Run interactive credentials setup guide")
):
    """
    TerminalAI — Convert plain English descriptions into executable shell commands.
    """
    # 1. Option handling: Clear History
    if clear_history:
        history_manager.clear()
        raise typer.Exit()

    # 2. Option handling: List History
    if history:
        history_manager.list_history()
        raise typer.Exit()

    # 3. Option handling: Interactive configuration
    if configure:
        run_configuration_flow()
        raise typer.Exit()

    # 4. Auto-configuration fallback if API key is missing
    if not Config.API_KEY:
        console.print("[yellow]⚠️  NVIDIA API Key not found![/yellow]")
        try:
            setup_choice = input("Would you like to run the interactive setup now? [Y/n]: ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[bold red]Cancelled setup. API key is required.[/bold red]")
            raise typer.Exit(code=1)
        if setup_choice in ("", "y", "yes"):
            run_configuration_flow()
            raise typer.Exit()
        else:
            console.print("[bold red]Error: NVIDIA API Key is required to run translations.[/bold red]")
            raise typer.Exit(code=1)

    # 5. Option handling: Explain Command (direct CLI option)
    if explain:
        try:
            client = NvidiaClient()
            os_name, shell_name, _ = detect_os_and_shell()
            with console.status("[bold green]Generating explanation using NVIDIA NIM...[/bold green]"):
                explanation = client.explain_command(explain, os_name, shell_name)
            
            console.print(Panel(
                Text(explanation),
                title=f"Explanation: {explain}",
                border_style="magenta",
                padding=(1, 2)
            ))
        except Exception as e:
            console.print(f"[bold red]Error explaining command:[/bold red] {e}")
            raise typer.Exit(code=1)
        raise typer.Exit()

    # 6. Handle default empty run
    if not query:
        console.print("[bold cyan]Welcome to TerminalAI 🤖[/bold cyan]")
        console.print("Usage: [bold green]ai \"your query in english\"[/bold green]")
        console.print("Try:   [bold]ai \"list all python files\"[/bold]")
        console.print("Help:  [bold]ai --help[/bold]")
        raise typer.Exit()

    # 7. Core flow: Translate English to Shell Command
    try:
        client = NvidiaClient()
    except Exception as e:
        console.print(f"[bold red]Configuration Error:[/bold red] {e}")
        raise typer.Exit(code=1)

    os_name, shell_name, _ = detect_os_and_shell()
    
    console.print(f"[cyan]OS detected:[/cyan] [bold]{os_name}[/bold] | [cyan]Shell:[/cyan] [bold]{shell_name}[/bold]")
    
    with console.status("[bold green]Translating query using NVIDIA NIM...[/bold green]"):
        try:
            command = client.generate_command(query, os_name, shell_name)
        except Exception as e:
            # Error messages printed inside the generate_command method
            raise typer.Exit(code=1)

    # If the response starts with "ERROR:", LLM couldn't generate command
    if command.startswith("ERROR:"):
        reason = command.replace("ERROR:", "").strip()
        console.print(Panel(
            f"[bold red]Unable to generate command:[/bold red] {reason}",
            title="TerminalAI Error",
            border_style="red"
        ))
        raise typer.Exit(code=1)

    # Display the suggested command
    console.print(Panel(
        f"[bold white]{command}[/bold white]",
        title="Suggested Command",
        border_style="cyan",
        padding=(1, 2)
    ))

    # Danger pattern scanning
    is_dangerous, danger_reason = scan_danger(command)
    if is_dangerous:
        console.print(Panel(
            f"[bold yellow]⚠️  WARNING: Potentially dangerous command detected![/bold yellow]\n"
            f"[bold red]Reason:[/bold red] {danger_reason}\n\n"
            f"Executing this could cause permanent system damage, data loss, or disruption.",
            title="🚨 DANGER FLAG",
            border_style="red",
            padding=(1, 2)
        ))
        
        # Danger confirmation requires explicit "yes" typing
        console.print("[bold red]Are you absolutely sure you want to run this? Type 'yes' to proceed: [/bold red]", end="")
        try:
            ans = input().strip().lower()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[bold yellow]Aborted.[/bold yellow]")
            history_manager.add(query, command, "Aborted")
            raise typer.Exit()
            
        if ans != "yes":
            console.print("[bold yellow]Safety override: Execution cancelled.[/bold yellow]")
            history_manager.add(query, command, "Aborted")
            raise typer.Exit()
            
        # If danger approved, proceed to execution
        console.print("[bold red]Execution approved by safety override...[/bold red]")
        return_code = execute_command(command)
        status = "Executed" if return_code == 0 else "Failed"
        history_manager.add(query, command, status)
        raise typer.Exit(code=return_code)

    # Standard confirmation loop [y/N/e/c]
    actions_left = {"explain": True, "copy": True}
    
    while True:
        prompt_options = ["y(es)", "N(o)"]
        if actions_left["explain"]:
            prompt_options.append("e(xplain)")
        if actions_left["copy"]:
            prompt_options.append("c(opy)")
            
        prompt_str = f"Execute? [{' / '.join(prompt_options)}]: "
        console.print(f"[bold green]{prompt_str}[/bold green]", end="")
        
        try:
            choice = get_single_keypress()
        except KeyboardInterrupt:
            console.print("\n[bold yellow]Aborted.[/bold yellow]")
            history_manager.add(query, command, "Aborted")
            raise typer.Exit()

        # Echo the typed choice to the line
        console.print(choice)

        if choice in ("y", "\r", "\n", " "):
            # Execute command
            console.print("[bold green]Executing...[/bold green]\n")
            return_code = execute_command(command)
            status = "Executed" if return_code == 0 else "Failed"
            history_manager.add(query, command, status)
            raise typer.Exit(code=return_code)
            
        elif choice == "e" and actions_left["explain"]:
            # Explain command
            with console.status("[bold green]Explaining command...[/bold green]"):
                explanation = client.explain_command(command, os_name, shell_name)
            
            console.print(Panel(
                Text(explanation),
                title="Command Breakdown",
                border_style="magenta",
                padding=(1, 2)
            ))
            # Disable explain option after use to prevent redundancy
            actions_left["explain"] = False
            continue
            
        elif choice == "c" and actions_left["copy"]:
            # Copy to clipboard
            if try_copy_to_clipboard(command):
                console.print("[bold green]✓ Command successfully copied to clipboard![/bold green]")
            # Disable copy option after use
            actions_left["copy"] = False
            continue
            
        else:
            # Abort/No
            console.print("[bold yellow]Execution cancelled.[/bold yellow]")
            history_manager.add(query, command, "Aborted")
            raise typer.Exit()

if __name__ == "__main__":
    app()
