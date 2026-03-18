from dataclasses import dataclass
from enum import Enum


class Colors(Enum):
    BLUE = "\033[94m"
    YELLOW = "\033[93m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    RESET = "\033[0m"


@dataclass
class ColorStr:
    color: Colors
    text: str

    def __str__(self) -> str:
        return f"{self.color.value}{self.text}{Colors.RESET.value}"


def c(color: Colors, text: str) -> str:
    return str(ColorStr(color, text))


def print_success(message: str) -> None:
    print(c(Colors.GREEN, f"Success: {message}"))


def print_error(message: str) -> None:
    print(c(Colors.RED, f"Error: {message}"))


def print_warning(message: str) -> None:
    print(c(Colors.YELLOW, f"Warning: {message}"))


def print_info(message: str) -> None:
    print(c(Colors.BLUE, f"Info: {message}"))


def print_step(message: str) -> None:
    print(f"+ {c(Colors.GREEN, 'Created')}: {c(Colors.GREEN, message)}")


def print_move(from_path: str, to_path: str) -> None:
    print(f"""Moving file:
- {c(Colors.RED, 'From')}: {c(Colors.RED, from_path)}
- {c(Colors.GREEN, 'To')}: {c(Colors.GREEN, to_path)}""")


def print_download(task: str, output_path: str) -> None:
    print(f"""Downloading and saving {task}:
- {c(Colors.GREEN, 'To')}: {c(Colors.GREEN, output_path)}""")


def print_extracted(label: str, value: str) -> None:
    print(f"Extracted {label}: {c(Colors.BLUE, value)}")


def print_directory_created(path: str) -> None:
    print(f"  {c(Colors.GREEN, '+')} {c(Colors.GREEN, path)}")


UNSAFE_CHARS = {
    "\\": "￦",
    "/": "／",
    ":": "：",
    "*": "＊",
    "?": "？",
    "\"": "＂",
    "<": "＜",
    ">": "＞",
    "|": "｜",
    "\n": "",
    "\r": "",
}

def sanitize_filename(title: str) -> str:
    result = title
    for char, replacement in UNSAFE_CHARS.items():
        result = result.replace(char, replacement)
    return result
