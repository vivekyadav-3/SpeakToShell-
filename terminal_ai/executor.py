import re
import subprocess
import sys
from terminal_ai.config import detect_os_and_shell

# Comprehensive dangerous pattern detection
DANGEROUS_RULES = [
    # Unix destructive removals
    (r"\brm\s+-[rf]*[rfv]*\s+/", "Recursive removal of root directory"),
    (r"\brm\s+-[rf]*[rfv]*\s+\*", "Wildcard removal in critical directories"),
    # Block device writing/formatting
    (r"\bdd\s+if=", "Low-level drive/block device writing using dd"),
    (r"\bmkfs(\b|\.)", "Filesystem creation/formatting"),
    (r"\bformat\s+[a-zA-Z]:", "Windows disk formatting command"),
    (r"\b> /dev/sd[a-z]", "Direct raw writing to disk device"),
    # Fork bomb (classic signature)
    (r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:", "Fork bomb (denial of service)"),
    # Bulk permissions alteration (dangerous system-wide changes)
    (r"\bchmod\s+-[R]*\s+777\s+/", "System-wide permissive folder permission change"),
    (r"\bchown\s+-[R]*\s+[^ ]+\s+/", "System-wide folder ownership change"),
    # Unprompted power operations (if potentially harmful context)
    (r"\bshutdown\b", "System shutdown command"),
    (r"\breboot\b", "System reboot command"),
    (r"\binit\s+0", "System power off"),
]

def scan_danger(command: str) -> tuple[bool, str]:
    """
    Scans the command for known dangerous patterns.
    Returns:
       (is_dangerous, reason)
    """
    cmd_lower = command.lower().strip()
    
    # Check simple exact rules
    for regex, description in DANGEROUS_RULES:
        if re.search(regex, cmd_lower, re.IGNORECASE):
            return True, description
            
    # Extra check for dangerous Windows commands
    if "del " in cmd_lower and "/s" in cmd_lower and ("/q" in cmd_lower or "/f" in cmd_lower):
        if any(p in cmd_lower for p in ["c:\\", "d:\\", "windows", "system32"]):
            return True, "Destructive file deletion on a system drive"

    return False, ""

def execute_command(command: str) -> int:
    """
    Executes a shell command in the context of the user's OS and detected shell.
    Streams output directly to standard output/error.
    Returns:
        The exit code of the execution.
    """
    os_name, shell_name, shell_exec = detect_os_and_shell()
    
    # Combine the shell runner arguments with the command to run
    # e.g., ["powershell.exe", "-NoProfile", "-Command", "Get-Process"]
    full_cmd = shell_exec + [command]
    
    try:
        # Run subprocess with direct console I/O
        result = subprocess.run(
            full_cmd,
            stdout=sys.stdout,
            stderr=sys.stderr,
            stdin=sys.stdin,
            text=True
        )
        return result.returncode
    except KeyboardInterrupt:
        print("\n[Execution interrupted by user]", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"\n[Execution failed]: {e}", file=sys.stderr)
        return 1
