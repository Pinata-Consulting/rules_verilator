"""
Intenteded to provide a way to limit the number of running Verilator
instances by using Bazel's worker mechanism.

https://bazel.build/remote/persistent#number-of-workers

This is less than ideal, hopefully more fine grained control
over job scheduling will be provided in the future:

https://github.com/bazelbuild/bazel/issues/27950
https://github.com/bazelbuild/bazel/pull/28013

In short, this mechanism allows us to add
--worker_max_instances=FirGeneration=N to a bazel invocation.
"""

import sys
import json
import subprocess
import os


def main():
    while True:
        # 1. Read the length of the JSON message (varint delimiter not strictly
        # required for JSON protocol, but standard read is safer)
        # For 'requires-worker-protocol': 'json', Bazel sends raw JSON lines or
        # length-delimited JSON. The simplest Python implementation usually
        # just reads line-by-line if Bazel is sending one request per line.

        # Robust method: Read a single line
        line = sys.stdin.readline()
        if not line:
            break

        request = json.loads(line)

        # 2. Extract arguments
        # The 'arguments' field contains the flags you passed in ctx.actions.run
        args = request.get("arguments", [])
        inputs = request.get(
            "inputs",
            [])  # You usually don't need to parse this for local execution

        # 3. Run Verilator
        # specific_verilator_path needs to be known, or passed as the first arg
        # to this script in the rule definition.
        # Let's assume the first arg in 'args' is the tool, or we hardcode it.
        # In your rule, you passed 'verilator_toolchain.verilator' as the first arg.

        try:
            # We run the actual command.
            # Note: The worker stays alive, so be careful with environment variables!
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                env=os.environ  # Pass through environment
            )

            exit_code = result.returncode
            output = result.stderr + result.stdout  # Verilator is chatty on stderr

        except Exception as e:
            exit_code = 1
            output = str(e)

        # 4. Send Response
        response = {
            "exitCode": exit_code,
            "output": output,
            "requestId": request.get("requestId")  # Echo back the ID
        }

        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
