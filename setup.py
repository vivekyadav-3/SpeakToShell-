from setuptools import setup, find_packages

setup(
    name="terminal-ai-cli",
    version="0.1.0",
    author="TerminalAI Developer",
    description="A Python CLI tool that converts plain English into shell commands using NVIDIA NIM API.",
    packages=find_packages(),
    install_requires=[
        "openai>=1.0.0",
        "typer[all]>=0.9.0",
        "rich>=13.0.0",
        "python-dotenv>=1.0.0",
        "pyperclip>=1.8.2",
    ],
    entry_points={
        "console_scripts": [
            "ai=terminal_ai.cli:app",
        ],
    },
    python_requires=">=3.10",
)
