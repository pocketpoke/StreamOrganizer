import os
import pathlib
import re
from .models import FOLDER_DATE_SUFFIX, FOLDER_NUMBER_PREFIX, FOLDER_SEPARATOR, VODDirectory
from .io_utils import Colors, c, print_extracted, print_warning


def get_incremented_vod_number(*, file_path: str | None = None, base_directory: str | None = None) -> str:
    if base_directory is None:
        if file_path:
            base_directory = os.path.dirname(file_path)
        else:
            base_directory = os.getcwd()

    print_warning(f"Searching for existing VOD folders in: {base_directory}")

    try:
        all_items = os.listdir(base_directory)
        numbered_folders: list[str] = []

        for item in all_items:
            item_path = os.path.join(base_directory, item)
            if os.path.isdir(item_path) and FOLDER_SEPARATOR in item:
                parts = item.split(FOLDER_SEPARATOR)
                if len(parts) >= 1:
                    number_part = parts[0].replace(FOLDER_NUMBER_PREFIX, "")
                    if number_part.isdigit():
                        numbered_folders.append(number_part)

        if not numbered_folders:
            print_warning("No numbered VOD folders found. Starting with 1")
            return "1"

        sorted_numbers = sorted(numbered_folders, key=int)
        highest_number = sorted_numbers[-1]
        next_number = str(int(highest_number) + 1)

        print_extracted("next VOD number", next_number)
        return next_number

    except Exception:
        print_warning("No existing numbered VODs found, assuming this is the first...")
        return "1"


def get_vod_date_from_file(*, file_path: str) -> str | None:
    file_name = os.path.basename(file_path)

    date_pattern = r"\[(\d{4})-(\d{2})-(\d{2})\]"
    match = re.search(date_pattern, file_name)

    if match:
        year, month, day = match.groups()
        date_string = f"{month}-{day}-{year[2:]}"
        print_extracted("date from filename", date_string)
        return date_string

    print_warning("Couldn't extract date from filename...")
    return None


def get_stream_title_from_file(*, file_path: str) -> str:
    path = pathlib.Path(file_path)
    stream_title = path.stem

    parts = stream_title.split("]")
    if len(parts) > 1:
        stream_title = parts[-1].strip()

    for suffix in [" 1080p60 (Source)", " 720p60", " 1080p", " 720p"]:
        stream_title = stream_title.replace(suffix, "")

    print_extracted("stream title from file", stream_title)
    return stream_title


def list_existing_vod_directories(base_directory: str) -> list[VODDirectory]:
    directories: list[VODDirectory] = []

    try:
        for item in os.listdir(base_directory):
            item_path = os.path.join(base_directory, item)
            if os.path.isdir(item_path) and FOLDER_SEPARATOR in item:
                try:
                    vod_dir = VODDirectory.from_path(item_path)
                    directories.append(vod_dir)
                except (ValueError, IndexError):
                    continue
    except OSError:
        pass

    directories.sort(key=lambda d: d.get_vod_number())
    return directories


def find_vod_directory(
    *,
    vod_number: str | None = None,
    vod_date: str | None = None,
    base_directory: str,
) -> VODDirectory | None:
    if not (vod_number or vod_date):
        raise ValueError("Either vod_number or vod_date must be set!")

    for item in os.listdir(base_directory):
        item_path = os.path.join(base_directory, item)
        if not os.path.isdir(item_path) or FOLDER_SEPARATOR not in item:
            continue

        parts = item.split(FOLDER_SEPARATOR)
        if len(parts) != 2:
            continue

        existing_number = parts[0].replace(FOLDER_NUMBER_PREFIX, "")
        existing_date = parts[1].replace(FOLDER_DATE_SUFFIX, "")

        if vod_number and existing_number == vod_number:
            return VODDirectory.from_path(item_path)

        if vod_date and existing_date == vod_date:
            return VODDirectory.from_path(item_path)

    return None


def find_vod_directory_for_stream(*, base_directory: str) -> VODDirectory | None:
    directories = list_existing_vod_directories(base_directory)
    if directories:
        return directories[-1]
    return None
