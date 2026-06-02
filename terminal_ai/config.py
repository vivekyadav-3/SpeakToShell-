import os
import platform
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from active directory or package root
dotenv_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=dotenv_path)

# Also load from user home directory as a fallback for installed CLI
user_home_dotenv = Path.home() / ".terminal_ai.env"
if user_home_dotenv.exists():
    load_dotenv(dotenv_path=user_home_dotenv)

class Config:
    API_KEY = os.getenv("NVIDIA_API_KEY")
    MODEL = os.getenv("NVIDIA_MODEL", "meta/llama-3.1-70b-instruct")
    BASE_URL = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
    
    @classmethod
    def validate(cls):
        """Validates that the required API key exists."""
        if not cls.API_KEY:
            raise ValueError(
                "NVIDIA API Key not found.\n"
                "Please configure NVIDIA_API_KEY in a .env file inside your project root or "
                "run `ai --configure` to set it up interactively."
            )

    @classmethod
    def reload(cls):
        """Reload environment variables from disk."""
        # Reload from workspace .env
        if dotenv_path.exists():
            load_dotenv(dotenv_path=dotenv_path, override=True)
        # Reload from user home .env
        if user_home_dotenv.exists():
            load_dotenv(dotenv_path=user_home_dotenv, override=True)
        
        cls.API_KEY = os.getenv("NVIDIA_API_KEY")
        cls.MODEL = os.getenv("NVIDIA_MODEL", "meta/llama-3.1-70b-instruct")
        cls.BASE_URL = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")

    @classmethod
    def save_config(cls, api_key: str, model: str = None, base_url: str = None) -> bool:
        """
        Saves the config values directly to ~/.terminal_ai.env
        and reloads them.
        """
        model = model or cls.MODEL
        base_url = base_url or cls.BASE_URL
        
        content = (
            f'NVIDIA_API_KEY="{api_key}"\n'
            f'NVIDIA_MODEL="{model}"\n'
            f'NVIDIA_BASE_URL="{base_url}"\n'
        )
        try:
            with open(user_home_dotenv, "w", encoding="utf-8") as f:
                f.write(content)
            cls.reload()
            return True
        except Exception as e:
            raise IOError(f"Failed to write configuration file: {e}")

def detect_os_and_shell():
    """
    Detects the user's Operating System and Active Shell.
    Returns a tuple of:
    - os_name (str): e.g., 'Windows', 'Linux', 'Darwin' (macOS)
    - shell_name (str): e.g., 'PowerShell', 'cmd', 'bash', 'zsh'
    - shell_exec (list): command prefix list for executing in the terminal
    """
    os_name = platform.system()
    
    if os_name == "Windows":
        # Check if PSModulePath or other powershell markers exist
        if "PSModulePath" in os.environ:
            shell_name = "PowerShell"
            shell_exec = ["powershell.exe", "-NoProfile", "-Command"]
        else:
            shell_name = "cmd"
            shell_exec = ["cmd.exe", "/c"]
    else:
        # macOS or Linux
        shell_path = os.environ.get("SHELL", "/bin/bash")
        shell_name = os.path.basename(shell_path)
        shell_exec = [shell_path, "-c"]
        
    return os_name, shell_name, shell_exec
