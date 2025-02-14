import argparse
import getpass
import os
import sys
import traceback

from colorama import Fore

import navi_internal
from chips import SSG
from install import local_model
from navi_updater import check_version, update_script


def handle_exception(exc_type, exc_value, exc_traceback) -> None:
    from datetime import datetime

    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = os.path.join(log_dir, f'crash_{timestamp}.log')

    with open(log_file, 'w') as f:
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)

    log_file_path = os.path.abspath(log_file)

    print(
        f"\nDang! Navi crashed. A crash log has been created at:\n{log_file_path}. \n\nYou can create a new Navi GitHub issue here: \nhttps://github.com/SaintsSec/Navi/issues. \n\nThank you for helping us make Navi better!")

    print("\nWould you like to:")
    print("1) Open the crash log")
    print("2) Ignore and close the app")
    choice = input("Please enter 1 or 2: ")

    if choice == '1':
        import subprocess
        try:
            if sys.platform == 'win32':
                os.startfile(log_file_path)
            elif sys.platform == 'darwin':
                subprocess.call(['open', log_file_path])
            else:
                subprocess.call(['xdg-open', log_file_path])
        except Exception as e:
            print(f"Failed to open the log file: {e}")
        print("Closing the application.")

    sys.exit(1)


sys.excepthook = handle_exception

user = getpass.getuser()

parser = argparse.ArgumentParser(description='Check for new releases and handle updates.')
parser.add_argument('-q', type=str, help='Ask Navi a question')
parser.add_argument('--edge', action='store_true', help='Check for the edge version')
parser.add_argument('--noupdate', action='store_true', help='Do not check for updates')
parser.add_argument('--update', action='store_true', help='Update the script to the latest version if available')
parser.add_argument('--skip-update', action='store_true',
                    help='Skip the update check (used internally to prevent update loop)')
parser.add_argument('--install', action='store_true', help='installs Navi based on the current downloaded version.')
parser.add_argument('--remote', action='store_true', help='Use remote server instead of local server')

args = parser.parse_args()


def restart_navi(custom_flag: bool = False, flag: str = "") -> None:
    import subprocess  # nosec
    command = [sys.executable] + sys.argv + (["--skip-update"] if not custom_flag else [flag])
    subprocess.run(command, check=True)

    sys.exit()


def local_model_check():
    if local_model.ollama_installed():
        if not local_model.is_ollama_service_running():
            local_model.start_ollama_service()
        is_installed, has_unexpected_error = local_model.check_model_installed()
        if is_installed:
            local_model.start_ollama_service()
        else:
            if has_unexpected_error:
                print(f"{Fore.YELLOW}Warning: We can't verify that the local navi model is installed.{Fore.RESET}")
                install_decision()
            else:
                print(f"{Fore.YELLOW}The local Navi model not installed.{Fore.RESET}")
                install_decision()
    else:
        print(f"{Fore.YELLOW}Warning: Ollama is required to run the local Navi model.{Fore.RESET}")
        install_decision()


def install_decision():
    user_decision = input("(C)ontinue with --remote flag or begin (i)nstallation: ")
    if user_decision == "c" or user_decision == "C":
        print("To never see this prompt again, set 'use_local_model' to False using the 'settings'"
              "command.")
        default_input = input("Would you like us to set it for you? (Y)es, (N)o, please restart: ")
        if default_input.lower() == "y" or default_input.lower() == "yes":
            modify_navi_settings("use_local_model", False)
        restart_navi(True, "--remote")
    if user_decision == "i" or user_decision == "I":
        print("Beginning installation")
        local_model.install_model()


def get_navi_settings() -> dict:
    return SSG.navi_settings.settings_init()


def modify_navi_settings(key, value) -> None:
    SSG.navi_settings.modify_config(key, value)


def main() -> None:
    navi_instance = navi_internal.navi_instance
    navi_settings = get_navi_settings()
    navi_instance.set_user(navi_settings["username"])
    navi_instance.set_navi_name(navi_settings["navi_name"])
    try:
        if args.q:
            response_message, http_status = navi_instance.llm_chat(
                f"{args.q}",
                True,
                args.remote
            )
            navi_instance.print_message(
                f"{response_message if http_status == 200 else f'Trouble connecting to Navi server.'}"
            )
            exit(0)
        if not args.noupdate and not args.skip_update and not navi_settings["dont_check_for_updates"]:
            if navi_settings["update_branch"] == "edge":
                args.edge = True
            download_url = check_version(args.edge)
            if download_url:
                update_script(download_url)
        if args.install:
            os.system('cd ./install && ./install.sh')
        if args.remote or not navi_settings["use_local_model"]:
            navi_instance.set_local(False)
        if not args.remote and navi_settings["use_local_model"]:
            local_model_check()
            # Only process files if local model is used
            navi_instance.process_knowledge_files()
        navi_instance.setup_navi_vocab()
        navi_instance.clear_terminal()
        navi_instance.setup_history()
        navi_instance.setup_memory()
        navi_instance.set_active_session(navi_settings["session"])
        navi_instance.chat_with_navi()
        navi_instance.print_message(f"How can I help you, {user}")
    except KeyboardInterrupt:
        navi_instance.print_message(f"\nKeyboard interrupt has been registered, talk soon {user}!")
        exit(0)


if __name__ == "__main__":
    main()
