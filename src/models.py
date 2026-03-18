from dataclasses import dataclass, field
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
                f"{FOLDER_NUMBER_PREFIX}{vod_number}{FOLDER_SEPARATOR}{vod_date}{FOLDER_DATE_SUFFIX}",
            )
        if base_path:
            base_directory = os.path.join(
                base_path,
                f"{FOLDER_NUMBER_PREFIX}{vod_number}{FOLDER_SEPARATOR}{vod_date}{FOLDER_DATE_SUFFIX}",
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
        folder_name = os.path.basename(path)
        
        if FOLDER_SEPARATOR not in folder_name:
            raise ValueError(f"Invalid VOD directory path format: {path}")

        number_part = folder_name.split(FOLDER_SEPARATOR)[0].replace(FOLDER_NUMBER_PREFIX, "")
        date_part = folder_name.split(FOLDER_SEPARATOR)[1].replace(FOLDER_DATE_SUFFIX, "")

        return cls.create(
            base_path=os.path.dirname(path), vod_number=number_part, vod_date=date_part
        )

    def get_vod_number(self) -> str:
        folder_name = os.path.basename(self.base_directory)
        return folder_name.split(FOLDER_SEPARATOR)[0].replace(FOLDER_NUMBER_PREFIX, "")

    def get_vod_date(self) -> str:
        folder_name = os.path.basename(self.base_directory)
        return folder_name.split(FOLDER_SEPARATOR)[1].replace(FOLDER_DATE_SUFFIX, "")

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


@dataclass
class OperationResult:
    operation: str
    status: str
    description: str
    path: str | None
    duration_seconds: float
    error: str | None = None


@dataclass
class ArchiveSummary:
    results: list[OperationResult] = field(default_factory=list)

    def add(
        self,
        operation: str,
        status: str,
        description: str,
        path: str | None,
        duration: float,
        error: str | None = None,
    ) -> None:
        self.results.append(
            OperationResult(
                operation=operation,
                status=status,
                description=description,
                path=path,
                duration_seconds=duration,
                error=error,
            )
        )

    def add_success(
        self, operation: str, description: str, path: str | None, duration: float
    ) -> None:
        self.add(operation, "success", description, path, duration)

    def add_failed(
        self,
        operation: str,
        description: str,
        path: str | None,
        duration: float,
        error: str,
    ) -> None:
        self.add(operation, "failed", description, path, duration, error)

    def add_skipped(
        self, operation: str, description: str, path: str | None, duration: float = 0.0
    ) -> None:
        self.add(operation, "skipped", description, path, duration)

    @property
    def total_duration(self) -> float:
        return sum(r.duration_seconds for r in self.results)

    def all_success(self) -> bool:
        return all(r.status == "success" for r in self.results)

    @property
    def success_count(self) -> int:
        return sum(1 for r in self.results if r.status == "success")

    @property
    def failed_count(self) -> int:
        return sum(1 for r in self.results if r.status == "failed")

    @property
    def skipped_count(self) -> int:
        return sum(1 for r in self.results if r.status == "skipped")

    def print_summary(self) -> None:
        from .io_utils import Colors, c

        print()
        print(c(Colors.BLUE, "=" * 60))
        print(c(Colors.BLUE, "                      ARCHIVE SUMMARY"))
        print(c(Colors.BLUE, "=" * 60))
        print()

        for result in self.results:
            if result.status == "success":
                status_icon = c(Colors.GREEN, "[ \u2713 ]")
            elif result.status == "failed":
                status_icon = c(Colors.RED, "[ \u2717 ]")
            else:
                status_icon = c(Colors.YELLOW, "[ - ]")

            print(f"{status_icon} {result.operation}")
            print(f"      {result.description}")
            if result.path:
                print(f"      {c(Colors.BLUE, 'Path')}: {result.path}")
            if result.error:
                print(f"      {c(Colors.RED, 'Error')}: {result.error}")
            print(
                f"      {c(Colors.YELLOW, 'Duration')}: {result.duration_seconds:.2f}s"
            )
            print()

        print(c(Colors.BLUE, "-" * 60))

        total = self.total_duration
        if total >= 60:
            minutes = int(total // 60)
            seconds = total % 60
            duration_str = f"{total:.2f}s ({minutes}m {seconds:.0f}s)"
        else:
            duration_str = f"{total:.2f}s"

        print(f"Total Duration: {duration_str}")

        if self.failed_count > 0:
            status_line = (
                f"{self.success_count} operations completed, {self.failed_count} failed"
            )
            print(c(Colors.RED, f"Status: {status_line}"))
        else:
            status_line = f"{self.success_count} operations completed, 0 failed"
            print(c(Colors.GREEN, f"Status: {status_line}"))

        print(c(Colors.BLUE, "=" * 60))
