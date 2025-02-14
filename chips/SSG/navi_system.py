#!/bin/python3
import shlex
import subprocess  # nosec

import navi_internal
from navi import get_command_path

command = "navi_sys"
use = "Execute system command created by Navi"


def run(arguments=None):
    navi_instance = navi_internal.navi_instance
    navi_command = str(arguments).replace("TERMINAL OUTPUT", "", 1).strip()
    base_command = navi_command.split()[0]
    if get_command_path(base_command) is not None:
        navi_instance.print_message(
            f"\nDo I have your permission to use your **shell** to execute the following: \n\n{navi_command}\n")
        user_input = input("Do you want me to continue (y/n): ").strip().lower()
        if user_input == 'y':
            result = subprocess.run(
                shlex.split(navi_command, comments=False, posix=True),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                shell=False  # nosec
            )
            output = f"Output: \n{result.stdout}" if result.stdout else ""
            navi_instance.print_message(f"\nDone! {output}")
        else:
            navi_instance.print_message("\nUnderstood! I will not execute the command.")
    else:
        navi_instance.print_message(f"\nSorry, it looks like {base_command} is not installed on your system.")
