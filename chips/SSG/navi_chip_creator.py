import navi_internal
import sys
import os
from colorama import Fore
import subprocess
import webbrowser

command: str = "chip-create"
use: str = "Creates a new Navi chip"
aliases: list = ['chip-create', 'cc']
params: dict[str, str] = {
    '-help': 'Display help information',
    '-h': 'Display help information',
}

help_params: tuple = ('-help', '-h')
template_file: str = "chips/SSG/chip-template.txt"
chip_install_path: str = "chips/Dev/"
chip_documentation_link: str = "https://github.com/SaintsSec/Navi/wiki/4.-Developing-Chips-%E2%80%90-Indepth"


def print_params() -> None:
    """Prints the available parameters and their descriptions."""
    print(f"{'Parameter':<10} | {'Description'}")
    print("-" * 40)
    for param, description in params.items():
        print(f"{param:<10} | {description}")


def get_user_input(prompt):
    """Gets input from the user."""
    return input(prompt).strip()


def confirm_details(chip_name, chip_file_name, navi_instance):
    """Asks the user to confirm the chip details or make changes."""
    while True:
        navi_instance.print_message(f"Perfect! Here's a recap:"
                                    f"\nChip Name: {chip_name}"
                                    f"\nPython File Name: {chip_file_name}.py\n")
        choice = get_user_input("Are you ready to proceed or do you want to make changes? "
                                f"({Fore.YELLOW}c{Fore.RESET})ontinue or ({Fore.YELLOW}m{Fore.RESET})ake changes: ").lower()
        if choice == 'c':
            return chip_name, chip_file_name
        elif choice == 'm':
            return make_changes(chip_name, chip_file_name, navi_instance)
        else:
            navi_instance.print_message("Invalid input. Please choose 'c' to continue or 'm' to make changes.")


def make_changes(chip_name, chip_file_name, navi_instance):
    """Allows the user to change the chip name or file name."""
    while True:
        change_choice = get_user_input(f"What do you want to change? ({Fore.YELLOW}chip{Fore.RESET}) name or "
                                       f"({Fore.YELLOW}file{Fore.RESET}) name: ").lower()
        if change_choice == 'chip':
            navi_instance.print_message("Let's update the Chip Name.")
            chip_name = get_user_input("New Chip Name: ")
            return confirm_details(chip_name, chip_file_name, navi_instance)
        elif change_choice == 'file':
            navi_instance.print_message("Let's update the File Name.")
            chip_file_name = get_user_input("New File Name: ")
            return confirm_details(chip_name, chip_file_name, navi_instance)
        else:
            navi_instance.print_message("Invalid choice. Please enter 'chip' or 'file'.")


def create_chip_file(chip_name, chip_file_name):
    """Creates the chip file from a template."""
    if not os.path.exists(template_file):
        print(f"{Fore.RED}ERROR:{Fore.RESET} Template file '{template_file}' is missing. Aborting.")
        return None

    with open(template_file, "r") as template:
        template_content = template.read()

    chip_file_name_final = chip_file_name.replace(".py", "") + ".py"
    template_content = template_content.replace("{{CHIP_NAME}}", chip_name)
    chip_file_path = os.path.join(os.getcwd(), chip_install_path, chip_file_name_final)

    with open(chip_file_path, "w") as chip_dev:
        chip_dev.write(template_content)

    print(f"{Fore.GREEN}Chip '{chip_name}' created successfully!{Fore.RESET}")
    return chip_file_path


def post_creation_options(chip_file_path, navi_instance):
    """Provides options to the user after chip creation."""
    print(f"Here are some options for you:\n"
          f"{Fore.YELLOW}1{Fore.RESET}: Open directory of Chip location\n"
          f"{Fore.YELLOW}2{Fore.RESET}: Open in your preferred code editor\n"
          f"{Fore.YELLOW}3{Fore.RESET}: Reload Navi to load the new Chip\n"
          f"{Fore.YELLOW}4{Fore.RESET}: Review the documentation online\n"
          f"{Fore.YELLOW}5{Fore.RESET} or other value: I'm finished")
    choice = get_user_input("Please enter 1, 2, 3, 4, or 5: ")
    if choice == '1':
        print("Opening directory of Chip location")
        try:
            if sys.platform.startswith('win'):
                os.startfile(os.path.dirname(chip_file_path))
            elif sys.platform == 'darwin':
                subprocess.call(['open', os.path.dirname(chip_file_path)])
            else:
                subprocess.call(['xdg-open', os.path.dirname(chip_file_path)])
        except Exception as e:
            print(f"Failed to open the directory: {e}")
    elif choice == '2':
        print("Opening in your preferred code editor")
        try:
            if sys.platform == 'win32':
                os.startfile(chip_file_path)
            elif sys.platform == 'darwin':
                subprocess.call(['open', chip_file_path])
            else:
                subprocess.call(['xdg-open', chip_file_path])
        except Exception as e:
            print(f"Failed to open the file: {e}")
    elif choice == '3':
        navi_instance.reload()
    elif choice == '4':
        webbrowser.open(chip_documentation_link)
    else:
        pass


def run(arguments=None):
    navi_instance = navi_internal.navi_instance
    arg_array = arguments.text.split()[1:]  # Exclude the command itself

    if arg_array:
        for arg in arg_array:
            if arg in help_params:
                print_params()
                return
            else:
                choice = get_user_input(f"Invalid parameter: {arg}\n"
                                        f"Do you want to review the available parameters? (y/n): ").lower()
                if choice == 'y':
                    print_params()
                return

    navi_instance.print_message(
        f"Welcome to Navi Chip creator, {navi_instance.get_user()}. Please enter the name of your new Chip.")
    chip_name = get_user_input("Chip Name: ")
    navi_instance.print_message(f"Great name, {navi_instance.get_user()}! What do you want the python file to be called?")
    chip_file_name = get_user_input("Chip File Name: ")

    chip_name, chip_file_name = confirm_details(chip_name, chip_file_name, navi_instance)
    chip_file_path = create_chip_file(chip_name, chip_file_name)
    if chip_file_path:
        post_creation_options(chip_file_path, navi_instance)
