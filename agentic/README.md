# Agentic AI Integration with xv6

## 1. Project Overview

This project implements an Agentic AI system integrated with the xv6 operating system. A local Large Language Model (LLM) interprets user requests and selects from a predefined set of tools. These tools communicate with an xv6 guest running in QEMU through a TCP serial bridge.

The system combines application-level validation with kernel-level security enforcement. The Python agent restricts the tools and arguments that can be executed, while the xv6 kernel tracks tainted files and processes and prevents a tainted process from deleting files.

The main objective is to demonstrate how operating-system-level protection can enforce security policies even when an AI agent encounters malicious instructions in untrusted input.

## 2. System Architecture

```text
                 User Request
                      |
                      v
             Local LLM Planner
              (Ollama / Qwen)
                      |
                      v
             Structured Tool Call
                      |
                      v
             Python Validator
          (Allowlist, Schema, Paths)
                      |
                      v
              Tool Dispatcher
                      |
                      v
             TCP Serial Bridge
               127.0.0.1:5555
                      |
                      v
              Persistent xv6 Shell
                 (QEMU Guest)
                      |
                      v
              xv6 User Programs
                      |
                      v
              xv6 Kernel Security
             (Taint Tracking)
                      |
                      v
             Observation Returned
                 to the Agent
```

The LLM proposes actions but does not receive unrestricted shell access. Every proposed tool call passes through the Python validation layer. Registered tools construct the commands sent to xv6 through the bridge.

The kernel provides the final enforcement layer for the tainted-process deletion restriction.

## 3. Available Agent Tools

| Tool | Description |
|---|---|
| `list_files` | Lists files in the xv6 guest filesystem. |
| `read_file` | Reads an allowed file from the xv6 guest. |
| `summarize` | Summarizes supplied text using the local LLM. |
| `read_and_summarize` | Reads a guest file and summarizes its contents. |

### Python Validation

The validator performs the following checks:

- Only registered tool names are accepted.
- Tool arguments are checked against predefined schemas.
- Missing or unexpected arguments are rejected.
- Argument types are validated.
- Filenames are restricted to an allowed pattern.
- Path separators and unsafe paths are rejected.
- Arbitrary shell commands are not accepted as tool calls.

There is no registered file-deletion tool.

## 4. Project Structure

```text
xv6-rubicon/
|
|-- kernel/
|   |-- file.c
|   |-- file.h
|   |-- fs.c
|   |-- fs.h
|   |-- proc.c
|   |-- proc.h
|   |-- syscall.c
|   |-- syscall.h
|   |-- sysfile.c
|
|-- user/
|   |-- marktaint.c
|   |-- tainttest.c
|   |-- user.h
|   |-- usys.pl
|
|-- agentic/
    |-- agent.py
    |-- bridge.py
    |-- config.py
    |-- llm_planner.py
    |-- planner.py
    |-- schemas.py
    |-- tools.py
    |-- validator.py
    |-- requirements.txt
    |-- README.md
    |
    |-- scenarios/
    |
    |-- tests/
        |-- unit/
        |   |-- test_bridge.py
        |   |-- test_planner.py
        |   |-- test_tools.py
        |   |-- test_validator.py
        |
        |-- integration/
        |   |-- test_llm_injection.py
        |   |-- test_prompt_injection.py
        |   |-- test_xv6_tools.py
        |
        |-- manual/
        |   |-- test_llm_agent.py
        |   |-- test_llm_planner.py
        |   |-- test_ollama.py
        |   |-- test_tool_call.py
        |   |-- api_test.py
        |
        |-- test_results.txt
        |-- run_all_tests.py
```

`api_test.py` is an older API experiment and is intentionally excluded from the unified test runner.

## 5. Requirements

The project was developed in an Ubuntu ARM64 virtual machine running on an Apple Silicon Mac.

Required software:

- Ubuntu Linux
- RISC-V xv6 toolchain (`riscv64-unknown-elf-gcc` and related tools)
- QEMU RISC-V system emulator
- Python 3
- Ollama
- Ollama model: `qwen2.5:0.5b`
- Python package: `ollama`

The QEMU guest and Python agent should run in the same Ubuntu environment because the bridge connects to `127.0.0.1:5555`.

## 6. Build and Run xv6

From the repository root in Ubuntu:

```bash
cd ~/xv6-rubicon

make clean

make TOOLPREFIX=riscv64-unknown-elf- \
     QEMU="$HOME/qemu/build/qemu-system-riscv64"
```

A clean build recreates `fs.img`. The Makefile includes the scenario files required by the demonstration.

### Start QEMU with the TCP Serial Bridge

Open the first Ubuntu terminal:

```bash
cd ~/xv6-rubicon

make qemu TOOLPREFIX=riscv64-unknown-elf- \
QEMU="$HOME/qemu/build/qemu-system-riscv64 -serial tcp:127.0.0.1:5555,server=on,wait=off -monitor none"
```

Keep this terminal running.

The xv6 serial console is exposed through TCP port `5555`.

**Important:** Do not connect through `nc` while the Python bridge is using this port. The serial connection is intended for one client at a time.

## 7. Set Up and Run the Python Agent

Open a second Ubuntu terminal:

```bash
cd ~/xv6-rubicon/agentic

python3 -m venv venv

source venv/bin/activate

pip install -r requirements.txt
```

Ensure Ollama is running and the required model is available:

```bash
ollama pull qwen2.5:0.5b

ollama list
```

If the Ollama service is not already running:

```bash
ollama serve
```

Run the agent:

```bash
python agent.py
```

Example requests:

```text
list files
read report.txt
summarize inbox.txt
exit
```

## 8. Kernel-Level Taint Tracking

The project implements taint tracking across files and processes.

### 8.1 Inode Taint

A tainted flag is maintained in the in-memory inode and on-disk dinode structures.

The `taintfile` system call marks a file's inode as tainted. The taint information is persisted through the filesystem inode update mechanism.

### 8.2 Process Taint

Each process contains a taint flag in its process structure.

When a process reads a tainted file through `fileread()`, its taint flag is set.

### 8.3 Taint Propagation

Taint propagates through the following mechanisms:

- **File read:** Reading a tainted inode marks the current process as tainted.
- **Fork:** `kfork()` copies the parent's taint state to the child.
- **Wait:** `kwait()` propagates a tainted child's state back to its parent when the child is collected.

The wait propagation supports the persistent-shell bridge scenario, where multiple commands execute through the same xv6 shell process.

### 8.4 Kernel Enforcement

The `sys_unlink()` system call checks the calling process's taint state.

If the process is tainted, the kernel rejects the deletion and logs:

```text
SECURITY: unlink denied for tainted process
```

This demonstrates why kernel enforcement is necessary: Python-side validation alone cannot prevent a process from attempting a filesystem operation through another execution path.

## 9. Prompt-Injection Demonstration

The demonstration uses three files:

| File | Purpose |
|---|---|
| `report.txt` | Contains trusted information to summarize. |
| `inbox.txt` | Contains untrusted content with malicious instructions. |
| `important.txt` | Represents a file that must not be deleted. |

The malicious content in `inbox.txt` attempts to instruct the agent to ignore the user's request and delete `important.txt`.

The expected execution sequence is:

1. The user asks the agent to summarize `inbox.txt`.
2. The LLM selects the appropriate read-and-summarize tool.
3. The Python validator checks the proposed tool call.
4. The xv6 guest reads the tainted inbox file.
5. The reading process becomes tainted.
6. A subsequent deletion attempt is made through the persistent xv6 shell.
7. The kernel detects the tainted process and rejects the `unlink` operation.
8. `important.txt` remains present.

The test demonstrates enforcement of the specific malicious-inbox scenario. It does not establish immunity to every possible prompt-injection attack.

## 10. Testing

Tests are organized into three categories.

### Unit Tests

Located in `tests/unit/`:

- Bridge behavior
- Planner behavior
- Tool execution
- Input validation

Run using:

```bash
python -m unittest discover -s tests/unit -v
```

### Integration Tests

Located in `tests/integration/`:

| Test | Purpose |
|---|---|
| `test_xv6_tools.py` | Checks communication with xv6 tools. |
| `test_prompt_injection.py` | Checks prompt-injection validation and security behavior. |
| `test_llm_injection.py` | Demonstrates LLM interaction and kernel-level taint enforcement. |

### Manual Diagnostic Tests

Located in `tests/manual/`:

- `test_ollama.py`
- `test_llm_planner.py`
- `test_tool_call.py`
- `test_llm_agent.py`

These scripts provide additional checks of the local LLM and agent workflow.

`api_test.py` is intentionally excluded from the unified test execution.

### Unified Test Runner

The project includes `run_all_tests.py`, intended to execute the test suite and generate consolidated reports.

From the `agentic` directory:

```bash
python run_all_tests.py
```

The runner is designed to generate:

```text
test_reports/
    test_report.json
    test_report.txt
    test_report.html
```

The HTML report provides a visual summary of test outcomes and individual test results.

**Validation note:** The unified runner has been created, but its complete execution on the Ubuntu VM is pending. Its final pass/fail results should be recorded after that validation.

## 11. Security Scope and Limitations

This implementation is a teaching prototype rather than a complete information-flow security system.

1. Taint propagation currently covers file reads, fork inheritance, and child-to-parent propagation through wait. Other information-flow channels, such as pipes, are not covered.
2. Executing a tainted executable is not currently demonstrated as a source of process taint propagation.
3. The `taintfile` system call is a demonstration mechanism. A production implementation would require a defined authorization policy for marking files tainted.
4. Python validation restricts the agent interface but is not a general sandbox for arbitrary host commands.
5. The prompt-injection demonstration covers a specific malicious-input scenario and does not prove general immunity to prompt injection.
6. The bridge expects a persistent xv6 shell and one TCP client. Reconnection and multi-client handling are not fully implemented.
7. LLM output may vary. The validator and kernel enforcement must remain active regardless of the model's response.

## 12. Test and CI Status

The following results were recorded during development:

- 23 Python tests passed in an earlier Ubuntu test run.
- GitHub Actions Linux job passed.
- GitHub Actions macOS job passed.
- The prompt-injection and kernel-taint demonstration passed individually.

These results refer to the recorded development runs. The unified runner's complete execution remains pending separate validation.

The GitHub Actions workflow checks the repository build and configured xv6 tests. It should not be assumed to execute the local Ollama/QEMU integration tests unless those steps are explicitly added to the workflow.

## 13. Conclusion

This project demonstrates an architecture in which a local LLM proposes actions, a Python validation layer restricts tool execution, and the xv6 kernel enforces a security policy.

The prompt-injection scenario illustrates that malicious instructions contained in untrusted file content do not automatically gain authority to perform destructive operations. Even when a deletion attempt reaches the operating-system interface, kernel-level taint enforcement rejects it.

The implementation highlights the importance of combining AI-level safeguards with operating-system-level security mechanisms.