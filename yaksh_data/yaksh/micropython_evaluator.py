# import os
# import tempfile
# import subprocess
# from .stdio_evaluator import StdIOEvaluator
# from .base_evaluator import BaseEvaluator
# from .file_utils import copy_files, delete_files

# class QemuStdIOEvaluator(StdIOEvaluator):
#     """
#     Evaluator that runs a MicroPython .py under your QEMU runner script.

#     Expected metadata keys:
#       - 'user_answer' (string) : the submitted python source
#       - 'file_paths' (list) : optional other files to copy into workdir
#       - 'runner_path' (str) : optional path to your qemu-runner script; if not provided,
#                               falls back to YAKSH_QEMU_RUNNER environment var or
#                               '/usr/local/bin/qemu_run.py'
#       - 'runner_args' (list/str) : optional extra args to the runner
#       - 'partial_grading' (bool)
#     """
#     DEFAULT_RUNNER = os.environ.get('YAKSH_QEMU_RUNNER', '/usr/local/bin/qemu_run.py')

#     def __init__(self, metadata, test_case_data):
#         self.files = []
#         self.user_answer = metadata.get('user_answer', '')
#         self.file_paths = metadata.get('file_paths') or []
#         self.runner_path = metadata.get('runner_path') or self.DEFAULT_RUNNER
#         self.runner_args = metadata.get('runner_args') or ''
#         self.partial_grading = metadata.get('partial_grading', False)

#         self.expected_input = test_case_data.get('expected_input')
#         self.expected_output = test_case_data.get('expected_output')
#         self.weight = test_case_data.get('weight')
#         self.hidden = test_case_data.get('hidden')

#         # prepare working dir
#         self.workdir = tempfile.mkdtemp(prefix='yaksh_qemu_')

#     def teardown(self):
#         # delete any files we created
#         if self.files:
#             try:
#                 delete_files(self.files)
#             except Exception:
#                 pass
#         # remove workdir
#         try:
#             delete_files([self.workdir])
#         except Exception:
#             pass

#     def compile_code(self):
#         # For MicroPython, usually no compile step; just write the file.
#         self.submit_path = os.path.join(self.workdir, 'submission.py')
#         with open(self.submit_path, 'w') as f:
#             f.write(self.user_answer.lstrip())

#         # copy any supporting files into workdir
#         if self.file_paths:
#             # copy_files returns list of created paths (existing file_utils handles)
#             self.files = copy_files(self.file_paths)
#             # If copy_files copies relative to cwd, you may need to move them into workdir.
#         return True, None

#     def check_code(self):
#         # Decide output file path
#         output_path = os.path.join(self.workdir, 'qemu_output.txt')
#         # Build command to call your runner. It must accept input path and output path.
#         # Example assumed runner CLI: python3 /path/to/qemu_run.py --input submission.py --output qemu_output.txt
#         cmd = [
#             'python3', self.runner_path,
#             '--input', self.submit_path,
#             '--output', output_path
#         ]
#         # add optional runner args if provided (string or list)
#         if isinstance(self.runner_args, (list, tuple)):
#             cmd += list(self.runner_args)
#         elif isinstance(self.runner_args, str) and self.runner_args:
#             cmd += self.runner_args.split()

#         # spawn runner with a preexec_fn to create its own process group so grader can kill on timeout
#         proc = subprocess.Popen(cmd,
#                                 stdin=subprocess.PIPE,
#                                 stdout=subprocess.PIPE,
#                                 stderr=subprocess.PIPE,
#                                 preexec_fn=os.setpgrp)

#         # use StdIOEvaluator's evaluate_stdio to handle communicate() and output comparison
#         # evaluate_stdio expects a proc and will call proc.communicate with expected_input bytes.
#         success, err = self.evaluate_stdio(self.user_answer, proc,
#                                            self.expected_input,
#                                            self._read_output(output_path))
#         mark_fraction = 1.0 if self.partial_grading and success else 0.0
#         return success, err, mark_fraction

#     def _read_output(self, output_path):
#         try:
#             with open(output_path, 'r') as f:
#                 return f.read()
#         except Exception:
#             # If runner didn't create output file, capture stderr from runner
#             return ''