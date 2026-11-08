"""
AGENTIC AI - COMPLETE DEMONSTRATION TEST RUNNER

BEFORE RUNNING:

1. Start xv6/QEMU in Terminal 1.
2. Make sure Ollama is running.
3. Open another terminal:

   cd ~/xv6-rubicon/agentic
   source venv/bin/activate
   python run_all_tests.py

The script automatically:
- Runs Python unit tests.
- Runs xv6 integration tests.
- Runs prompt-injection and kernel-taint tests.
- Runs Ollama and LLM diagnostic tests.
- Generates HTML, JSON and TXT reports.

NOTE:
- Do not connect to port 5555 using nc.
- Run inside Ubuntu, not Mac.
- api_test.py is intentionally excluded.
"""

import os
import sys
import json
import html
import subprocess
import urllib.request

from pathlib import Path
from datetime import datetime


BASE_DIR = Path(__file__).resolve().parent
REPORT_DIR = BASE_DIR / "test_reports"

REPORT_DIR.mkdir(exist_ok=True)

results = []


# ---------------------------------------------------------
# Run one test and record its output
# ---------------------------------------------------------

def run_test(name, command, timeout=300):

    print("\n" + "=" * 65)
    print("RUNNING:", name)
    print("=" * 65)

    start = datetime.now()

    # Make parent directory available for Python imports.
    env = os.environ.copy()
    env["PYTHONPATH"] = (
        str(BASE_DIR) + os.pathsep + env.get("PYTHONPATH", "")
    )

    try:
        process = subprocess.run(
            command,
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env
        )

        output = process.stdout + process.stderr

        status = "PASS" if process.returncode == 0 else "FAIL"

    except subprocess.TimeoutExpired as e:

        output = e.stdout or ""

        if isinstance(output, bytes):
            output = output.decode(errors="replace")

        error = e.stderr or ""

        if isinstance(error, bytes):
            error = error.decode(errors="replace")

        output += error
        output += "\nTest timed out."

        status = "FAIL"

    except Exception as e:

        output = str(e)
        status = "FAIL"

    duration = (datetime.now() - start).total_seconds()

    print(output)
    print("\nRESULT:", status)
    print("TIME:", round(duration, 2), "seconds")

    results.append({
        "name": name,
        "status": status,
        "duration": round(duration, 2),
        "output": output
    })


# ---------------------------------------------------------
# Check Ollama connection
# ---------------------------------------------------------

def check_ollama():

    print("\nChecking Ollama connection...")

    try:
        request = urllib.request.Request(
            "http://127.0.0.1:11434/api/tags"
        )

        with urllib.request.urlopen(request, timeout=5) as response:

            if response.status == 200:
                print("Ollama is reachable.")
                return True

    except Exception:
        pass

    print("Ollama is not reachable.")
    print("Start it using: ollama serve")

    return False


# ---------------------------------------------------------
# Run all tests
# ---------------------------------------------------------

def main():

    print("\n" + "=" * 65)
    print("       AGENTIC AI - COMPLETE TEST EXECUTION")
    print("=" * 65)

    print("Started:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    if not check_ollama():

        print("\nCannot continue without Ollama.")
        print("Start Ollama and run this script again.")
        sys.exit(1)

    # -----------------------------------------------------
    # 1. Python unit tests
    # -----------------------------------------------------

    print("\n\n[1/3] PYTHON UNIT TESTS")

    run_test(
        "Python Unit Tests",
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            "tests/unit",
            "-v"
        ]
    )

    # -----------------------------------------------------
    # 2. xv6 integration tests
    # -----------------------------------------------------

    print("\n\n[2/3] XV6 INTEGRATION TESTS")

    integration_tests = [
        (
            "xv6 Tools Test",
            "tests/integration/test_xv6_tools.py"
        ),
        (
            "Prompt Injection Test",
            "tests/integration/test_prompt_injection.py"
        ),
        (
            "LLM + Kernel Taint Test",
            "tests/integration/test_llm_injection.py"
        )
    ]

    for name, file_path in integration_tests:

        path = BASE_DIR / file_path

        if path.exists():

            run_test(
                name,
                [sys.executable, str(path)]
            )

        else:

            results.append({
                "name": name,
                "status": "SKIP",
                "duration": 0,
                "output": "File not found: " + file_path
            })

    # -----------------------------------------------------
    # 3. Ollama / LLM diagnostic tests
    # -----------------------------------------------------

    print("\n\n[3/3] OLLAMA AND LLM DIAGNOSTICS")

    manual_tests = [
        (
            "Ollama Connectivity Test",
            "tests/manual/test_ollama.py"
        ),
        (
            "LLM Planner Test",
            "tests/manual/test_llm_planner.py"
        ),
        (
            "Structured Tool Call Test",
            "tests/manual/test_tool_call.py"
        ),
        (
            "LLM Agent Test",
            "tests/manual/test_llm_agent.py"
        )
    ]

    for name, file_path in manual_tests:

        path = BASE_DIR / file_path

        if path.exists():

            run_test(
                name,
                [sys.executable, str(path)]
            )

        else:

            results.append({
                "name": name,
                "status": "SKIP",
                "duration": 0,
                "output": "File not found: " + file_path
            })

    generate_reports()


# ---------------------------------------------------------
# Generate TXT, JSON and HTML reports
# ---------------------------------------------------------

def generate_reports():

    passed = sum(r["status"] == "PASS" for r in results)
    failed = sum(r["status"] == "FAIL" for r in results)
    skipped = sum(r["status"] == "SKIP" for r in results)

    total = len(results)

    report = {
        "date": datetime.now().isoformat(),
        "summary": {
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "total": total
        },
        "tests": results
    }

    # JSON report
    with open(REPORT_DIR / "test_report.json", "w") as f:
        json.dump(report, f, indent=4)

    # Text report
    with open(REPORT_DIR / "test_report.txt", "w") as f:

        f.write("AGENTIC AI TEST REPORT\n")
        f.write("=" * 60 + "\n\n")

        for r in results:

            f.write(
                f"{r['status']} | {r['name']} | "
                f"{r['duration']} seconds\n"
            )

            f.write(r["output"] + "\n\n")

        f.write("\nPASSED: " + str(passed))
        f.write("\nFAILED: " + str(failed))
        f.write("\nSKIPPED: " + str(skipped))
        f.write("\nTOTAL: " + str(total))

    # HTML dashboard
    colors = {
        "PASS": "#16a34a",
        "FAIL": "#dc2626",
        "SKIP": "#d97706"
    }

    bars = ""
    y = 65

    for r in results:

        label = html.escape(r["name"])
        color = colors[r["status"]]

        bars += f"""
        <text x="15" y="{y}" font-size="13">{label}</text>
        <rect x="290" y="{y-15}" width="230"
              height="20" rx="4" fill="{color}"/>
        <text x="535" y="{y}" font-size="13">
            {r["status"]}
        </text>
        """

        y += 42

    details = ""

    for r in results:

        details += f"""
        <div class="test">
            <h3>{html.escape(r["name"])}
                - {r["status"]}</h3>
            <p>Duration: {r["duration"]} seconds</p>
            <pre>{html.escape(r["output"])}</pre>
        </div>
        """

    dashboard = f"""
    <html>
    <head>
        <title>Agentic AI Test Dashboard</title>

        <style>
            body {{
                font-family: Arial, sans-serif;
                background: #f4f6fa;
                color: #172033;
                margin: 35px;
            }}

            .card {{
                background: white;
                padding: 22px;
                border-radius: 12px;
                margin-bottom: 20px;
            }}

            .stats {{
                display: flex;
                gap: 35px;
                font-size: 21px;
            }}

            .PASS {{ color: #16a34a; }}
            .FAIL {{ color: #dc2626; }}
            .SKIP {{ color: #d97706; }}

            pre {{
                background: #f1f3f7;
                padding: 12px;
                border-radius: 8px;
                white-space: pre-wrap;
                overflow-wrap: anywhere;
            }}

            .test {{
                border-bottom: 1px solid #ddd;
                padding: 10px 0;
            }}
        </style>
    </head>

    <body>

        <h1>Agentic AI - Test Dashboard</h1>

        <p>Generated: {datetime.now()}</p>

        <div class="card stats">
            <div class="PASS">Passed: {passed}</div>
            <div class="FAIL">Failed: {failed}</div>
            <div class="SKIP">Skipped: {skipped}</div>
        </div>

        <div class="card">
            <h2>Test Execution Overview</h2>

            <svg width="650" height="{y}">
                {bars}
            </svg>
        </div>

        <div class="card">
            <h2>Detailed Test Results</h2>
            {details}
        </div>

    </body>
    </html>
    """

    with open(REPORT_DIR / "test_report.html", "w") as f:
        f.write(dashboard)

    # Final summary
    print("\n" + "=" * 65)
    print("             FINAL TEST SUMMARY")
    print("=" * 65)

    print("Passed :", passed)
    print("Failed :", failed)
    print("Skipped:", skipped)
    print("Total  :", total)

    print("\nReports saved in:")
    print(REPORT_DIR)

    print("\nOpen the visual dashboard using:")
    print("xdg-open test_reports/test_report.html")

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
