import concurrent.futures
import os
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from shutil import get_terminal_size

from .io_utils import Colors, c, print_error, print_info, print_step


def _clear_line():
    columns, _ = get_terminal_size()
    print("\r" + " " * columns + "\r", end="", flush=True)


@dataclass
class UploadResult:
    local_path: str
    remote_path: str
    success: bool
    duration_seconds: float
    bytes_transferred: int = 0
    error: str | None = None


@dataclass
class UploadConfig:
    remote_host: str
    remote_path: str
    max_jobs: int = 6
    rsync_opts: str = "--compress --partial --progress --human-readable"


def _parse_destination(destination: str) -> tuple[str, str]:
    if "@" not in destination:
        raise ValueError(
            f"Invalid destination format: '{destination}'. Expected user@hostname or user@hostname:/path"
        )

    if ":" in destination:
        parts = destination.split(":", 1)
        remote_host = parts[0]
        remote_path = parts[1] if parts[1] else ""
    else:
        remote_host = destination
        remote_path = ""

    if not remote_path.endswith("/"):
        remote_path += "/"

    return remote_host, remote_path


def _check_rsync() -> bool:
    return shutil.which("rsync") is not None


def _get_directory_name(path: str) -> str:
    basename = os.path.basename(path.rstrip("/"))
    return basename


def _build_rsync_command(
    src: str,
    remote_host: str,
    remote_dest: str,
    rsync_opts: str,
) -> list[str]:
    src_name = _get_directory_name(src)
    remote_full = f"{remote_host}:{remote_dest}{src_name}/"

    cmd = [
        "rsync",
        "-r",
    ]

    for opt in rsync_opts.split():
        if opt:
            cmd.append(opt)

    cmd.extend(["--rsh=ssh", f"{src}/", remote_full])

    return cmd


def upload_single(
    local_path: str,
    config: UploadConfig,
    base_directory: str | None = None,
) -> UploadResult:
    if base_directory:
        rel_path = os.path.relpath(local_path, base_directory)
    else:
        rel_path = _get_directory_name(local_path)
    remote_full = f"{config.remote_host}:{config.remote_path}{rel_path}/"

    print_info(f"Starting upload: {local_path}  ->  {remote_full}")

    cmd = [
        "rsync",
        "-r",
    ]

    for opt in config.rsync_opts.split():
        if opt:
            cmd.append(opt)

    cmd.extend(["--rsh=ssh", f"{local_path}/", remote_full])

    start_time = time.time()

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        output_lines: list[str] = []
        for line in iter(process.stdout.readline, ""):
            if line:
                output_lines.append(line.strip())
                stripped = line.strip()
                if stripped:
                    _clear_line()
                    print(stripped, end="\r", flush=True)

        process.wait()
        _clear_line()
        print()

        duration = time.time() - start_time

        bytes_transferred = 0
        for line in output_lines:
            if "received" in line and "bytes" in line:
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == "bytes" and i > 0:
                        try:
                            bytes_transferred = int(parts[i - 1].replace(",", ""))
                        except ValueError:
                            pass

        if process.returncode == 0:
            print(c(Colors.GREEN, f"Done: {rel_path}"))
            return UploadResult(
                local_path=local_path,
                remote_path=remote_full,
                success=True,
                duration_seconds=duration,
                bytes_transferred=bytes_transferred,
            )
        else:
            error_msg = f"rsync exited with code {process.returncode}"
            print(c(Colors.RED, f"Failed: {rel_path}"))
            return UploadResult(
                local_path=local_path,
                remote_path=remote_full,
                success=False,
                duration_seconds=duration,
                error=error_msg,
            )

    except FileNotFoundError:
        duration = time.time() - start_time
        return UploadResult(
            local_path=local_path,
            remote_path=remote_full,
            success=False,
            duration_seconds=duration,
            error="rsync not found. Ensure rsync is installed.",
        )
    except Exception as e:
        duration = time.time() - start_time
        return UploadResult(
            local_path=local_path,
            remote_path=remote_full,
            success=False,
            duration_seconds=duration,
            error=str(e),
        )


def parallel_upload(
    paths: list[str],
    config: UploadConfig,
    base_directory: str | None = None,
) -> list[UploadResult]:
    if not paths:
        return []

    if not _check_rsync():
        print_error("rsync is not installed. Please install rsync to enable uploads.")
        return [
            UploadResult(
                local_path=p,
                remote_path="",
                success=False,
                duration_seconds=0.0,
                error="rsync not installed",
            )
            for p in paths
        ]

    valid_paths = []
    for path in paths:
        if not os.path.isdir(path):
            print_info(f"Skipping (not a directory): {path}")
            continue
        valid_paths.append(path)

    if not valid_paths:
        return []

    print_info(f"Target: {config.remote_host}:{config.remote_path}")
    print_info(f"Uploading {len(valid_paths)} directory(ies) (max {config.max_jobs} concurrent)")

    results: list[UploadResult] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=config.max_jobs) as executor:
        future_to_path = {
            executor.submit(upload_single, path, config, base_directory): path
            for path in valid_paths
        }

        for future in concurrent.futures.as_completed(future_to_path):
            path = future_to_path[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                results.append(
                    UploadResult(
                        local_path=path,
                        remote_path="",
                        success=False,
                        duration_seconds=0.0,
                        error=str(e),
                    )
                )

    return results
