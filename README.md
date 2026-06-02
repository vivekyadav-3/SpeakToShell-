# TerminalAI — AI-Powered CLI Tool 🤖

> Let your terminal understand plain English. Translate natural language into optimized, OS-aware shell commands in seconds using NVIDIA NIM API.

---

## 🌟 Features

- 🧠 **Plain English to Shell Commands (`ai "..."`)**: Turns standard english phrases into syntactically correct, optimized shell commands.
- 💻 **OS & Shell Aware**: Automatically detects your Operating System (Windows, macOS, Linux) and target Shell (PowerShell, cmd, bash, zsh) to generate appropriate syntax.
- 🚨 **Safety First (Danger Detection)**: Scans generated commands against destructive patterns (like recursive deletion, drive formatting, block device writes) and alerts you before prompting for safety bypass.
- 📋 **Interactive Options (`[y/N/e/c]`)**: Single-keypress confirmation prompts to:
  - `y` — **Execute** the command instantly.
  - `N` — **Cancel** execution and exit.
  - `e` — **Explain** the command in-place before executing it.
  - `c` — **Copy** the command to your clipboard.
- 📜 **Audit History (`ai --history`)**: View your historical queries, generated commands, and execution status.
- 🌐 **NVIDIA NIM Powered**: Employs state-of-the-art models like `meta/llama-3.1-70b-instruct` for robust code generation.

---

## 🚀 Installation & Setup

### 1. Clone or Move Into Workspace
Ensure you are in the project folder:
```bash
cd clitool
```

### 2. Install Package
Install the package in editable mode:
```bash
pip install -e .
```
This registers the global `ai` executable in your environment.

### 3. Add API Credentials
You can configure your credentials automatically using the interactive setup command:
```bash
ai --configure
```
This guides you through securing your NVIDIA NIM API Key and choosing a default model, saving them to `~/.terminal_ai.env` so that `ai` is accessible globally.

Alternatively, you can manually create a `.env` file in the project folder containing:
```env
NVIDIA_API_KEY="your-nvapi-key-here"
```

> [!NOTE]
> Free API credits are available from [build.nvidia.com](https://build.nvidia.com).

---

## 📖 Usage Examples

### 1. Simple Translation
Ask for a command in plain English:
```bash
ai "list all python files modified today"
```
*Output:*
```
OS detected: Windows | Shell: PowerShell
[Suggested Command]
Get-ChildItem -Filter *.py | Where-Object { $_.LastWriteTime -ge (Get-Date).Date }

Execute? [y(es) / N(o) / e(xplain) / c(opy)]:
```

### 2. Command Breakdown and Explanation
Press `e` at the confirmation prompt or request explanation directly:
```bash
ai --explain "kill -9 8080"
```

### 3. Review Command Logs
To see previously requested commands:
```bash
ai --history
```

### 4. Clear Command Logs
To wipe stored history:
```bash
ai --clear-history
```

### 5. Destructive Operations Warning
If you query a destructive action:
```bash
ai "delete everything in root folder"
```
*Output:*
```
🚨 DANGER DETECTED: Recursive removal of root directory
Are you absolutely sure you want to run this? Type 'yes' to proceed:
```

---

## 🛠️ Tech Stack & Dependencies

- **Typer**: Smooth, user-friendly CLI parsing.
- **Rich**: Elegant formatting, syntax highlighting, and progress spinners.
- **OpenAI Python SDK**: Seamless client wrapper for OpenAI-compatible NVIDIA endpoints.
- **Pyperclip**: Safe, cross-platform clipboard copy mechanics.
- **Python-dotenv**: Secure environment loading.
