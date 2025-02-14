#!/bin/python3
import chips

command = "navi_help"
use = "Displays the help screen"
aliases = ['--nhelp', 'nhelp']


def run(arguments=None):
    max_command_length = 0
    max_use_length = 0
    max_alias_length = 0
    command_data = []

    for command_name, module in chips.modules.items():
        command_aliases = getattr(module, 'aliases', [])
        command_use = getattr(module, 'use', "")

        # Update maximum lengths
        max_command_length = max(max_command_length, len(command_name))
        max_use_length = max(max_use_length, len(command_use))
        max_alias_length = max(max_alias_length, max((len(alias) for alias in command_aliases), default=0))

        # Store command data
        command_data.append((command_name, command_use, command_aliases))

    commands_bulk_text = ""
    for command_name, command_use, command_aliases in command_data:
        commands_bulk_text += f"{command_name:<{max_command_length}} \t {command_use:<{max_use_length}} \t{command_aliases}\n"

    # Print the results
    print("\nCurrently installed Navi custom scripts:\n")
    print(f"{'Command':<{max_command_length}} {'Description':^{max_use_length}} \t\t{'Aliases':^{max_alias_length}}")
    print("-" * (max_command_length + max_use_length + 40 + max_alias_length))  # Add separator
    print(commands_bulk_text)
    print("\nHELP: To use any of these commands simply type the alias into \nthe user prompt and run the "
          "corresponding script!")
    print("-" * (max_command_length + max_use_length + 40 + max_alias_length))  # Add separator

    return None
