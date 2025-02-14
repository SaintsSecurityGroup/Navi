import navi_internal

command = "clear"
use = "Clear the screen"
aliases = ['cls']


def run(arguments=None):
    navi_instance = navi_internal.navi_instance
    navi_instance.clear_terminal()
    navi_instance.print_message(f"How can I help you, {navi_instance.get_user()}?")
