import platform
import re
import subprocess  # nosec


def get_command_path(command: str) -> bool | str:
    windows_commands = get_windows_builtin_commands()

    if windows_commands and is_windows_command(command, windows_commands):
        return True

    if platform.python_version() >= "3.12":
        from shutil import which
        return which(command)
    else:
        from distutils.spawn import find_executable
        return find_executable(command)


def is_windows_command(command: str, windows_commands: list[str]) -> bool:
    return command.upper() in (cmd.upper() for cmd in windows_commands)


def get_windows_builtin_commands() -> list[str]:
    if platform.system() != "Windows":
        return []
    result = subprocess.run(["help"], capture_output=True, text=True)  # nosec
    if result.stdout:
        help_text = result.stdout
        # Extract commands from help text
        commands = []
        lines = help_text.splitlines()
        for line in lines:
            # Command names are typically in uppercase and are single words
            match = re.match(r'^[A-Z]+\b', line.strip())
            if match:
                commands.append(match.group(0))
        return commands
    return []


def get_ip_address(input_str: str) -> str | None:
    if re.match(r'(\d{1,3}\.){3}\d{1,3}', input_str):
        return input_str
    else:
        return None


def get_hostname(input_str: str) -> str | None:
    if re.match(r'[a-zA-Z0-9\-]+\.[a-zA-Z]{2,3}', input_str):
        return input_str
    else:
        return None


def get_parameters(input_str: str) -> list[str]:
    pattern = re.compile(r'''
        "([^"]*)"|       # Capture text within quotes
        (\S+)            # Capture other non-whitespace sequences
    ''', re.VERBOSE)

    matches = pattern.findall(input_str)
    # Flatten the list and filter out empty strings
    parameters = [item for sublist in matches for item in sublist if item]

    return parameters
