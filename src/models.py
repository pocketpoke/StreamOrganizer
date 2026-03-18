from dataclasses import dataclass
import os

FOLDER_SEPARATOR = " ] - [ "
FOLDER_NUMBER_PREFIX = "[ "
FOLDER_DATE_SUFFIX = " ]"

DISABLE_FILE_MOVING = False
DISABLE_FILE_DOWNLOADING = False
DISABLE_FOLDER_CREATING = False


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
    ) -> "VODDirectory":
        if not (file_path or base_path):
            raise ValueError("Either file_path or base_path must be set!")

        base_directory: str | None = None

        if file_path:
            base_directory = os.path.join(
                os.path.dirname(file_path),
                f"{FOLDER_NUMBER_PREFIX}{vod_number}{FOLDER_SEPARATOR}{vod_date}{FOLDER_DATE_SUFFIX}"
            )
        if base_path:
            base_directory = os.path.join(
                base_path,
                f"{FOLDER_NUMBER_PREFIX}{vod_number}{FOLDER_SEPARATOR}{vod_date}{FOLDER_DATE_SUFFIX}"
            )

        assert base_directory

        twitch_directory = os.path.join(base_directory, "[ Twitch ]")
        youtube_directory = os.path.join(base_directory, "[ YouTube ]")
        twitch_chat_directory = os.path.join(twitch_directory, "[ Chat ]")
        youtube_chat_directory = os.path.join(youtube_directory, "[ Chat ]")

        if not DISABLE_FOLDER_CREATING:
            os.makedirs(twitch_directory, exist_ok=True)
            os.makedirs(youtube_directory, exist_ok=True)
            os.makedirs(twitch_chat_directory, exist_ok=True)
            os.makedirs(youtube_chat_directory, exist_ok=True)

        return cls(
            base_directory=base_directory,
            twitch_directory=twitch_directory,
            youtube_directory=youtube_directory,
            twitch_chat_directory=twitch_chat_directory,
            youtube_chat_directory=youtube_chat_directory,
        )

    @classmethod
    def from_path(cls, path: str) -> "VODDirectory":
        parts = path.split(FOLDER_SEPARATOR)
        if len(parts) != 2:
            raise ValueError(f"Invalid VOD directory path format: {path}")

        number_part = parts[0].replace(FOLDER_NUMBER_PREFIX, "")
        date_part = parts[1].replace(FOLDER_DATE_SUFFIX, "")

        return cls.create(base_path=os.path.dirname(path), vod_number=number_part, vod_date=date_part)

    def get_vod_number(self) -> str:
        return self.base_directory.split(FOLDER_SEPARATOR)[0].replace(FOLDER_NUMBER_PREFIX, "")

    def get_vod_date(self) -> str:
        return self.base_directory.split(FOLDER_SEPARATOR)[1].replace(FOLDER_DATE_SUFFIX, "")

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


@dataclass
class UserInput:
    file_path: str | None = None
    twitch_url: str | None = None
    youtube_url: str | None = None
    vod_number: str | None = None
    vod_date: str | None = None
    selected_directory: VODDirectory | None = None
    proceed_without_cookies: bool = False
