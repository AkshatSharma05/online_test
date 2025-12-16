#!/usr/bin/env python3
import subprocess, time, sys, threading, os, pty

import argparse

FIRMWARE = os.environ.get(
    'PYAUTO_FIRMWARE',
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'firmware.bin')
)

parser = argparse.ArgumentParser(description='Run MicroPython script under QEMU')
parser.add_argument('script', nargs='?', default='./main.py',
                    help='Path to MicroPython .py script to run')
parser.add_argument('--output', '-o', dest='output', default=None,
                    help='Optional file to write console output to')
args = parser.parse_args()

SCRIPT = args.script
OUTPUT_FILE = args.output

# Validate firmware path before starting QEMU
if not os.path.exists(FIRMWARE):
    sys.stderr.write(f"Firmware file not found: {FIRMWARE}\n")
    sys.exit(2)

# Create a pseudo-terminal pair
master, slave = pty.openpty()

# Start QEMU process
p = subprocess.Popen(
    [
        "qemu-system-xtensa",
        "-nographic",
        "-machine", "esp32",
        "-drive", f"file={FIRMWARE},format=raw,if=mtd"
    ],
    stdin=slave,
    stdout=slave,
    stderr=slave,
    text=True
)

output_buffer = ""

def reader():
    global output_buffer
    while True:
        try:
            data = os.read(master, 1024).decode(errors="ignore")
            if data:
                output_buffer += data
                print(data, end="")
            else:
                break
        except:
            break

# Start async reader
t = threading.Thread(target=reader, daemon=True)
t.start()

print("Waiting for MicroPython to finish booting...")

# Wait for MicroPython boot completion
while 'help()' not in output_buffer:
    time.sleep(0.1)

print("Boot complete. Waiting 0.5s for REPL to stabilize...")
time.sleep(0.5)

# Now REPL is stable → send Ctrl-E
os.write(master, b"\x05")
time.sleep(0.2)

# Send the script contents
with open(SCRIPT, "rb") as f:
    os.write(master, f.read())

time.sleep(0.2)

# Send Ctrl-D to execute
os.write(master, b"\x04")
# After sending Ctrl-D, wait for an explicit completion marker ('done') from the guest
# before writing output and exiting. Fallbacks: QEMU process exit or timeout.
try:
    TIMEOUT = int(os.environ.get('PYAUTO_TIMEOUT', '3'))
except Exception:
    TIMEOUT = 3

wait_start = time.time()
while True:
    # Prefer an explicit completion marker from the guest: wait until 'done' appears
    # in the console output. This ensures the script printed its final marker.
    if 'DONE' in output_buffer:
        # give a tiny moment for any trailing output to arrive
        time.sleep(0.1)
        break
    # If QEMU process exited unexpectedly, proceed to write whatever we have
    if p.poll() is not None:
        break
    # Timeout fallback
    if time.time() - wait_start > TIMEOUT:
        # timeout reached
        break
    time.sleep(0.1)

# If an output file was requested, write the captured output to it.
if OUTPUT_FILE:
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as out_f:
            out_f.write(output_buffer)
    except Exception as e:
        # Best-effort: if writing fails, print a warning to stderr and continue
        sys.stderr.write('Failed to write output file: {}\n'.format(e))

# Try to terminate the QEMU process cleanly, then force-kill if necessary
try:
    if p.poll() is None:
        p.terminate()
        # give it a moment to exit
        time.sleep(0.5)
        if p.poll() is None:
            p.kill()
except Exception:
    pass

# Close master fd to signal reader thread to finish and join it
try:
    os.close(master)
except Exception:
    pass

try:
    t.join(timeout=1.0)
except Exception:
    pass

# Ensure stdout is flushed and exit
sys.stdout.flush()
sys.exit(0)
