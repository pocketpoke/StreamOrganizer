import os
import shutil
from .io_utils import Colors, c, print_download, print_move, print_success, print_error, sanitize_filename
from .models import Details, DISABLE_FILE_DOWNLOADING, DISABLE_FILE_MOVING, DISABLE_FOLDER_CREATING, VODDirectory
from .subprocess_utils import get_yt_dlp_base_args, run_command_streaming


def organize_file(*, details: Details, file_path: str) -> bool:
    new_file_path = os.path.join(
        details.vod_directory.twitch_directory, f"{details.stream_title}.mp4"
    )

    print_move(file_path, new_file_path)

    if DISABLE_FILE_MOVING:
        print(c(Colors.YELLOW, "File moving disabled (dry run)"))
        return True

    try:
        shutil.move(file_path, new_file_path)
        print_success("File moved!")
        return True
    except Exception as e:
        print_error(f"Failed to move file: {e}")
        return False


def organize_twitch_chat(*, details: Details, twitch_url: str) -> bool:
    chat_output_path = os.path.join(
        details.vod_directory.twitch_chat_directory,
        f"{details.stream_title}.json",
    )

    print_download("Twitch chat", chat_output_path)

    cmd = [
        "TwitchDownloaderCLI",
        "chatdownload",
        "-u",
        twitch_url,
        "-E",
        "--collision",
        "Overwrite",
        "-o",
        chat_output_path,
    ]

    result = run_command_streaming(
        cmd,
        task_name="Twitch chat download",
        disable_flag=DISABLE_FILE_DOWNLOADING,
    )

    if result.returncode == 0:
        print_success(f"Downloaded Twitch chat to {chat_output_path}")
        return True
    else:
        print_error(f"Twitch chat download failed (exit code: {result.returncode})")
        return False


def organize_youtube(
    *, 
    details: Details, 
    chat_only: bool, 
    youtube_url: str,
    browser: str | None = None,
) -> tuple[bool, bool]:
    vod_success = True
    chat_success = True

    if not chat_only:
        vod_output_path = os.path.join(
            details.vod_directory.youtube_directory, details.stream_title
        )

        print_download("YouTube VOD", vod_output_path)

        cmd = [
            "yt-dlp",
            "--no-write-subs",
            "--concurrent-fragments",
            "5",
            "--no-part",
            *get_yt_dlp_base_args(browser=browser),
            "-o",
            vod_output_path,
            youtube_url,
        ]

        result = run_command_streaming(
            cmd,
            task_name="YouTube VOD download",
            disable_flag=DISABLE_FILE_DOWNLOADING,
        )

        if result.returncode == 0:
            print_success(f"Downloaded YouTube VOD to {vod_output_path}")
        else:
            print_error(f"YouTube VOD download failed (exit code: {result.returncode})")
            vod_success = False

    chat_title = details.stream_title
    for ext in [".webm", ".mkv", ".mp4", ".avi", ".mov"]:
        if chat_title.endswith(ext):
            chat_title = chat_title[:-len(ext)]
            break

    chat_title = sanitize_filename(chat_title)

    chat_output_path = os.path.join(
        details.vod_directory.youtube_chat_directory,
        f"{chat_title}.live_chat.json",
    )

    print_download("YouTube chat", chat_output_path)

    cmd = [
        "yt-dlp",
        "--write-subs",
        "--sub-lang",
        "live_chat",
        "--skip-download",
        *get_yt_dlp_base_args(browser=browser),
        "-o",
        chat_output_path,
        youtube_url,
    ]

    result = run_command_streaming(
        cmd,
        task_name="YouTube chat download",
        disable_flag=DISABLE_FILE_DOWNLOADING,
    )

    if result.returncode == 0:
        print_success(f"Downloaded YouTube chat to {chat_output_path}")
    else:
        print_error(f"YouTube chat download failed (exit code: {result.returncode})")
        chat_success = False

    return vod_success, chat_success


def fetch_youtube_title(youtube_url: str) -> str | None:
    import subprocess

    try:
        result = subprocess.run(
            [
                "yt-dlp",
                "--print",
                "%(title)s.%(ext)s",
                youtube_url,
                "--no-warnings",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            title = result.stdout.strip()
            if title:
                return sanitize_filename(title)
    except Exception:
        pass

    return None
