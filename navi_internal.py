import json
import os
import platform
import random
import textwrap
import time

import requests
import spacy
from PyPDF2 import PdfReader
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from sentence_transformers import SentenceTransformer, util

import chips
import config
import navi_banner


class NaviApp:
    art: str = navi_banner.art
    three_b_art: str = navi_banner.three_b_art
    helpAr: str = navi_banner.helpArt
    breakline: str = navi_banner.breakline
    ai_name_rep: str = "Navi"

    server: str = config.remote
    port: int = config.port
    local: str = config.local

    memory_dir: str = "memories"
    default_session: str = "DEFAULT_SESSION"
    token_limit_max: int = 4096
    active_session: str = default_session

    knowledge_store_path: str = "data/knowledge_store.json"
    input_directory: str = "data/input_files"
    archive_directory: str = "data/archive"
    # Initialize SentenceTransformer for RAG
    retriever_model = SentenceTransformer('all-MiniLM-L6-v2')

    llm_chat_prompt: str = (
        "You are a highly intelligent chatbot. "
        "You must answer user questions conversationally unless the user explicitly requests a terminal command. "
        "Rules: "
        "1. Respond conversationally for all general questions. Do not include TERMINAL OUTPUT for these responses. "
        "2. Only respond with terminal commands if the user explicitly requests terminal execution (e.g., 'write to a file,' 'run a command'). "
        "3. When responding with a terminal command, follow this exact format: "
        "   TERMINAL OUTPUT {terminal code to execute (do not use quotes, backticks, or markdown)}. "
        "4. Do not include additional text, explanations, or formatting (e.g., markdown, backticks, or language tags like `bash`). "
        "Examples: "
        "- User: 'What job did Katie apply to?' "
        "- Response: 'Katie applied to the position of Office Associate II at the Maine Department of Health.' "
        "- User: 'Write her job to a file called job.txt.' "
        "- Response: 'TERMINAL OUTPUT {echo Office Associate II at Maine Department of Health > job.txt}' "
        "Never include TERMINAL OUTPUT unless explicitly requested. "
        f"The user's operating system is {platform.system()}. User message:"
    )

    is_local: bool = True

    script_dir = os.path.dirname(os.path.abspath(__file__))
    hist_file = os.path.join(script_dir, ".navi_history")

    # NLP setup
    nlp: spacy.language.Language = spacy.load("en_core_web_sm")
    ruler: spacy.pipeline.EntityRuler = nlp.add_pipe("entity_ruler")

    user: str = None

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(NaviApp, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        self.knowledge_store = self.load_knowledge_store()
        self.setup_knowledge_input_dir()

    # ------------------------------ RAG MANAGEMENT ------------------------------

    def setup_knowledge_input_dir(self):
        os.makedirs(self.input_directory, exist_ok=True)
        os.makedirs(self.archive_directory, exist_ok=True)

    def load_knowledge_store(self):
        if os.path.exists(self.knowledge_store_path):
            with open(self.knowledge_store_path, "r") as f:
                return json.load(f)
        return []

    def save_knowledge_store(self):
        with open(self.knowledge_store_path, "w") as f:
            json.dump(self.knowledge_store, f, indent=4)

    def process_knowledge_files(self):
        for file_name in os.listdir(self.input_directory):
            file_path = os.path.join(self.input_directory, file_name)
            if not os.path.isfile(file_path):
                continue

            content = ""
            if file_name.endswith(".pdf"):
                content = self.extract_text_from_pdf(file_path)
            elif file_name.endswith(".txt"):
                content = self.extract_text_from_txt(file_path)

            if content:
                self.knowledge_store.append({"content": content, "source": file_name})
                self.save_knowledge_store()
                print(f"Added knowledge from {file_name}")
            # Move processed files to the archive directory
            import shutil
            archive_path = os.path.join(self.archive_directory, file_name)
            shutil.move(file_path, archive_path)
            print(f"Processed {file_name}")

    def retrieve_context(self, query):
        if not self.knowledge_store:
            return "No relevant knowledge available."

        query_embedding = self.retriever_model.encode(query, convert_to_tensor=True)
        knowledge_embeddings = self.retriever_model.encode(
            [item["content"] for item in self.knowledge_store], convert_to_tensor=True
        )

        scores = util.pytorch_cos_sim(query_embedding, knowledge_embeddings)[0]
        top_indices = scores.argsort(descending=True)[:3]  # Retrieve top 3 matches

        retrieved_snippets = [
            f"{self.knowledge_store[i]['content']} (Source: {self.knowledge_store[i]['source']})"
            for i in top_indices
        ]
        return "\n".join(retrieved_snippets)

    def extract_text_from_pdf(self, file_path):
        try:
            text = []
            reader = PdfReader(file_path)
            for page in reader.pages:
                text.append(page.extract_text())
            return "\n".join(text)
        except Exception as e:
            print(f"Error extracting text from {file_path}: {e}")
            return ""

    def extract_text_from_txt(self, file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"Error reading text file {file_path}: {e}")
            return ""

    def trim_rag_to_token_limit(self, text, token_limit):
        words = text.split()
        if len(words) > token_limit:
            trimmed_text = " ".join(words[:token_limit])
            return trimmed_text + "..."
        return text

    # ------------------------------ MEMORY MANAGEMENT ---------------------------

    def setup_memory(self) -> None:
        if not os.path.exists(self.memory_dir):
            os.makedirs(self.memory_dir)
        if not os.path.exists(self.get_session_path(self.default_session)):
            self.create_new_session(self.default_session)

    def get_session_path(self, session_name):
        return os.path.join(self.memory_dir, f"{session_name}.json")

    def trim_history_to_token_limit(self, chat_history, token_limit):
        while chat_history and self.calculate_tokens(chat_history) > token_limit:
            chat_history.pop(0)

        return chat_history

    def load_session(self, session_name):
        path = self.get_session_path(session_name)
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
        return []

    def save_session(self, session_name, chat_history):
        path = self.get_session_path(session_name)
        with open(path, 'w') as f:
            json.dump(chat_history, f, indent=4)

    def calculate_tokens(self, chat_history):
        return sum(len(entry['content'].split()) for entry in chat_history)

    def create_new_session(self, session_name):
        if not session_name.upper():
            print("Session name cannot be empty.")
            return
        if os.path.exists(self.get_session_path(session_name.upper())):
            print("Session with this name already exists.")
            return
        self.save_session(session_name.upper(), [])

    def set_active_session(self, session_name):
        if not os.path.exists(self.get_session_path(session_name)):
            print(f"Session {session_name} does not exist.")
            return None
        self.active_session = session_name

    def save_chat_to_session(self, session_name, history, chat_user, chat_assistant, token_limit):
        chat_history = history
        chat_history.append(chat_user)
        chat_history.append(chat_assistant)

        # Handle token overflow
        from navi_shell import get_navi_settings
        if get_navi_settings()["overwrite_session"] and self.calculate_tokens(chat_history) > token_limit:
            chat_history.pop(0)

        self.save_session(session_name, chat_history)

    def get_active_session(self):
        return self.active_session

    def remove_session(self, session_name):
        if os.path.exists(self.get_session_path(session_name)):
            if session_name == self.default_session:
                # Clear the default session
                self.save_session(self.default_session, [])
            else:
                # Set active session to the default session
                self.set_active_session(self.default_session)
                # Remove the session file
                os.remove(self.get_session_path(session_name))
                # If the removed session was a config default, set it to the default session
                from navi_shell import get_navi_settings, modify_navi_settings
                if get_navi_settings()["session"] is session_name:
                    modify_navi_settings("session", self.default_session)
        else:
            print(f"{session_name} does not exist.")

    # ------------------------------ CORE NAVI FUNCTIONS --------------------------

    def setup_history(self) -> None:
        self.session = PromptSession(history=FileHistory(self.hist_file))

    def get_user(self) -> str:
        return self.user

    def set_user(self, sys_user: str) -> None:
        self.user = sys_user

    def set_local(self, local_state) -> None:
        self.is_local = local_state

    def set_navi_name(self, navi_name: str) -> None:
        self.ai_name_rep = navi_name

    def print_message(self, text: str, include_ai_name: bool = True) -> None:
        to_print = text
        if include_ai_name:
            to_print = self.ai_name_rep + "> " + text
        sleep_times = {
            (0, 0.1): 0.0,
            (0.1, 0.2): 0.05,
            (0.2, 1.0): 0.01
        }

        try:
            terminal_width = os.get_terminal_size().columns
        except OSError:
            # If we cannot get the terminal size, use a default width
            terminal_width = 80
        # Adjust the wrap width based on 60% of the terminal width
        wrap_width = int(terminal_width * 0.6)

        # Split text into lines to preserve line breaks
        lines = to_print.split('\n')

        for line in lines:
            # Wrap each line individually
            wrapped_lines = textwrap.fill(line, width=wrap_width)
            for char in wrapped_lines:
                print(char, end="", flush=True)
                random_num = random.uniform(0, 1)  # nosec
                for range_tuple, sleep_time in sleep_times.items():
                    if range_tuple[0] <= random_num < range_tuple[1]:
                        time.sleep(sleep_time)
                        break
            # Print a newline character after each wrapped line
            print()

    def clear_terminal(self) -> None:
        os.system('cls' if os.name == 'nt' else 'clear')
        if self.is_local:
            print(self.three_b_art)
        else:
            print(self.art)

    def fetch_token_limits(self):
        from navi_shell import get_navi_settings
        try:
            navi_settings = get_navi_settings()

            token_limit_rag = int(navi_settings["token_limit_rag"])
            token_limit_chat = int(navi_settings["token_limit_chat"])

            # Check if the combined total exceeds the maximum allowed
            return_default = False
            if token_limit_rag < 0 or token_limit_chat < 0:
                print("Warning: Negative token values are invalid. Using default values")
                return_default = True
            if token_limit_rag + token_limit_chat > self.token_limit_max:
                print("Warning: Combined token limits exceed the maximum allowed. Using default values")
                return_default = True
            if return_default:
                return 2048, 2048
            else:
                return token_limit_rag, token_limit_chat
        except (ValueError, TypeError, KeyError) as e:
            print(f"Warning: Issue fetching token limits: {e}. Using default values.")
            return 2048, 2048

    def get_max_token_limit(self):
        return self.token_limit_max

    def llm_chat(self, user_message: str, called_from_app: bool = False, call_remote: bool = False) -> tuple[str, int]:
        # Define the API endpoint and payload
        message_amendment = user_message
        if not called_from_app:
            message_amendment = self.llm_chat_prompt
        message_amendment += user_message

        token_limit_rag, token_limit_chat = self.fetch_token_limits()

        # Check if RAG should be used
        retrieved_context = ""
        if self.is_local:
            # Retrieve context and trim to token limit
            retrieved_context = self.retrieve_context(user_message)
            retrieved_context = self.trim_rag_to_token_limit(retrieved_context, token_limit_rag)

        # Load chat history and trim for token limit
        chat_history = self.load_session(self.active_session)
        chat_submission = self.trim_history_to_token_limit(chat_history, token_limit_chat)

        # Create combined input for API call
        if retrieved_context:
            combined_input = f"Retrieved Context:\n{retrieved_context}\n\nUser Query:\n{message_amendment}"
        else:
            combined_input = message_amendment
        payload = {
            "model": "navi-cli",
            "messages": chat_submission + [{"role": "user", "content": combined_input}]
        }
        headers = {'Content-Type': 'application/json'}
        url = f"http://{self.local}:{self.port}/api/chat"
        if call_remote or not self.is_local:
            url = f"http://{self.server}:{self.port}/api/chat"

        response = requests.post(url, headers=headers, json=payload)

        # Process the response
        if response.status_code == 200:
            response_text = response.text
            messages = [line for line in response_text.split('\n') if line]
            extracted_responses = []

            for msg in messages:
                try:
                    json_msg = json.loads(msg)
                    if json_msg.get('message', {}).get('role') == 'assistant':
                        extracted_responses.append(json_msg['message']['content'])
                except json.JSONDecodeError as e:
                    print("Error decoding JSON:", e)
                except KeyboardInterrupt:
                    self.print_message(f"Keyboard interrupt registered, talk soon {self.user}!")

            # Concatenate assistant responses
            full_response = "".join(extracted_responses)

            # Save only the user message and assistant response to chat history
            self.save_chat_to_session(
                self.active_session,
                chat_history,
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": full_response},
                token_limit_chat
            )

            return full_response, 200
        else:
            return f"Error: {response.status_code}, {response.text}", 400

    def process_message(self, user_message: str) -> None:
        processed_message = self.nlp(user_message.strip())
        navi_commands = [ent for ent in processed_message.ents if ent.label_ == "NAVI_COMMAND"]

        # Check if the message is a question
        question_keywords = {"is", "does", "do", "what", "when", "where", "who", "why", "what", "how"}
        is_question = any(token.text.lower() in question_keywords for token in processed_message if token.i == 0)

        if navi_commands and not is_question:
            command = navi_commands[0].text
            main_command = chips.alias_to_command.get(command)
            if main_command:
                chips.modules[main_command].run(processed_message)
        else:
            response_message, http_status = self.llm_chat(user_message)

            # Normalize TERMINAL OUTPUT and process terminal-related responses
            if "TERMINAL OUTPUT" in response_message.upper():  # Case-insensitive check
                # Normalize TERMINAL OUTPUT
                response_message = response_message.replace("Terminal Output", "TERMINAL OUTPUT").replace(
                    "terminal output", "TERMINAL OUTPUT")

                # Remove unwanted formatting
                clean_response = (
                    response_message.replace("```", "")
                    .replace("bash", "")
                    .replace("TERMINAL OUTPUT", "")
                    .strip()
                )
                if clean_response.startswith("{") and clean_response.endswith("}"):
                    clean_response = clean_response[1:-1].strip()  # Remove surrounding braces

                if clean_response:  # Ensure the command isn't empty
                    chips.modules["navi_sys"].run(clean_response)
                else:
                    self.print_message("Invalid terminal command received.")
            else:
                self.print_message(f"{response_message if http_status == 200 else 'Issue with server'}")

    def chat_with_navi(self) -> None:
        while True:
            # Get user input
            try:
                user_message = self.session.prompt(f"\n{self.user}> ")
            except EOFError:
                self.print_message("Encountered an unexpected end of input.")
                break
            self.process_message(user_message)

    def setup_navi_vocab(self) -> None:
        # Register commands and aliases with the entity ruler
        for command, module in chips.modules.items():
            patterns = [{"label": "NAVI_COMMAND", "pattern": command}]
            aliases = getattr(module, 'aliases', [])  # Safely get the aliases attribute, default to an empty list
            for alias in aliases:
                patterns.append({"label": "NAVI_COMMAND", "pattern": alias})
            self.ruler.add_patterns(patterns)


navi_instance = NaviApp()
