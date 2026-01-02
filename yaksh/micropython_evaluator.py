import os
import tempfile
import subprocess
from .stdio_evaluator import StdIOEvaluator
from .base_evaluator import BaseEvaluator
from .file_utils import copy_files, delete_files
from .error_messages import compare_outputs
import shutil
import sys
import re
class QemuStdIOEvaluator(StdIOEvaluator):
    """
    Evaluator that runs a MicroPython .py under your QEMU runner script.

    Expected metadata keys:
      - 'user_answer' (string) : the submitted python source
      - 'file_paths' (list) : optional other files to copy into workdir
      - 'runner_path' (str) : optional path to your qemu-runner script; if not provided,
                              falls back to YAKSH_QEMU_RUNNER environment var or
                              '/usr/local/bin/qemu_run.py'
      - 'runner_args' (list/str) : optional extra args to the runner
      - 'partial_grading' (bool)
    """
    DEFAULT_RUNNER = os.environ.get(
        'YAKSH_QEMU_RUNNER',
        os.path.join(os.path.dirname(__file__), 'micropy_eval', 'pyauto.py')
    )

    def __init__(self, metadata, test_case_data):
        self.files = []
        self.user_answer = metadata.get('user_answer', '')
        self.file_paths = metadata.get('file_paths') or []
        self.runner_path = metadata.get('runner_path') or self.DEFAULT_RUNNER
        self.runner_args = metadata.get('runner_args') or ''
        self.partial_grading = metadata.get('partial_grading', False)

        self.expected_input = test_case_data.get('expected_input')
        self.expected_output = test_case_data.get('expected_output')
        self.weight = test_case_data.get('weight')
        self.hidden = test_case_data.get('hidden')

        # prepare working dir
        self.workdir = tempfile.mkdtemp(prefix='yaksh_qemu_')

    def teardown(self):
        # delete any files we created
        if self.files:
            try:
                delete_files(self.files)
            except Exception:
                pass

    def compile_code(self):
        self.submit_path = os.path.join(self.workdir, 'submission.py')
        with open(self.submit_path, 'w') as f:
            f.write(self.user_answer.lstrip())

        base = os.path.join(os.path.dirname(__file__), 'micropy_eval')

        # copy machine.py
        shutil.copyfile(
            os.path.join(base, 'machine.py'),
            os.path.join(self.workdir, 'machine.py')
        )

        #Copy time.py so `import time` uses fake module
        shutil.copyfile(
            os.path.join(base, 'time.py'),
            os.path.join(self.workdir, 'time.py')
        )

        return True, None


        #GPIO Pin Detection
    def _detect_gpio_pins(self, source_code):
        pins = set(re.findall(r'Pin\s*\(\s*(\d+)', source_code))
        if not pins:
            return "No GPIO detected"
        return ", ".join(f"GPIO{p}" for p in sorted(pins))
    
    def _detect_temp_threshold(self, source_code):
        match = re.search(r'temp_threshold\s*=\s*(\d+)', source_code)
        if match:
            return int(match.group(1))
        return None

    
    #Function to store code output info
    def _write_report(self, report_path, runner_output, pin_config, errors):
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("RAW OUTPUT\n")
            f.write("=============\n\n")
            f.write(runner_output.strip() + "\n\n")

            f.write("PIN_CONFIG\n")
            f.write("================\n")
            f.write(pin_config + "\n\n")

            f.write("ERRORS\n")
            if errors:
                f.write(errors + "\n")
            else:
                f.write("No runtime errors\n")
    
    def _extract_runtime_error(self, output_text):
        if "Traceback" in output_text or "Error" in output_text:
            return output_text.strip()
        return ""       


    def check_code(self):
        temp_threshold = self._detect_temp_threshold(self.user_answer)
        # Decide output file path
        output_path = os.path.join(self.workdir, 'qemu_output.txt')
        report_path = os.path.join(self.workdir, 'micropython_report.txt') #File to store current output and GPIO Storage
        # Build command to call your runner. It must accept input path and output path.
        # Example assumed runner CLI: python3 /path/to/qemu_run.py --input submission.py --output qemu_output.txt
        # pyauto accepts positional script path and an --output option
        cmd = [
            'python3', self.runner_path,
            self.submit_path,
            '--output', output_path
        ]
        # add optional runner args if provided (string or list)
        if isinstance(self.runner_args, (list, tuple)):
            cmd += list(self.runner_args)
        elif isinstance(self.runner_args, str) and self.runner_args:
            cmd += self.runner_args.split()
        
        env = os.environ.copy()
        if temp_threshold is not None:
            env["SIM_TEMP_INJECT"] = str(temp_threshold)
        else:
            if self.expected_input is None:
                raise ValueError(
                    "StdIO test case must define expected_input "
                    "(ADC value to inject)"
                )

            env["SIM_TEMP_INJECT"] = str(self.expected_input)

        # spawn runner with a preexec_fn to create its own process group so grader can kill on timeout
        proc = subprocess.Popen(cmd,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                preexec_fn=os.setpgrp,
                                env=env)

        # Wait for process to finish and capture stderr/stdout.
        try:
            stdout_bytes, stderr_bytes = proc.communicate()
        except Exception:
            # In case of unexpected errors, try to kill process group and re-raise
            try:
                os.killpg(os.getpgid(proc.pid), 9)
            except Exception:
                pass
            raise

        # If the runner returned non-zero, include stderr and any produced
        # output in the error message so the UI can show expected vs actual.
        if proc.returncode != 0:
            err_msg = self._remove_null_substitute_char(
                stderr_bytes.decode('utf-8', errors='ignore')
            )
            # Try to read any output the runner may have written
            runner_output = ''
            try:
                with open(output_path, 'r', encoding='utf-8') as f:
                    runner_output = f.read()
            except Exception:
                runner_output = ''

            # Use the same compare_outputs helper so the error payload
            # contains the expected/user output arrays and error_line_numbers
            success_flag, msg = compare_outputs(self.expected_output or '',
                                                runner_output,
                                                self.expected_input)
            # Attach runtime stderr so debugging is easier in the UI
            msg.setdefault('runtime_stderr', err_msg)
            # Ensure we mark this as a failing run
            pin_config = self._detect_gpio_pins(self.user_answer)
            errors = self._extract_runtime_error(runner_output)

            self._write_report(report_path, runner_output, pin_config, errors)

            # attach data for HTML
            if isinstance(msg, dict):
                msg['raw_output'] = runner_output
                msg['pin_config'] = pin_config
                msg['runtime_errors'] = errors

            return False, msg, 0.0

        # Read output file written by the runner and compare with expected output
        runner_output = ''
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                runner_output = f.read()
        except Exception:
            runner_output = ''

        success, err = compare_outputs(self.expected_output or '',
                                       runner_output,
                                       self.expected_input)
        mark_fraction = 1.0 if self.partial_grading and success else 0.0
        pin_config = self._detect_gpio_pins(self.user_answer)
        errors = self._extract_runtime_error(runner_output)

        self._write_report(report_path, runner_output, pin_config, errors)


        # attach data for HTML
        if isinstance(err, dict):
            err['raw_output'] = runner_output
            err['pin_config'] = pin_config
            err['runtime_errors'] = errors

        return success, err, mark_fraction


    def _read_output(self, output_path):
        try:
            with open(output_path, 'r') as f:
                return f.read()
        except Exception:
            # If runner didn't create output file, capture stderr from runner
            return ''