# Agentic AI Integration with xv6

**Course:** CSL3030 – Operating Systems Lab
**Project:** Agentic AI and Kernel-Level Taint Tracking

## 1. Overview

This project implements an AI-powered agent that interacts with an xv6 operating system running inside QEMU.

The agent accepts natural-language requests, uses an LLM to select predefined tools, validates the proposed actions, and executes approved commands inside the xv6 environment through a Python-to-QEMU bridge.

The project also implements kernel-level taint tracking to demonstrate how the operating system can prevent potentially dangerous operations performed by processes influenced by untrusted data.

The main objective is to demonstrate that AI-generated actions should not be trusted directly. Tool-level validation and kernel-level security enforcement are both necessary.

## 2. System Architecture

The system consists of the following components:

1. **Python Agent:** Receives user requests and manages the execution workflow.
2. **LLM Planner:** Uses Ollama with the `qwen2.5:0.5b` model to interpret requests and propose structured tool calls.
3. **Tool Validator:** Checks tool names, arguments, and file paths before execution.
4. **Python-to-xv6 Bridge:** Communicates with the xv6 shell through a TCP connection.
5. **xv6 User Space:** Executes approved commands inside the guest operating system.
6. **Kernel Security Layer:** Tracks tainted files and processes and enforces restrictions on selected operations.

### Execution Flow

```text
User Request
     |
     v
Python Agent
     |
     v
LLM Planner (Ollama)
     |
     v
Structured Tool Call
     |
     v
Tool Validator
     |
     v
Python Tool Execution
     |
     v
QEMU TCP Bridge
     |
     v
xv6 Shell / User Programs
     |
     v
xv6 Kernel
     |
     v
Execution Result
     |
     v
Observation Returned to Agent
```

The LLM proposes actions, but it does not directly execute arbitrary shell commands.

## 3. Repository Structure

Important project files and directories:

```text
xv6-rubicon/
│
├── agentic/
│   ├── agent.py
│   ├── llm_planner.py
│   ├── schemas.py
│   ├── validator.py
│   ├── tools.py
│   ├── bridge.py
│   ├── requirements.txt
│   ├── README.md
│   ├── run_all_tests.py
│   ├── scenarios/
│   └── test_reports/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── manual/
│
├── kernel/
│   ├── proc.c
│   ├── proc.h
│   ├── file.c
│   ├── file.h
│   ├── fs.c
│   ├── fs.h
│   ├── sysfile.c
│   ├── syscall.c
│   └── syscall.h
│
├── user/
│   ├── marktaint.c
│   ├── tainttest.c
│   ├── user.h
│   └── usys.pl
│
└── Makefile
```

## 4. Requirements

The project was developed and tested using:

- Ubuntu ARM64 virtual machine on an Apple M1 host.
- xv6-riscv.
- QEMU.
- RISC-V cross-compilation toolchain.
- Python 3.
- Ollama.
- `qwen2.5:0.5b` language model.

The Python agent and QEMU guest should run inside the same Ubuntu VM because the bridge connects to `127.0.0.1:5555`.

## 5. Build and Run xv6

Navigate to the repository:

```bash
cd ~/xv6-rubicon
```

Build xv6:

```bash
make clean
make TOOLPREFIX=riscv64-unknown-elf-
```

Start QEMU with the TCP serial bridge:

```bash
make qemu TOOLPREFIX=riscv64-unknown-elf- QEMU="$HOME/qemu/build/qemu-system-riscv64 -serial tcp:127.0.0.1:5555,server=on,wait=off -monitor none"
```

Keep this terminal running.

The xv6 shell is now accessible through the TCP connection on port `5555`.

## 6. Set Up the Python Agent

Open a second Ubuntu terminal:

```bash
cd ~/xv6-rubicon/agentic
```

Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

Install the required Python dependency:

```bash
pip install -r requirements.txt
```

### Set Up Ollama

Make sure Ollama is installed and running.

Download the model:

```bash
ollama pull qwen2.5:0.5b
```

Verify that the model is available:

```bash
ollama list
```

If Ollama is not already running as a service, start it in another terminal:

```bash
ollama serve
```

## 7. Run the Agent

With QEMU running and the Python virtual environment activated:

```bash
cd ~/xv6-rubicon/agentic
python agent.py
```

Example requests:

```text
list files
read report.txt
summarize inbox.txt
exit
```

The agent uses predefined tools to interact with xv6.

### Implemented Tools

| Tool | Purpose |
|---|---|
| `list_files` | Lists files inside the xv6 guest |
| `read_file` | Reads an approved file |
| `summarize` | Summarizes supplied text |
| `read_and_summarize` | Reads and summarizes a file |

Tool calls are validated before execution. File access is restricted to the configured scenario directory.

## 8. Python-to-xv6 Bridge

The bridge is implemented in:

```text
agentic/bridge.py
```

It establishes a TCP connection to:

```text
127.0.0.1:5555
```

The bridge:

- Establishes a connection with the xv6 serial console.
- Sends commands to the xv6 shell.
- Waits for the shell prompt to identify command completion.
- Captures command output.
- Handles connection errors and timeouts.
- Closes the socket when an execution error occurs.
- Allows a new connection to be created when the previous socket has been closed.

The bridge maintains a persistent shell connection during normal operation.

### Bridge Recovery

The bridge recovery mechanism is implemented through `get_bridge()` in `agentic/tools.py`.

If the previous socket is closed, the next tool invocation creates a new `XV6Bridge` instance.

This recovery behavior was tested by deliberately closing the existing socket and verifying that a new bridge could successfully execute `list_files()`.

Note: This verifies recovery after socket closure. Automatic retry of a command after an uncertain execution failure is intentionally not performed.

## 9. Kernel-Level Taint Tracking

Kernel-level taint tracking is implemented to prevent selected dangerous operations by processes influenced by untrusted files.

### 9.1 File Tainting

A new system call named `taintfile()` marks a file as tainted.

The taint information is stored in the inode structure and persisted through the filesystem metadata.

### 9.2 Process Tainting

When a process reads a tainted file, its taint flag is set.

The relevant implementation is in:

```text
kernel/file.c
```

### 9.3 Taint Propagation

Taint propagates through relevant process operations:

- A child process inherits its parent's taint during `fork()`.
- A parent process inherits taint from a tainted child when collecting its exit status through `wait()`.

The process taint flag is maintained in:

```text
kernel/proc.h
```

### 9.4 Kernel Enforcement

The kernel restricts `unlink()` when the calling process is tainted.

The enforcement is implemented in:

```text
kernel/sysfile.c
```

When a tainted process attempts to delete a file, the kernel rejects the operation and prints:

```text
SECURITY: unlink denied for tainted process
```

This demonstrates that security enforcement occurs inside the operating system rather than relying only on Python-side validation.

**Scope limitation:** The current implementation enforces this policy for `unlink()`. It does not claim to prevent every possible destructive operation or provide complete information-flow security.

## 10. Prompt Injection Demonstration

The project includes a controlled prompt-injection scenario using files inside the xv6 guest.

### Scenario Files

`report.txt` contains ordinary project information.

`inbox.txt` contains ordinary information along with a malicious instruction asking the agent to delete:

```text
important.txt
```

The agent is asked to summarize the files.

The malicious text is treated as untrusted file content rather than an authoritative instruction.

A repeatable test planner proposes the prohibited action after reading the malicious content.

The taint-tracking mechanism then demonstrates that a tainted process cannot perform the protected `unlink()` operation.

### Expected Security Result

```text
SECURITY: unlink denied for tainted process
```

The file `important.txt` remains present in the xv6 filesystem.

This demonstrates the importance of enforcing security policies at the kernel level, even when an AI agent or an application layer proposes an unsafe action.

## 11. Running Tests

The project contains unit, integration, and manual diagnostic tests.

### 11.1 Python Unit Tests

From the repository root:

```bash
cd ~/xv6-rubicon
python -m unittest discover -s tests/unit -v
```

The latest recorded unit-test run passed all 22 tests.

### 11.2 Complete Test Runner

Run the unified test runner:

```bash
python agentic/run_all_tests.py
```

The runner executes the configured unit tests, xv6 integration tests, prompt-injection tests, and manual LLM diagnostics.

Ollama must be available for the LLM-dependent checks, and QEMU must be running for the xv6 integration tests.

The latest complete test run produced:

```text
FINAL TEST SUMMARY

Passed : 8
Failed : 0
Skipped: 0
Total  : 8
```

### 11.3 Test Reports

The unified test runner generates reports in:

```text
agentic/test_reports/
```

Open the HTML dashboard:

```bash
cd ~/xv6-rubicon/agentic
xdg-open test_reports/test_report.html
```

The dashboard provides a visual summary of the test execution results.

## 12. Verified Results

The following checks have been completed:

| Test | Result |
|---|---|
| Python unit tests | 22/22 passed |
| xv6 tool integration | Passed |
| Prompt-injection demonstration | Passed |
| LLM and kernel taint test | Passed |
| Ollama connectivity | Passed |
| LLM planner | Passed |
| Structured tool-call validation | Passed |
| LLM agent execution | Passed |
| Bridge normal operation | Passed |
| Bridge recovery after socket closure | Passed |
| Unified test runner | 8/8 passed |
| HTML dashboard generation | Verified |

These results describe the latest recorded test runs and the separate bridge recovery check.

## 13. Security Considerations and Limitations

- The LLM is not trusted to generate executable shell commands.
- Tool calls are validated before execution.
- File paths are restricted to the configured scenario directory.
- The bridge communicates with the xv6 guest rather than providing unrestricted host-shell access.
- Kernel-level taint tracking provides an additional security boundary.
- The current kernel policy specifically restricts `unlink()` for tainted processes.
- The implementation does not guarantee complete protection against all forms of prompt injection.
- The TCP bridge uses shell-prompt detection and is intended for this controlled lab environment.
- Automatic command retry is not implemented because a failed response does not prove that the original command was never executed.

## 14. Conclusion

This project demonstrates the integration of an LLM-based agent with a modified xv6 operating system.

It combines structured tool calls, Python-side validation, a TCP bridge to QEMU, and kernel-level taint tracking.

The prompt-injection scenario demonstrates why application-level safeguards alone are insufficient and why the operating system must enforce critical security policies independently.

The implementation and its unified test suite have been successfully executed in the Ubuntu/QEMU environment.

---
