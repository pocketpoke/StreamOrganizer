import subprocess
from dataclasses import dataclass
from .io_utils import Colors, c, print_error


@dataclass
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


def run_command_streaming(
    cmd: list[str],
    *,
    task_name: str,
    disable_flag: bool = False,
) -> CommandResult:
    if disable_flag:
        print(c(Colors.YELLOW, f"[{task_name}] Skipping (disabled)"))
        return CommandResult(returncode=0, stdout="", stderr="")

    print(c(Colors.YELLOW, f"[{task_name}] Starting..."))

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )

        stdout_lines: list[str] = []
        stderr_lines: list[str] = []

        while True:
            if process.stdout is None:
                break
            output = process.stdout.readline()
            if output == "" and process.poll() is not None:
                break
            if output:
                print(output.strip())
                stdout_lines.append(output.strip())

        if process.stderr:
            stderr_output = process.stderr.read()
            if stderr_output:
                print_error(f"{task_name} error output:")
                print(stderr_output)
                stderr_lines.append(stderr_output)

        if process.returncode == 0:
            print(c(Colors.GREEN, f"[{task_name}] Completed successfully"))
        else:
            print(c(Colors.RED, f"[{task_name}] Failed with exit code {process.returncode}"))

        return CommandResult(
            returncode=process.returncode or 0,
            stdout="\n".join(stdout_lines),
            stderr="\n".join(stderr_lines),
        )

    except FileNotFoundError:
        print_error(f"{task_name}: Command not found. Ensure it's installed and in PATH.")
        return CommandResult(returncode=1, stdout="", stderr=f"Command not found: {cmd[0]}")


def run_command_simple(cmd: list[str]) -> CommandResult:
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )
        return CommandResult(
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
        )
    except FileNotFoundError:
        return CommandResult(returncode=1, stdout="", stderr=f"Command not found: {cmd[0]}")


def get_yt_dlp_base_args(*, browser: str | None) -> list[str]:
    args = [
        "--retries", "infinite",
        "--fragment-retries", "infinite",
        "--file-access-retries", "infinite",
    ]
    if browser:
        args.extend(["--cookies-from-browser", browser])
    return args
