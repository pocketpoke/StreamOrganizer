#!/usr/bin/env python3
import argparse
import pathlib as path
import os
import shutil
from dataclasses import dataclass
import subprocess

DISABLE_FILE_MOVING = False
DISABLE_FILE_DOWNLOADING = False
DISABLE_FOLDER_CREATING = False
BLUE = "\033[94m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"


@dataclass
class VODDirectory:
    base_directory: str
    twitch_directory: str
    youtube_directory: str
    twitch_chat_directory: str
    youtube_chat_directory: str

    @classmethod
    def create(
        cls,
        *,
        file_path: str | None = None,
        base_path: str | None = None,
        vod_number: str,
        vod_date: str,
    ):
        if not (file_path or base_path):
            raise ValueError("Either file_path or base_path must be set!")

        base_directory: str | None = None

        if file_path:
            base_directory = os.path.join(
                path.Path(file_path).parent, f"[ {vod_number} ] - [ {vod_date} ]"
            )
        if base_path:
            base_directory = os.path.join(
                base_path, f"[ {vod_number} ] - [ {vod_date} ]"
            )

        assert base_directory

        twitch_directory = os.path.join(base_directory, "[ Twitch ]")
        youtube_directory = os.path.join(base_directory, "[ YouTube ]")
        twitch_chat_directory = os.path.join(twitch_directory, "[ Chat ]")
        youtube_chat_directory = os.path.join(youtube_directory, "[ Chat ]")

        if not DISABLE_FOLDER_CREATING:
            os.makedirs(twitch_directory, exist_ok=True)
            print(f"+ {GREEN}Created{RESET}: {GREEN}{twitch_directory}{RESET}")
            os.makedirs(youtube_directory, exist_ok=True)
            print(f"+ {GREEN}Created{RESET}: {GREEN}{youtube_directory}{RESET}")
            os.makedirs(twitch_chat_directory, exist_ok=True)
            print(f"+ {GREEN}Created{RESET}: {GREEN}{twitch_chat_directory}{RESET}")
            os.makedirs(youtube_chat_directory, exist_ok=True)
            print(f"+ {GREEN}Created{RESET}: {GREEN}{youtube_chat_directory}{RESET}")

        return cls(
            base_directory=base_directory,  # type: ignore
            twitch_directory=twitch_directory,
            youtube_directory=youtube_directory,
            twitch_chat_directory=twitch_chat_directory,
            youtube_chat_directory=youtube_chat_directory,
        )

    def all(self) -> list[str]:
        return [
            self.base_directory,
            self.twitch_directory,
            self.youtube_directory,
            self.twitch_chat_directory,
            self.youtube_chat_directory,
        ]


@dataclass
class Details:
    stream_title: str
    vod_number: str
    vod_date: str
    vod_directory: VODDirectory


def organize_file(*, details: Details, file_path: str):
    new_file_path = os.path.join(
        details.vod_directory.twitch_directory, f"{details.stream_title}.mp4"
    )

    print(
        f"""Moving file:
- {RED}From{RESET}: {RED}{file_path}{RESET}
- {GREEN}To{RESET}: {GREEN}{new_file_path}{RESET}"""
    )

    if not DISABLE_FILE_MOVING:
        shutil.move(file_path, new_file_path)

    print(f"{GREEN}Success{RESET}: File moved!{RESET}")


def organize_twitch_chat(*, details: Details, twitch_url: str):
    chat_output_path = os.path.join(
        details.vod_directory.twitch_chat_directory,
        f"{details.stream_title}.json",
    )

    print(
        f"""Downloading and saving Twitch chat:
- {GREEN}To{RESET}: {GREEN}{chat_output_path}{RESET}"""
    )

    if not DISABLE_FILE_DOWNLOADING:
        try:

            process = subprocess.Popen(
                [
                    "TwitchDownloaderCLI",
                    "chatdownload",
                    "-u",
                    twitch_url,
                    "-E",
                    "--collision",
                    "Overwrite",
                    "-o",
                    chat_output_path,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
            )

            while True and process.stdout:
                output = process.stdout.readline()
                if output == "" and process.poll() is not None:
                    break
                if output:
                    print(output.strip())

            if process.stderr:
                stderr_output = process.stderr.read()

                if stderr_output:
                    print(f"{RED}Error output:{RESET}")
                    print(stderr_output)

            if process.returncode == 0:
                print(
                    f"{GREEN}Success{RESET}: Downloaded Twitch chat to {BLUE}{chat_output_path}{RESET}"
                )
            else:
                print(
                    f"{RED}Failure{RESET}: Twitch chat download (exit code: {RED}{process.returncode}{RESET})"
                )

        except subprocess.CalledProcessError as e:
            print(f"{RED}Error downloading Twitch chat:{RESET}")
            print(e.stderr if e.stderr else e.stdout)

        except FileNotFoundError:
            print(
                f"{RED}TwitchDownloaderCLI not found. Please ensure it's installed and in your PATH.{RESET}"
            )


def organize_youtube(*, details: Details, chat_only: bool, youtube_url: str):
    if not chat_only:
        vod_output_path = os.path.join(
            details.vod_directory.youtube_directory, details.stream_title
        )

        print(
            f"""Downloading and saving YouTube VOD:
- {GREEN}To{RESET}: {GREEN}{vod_output_path}{RESET}"""
        )

        if not DISABLE_FILE_DOWNLOADING:
            try:
                process = subprocess.Popen(
                    [
                        "yt-dlp",
                        "--no-write-subs",
                        "--concurrent-fragments",
                        "5",
                        "--no-part",
                        "--cookies-from-browser",
                        "brave",
                        "--retries",
                        "infinite",
                        "--fragment-retries",
                        "infinite",
                        "--file-access-retries",
                        "infinite",
                        "-o",
                        vod_output_path,
                        youtube_url,
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                )

                while True and process.stdout:
                    output = process.stdout.readline()
                    if output == "" and process.poll() is not None:
                        break
                    if output:
                        print(output.strip())

                if process.stderr:
                    stderr_output = process.stderr.read()
                    if stderr_output:
                        print(f"{RED}Error output:{RESET}")
                        print(stderr_output)

                if process.returncode == 0:
                    print(
                        f"{GREEN}Success{RESET}: Downloaded YouTube VOD to {BLUE}{vod_output_path}{RESET}"
                    )
                else:
                    print(
                        f"{RED}Failure{RESET}: YouTube VOD download (exit code: {RED}{process.returncode}{RESET})"
                    )

            except subprocess.CalledProcessError as e:
                print(f"{RED}Error downloading YouTube VOD:{RESET}")
                print(e.stderr if e.stderr else e.stdout)

            except FileNotFoundError:
                print(
                    f"{RED}yt-dlp not found. Please ensure it's installed and in your PATH.{RESET}"
                )

    chat_output_path = os.path.join(
        details.vod_directory.youtube_chat_directory,
        details.stream_title.replace(".webm", "")
        .replace(".mkv", "")
        .replace(".mp4", ""),
    )

    print(
        f"""Downloading and saving YouTube chat:
- {GREEN}To{RESET}: {GREEN}{chat_output_path}.live_chat.json{RESET}"""
    )

    if not DISABLE_FILE_DOWNLOADING:
        try:

            process = subprocess.Popen(
                [
                    "yt-dlp",
                    "--write-subs",
                    "--sub-lang",
                    "live_chat",
                    "--skip-download",
                    "--cookies-from-browser",
                    "brave",
                    "--retries",
                    "infinite",
                    "--fragment-retries",
                    "infinite",
                    "--file-access-retries",
                    "infinite",
                    "-o",
                    chat_output_path,
                    youtube_url,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
            )

            while True and process.stdout:
                output = process.stdout.readline()
                if output == "" and process.poll() is not None:
                    break
                if output:
                    print(output.strip())

            if process.stderr:
                stderr_output = process.stderr.read()

                if stderr_output:
                    print(f"{RED}Error output:{RESET}")
                    print(stderr_output)

            if process.returncode == 0:
                print(
                    f"{GREEN}Success{RESET}: Downloaded YouTube chat to {BLUE}{chat_output_path}{RESET}"
                )
            else:
                print(
                    f"{RED}Failure{RESET}: YouTube chat download (exit code: {RED}{process.returncode}{RESET})"
                )

        except subprocess.CalledProcessError as e:
            print(f"{RED}Error downloading YouTube chat:{RESET}")
            print(e.stderr if e.stderr else e.stdout)

        except FileNotFoundError:
            print(
                f"{RED}yt-dlp not found. Please ensure it's installed and in your PATH.{RESET}"
            )


def get_incremented_vod_number(*, file_path: str | None = None) -> str:
    if not file_path:
        base_directory = os.getcwd()

        print(f"{YELLOW}Using current directory to find numbered VOD folders...{RESET}")
    else:
        base_directory = path.Path(file_path).parent

    try:
        print(f"{YELLOW}Searching for existing VOD folders in: {base_directory}{RESET}")

        # Get all directory names in the base directory
        all_directories = os.listdir(base_directory)
        print(f"{YELLOW}Found {len(all_directories)} items in directory{RESET}")

        # Filter for directories that match our naming pattern
        numbered_folders: list[str] = []
        for item in all_directories:
            if " ] - [ " in item:
                # Extract the number part
                number_part = item.split(" ] - [ ")[0].replace("[ ", "")
                if number_part.isdigit():
                    numbered_folders.append(number_part)
                    print(f"{YELLOW}Found numbered folder: {number_part}{RESET}")

        if not numbered_folders:
            print(f"{YELLOW}No numbered VOD folders found. Starting with 1{RESET}")
            return "1"

        print(f"{YELLOW}Found {len(numbered_folders)} numbered VOD folders{RESET}")

        # Sort the numbers and get the highest one
        sorted_numbers = sorted(numbered_folders, key=int)
        highest_number = sorted_numbers[-1]
        print(f"{YELLOW}Highest VOD number found: {highest_number}{RESET}")

        # Calculate next number
        next_number = str(int(highest_number) + 1)
        print(f"{YELLOW}Next VOD number will be: {next_number}{RESET}")

        print(
            f"Extracted VOD number from file directory: {BLUE}{int(highest_number) + 1}{RESET}"
        )
        return next_number
    except IndexError:
        print(
            f"{YELLOW}No existing numbered VODs found, assuming this is the first...{RESET}"
        )
        return str(1)


def get_vod_date_from_file(*, file_path: str) -> str | None:
    file_name = os.path.split(file_path)[-1]

    try:
        year, month, day = file_name.split("]")[2].replace("[", "").split("-")
    except IndexError:
        print(f"{YELLOW}Couldn't extract date from title...{RESET}")
        return None

    date_string = f"{month.strip()}-{day.strip()}-{year.strip()[2:]}"

    print(f"Extracted date from file name: {BLUE}{date_string}{RESET}")

    return date_string


def get_stream_title_from_file(*, file_path: str) -> str:
    stream_title = os.path.split(file_path)[-1]
    stream_title = stream_title.split("]")[-1] if "]" in stream_title else stream_title
    stream_title = (
        stream_title.replace(" 1080p60 (Source)", "")
        .replace(".mp4", "")
        .replace(".webm", "")
        .replace(".mkv", "")
    )

    print(f"Extracted stream title from file: {BLUE}{stream_title}{RESET}")

    return stream_title


def find_vod_directory(
    *, vod_number: str | None = None, vod_date: str | None = None, base_directory: str
) -> VODDirectory | None:
    def find_vod_directory_from_vod_number(
        *, vod_number: str, base_directory: str
    ) -> VODDirectory | None:
        for item in os.listdir(base_directory):
            if " ] - [ " in item and (
                existing_vod_number := item.split(" ] - [ ")[0].replace("[ ", "")
            ):
                if existing_vod_number == vod_number:
                    return VODDirectory.create(
                        base_path=base_directory,
                        vod_number=item.split(" ] - [ ")[0].replace("[ ", ""),
                        vod_date=item.split(" ] - [ ")[1].replace(" ]", ""),
                    )

        return None

    def find_vod_directory_from_vod_date(
        *, vod_date: str, base_directory: str
    ) -> VODDirectory | None:
        for item in os.listdir(base_directory):
            if " ] - [ " in item and (
                existing_vod_date := item.split(" ] - [ ")[1].replace(" ]", "")
            ):
                if existing_vod_date == vod_date:
                    return VODDirectory.create(
                        base_path=base_directory,
                        vod_number=item.split(" ] - [ ")[0].replace("[ ", ""),
                        vod_date=item.split(" ] - [ ")[1].replace(" ]", ""),
                    )

        return None

    if not (vod_number or vod_date):
        raise ValueError("Either vod_number or vod_date must be set!")
    if vod_number and (
        vod_directory := find_vod_directory_from_vod_number(
            vod_number=vod_number, base_directory=base_directory
        )
    ):
        return vod_directory
    if vod_date and (
        vod_directory := find_vod_directory_from_vod_date(
            vod_date=vod_date, base_directory=base_directory
        )
    ):
        return vod_directory

    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", help="Path to VOD to be organized")
    parser.add_argument(
        "--twitch-url", help="URL for the Twitch VOD to download chat from"
    )
    parser.add_argument("--youtube-url", help="URL for the YouTube VOD")
    parser.add_argument(
        "--chat-only", help="Download only the chat from the YouTube VOD", type=bool
    )
    parser.add_argument("--vod-number", help="Set the number for the VOD")
    parser.add_argument("--vod-date", help="Set the date for the VOD")
    args = parser.parse_args()

    if not (args.file or args.twitch_url or args.youtube_url):
        print(
            f"{RED}You must specify at least one of the following: --file | --twitch-url | --youtube-url{RESET}"
        )
        exit(1)

    vod_details: Details | None = None
    vod_directory: VODDirectory | None = None

    if args.file:
        file_path = args.file

        stream_title = get_stream_title_from_file(file_path=file_path)

        vod_number = (
            args.vod_number
            if args.vod_number
            else get_incremented_vod_number(file_path=file_path)
        )

        if not (
            vod_date := (
                args.vod_date
                if args.vod_date
                else get_vod_date_from_file(file_path=file_path)
            )
        ):
            print(
                f"{RED}Couldn't extract VOD date from filename, please specify it with --vod-date{RESET}"
            )
            exit(1)

        vod_directory = VODDirectory.create(
            file_path=file_path, vod_number=vod_number, vod_date=vod_date
        )

        vod_details = Details(
            stream_title=stream_title,
            vod_number=vod_number,
            vod_date=vod_date,
            vod_directory=vod_directory,
        )

        organize_file(details=vod_details, file_path=file_path)

    if not args.file and not (args.vod_number or args.vod_date):
        print(
            f"{RED}You must set either --vod-number or --vod-date when --file is not provided!{RESET}"
        )
        exit(1)

    if args.twitch_url:
        if not vod_details:
            vod_directory = find_vod_directory(
                vod_number=args.vod_number,
                vod_date=args.vod_date,
                base_directory=os.getcwd(),
            )

            if not vod_directory:
                if args.vod_number and args.vod_date:
                    vod_directory = VODDirectory.create(
                        base_path=os.getcwd(),
                        vod_number=args.vod_number,
                        vod_date=args.vod_date,
                    )
                else:
                    print(
                        f"{RED}Couldn't locate a VOD directory, please specify either --vod-number or --vod-date. If the folder doesn't exist specify both to create it.{RESET}"
                    )
                    exit(1)

            if mp4_files := [
                x
                for x in os.listdir(vod_directory.twitch_directory)
                if x.endswith(".mp4")
            ]:
                file_path = os.path.join(vod_directory.twitch_directory, mp4_files[0])
                stream_title = get_stream_title_from_file(file_path=file_path)
            else:
                stream_title = "Untitled"

                print(
                    f"{YELLOW}VOD not found, chat file will be saved using a default name!"
                )

            vod_details = Details(
                stream_title=stream_title,
                vod_number=vod_directory.base_directory.split(" ] - [ ")[0].replace(
                    "[ ", ""
                ),
                vod_date=vod_directory.base_directory.split(" ] - [ ")[1].replace(
                    " ]", ""
                ),
                vod_directory=vod_directory,
            )

        organize_twitch_chat(details=vod_details, twitch_url=args.twitch_url)
    elif args.file:
        ...

    if args.youtube_url:
        print(f"{YELLOW}Fetching YouTube stream title...{RESET}")

        stream_title = subprocess.check_output(
            [
                "yt-dlp",
                "--print",
                "%(title)s.%(ext)s",
                args.youtube_url,
                "--no-warnings",
            ],
            universal_newlines=True,
        ).strip()

        print(f"Extracted YouTube stream title: {BLUE}{stream_title}{RESET}")

        if vod_details:
            vod_details.stream_title = stream_title

            organize_youtube(
                details=vod_details,
                chat_only=True if args.chat_only else False,
                youtube_url=args.youtube_url,
            )
        else:
            vod_directory = find_vod_directory(
                vod_number=args.vod_number,
                vod_date=args.vod_date,
                base_directory=os.getcwd(),
            )

            if not vod_directory:
                print(
                    f"{RED}Couldn't locate a VOD directory, please specify either --vod-number or --vod-date, or ensure that the data is correct{RESET}"
                )
                exit(1)

            vod_details = Details(
                stream_title=stream_title,
                vod_number=vod_directory.base_directory.split(" ] - [ ")[0].replace(
                    "[ ", ""
                ),
                vod_date=vod_directory.base_directory.split(" ] - [ ")[1].replace(
                    " ]", ""
                ),
                vod_directory=vod_directory,
            )

            organize_youtube(
                details=vod_details,
                chat_only=args.chat_only if args.chat_only else False,
                youtube_url=args.youtube_url,
            )
    elif args.file:
        ...


if __name__ == "__main__":
    main()
