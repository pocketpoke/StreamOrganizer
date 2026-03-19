from .discovery import (
    get_incremented_vod_number,
    list_existing_vod_directories,
    get_vod_date_from_file,
)
from .io_utils import print_info, print_warning
from .models import (
    FOLDER_DATE_SUFFIX,
    FOLDER_NUMBER_PREFIX,
    FOLDER_SEPARATOR,
    UserInput,
    VODDirectory,
)


def ask_yes_no(question: str, default: bool = False) -> bool:
    suffix = "[Y/n]" if default else "[y/N]"
    while True:
        response = input(f"{question} {suffix}: ").strip().lower()
        if not response:
            return default
        if response in ("y", "yes"):
            return True
        if response in ("n", "no"):
            return False
        print_warning("Please enter 'y' or 'n'")


def ask_url(prompt_text: str) -> str | None:
    while True:
        url = input(f"{prompt_text}: ").strip()
        if not url:
            return None
        if url.startswith("http://") or url.startswith("https://"):
            return url
        print_warning("Please enter a valid URL starting with http:// or https://")


def select_existing_directory(base_directory: str) -> VODDirectory | None:
    directories = list_existing_vod_directories(base_directory)

    if not directories:
        return None

    print_info("Existing VOD directories:")
    for i, vod_dir in enumerate(directories, 1):
        print(f"  [{i}] {vod_dir.base_directory}")

    print("  [n] Create new directory")
    print()

    while True:
        choice = (
            input("Select directory [1-{} or n]: ".format(len(directories)))
            .strip()
            .lower()
        )

        if choice == "n":
            return None

        try:
            index = int(choice) - 1
            if 0 <= index < len(directories):
                return directories[index]
            print_warning(f"Please enter a number between 1 and {len(directories)}")
        except ValueError:
            print_warning("Please enter a valid number or 'n'")


def prompt_for_vod_info() -> tuple[str | None, str | None]:
    print_info("VOD Directory:")

    vod_number = input("  VOD number (press Enter for auto-increment): ").strip()
    if not vod_number:
        vod_number = get_incremented_vod_number()

    vod_date = input("  VOD date (MM-DD-YY): ").strip()

    if vod_date and vod_number:
        return vod_number, vod_date
    return None, None


def prompt_for_new_directory_confirmation(
    vod_number: str,
    vod_date: str,
) -> tuple[str, str]:
    folder_preview = f"{FOLDER_NUMBER_PREFIX}{vod_number}{FOLDER_SEPARATOR}{vod_date}{FOLDER_DATE_SUFFIX}"
    print_info(f"New folder would be: {folder_preview}")
    print()

    new_number = input(f"  VOD number [{vod_number}]: ").strip()
    if not new_number:
        new_number = vod_number

    new_date = input(f"  VOD date [{vod_date}]: ").strip()
    if not new_date:
        new_date = vod_date

    return new_number, new_date


def prompt_for_missing_info(
    provided_file: bool,
    provided_twitch: bool,
    provided_youtube: bool,
    base_directory: str,
    file_path: str | None = None,
) -> UserInput:
    result = UserInput()

    print_info("=" * 60)
    print_info("Missing Information Required")
    print_info("=" * 60)
    print()

    if not provided_twitch:
        download_twitch = ask_yes_no("Download Twitch chat?")
        if download_twitch:
            result.twitch_url = ask_url("  Enter Twitch VOD URL")

    if not provided_youtube:
        download_youtube = ask_yes_no("Download from YouTube?")
        if download_youtube:
            result.youtube_url = ask_url("  Enter YouTube URL")

    print()

    if provided_file and file_path:
        vod_date = get_vod_date_from_file(file_path=file_path)
        if vod_date:
            vod_number = get_incremented_vod_number(file_path=file_path)
            folder_preview = f"{FOLDER_NUMBER_PREFIX}{vod_number}{FOLDER_SEPARATOR}{vod_date}{FOLDER_DATE_SUFFIX}"

            use_new = ask_yes_no(f"Create new directory? ( {folder_preview} )")

            if use_new:
                result.vod_number = vod_number
                result.vod_date = vod_date
                return result

            print()

    print_info("VOD Directory:")
    selected_dir = select_existing_directory(base_directory)

    if selected_dir:
        result.selected_directory = selected_dir
        result.vod_number = selected_dir.get_vod_number()
        result.vod_date = selected_dir.get_vod_date()
    else:
        vod_num, vod_date = prompt_for_vod_info()
        result.vod_number = vod_num
        result.vod_date = vod_date

    return result


def warn_about_cookies() -> bool:
    print()
    print_warning("=" * 60)
    print_warning("Cookie Warning")
    print_warning("=" * 60)
    print_warning("yt-dlp may fail on age-restricted or subscriber-only content")
    print_warning("without browser cookies. Downloads may be incomplete or fail.")
    print()

    return ask_yes_no("Proceed without cookies?", default=False)


def prompt_for_retry_confirmation(vod_dir: VODDirectory, stream_title: str) -> bool:
    print_info(f"VOD directory detected: {vod_dir.base_directory}")
    print_info(f"Stream: {stream_title}")
    return ask_yes_no("Use this VOD directory?", default=True)


def prompt_for_browser() -> str | None:
    print_info("=" * 60)
    print_info("Browser for cookie authentication:")
    print_info("=" * 60)
    print("  [1] Brave")
    print("  [2] Chrome")
    print("  [3] Firefox")
    print("  [4] Edge")
    print("  [5] Skip (proceed without cookies)")

    browsers = {
        "1": "brave",
        "2": "chrome",
        "3": "firefox",
        "4": "edge",
    }

    while True:
        choice = input("Select browser [1-5]: ").strip()
        if choice == "5":
            return None
        if choice in browsers:
            return browsers[choice]
        print_warning("Please enter a number between 1 and 5")
