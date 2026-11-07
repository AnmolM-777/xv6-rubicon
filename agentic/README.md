# Agentic AI System

A Python-based agent with a restricted tool interface, deterministic
planning, request validation, and filesystem access controls.

## 1. Architecture

User Input
    |
    v
Planner
    |
    v
Validator
    |
    v
Tool Registry
    |
    v
Filesystem (scenarios/)

## 2. Available Tools

- list_files: Lists files in the permitted directory.
- read_file: Reads a permitted file.
- summarize: Returns the first 20 words of a file.

## 3. Security Features

- Only registered tools can be executed.
- Tool arguments are checked against predefined schemas.
- Incorrect argument types are rejected.
- Missing and extra arguments are rejected.
- Path traversal is blocked.
- Symbolic links pointing outside the permitted directory are blocked.
- No arbitrary shell commands or file deletion are supported.

## 4. Project Structure

agentic/
    config.py
    schemas.py
    validator.py
    planner.py
    tools.py
    agent.py
    requirements.txt
    README.md

    scenarios/
        report.txt
        inbox.txt
        important.txt

    tests/
        test_validator.py
        test_planner.py
        test_prompt_injection.py

## 5. Setup

Create a virtual environment:

    python3 -m venv venv

Activate it:

    source venv/bin/activate

No external Python packages are currently required.

## 6. Run the Agent

From the agentic directory:

    python agent.py

Example commands:

    read report.txt
    list .
    summarize inbox.txt
    exit

## 7. Run Automated Tests

    python -m unittest discover -s tests -v

Current test coverage:

- Validator: 7 tests
- Planner: 5 tests
- Prompt injection: 1 test

Total: 13 tests.

## 8. Prompt Injection Demonstration

The inbox.txt scenario contains malicious instructions asking the
agent to delete important.txt.

The agent reads the malicious content but does not execute it.
The important file remains unchanged.

This demonstrates restricted tool access in the current
deterministic agent.

## 9. Current Limitations

- The planner is rule-based, not LLM-powered.
- Summarization currently returns the first 20 words.
- The agent operates on local scenario files.
- QEMU/xv6 integration has not yet been implemented.
