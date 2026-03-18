import argparse
import os
import sys

from .commands import (
    fetch_youtube_title,
    organize_file,
    organize_twitch_chat,
    organize_youtube,
)
from .discovery import (
    find_vod_directory,
    get_incremented_vod_number,
    get_stream_title_from_file,
    get_vod_date_from_file,
)
from .io_utils import Colors, c, print_error, print_info, print_step, print_success, print_warning
from .models import Details, VODDirectory
from .prompts import (
    prompt_for_browser,
    prompt_for_missing_info,
    prompt_for_retry_confirmation,
    warn_about_cookies,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="StreamOrganizer - Archive Twitch and YouTube VODs"
    )
    parser.add_argument("--file", help="Path to VOD file to organize")
    parser.add_argument(
        "--twitch-url", 
        help="Twitch VOD URL for chat download (e.g., https://twitch.tv/videos/123456789)"
    )
    parser.add_argument(
        "--youtube-url", 
        help="YouTube VOD URL for download"
    )
    parser.add_argument(
        "--chat-only", 
        action="store_true", 
        help="Download only the chat from YouTube VOD (not the video)"
    )
    parser.add_argument(
        "--vod-number", 
        help="VOD number (overrides auto-detection)"
    )
    parser.add_argument(
        "--vod-date", 
        help="VOD date in MM-DD-YY format"
    )
    parser.add_argument(
        "--browser",
        choices=["brave", "chrome", "firefox", "edge"],
        help="Browser for cookie authentication (omit to skip cookies)"
    )
    parser.add_argument(
        "--no-prompts",
        action="store_true",
        help="Batch mode: exit with error instead of prompting for missing info"
    )
    parser.add_argument(
        "--base-path",
        default=os.getcwd(),
        help="Base directory for VOD organization (default: current directory)"
    )

    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> bool:
    if not (args.file or args.twitch_url or args.youtube_url):
        print_error(
            "You must specify at least one of: --file, --twitch-url, or --youtube-url"
        )
        return False

    if args.file and not os.path.exists(args.file):
        print_error(f"File not found: {args.file}")
        return False

    if args.vod_number and not args.vod_number.isdigit():
        print_error("VOD number must be a digit")
        return False

    return True


def ensure_vod_directory(
    *,
    file_path: str | None,
    vod_number: str | None,
    vod_date: str | None,
    base_path: str,
    selected_directory: VODDirectory | None = None,
) -> tuple[VODDirectory | None, Details | None]:
    if selected_directory:
        return selected_directory, None

    if file_path:
        stream_title = get_stream_title_from_file(file_path=file_path)

        if not vod_number:
            vod_number = get_incremented_vod_number(file_path=file_path)

        if not vod_date:
            vod_date = get_vod_date_from_file(file_path=file_path)

        if not vod_date:
            print_error("Couldn't extract VOD date from filename. Use --vod-date to specify.")
            return None, None

        vod_directory = VODDirectory.create(
            file_path=file_path,
            vod_number=vod_number,
            vod_date=vod_date,
        )

        for directory in vod_directory.all():
            print_step(directory)

        details = Details(
            stream_title=stream_title,
            vod_number=vod_number,
            vod_date=vod_date,
            vod_directory=vod_directory,
        )

        return vod_directory, details

    if not vod_number or not vod_date:
        return None, None

    existing = find_vod_directory(
        vod_number=vod_number,
        vod_date=vod_date,
        base_directory=base_path,
    )

    if existing:
        return existing, None

    vod_directory = VODDirectory.create(
        base_path=base_path,
        vod_number=vod_number,
        vod_date=vod_date,
    )

    for directory in vod_directory.all():
        print_step(directory)

    return vod_directory, None


def handle_file_organization(
    args: argparse.Namespace,
    details: Details,
    file_path: str,
) -> bool:
    return organize_file(details=details, file_path=file_path)


def handle_twitch_chat(
    args: argparse.Namespace,
    details: Details,
) -> bool:
    if not args.twitch_url:
        return True

    return organize_twitch_chat(details=details, twitch_url=args.twitch_url)


def handle_youtube_download(
    args: argparse.Namespace,
    details: Details,
    browser: str | None,
) -> tuple[bool, bool]:
    if not args.youtube_url:
        return True, True

    print_info("Fetching YouTube stream title...")
    stream_title = fetch_youtube_title(args.youtube_url)

    if stream_title:
        print_info(f"Extracted YouTube stream title: {stream_title}")
        details.stream_title = stream_title
    else:
        print_warning("Could not fetch YouTube title, using default")

    return organize_youtube(
        details=details,
        chat_only=args.chat_only,
        youtube_url=args.youtube_url,
        browser=browser,
    )


def main() -> int:
    args = parse_args()

    if not validate_args(args):
        return 1

    base_path = args.base_path
    browser: str | None = args.browser

    provided_file = bool(args.file)
    provided_twitch = bool(args.twitch_url)
    provided_youtube = bool(args.youtube_url)

    needs_prompts = not (provided_file and provided_twitch and provided_youtube)

    if needs_prompts and not args.no_prompts:
        user_input = prompt_for_missing_info(
            provided_file=provided_file,
            provided_twitch=provided_twitch,
            provided_youtube=provided_youtube,
            base_directory=base_path,
            file_path=args.file,
        )

        if not user_input.twitch_url and provided_twitch:
            user_input.twitch_url = args.twitch_url
        if not user_input.youtube_url and provided_youtube:
            user_input.youtube_url = args.youtube_url
        if not user_input.vod_number and args.vod_number:
            user_input.vod_number = args.vod_number
        if not user_input.vod_date and args.vod_date:
            user_input.vod_date = args.vod_date

        if user_input.selected_directory:
            vod_directory = user_input.selected_directory
            details = None
        else:
            vod_directory = None
            details = None

        args.twitch_url = user_input.twitch_url or args.twitch_url
        args.youtube_url = user_input.youtube_url or args.youtube_url

        if user_input.vod_number:
            args.vod_number = user_input.vod_number
        if user_input.vod_date:
            args.vod_date = user_input.vod_date

    elif needs_prompts and args.no_prompts:
        if provided_file and not (args.vod_number or args.vod_date):
            args.vod_number = get_incremented_vod_number(file_path=args.file)
            args.vod_date = get_vod_date_from_file(file_path=args.file)
            if not args.vod_date:
                print_error("Couldn't extract VOD date. Use --vod-date in batch mode.")
                return 1

        if (args.twitch_url or args.youtube_url) and not (args.vod_number and args.vod_date):
            print_error("In batch mode, you must specify both --vod-number and --vod-date when downloading without --file")
            return 1

    if not browser and not args.no_prompts:
        print_info("=" * 60)
        browser = prompt_for_browser()

    if not browser and (args.youtube_url or args.twitch_url):
        if not args.no_prompts:
            if not warn_about_cookies():
                print_info("Aborting download due to cookie requirements.")
                return 1
        else:
            print_warning("Running without browser cookies - downloads may fail on restricted content")

    vod_directory, details = ensure_vod_directory(
        file_path=args.file,
        vod_number=args.vod_number,
        vod_date=args.vod_date,
        base_path=base_path,
    )

    if not vod_directory:
        print_error("Failed to create or locate VOD directory")
        return 1

    if details is None:
        mp4_files = [
            f for f in os.listdir(vod_directory.twitch_directory)
            if f.endswith(".mp4")
        ]
        if mp4_files:
            file_path = os.path.join(vod_directory.twitch_directory, mp4_files[0])
            stream_title = get_stream_title_from_file(file_path=file_path)
        else:
            stream_title = "Untitled"
            print_warning("VOD not found, using default title")

        confirm = True
        if not args.no_prompts:
            confirm = prompt_for_retry_confirmation(vod_directory, stream_title)

        if not confirm:
            print_info("Aborted by user")
            return 1

        details = Details(
            stream_title=stream_title,
            vod_number=vod_directory.get_vod_number(),
            vod_date=vod_directory.get_vod_date(),
            vod_directory=vod_directory,
        )

    if args.file:
        if not handle_file_organization(args, details, args.file):
            return 1

    if args.twitch_url:
        if not handle_twitch_chat(args, details):
            print_warning("Twitch chat download had issues")

    if args.youtube_url:
        vod_ok, chat_ok = handle_youtube_download(args, details, browser)
        if not (vod_ok and chat_ok):
            print_warning("YouTube download had issues")

    print_success("Archive process completed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
