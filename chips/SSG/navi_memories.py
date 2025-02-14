import os

import navi_internal

command: str = "memory"
use: str = "Manage chat memory sessions."
aliases: list = ['session', 'memory']
params: dict = {
    'list': 'List all available sessions and indicate the active one',
    'create <name>': 'Create a new session with the specified name',
    'remove <name>': 'Remove a session with the specified name',
    'set-default <name>': 'Set the default session',
    'set-active <name>': 'Set the active session',
    '-help': 'Display help information',
    '-h': 'Display help information',
}

memory_dir = "memories"

# Ensure the memory directory exists
if not os.path.exists(memory_dir):
    os.makedirs(memory_dir)

help_params: tuple = ('-help', '-h')


def print_params() -> None:
    """Print available parameters and descriptions."""
    print(f"{'Parameter':<20} | {'Description'}")
    print("-" * 50)
    for param, description in params.items():
        print(f"{param:<20} | {description}")


def list_sessions(active_session) -> None:
    sessions = os.listdir(memory_dir)
    print("Available Sessions:")
    for session in sessions:
        session_name = os.path.splitext(session)[0]
        if session_name == active_session:
            print(f"* {session_name} (Active)")
        else:
            print(f"  {session_name}")


def does_session_exist(session_name) -> bool:
    if not os.path.exists(os.path.join(memory_dir, f"{session_name}.json")):
        print(f"Session '{session_name}' does not exist.")
        return False
    return True


def run(arguments=None) -> None:
    navi_instance = navi_internal.navi_instance
    active_session = navi_instance.get_active_session()

    arg_array = arguments.text.split()
    arg_array.pop(0)  # Remove the command itself

    if not arg_array:
        navi_instance.print_message("No arguments provided. Use '-help' for more information.")
        return

    match arg_array:
        case ['list']:
            list_sessions(active_session)
        case ['create', session_name]:
            navi_instance.create_new_session(session_name)
        case ['remove', session_name]:
            if does_session_exist:
                navi_instance.remove_session(session_name.upper())
        case ['set-default', session_name]:
            if does_session_exist:
                from navi_shell import modify_navi_settings
                modify_navi_settings("session", session_name.upper())
        case ['set-active', session_name]:
            if does_session_exist:
                navi_instance.set_active_session(session_name.upper())
        case x if x[0] in help_params:
            print_params()
        case _:
            navi_instance.print_message("Invalid arguments. Use '-help' for more information.")
