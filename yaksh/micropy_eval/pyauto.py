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

DEFAULT_BOOT_WAIT = 1.0      # seconds
DEFAULT_EXEC_TIME = 3.0      # seconds
READ_CHUNK = 1024

FIRMWARE = os.environ.get(
    "PYAUTO_FIRMWARE",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "firmware.bin")
)

# ===================== ARGS ========================

parser = argparse.ArgumentParser(
    description="Run MicroPython script under QEMU (grader-safe)"
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

log("=== pyauto starting ===")
log(f"Firmware path : {FIRMWARE}")
log(f"Script path   : {SCRIPT}")
log(f"Output file   : {OUTPUT_FILE}")

if not os.path.exists(FIRMWARE):
    log(f"ERROR: Firmware not found: {FIRMWARE}")
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

# ===================== START QEMU ==================

log("Starting QEMU...")

try:
    p = subprocess.Popen(
        [
            "qemu-system-xtensa",
            "-nographic",
            "-machine", "esp32",
            "-drive", f"file={FIRMWARE},format=raw,if=mtd"
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=0,
        preexec_fn=os.setsid
    )
except Exception as e:
    log(f"ERROR: Failed to start QEMU: {e}")
    sys.exit(2)

log(f"QEMU PID: {p.pid}")

output_buffer = b""

def read_available():
    global output_buffer
    try:
        while True:
            chunk = p.stdout.read(READ_CHUNK)
            if not chunk:
                break
            output_buffer += chunk
    except Exception:
        pass

# ===================== BOOT WAIT ===================

log("Waiting for firmware boot...")
time.sleep(DEFAULT_BOOT_WAIT)
read_available()

# ===================== ENTER PASTE MODE ============

log("Sending Ctrl-E (paste mode)")
try:
    p.stdin.write(b"\x05")   # Ctrl-E
    p.stdin.flush()
except Exception as e:
    log(f"WARNING: Failed to send Ctrl-E: {e}")

time.sleep(0.1)
read_available()

# ===================== SEND USER SCRIPT ============

log("Sending user script")

try:
    with open(SCRIPT, "rb") as f:
        p.stdin.write(f.read())
    p.stdin.flush()
except Exception as e:
    log(f"ERROR: Failed to send script: {e}")
    output_buffer += f"\nERROR sending script: {e}\n".encode()

time.sleep(0.1)
read_available()

# ===================== EXECUTE SCRIPT ==============

log("Sending Ctrl-D (execute)")
try:
    p.stdin.write(b"\x04")   # Ctrl-D
    p.stdin.flush()
except Exception as e:
    log(f"WARNING: Failed to send Ctrl-D: {e}")

# ===================== EXECUTION WINDOW ============

exec_time = float(os.environ.get("PYAUTO_TIMEOUT", DEFAULT_EXEC_TIME))
log(f"Execution window: {exec_time} seconds")

start = time.time()
while time.time() - start < exec_time:
    if p.poll() is not None:
        log("QEMU exited early")
        break
    read_available()
    time.sleep(0.05)

# ===================== FORCE TERMINATION ===========

log("Terminating QEMU")

try:
    if p.poll() is None:
        os.killpg(os.getpgid(p.pid), signal.SIGKILL)
except Exception as e:
    log(f"WARNING: Failed to kill QEMU: {e}")

time.sleep(0.1)
read_available()

# ===================== WRITE OUTPUT ================

final_output = output_buffer.decode(errors="ignore")

if OUTPUT_FILE:
    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(final_output)
        log(f"Output written to {OUTPUT_FILE}")
    except Exception as e:
        log(f"ERROR: Failed to write output file: {e}")

# Also emit output so Yaksh captures it
log("=== BEGIN QEMU OUTPUT ===")
sys.stdout.write(final_output)
sys.stderr.write(final_output)
sys.stdout.flush()
sys.stderr.flush()
log("=== END QEMU OUTPUT ===")

# ===================== HARD EXIT ===================

log("pyauto finished")
os._exit(0)
