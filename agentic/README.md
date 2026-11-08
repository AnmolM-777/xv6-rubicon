# Agentic AI Integration with xv6

A Python-based agent that uses a local Ollama language model to select from a restricted set of structured tools. The tools communicate with an xv6 guest through a TCP serial bridge. Python validates proposed tool calls, while xv6 enforces the final file-deletion restriction in the kernel using process and inode taint tracking.

## 1. Architecture

```text
User request
    |
    v
Local LLM planner (Ollama / Qwen 2.5 0.5B)
    |
    v
Structured tool call
    |
    v
Python validator (allowlist, schema and path checks)
    |
    v
Tool dispatcher
    |
    v
TCP serial bridge (127.0.0.1:5555)
    |
    v
Persistent xv6 shell in QEMU
    |
    v
xv6 user programs and kernel
    |
    v
Observation returned to the agent
```

The LLM proposes a tool call; it does not receive unrestricted shell access. The validator checks the tool name and arguments. The bridge sends commands constructed by registered tool implementations. Kernel policy is the final enforcement layer for tainted-process deletion attempts.

## 2. Available Tools

| Tool | Purpose |
|---|---|
| `list_files` | Lists files in the xv6 guest using `ls`. |
| `read_file` | Reads an allowed filename from the xv6 guest using `cat`. |
| `summarize` | Summarizes supplied text with the local LLM. |
| `read_and_summarize` | Reads a guest file and summarizes its contents. |

The Python validator accepts only registered tool names, checks exact argument keys and types, and restricts filenames to a simple filename pattern. It rejects path separators and unsafe paths. There is no registered delete tool.

## 3. Requirements

- Ubuntu Linux environment (QEMU guest and Python agent must run in the same Ubuntu environment).
- xv6 RISC-V toolchain: `riscv64-unknown-elf-gcc` and related tools.
- QEMU with the RISC-V system emulator.
- Python 3.
- Ollama and the `qwen2.5:0.5b` model.
- Python package: `ollama`.

The project was developed and tested in an Ubuntu ARM64 virtual machine on an Apple Silicon Mac. Commands and installed toolchain versions may differ on another machine.

## 4. Build xv6

From the repository root in Ubuntu:

```bash
cd ~/xv6-rubicon
make clean
make TOOLPREFIX=riscv64-unknown-elf- QEMU="$HOME/qemu/build/qemu-system-riscv64"
```

A clean build recreates `fs.img`. The Makefile includes the scenario files `report.txt`, `inbox.txt`, and `important.txt` in the guest filesystem image.

## 5. Start the xv6 Guest and TCP Serial Bridge

In the first Ubuntu terminal, from the repository root:

```bash
cd ~/xv6-rubicon
make qemu TOOLPREFIX=riscv64-unknown-elf- QEMU="$HOME/qemu/build/qemu-system-riscv64 -serial tcp:127.0.0.1:5555,server=on,wait=off -monitor none"
```

Keep QEMU running. The serial console is exposed on TCP port 5555 on the same Ubuntu VM.

Do not connect with `nc` while the Python bridge is using the port: the serial connection is intended for one client at a time.

## 6. Set Up the Python Agent

Open a second Ubuntu terminal:

```bash
cd ~/xv6-rubicon/agentic
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Make sure the Ollama service is running and the model is available:

```bash
ollama pull qwen2.5:0.5b
ollama list
```

If Ollama is not already running as a service, start it in another terminal:

```bash
ollama serve
```

## 7. Run the Agent

With QEMU running and the Python virtual environment activated, from `~/xv6-rubicon/agentic`:

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

The bridge connects to `127.0.0.1:5555`. Therefore, run the Python agent in the same Ubuntu VM as QEMU, not directly on the Mac host unless the bridge address and network setup are deliberately changed.

## 8. Run Tests

The project contains unit tests, integration tests, and manual diagnostic scripts. Some tests require external components such as the xv6 guest, QEMU, and Ollama.

### 8.1 Python Unit Tests

From `~/xv6-rubicon/agentic`, with the Python virtual environment activated:

```bash
python -m unittest discover -s tests/unit -v
```

The recorded unit-test run contains 23 passing tests covering the bridge, planner, tools, validator, and prompt-injection validation.

### 8.2 xv6 Taint Test

From the xv6 shell, run:

```text
tainttest
```

The test exercises trusted and untrusted reads, benign operations after taint, fork inheritance, and kernel denial of an unlink attempt by a tainted process.

### 8.3 Prompt-Injection / Kernel Enforcement Demonstration

With QEMU running, Ollama available, and the Python virtual environment activated, from `~/xv6-rubicon/agentic`:

```bash
python tests/integration/test_llm_injection.py
```

This test writes malicious instructions into `inbox.txt`, marks that guest file tainted, asks the agent to summarize it, attempts to delete `important.txt` through the persistent xv6 bridge session, and checks that the kernel denies the unlink and that the important file remains.

A separate validator demonstration can be run with:

```bash
python tests/integration/test_prompt_injection.py
```

The xv6 tools integration test can be run with:

```bash
python tests/integration/test_xv6_tools.py
```

Run the integration demonstrations only in the disposable xv6/QEMU guest used for this project.

### 8.4 Manual Diagnostic Scripts

The `tests/manual/` directory contains scripts used for individual experiments and debugging:

- `test_llm_agent.py`
- `test_llm_planner.py`
- `test_ollama.py`
- `test_tool_call.py`
- `api_test.py`

These scripts are not part of the regular unit-test discovery command. The OpenAI API test is an earlier experiment and is not required for the current Ollama-based implementation.

## 9. Development and Execution Environments

Development and execution are performed in separate environments.

### Mac — Development Environment

The Mac is used for:

- Editing source code in VS Code.
- Managing Git branches and commits.
- Reviewing changes and pushing to GitHub.
- Running tests that do not require external services.

QEMU and the xv6 guest are not installed on the Mac development environment.

Tests requiring the xv6 TCP bridge or Ollama may fail if the corresponding services are unavailable.

### Ubuntu VM — Execution Environment

The Ubuntu VM is used for:

- Building and running xv6 with QEMU.
- Running the RISC-V toolchain.
- Running the Python agent and TCP bridge.
- Running Ollama and the configured language model.
- Executing QEMU-dependent integration tests.

The Python bridge connects to `127.0.0.1:5555`. Therefore, the Python agent and QEMU must run in the same Ubuntu VM unless the networking configuration is deliberately changed.

The complete integration test suite should be executed in Ubuntu with the required services running.

## 10. Kernel Taint-Tracking Design

- **Inode taint:** A tainted flag is stored in the in-memory inode and on-disk dinode. The `taintfile` system call marks a file's inode as tainted.
- **Read propagation:** Reading a tainted inode through `fileread()` marks the current process tainted.
- **Fork propagation:** `kfork()` copies the parent's taint state to the child.
- **Wait propagation:** `kwait()` propagates a tainted child's state back to its parent when the child is collected. This supports the persistent-shell bridge scenario across sequential commands.
- **Enforcement:** `sys_unlink()` rejects deletion when the calling process is tainted and prints a security-denial message.

The kernel check is important because Python-side validation alone cannot stop a process from attempting a filesystem operation through another path.

## 11. Security Scope and Limitations

This is a teaching prototype, not a complete information-flow security system.

- Taint propagation currently covers file reads, fork inheritance, and child-to-parent propagation through wait. It is not implemented for every possible information-flow channel, including pipes.
- Executing a tainted executable is not currently shown to propagate taint to the new process image.
- The `taintfile` system call is a demonstration mechanism; a production system would need a carefully defined authorization model for who may mark files tainted.
- The Python path checks and fixed tool implementations constrain the agent interface, but they are not a general sandbox for arbitrary host commands.
- Prompt-injection tests demonstrate the specific malicious-inbox scenario. They do not prove immunity to all prompt-injection attacks.
- The bridge expects a persistent xv6 shell and one TCP client. Reconnection and multi-client handling are not fully implemented.
- LLM output can vary. The deterministic validation layer and kernel policy must remain in place regardless of the model's response.

## 12. Main Project Files

```text
agentic/
    agent.py
    llm_planner.py
    planner.py
    validator.py
    schemas.py
    tools.py
    bridge.py
    config.py
    requirements.txt
    README.md
    Agent_setup.md

    scenarios/
        important.txt
        inbox.txt
        report.txt

    tests/
        unit/
        integration/
        manual/
        test_results.txt

kernel/
    file.c
    file.h
    fs.c
    fs.h
    proc.c
    proc.h
    syscall.c
    syscall.h
    sysfile.c

user/
    marktaint.c
    tainttest.c
```

## 13. Test and CI Status

At the time of this documentation update:

- The recorded Python unit-test suite reports 23 passing tests in the configured Ubuntu environment.
- The GitHub Actions Linux job passed.
- The GitHub Actions macOS job passed.

The GitHub Actions workflow validates the repository build and configured xv6 tests. The Python unit tests and LLM/QEMU integration demonstrations are separate runs and should not be described as automatically executed by CI unless the workflow is extended to run them.

Tests that require QEMU or Ollama must be executed in an environment where those dependencies are available.