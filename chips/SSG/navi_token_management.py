import navi_internal

token_limit_max: int = 4096
navi_settings: dict = {}

command: str = "token-config"
use: str = "Adjust token limits for RAG and chat memory."
aliases: list = ['set_tokens', 'token_limits']
params: dict = {
    '-rag': 'Set the token limit for RAG (e.g., -rag 1024)',
    '-chat': 'Set the token limit for chat memory (e.g., -chat 3072)',
    '-show': 'Display the current token limit partition.',
    '-help': 'Display help information.',
}

help_params: tuple = ('-help', '-h')


def print_params() -> None:
    print(f"{'Parameter':<10} | {'Description'}")
    print("-" * 40)

    for param, description in params.items():
        print(f"{param:<10} | {description}")


def set_token_limit(rag: int = None, chat: int = None) -> str:
    global navi_settings
    token_limit_rag = int(navi_settings["token_limit_rag"])
    token_limit_chat = int(navi_settings["token_limit_chat"])

    # Calculate new limits if provided
    new_rag = token_limit_rag if rag is None else rag
    new_chat = token_limit_chat if chat is None else chat

    # Validate the total allocation
    if new_rag + new_chat > token_limit_max:
        return f"Error: Total allocation exceeds the maximum token limit of {token_limit_max}."

    from navi_shell import modify_navi_settings, get_navi_settings
    modify_navi_settings("token_limit_rag", new_rag)
    modify_navi_settings("token_limit_chat", new_chat)

    # Refresh the navi_settings dictionary
    navi_settings = get_navi_settings()

    return f"Token limits updated. RAG: {new_rag}, Chat: {new_chat}"


def show_token_limits() -> str:
    rag = int(navi_settings["token_limit_rag"])
    chat = int(navi_settings["token_limit_chat"])
    return f"Current Token Limits:\n- RAG: {rag}\n- Chat: {chat}\n- Total: {rag + chat} (Max: {token_limit_max})"


def run(arguments=None) -> None:
    navi_instance = navi_internal.navi_instance
    global token_limit_max
    token_limit_max = navi_instance.get_max_token_limit()
    arg_array = arguments.text.split()

    arg_array.pop(0)

    from navi_shell import get_navi_settings
    global navi_settings
    navi_settings = get_navi_settings()

    # Parse parameters
    if arg_array:
        rag_limit = None
        chat_limit = None
        show_only = False

        for i in range(len(arg_array)):
            arg = arg_array[i]

            match arg:
                case '-rag':
                    try:
                        # Fetch the next value and skip it in the loop
                        rag_limit = int(arg_array[i + 1])
                        arg_array[i + 1] = None  # Mark as processed
                    except (IndexError, ValueError):
                        navi_instance.print_message("Error: Invalid value for -rag.")
                        return
                case '-chat':
                    try:
                        # Fetch the next value and skip it in the loop
                        chat_limit = int(arg_array[i + 1])
                        arg_array[i + 1] = None  # Mark as processed
                    except (IndexError, ValueError):
                        navi_instance.print_message("Error: Invalid value for -chat.")
                        return
                case '-show':
                    show_only = True
                case x if x in help_params:
                    print_params()
                    return
                case _:
                    # Skip any previously processed value
                    if arg is not None:
                        navi_instance.print_message(f"Invalid parameter: {arg}")
                        return

        if show_only:
            navi_instance.print_message(show_token_limits())
            return

        result = set_token_limit(rag=rag_limit, chat=chat_limit)
        navi_instance.print_message(result)
    else:
        print_params()
