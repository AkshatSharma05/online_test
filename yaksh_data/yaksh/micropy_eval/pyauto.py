#!/usr/bin/env python3
import subprocess
import time
import sys
import os
import signal
import argparse

# ===================== LOGGING =====================

def log(msg):
    msg = str(msg)
    print(msg)
    sys.stderr.write(msg + "\n")
    sys.stderr.flush()

# ===================== CONFIG ======================

DEFAULT_EXEC_TIME = 3.0  # seconds

MICROPYTHON = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "micropython"
)

# ===================== ARGS ========================

parser = argparse.ArgumentParser(
    description="Run MicroPython script (grader-safe, no QEMU)"
)
parser.add_argument(
    "script",
    nargs="?",
    default="./main.py",
    help="Path to MicroPython .py script"
)
parser.add_argument(
    "-o", "--output",
    dest="output",
    default=None,
    help="File to write console output"
)
args = parser.parse_args()

SCRIPT = os.path.abspath(args.script)
OUTPUT_FILE = os.path.abspath(args.output) if args.output else None

# ===================== VALIDATION ==================

log("=== pyauto starting (micropython mode) ===")
log(f"MicroPython     : {MICROPYTHON}")
log(f"Script path     : {SCRIPT}")
log(f"Output file     : {OUTPUT_FILE}")

if not os.path.exists(MICROPYTHON):
    log(f"ERROR: micropython executable not found: {MICROPYTHON}")
    sys.exit(2)

if not os.access(MICROPYTHON, os.X_OK):
    log(f"ERROR: micropython is not executable")
    sys.exit(2)

if not os.path.exists(SCRIPT):
    log(f"ERROR: Script not found: {SCRIPT}")
    sys.exit(2)

if OUTPUT_FILE:
    try:
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    except Exception as e:
        log(f"ERROR: Failed to create output directory: {e}")
        sys.exit(2)

# ===================== RUN SCRIPT ==================

exec_time = float(os.environ.get("PYAUTO_TIMEOUT", DEFAULT_EXEC_TIME))
log(f"Execution timeout: {exec_time} seconds")

cmd = [MICROPYTHON, SCRIPT]
log("Command: " + " ".join(cmd))

try:
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid,
        text=True
    )

    try:
        stdout, stderr = proc.communicate(timeout=exec_time)
    except subprocess.TimeoutExpired:
        log("Execution timed out, killing process")
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        raise

except subprocess.TimeoutExpired:
    sys.stderr.write("ERROR: Execution timed out\n")
    sys.exit(1)
except Exception as e:
    log(f"ERROR: Failed to execute micropython: {e}")
    sys.exit(2)

# ===================== WRITE OUTPUT ================

final_output = stdout + stderr

if OUTPUT_FILE:
    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(final_output)
        log(f"Output written to {OUTPUT_FILE}")
    except Exception as e:
        log(f"ERROR: Failed to write output file: {e}")

# Emit output so Yaksh captures it
log("=== BEGIN OUTPUT ===")
sys.stdout.write(final_output)
sys.stderr.write(final_output)
sys.stdout.flush()
sys.stderr.flush()
log("=== END OUTPUT ===")

log("pyauto finished")

sys.exit(proc.returncode)