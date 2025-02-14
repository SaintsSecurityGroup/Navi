import navi_internal

command = "exit"
use = "Exit Navi"
aliases = ['quit', 'exit', 'goodbye']


def run(arguments=None):
    navi_instance = navi_internal.navi_instance
    navi_instance.print_message(f"Thank you for stopping by! {navi_instance.get_user()}")
    exit(0)
