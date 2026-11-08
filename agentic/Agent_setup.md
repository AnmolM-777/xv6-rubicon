# Agentic AI + xv6 Setup Guide

## 1. Project Overview

This project implements an Agentic AI system that accepts natural-language requests, converts them into structured tool calls, validates those calls, and executes approved operations inside an xv6 operating system running through QEMU.

The system uses a locally hosted Large Language Model (LLM) through Ollama. Python handles planning, validation and tool execution, while xv6 provides the isolated operating-system environment.

### Architecture

```text
                 User Request
                      |
                      v
             Local LLM (Qwen 2.5)
                  Ollama
                      |
                      v
              Python AI Agent
                  agent.py
                      |
                      v
              LLM Tool Planner
               llm_planner.py
                      |
                      v
                Validator
                validator.py
                      |
                      v
                Tool Layer
                 tools.py
                      |
                      v
                TCP Bridge
                 bridge.py
                      |
                      v
               QEMU Serial TCP
                127.0.0.1:5555
                      |
                      v
                 xv6 Shell
                      |
                      v
                xv6 Kernel
          Taint Tracking and Security
```

### Component Responsibilities

| Component | Responsibility |
|---|---|
| Ollama | Runs the local language model |
| Qwen 2.5 (0.5B) | Interprets user requests and proposes tool calls |
| agent.py | Coordinates the complete agent workflow |
| llm_planner.py | Converts natural-language requests into structured tool calls |
| schemas.py | Defines supported tools and their argument types |
| validator.py | Validates tool names, arguments and file paths |
| tools.py | Implements the available operations |
| bridge.py | Connects the Python agent to the xv6 guest |
| xv6 kernel | Enforces operating-system-level security restrictions |

**Important:** The LLM proposes actions; it does not directly execute shell commands. Python validates proposed actions, and the xv6 kernel provides an independent security boundary.

---

## 2. Development Environment

The project uses two environments.

### Mac — Development Environment

The Mac is used for:
- Editing source code through VS Code.
- Reviewing Python and C implementations.
- Managing Git commits and branches.
- Synchronizing changes through GitHub.
- Preparing documentation and reports.

QEMU is not required on the Mac in the current setup.

### Ubuntu VM — Execution Environment

The Ubuntu virtual machine is used for:
- Building and running xv6.
- Running QEMU.
- Executing the Python agent.
- Hosting the Ollama model.
- Testing kernel-level security mechanisms.

### Software Requirements

| Component | Configuration |
|---|---|
| Operating system | Ubuntu Linux VM |
| Architecture | ARM64 host environment |
| Simulator | QEMU RISC-V 64-bit |
| Compiler | riscv64-unknown-elf-gcc |
| Python | Python 3 |
| LLM runtime | Ollama |
| Language model | qwen2.5:0.5b |
| Communication | TCP serial connection |
| Repository | xv6-rubicon |

---

## 3. LLM Setup

The project uses Ollama to run a locally hosted language model.

### Install Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

If Ollama is already installed, this step can be skipped.

### Download the model

```bash
ollama pull qwen2.5:0.5b
```

### Verify model execution

```bash
ollama run qwen2.5:0.5b
```

Enter a simple prompt to verify that the model responds.

Exit the interactive session when finished.

### Ollama service

Ollama normally runs as a background service after installation.

If it is not running, start it using:

```bash
ollama serve
```

Do not start a second server if one is already running.

The Python client communicates with the local Ollama service.

---

## 4. Python Environment Setup

Navigate to the project directory:

```bash
cd ~/xv6-rubicon/agentic
```

Activate the virtual environment:

```bash
source venv/bin/activate
```

Install the project dependencies:

```bash
pip install -r requirements.txt
```

The Python agent uses the Ollama Python library to communicate with the local language model.

If required, install it separately:

```bash
pip install ollama
```

---

## 5. LLM Agent Workflow

The agent accepts natural-language requests and converts them into structured tool calls.

For example:

```text
User: List the available files.
```

The planner proposes:

```python
{
    "tool": "list_files",
    "arguments": {}
}
```

Another example:

```text
User: Read report.txt
```

The planner proposes:

```python
{
    "tool": "read_file",
    "arguments": {
        "path": "report.txt"
    }
}
```

The validator checks the proposed call before execution.

If the request is valid, the corresponding Python tool executes it through the bridge.

### Available Tools

| Tool | Purpose |
|---|---|
| list_files | Lists files in the allowed directory |
| read_file | Reads an allowed file |
| summarize | Summarizes supplied text |
| read_and_summarize | Reads a file and summarizes its contents |

The tool definitions are maintained in `schemas.py`.

### Security Validation

The validator checks:
- Whether the requested tool is supported.
- Whether arguments are supplied correctly.
- Whether argument types are valid.
- Whether file paths satisfy the allowed filename rules.
- Whether the requested file path stays within the permitted directory.

The Python validation layer is not the final security boundary. Kernel-level enforcement is implemented separately in xv6.

---

## 6. Python–xv6 Bridge Architecture

The Python agent communicates with xv6 through QEMU's serial console over TCP.

### Connection Configuration

| Setting | Value |
|---|---|
| Protocol | TCP |
| Host | 127.0.0.1 |
| Port | 5555 |
| QEMU role | TCP server |
| Python bridge role | TCP client |

The fixed TCP port avoids depending on dynamically assigned terminal device paths.

### Connection Architecture

```text
Python Agent
     |
     | TCP Client
     |
127.0.0.1:5555
     |
     | TCP Server
     |
QEMU Serial Console
     |
     |
xv6 Shell
```

The bridge is implemented in `bridge.py`.

It is responsible for:
- Establishing a TCP connection.
- Sending commands to the xv6 shell.
- Reading command output.
- Detecting the xv6 shell prompt.
- Handling connection failures and timeouts.

Only one client should control the xv6 serial console at a time.

---

## 7. Starting xv6 Through QEMU

The following commands assume:

- Repository path: `~/xv6-rubicon`
- QEMU binary: `~/qemu/build/qemu-system-riscv64`
- Toolchain prefix: `riscv64-unknown-elf-`

### Build xv6

```bash
cd ~/xv6-rubicon

make clean

make TOOLPREFIX=riscv64-unknown-elf- \
QEMU=$HOME/qemu/build/qemu-system-riscv64
```

### Start QEMU with TCP serial console

Open Terminal 1:

```bash
cd ~/xv6-rubicon

make qemu TOOLPREFIX=riscv64-unknown-elf- \
QEMU="$HOME/qemu/build/qemu-system-riscv64 -serial tcp:127.0.0.1:5555,server=on,wait=off -monitor none"
```

Keep this terminal running.

QEMU now exposes the xv6 serial console through TCP port 5555.

---

## 8. Starting the Python Agent

Open Terminal 2 in the same Ubuntu VM:

```bash
cd ~/xv6-rubicon/agentic

source venv/bin/activate

python agent.py
```

The Python bridge connects to the xv6 serial console.

Once connected, the user can enter supported natural-language requests.

Examples:

```text
List files
Read report.txt
Summarize report.txt
Summarize inbox.txt
```

The agent processes each request through its planning, validation and execution workflow.

---

## 9. Kernel-Level Security

The xv6 kernel implements taint tracking to prevent dangerous operations by processes that have consumed untrusted data.

### Taint Tracking

The implementation tracks taint information at two levels:

1. File/inode level — identifies files marked as untrusted.
2. Process level — records whether a process has consumed data from a tainted file.

### Taint Propagation

When a process reads a tainted file, its process taint state is updated.

Taint is inherited by child processes through `fork()`.

### Security Enforcement

The kernel checks the process taint state before allowing certain dangerous operations.

For example, a tainted process attempting to execute `unlink()` is denied.

The kernel prints a security message:

```text
SECURITY: unlink denied for tainted process
```

### Important Implementation Limitation

The standalone kernel test demonstrates taint tracking and enforcement within an xv6 process and its forked child.

However, the current Python bridge executes separate xv6 shell commands as separate processes. Taint does not automatically persist from one such command to the next.

Therefore, standalone kernel enforcement should not be confused with complete persistent taint continuity across separate Python-agent operations.

---

## 10. Manual Bridge Testing

Before starting the Python agent, the TCP connection can be tested manually.

Start QEMU using Section 7.

Open another Ubuntu terminal:

```bash
nc 127.0.0.1 5555
```

Press Enter if the prompt is not visible.

At the xv6 shell:

```bash
ls
```

If the command works, the TCP connection is functioning.

Exit the `nc` client before starting the Python agent.

Do not run `nc` and the Python agent simultaneously against the same serial console.

---

## 11. Prompt-Injection Test Scenario

The project uses a scenario involving three files:

| File | Purpose |
|---|---|
| report.txt | Contains trusted report information |
| inbox.txt | Contains untrusted content and malicious instructions |
| important.txt | Represents a file that should not be deleted |

The intended scenario is:

1. The user asks the agent to summarize `inbox.txt`.
2. The agent reads the file.
3. The file contains instructions attempting to manipulate the agent.
4. The agent should treat the file contents as data rather than trusted instructions.
5. A prohibited deletion operation is proposed in the security test.
6. The kernel-level taint mechanism should reject the operation when executed by a tainted process.
7. The test verifies that `important.txt` remains intact.

The Python-agent workflow and standalone kernel enforcement test must be evaluated separately until persistent cross-command taint continuity is implemented.

---

## 12. Troubleshooting

### Connection refused

- Confirm QEMU is running.
- Confirm the TCP serial option is configured.
- Confirm the bridge uses port 5555.

### Address already in use

Another process is listening on port 5555.

Stop the previous QEMU or serial-console process before starting a new instance.

### Agent connects but commands do not work

- Check that no `nc` client is connected.
- Ensure only one Python agent controls the serial console.
- Restart QEMU before restarting the agent.

### Ollama connection failure

- Confirm Ollama is installed.
- Confirm the Ollama service is running.
- Confirm the model is available.

Check installed models:

```bash
ollama list
```

### Model not found

```bash
ollama pull qwen2.5:0.5b
```

### Scenario files missing

Check the xv6 filesystem:

```bash
ls
```

Remember that rebuilding or recreating `fs.img` can remove previously added scenario files. Recreate the required files when necessary.

---

## 13. Normal Startup Checklist

1. Start the Ubuntu VM.
2. Confirm Ollama is running.
3. Confirm the Qwen model is installed.
4. Open Terminal 1 and start QEMU.
5. Wait for xv6 to boot.
6. Open Terminal 2.
7. Activate the Python virtual environment.
8. Start `agent.py`.
9. Enter supported requests.
10. Check the output and security logs.

---

## 14. Reproducibility Notes

The documented configuration reflects the development environment used for this project.

The following values may differ on another machine:
- Repository location.
- QEMU installation path.
- RISC-V toolchain path.
- Python virtual environment path.

The QEMU TCP server and Python bridge must use the same host and port.

The LLM runs locally through Ollama, so the project does not require a paid cloud LLM API.

The Python agent, bridge, and xv6 kernel provide separate layers of functionality and security. Kernel enforcement remains important because application-level validation alone cannot guarantee operating-system security.