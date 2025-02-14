import os
import platform
import shutil
import subprocess  # nosec
import tempfile
from getpass import getpass
from typing import Tuple


def install_ollama() -> bool:
    try:
        if platform.system() in ["Linux"]:
            print("Installing Ollama for Linux...")
            curl_process = subprocess.run(
                ["curl", "-fsSL", "https://ollama.com/install.sh"],
                check=True,
                capture_output=True,
                text=True,
            )

            subprocess.run(
                ["sh"],
                input=curl_process.stdout,
                check=True,
                capture_output=True,
                text=True,
            )
        elif platform.system() in ["Darwin"]:
            print("Installing Ollama for macOS...")
            print("Checking for Homebrew...")
            brew_check = subprocess.run(["brew", "--version"], capture_output=True, text=True)
            if brew_check.returncode != 0:
                print("Homebrew is not installed. Please install Homebrew first:")
                print("Visit: https://brew.sh/")
                return False

            print("Installing Ollama via Homebrew...")
            subprocess.run(["brew", "install", "ollama"], check=True)
            print("Ollama installed successfully on macOS!")
        elif platform.system() == "Windows":
            print("Installing Ollama for Windows...")

            # Download the installer
            subprocess.run(
                ["powershell", "-Command",
                 "Invoke-WebRequest", "-Uri", "https://ollama.com/download/OllamaSetup.exe",
                 "-OutFile", "ollama_installer.exe"],
                check=True,
                capture_output=True,
                text=True,
            )

            # Run the installer
            subprocess.run(
                ["powershell", "-Command",
                 "Start-Process", "-FilePath", "./ollama_installer.exe", "-Wait"],
                check=True,
                capture_output=True,
                text=True,
            )

            # Prompt the user to continue. Really tried to wait for installer but it kept detaching
            print("Please complete the Ollama installation. Once done, type 'c' and press Enter to continue.")
            while input("Type 'c' to continue: ").strip().lower() != 'c':
                print("Invalid input. Please type 'c' to continue.")
        else:
            print("Unsupported platform for Ollama installation.")
            return False
        if not ollama_installed():
            print("Oh dear, something went wrong installing Ollama.")
            return False
        print("Ollama installation succeeded!")
        return True
    except subprocess.CalledProcessError as e:
        print("Ollama installation failed!")
        print("Return code:", e.returncode)
        print("stdout:", e.stdout)
        print("stderr:", e.stderr)
        return False
    finally:
        if platform.system() == "Windows" and os.path.exists("ollama_installer.exe"):
            try:
                os.remove("ollama_installer.exe")
            except Exception as e:
                print(f"Failed to remove installer: {e}")


def ollama_installed() -> bool:
    try:
        subprocess.run(
            ["ollama", "--version"],
            check=True,
            capture_output=True,
            text=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        return False


def is_ollama_service_running() -> bool:
    try:
        process = subprocess.run(
            ["ollama", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        # If no warning is present, the service is running. Ollama doesn't have a proper check...
        if "Warning: could not connect to a running Ollama instance" in process.stderr:
            return False
        return True
    except subprocess.CalledProcessError as e:
        print("Error running 'ollama --version':", e.stderr)
        return False


def start_ollama_service():
    try:
        # Start Ollama serve in the background
        process = subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print(f"Ollama service started with PID: {process.pid}")
        return process
    except Exception as e:
        print(f"Failed to start Ollama service: {e}")
        return None


def check_and_start_ollama_service():
    if is_ollama_service_running():
        print("Ollama service is already running.")
    else:
        print("Ollama service is not running. Attempting to start it...")
        start_ollama_service()


def check_model_installed() -> Tuple[bool, bool]:
    try:
        # Run the command to check if the model exists
        subprocess.run(
            ["ollama", "show", "navi-cli"],
            check=True,
            capture_output=True,
            text=True,
        )
        return True, False  # Model is installed, no unexpected error
    except subprocess.CalledProcessError as e:
        if "Error: model 'navi-cli' not found" in e.stderr:
            return False, False  # Model not installed, no unexpected error
        else:
            print("An unexpected error occurred.")
            print("stderr:", e.stderr)
            return False, True  # Model not installed, unexpected error


def install_model():
    import platform
    is_windows = platform.system() == "Windows"
    temp_script_path = None
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_dir = os.path.join(script_dir, "navi3b")
    if not os.path.exists(repo_dir):
        os.mkdir(repo_dir)
    else:
        shutil.rmtree(repo_dir, ignore_errors=True)
        os.mkdir(repo_dir)

    if not ollama_installed():
        if not install_ollama():
            print("Failed to install Ollama. Visit https://ollama.com and install Ollama manually.")
            return

    if not is_windows:
        # Get sudo password for macOS/Linux
        password = getpass("Enter your sudo password: ")

        # Create a temporary sudo-askpass script
        with tempfile.NamedTemporaryFile("w", delete=False) as temp_script:
            temp_script.write(f"#!/bin/bash\necho {password}\n")
            temp_script_path = temp_script.name

    try:
        print("Cloning model from github.com/saintssec/navi3b...")
        subprocess.run(
            ["git", "clone", "https://github.com/saintssec/navi3b", repo_dir],
            check=True,
            capture_output=True,
            text=True,
        )
        print("Git clone succeeded!")
    except subprocess.CalledProcessError as e:
        print("Git clone failed!")
        print("Return code:", e.returncode)
        print("stdout:", e.stdout)
        print("stderr:", e.stderr)
        shutil.rmtree(repo_dir, ignore_errors=True)
        return

    print("Verifying model...")
    model_file_path = os.path.join(repo_dir, "navi3b.modelfile")
    if not os.path.exists(model_file_path):
        print(f"Error: {model_file_path} not found.")
        return

    # Create the model using Ollama
    try:
        print("Creating model... this may take a while...")
        if is_windows:
            subprocess.run(
                ["ollama", "create", "navi-cli", "-f", model_file_path],
                check=True,
                capture_output=True,
                text=True,
            )
        else:
            env = os.environ.copy()
            env["SUDO_ASKPASS"] = temp_script_path
            subprocess.run(
                ["sudo", "ollama", "create", "navi-cli", "-f", model_file_path],
                env=env,
                check=True,
                capture_output=True,
                text=True,
            )

        print("Model creation succeeded!")
    except subprocess.CalledProcessError as e:
        print("Model creation failed!")
        print("Return code:", e.returncode)
        print("stdout:", e.stdout)
        print("stderr:", e.stderr)
    finally:
        # Cleanup: Remove the temporary script and cloned directory
        if temp_script_path and os.path.exists(temp_script_path):
            os.remove(temp_script_path)
        shutil.rmtree(repo_dir, ignore_errors=True)
