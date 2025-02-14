import os
import shutil
import subprocess  # nosec
import sys
import uuid
import zipfile

import requests
from colorama import Fore

import navi_internal
from navi import get_parameters
from navi_shell import restart_navi

command = "chips"
use = "Manage Navi chips"
aliases = ['chip']
navi = None


def get_latest_release(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    response = requests.get(url)
    return response.json() if response.status_code == 200 else 'No release found'


def search_for_chips(name=None, per_page=10, page=1):
    query = f"topic:navi-chips" + (f"+{name} in:name" if name else "")
    url = f"https://api.github.com/search/repositories?q={query}&per_page={per_page}&page={page}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('items', [])
    else:
        print(f"Failed to retrieve repositories: {response.status_code}")
        return []


def search(command):
    try:
        _, name, page_size, page_num = command + [None, 10, 1][len(command) - 1:]
        page_size = int(page_size)
        page_num = int(page_num)
    except ValueError:
        print(f"{Fore.RED}Invalid command{Fore.RESET}\n"
              f"{Fore.YELLOW}chips search [*query] [*page size] [*page number]{Fore.RESET}\n"
              f"* = optional")
        return

    repos = search_for_chips(name, page_size, page_num)
    if not repos:
        print(f"{Fore.RED}No Navi Chips found.{Fore.RESET}")
        return

    available_repos = 0
    for repo in repos:
        owner, repo_name = repo['owner']['login'], repo['name']
        latest_release = get_latest_release(owner, repo_name).get('tag_name')
        if latest_release and latest_release != "No release found":
            available_repos += 1
            print(f"Name: {repo_name}, Owner: {owner}, Latest Release: {latest_release}")

    if available_repos == 0:
        print("No Navi Chips found with releases.")


def download_and_extract(download_url):
    download_guid = str(uuid.uuid4())
    zip_path = f"{download_guid}.zip"

    try:
        response = requests.get(download_url)
        with open(zip_path, 'wb') as file:
            file.write(response.content)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(download_guid)

        extracted_dir = os.path.join(download_guid, os.listdir(download_guid)[0])
        os.remove(zip_path)
        return extracted_dir, download_guid

    except Exception as e:
        print(f"An error occurred during the download and extraction of chip: {e}")
        return None, None


def copy_files_to_install_path(extracted_dir, install_path="/chips/Com"):
    installed_files = []
    try:
        for item in os.listdir(extracted_dir):
            if item == "LICENSE" or item.endswith(".md") or item == ".gitignore":
                continue
            s, d = os.path.join(extracted_dir, item), os.path.join(install_path, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)
            installed_files.append(d)
    except Exception as e:
        print(f"An error occurred while copying files: {e}")
    return installed_files


def install_requirements(extracted_dir):
    requirements_path = os.path.join(extracted_dir, "chip-requirements.txt")
    if os.path.exists(requirements_path):
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", requirements_path],
                check=True, capture_output=True, text=True)  # nosec
            print(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"Error occurred: {e}")  # Prevent the program from crashing from pip install errors
            print(e.stderr)
        os.remove(requirements_path)


def update_script(download_url, install_path="chips/Com"):
    print("Downloading chip...")
    extracted_dir, download_guid = download_and_extract(download_url)
    if extracted_dir:
        installed_files = copy_files_to_install_path(extracted_dir, install_path)
        install_requirements(install_path)
        shutil.rmtree(download_guid)  # Ensure the download_guid folder is removed
        return installed_files
    return []


def log_installation(repo, installed_files, version):
    log_entry = (
            f"Repo Name: {repo['name']}\n"
            f"Description: {repo['description']}\n"
            f"HTML URL: {repo['html_url']}\n"
            f"Owner: {repo['owner']['login']}\n"
            f"Version: {version}\n"
            f"Installed Files:\n" + "\n".join(installed_files) + "\n\n"
    )
    with open("installed_chips.txt", 'a') as log_file:
        log_file.write(log_entry)


def is_installed(repo_name: str) -> bool | str:
    if not os.path.exists("installed_chips.txt"):
        return False
    with open("installed_chips.txt", 'r') as log_file:
        return repo_name in log_file.read()


def install_chip(name: str, restart_app: bool = True) -> None:
    repos = search_for_chips(name)
    if not repos:
        print("No repositories found.")
        return

    repo = repos[0]
    if is_installed(repo['name']):
        print(f"The chip '{repo['name']}' is already installed.")
        return

    release = get_latest_release(repo['owner']['login'], repo['name'])
    if not release or release == "No release found":
        print("No release found for this repository.")
        return

    installed_files = update_script(release['zipball_url'])
    log_installation(repo, installed_files, release['tag_name'])
    print(f"Chip '{repo['name']}' installed successfully. Restarting Navi...")
    if restart_app:
        restart_navi()


def uninstall_chip(name: str, restart_app: bool = True) -> None:
    if not os.path.exists("installed_chips.txt"):
        print(f"{Fore.RED}No chips installed.{Fore.RESET}")
        return

    with open("installed_chips.txt", 'r') as log_file:
        lines = log_file.readlines()

    package_start = next((i for i, line in enumerate(lines) if line.strip() == f"Repo Name: {name}"), None)
    if package_start is None:
        print(f"The chip '{name}' is not installed.")
        return

    package_end = next((i for i in range(package_start, len(lines)) if lines[i].strip() == ""), len(lines))
    installed_files = [line.strip() for line in lines[package_start:package_end] if
                       not line.startswith("Installed Files:")]

    for file_path in installed_files:
        if os.path.exists(file_path):
            if os.path.isdir(file_path):
                shutil.rmtree(file_path)
            else:
                os.remove(file_path)

    with open("installed_chips.txt", 'w') as log_file:
        log_file.writelines(lines[:package_start] + lines[package_end + 1:])

    print(f"{Fore.GREEN}The chip {Fore.WHITE}'{name}' {Fore.GREEN}has been uninstalled successfully.{Fore.RESET}")
    if restart_app:
        restart_navi()


def get_installed_chips() -> list[dict[str, str]] | None:
    log_file_path = "installed_chips.txt"

    if not os.path.exists(log_file_path):
        return

    with open(log_file_path, 'r') as log_file:
        lines = log_file.readlines()

    if not lines:
        return

    modules = []
    module_info = {}
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("Repo Name:"):
            module_name = line.split("Repo Name: ")[1]
            description = lines[i + 1].split("Description: ")[1].strip()
            html_url = lines[i + 2].split("HTML URL: ")[1].strip()
            owner = lines[i + 3].split("Owner: ")[1].strip()
            version = lines[i + 4].split("Version: ")[1].strip()

            module_info = {
                "name": module_name,
                "description": description,
                "html_url": html_url,
                "owner": owner,
                "version": version
            }
            modules.append(module_info)
        i += 1
    return modules


def get_dev_chips():
    import chips
    dev_chips = []
    for command_name, module in chips.modules.items():
        if module.__name__.startswith("chips.Dev"):
            command_aliases = getattr(module, 'aliases', [])
            command_use = getattr(module, 'use', "")
            dev_chips.append((command_name, command_use, command_aliases))
    return dev_chips


def list_installed_chips() -> None:
    chips = get_installed_chips()
    if chips:
        print("Installed Community Chips:")
        for module in chips:
            print(f"- {module['name']} (Owner: {module['owner']}, Version: {module['version']})")
    else:
        print("No Community Chips are installed.")
    dev_chips = get_dev_chips()
    if not dev_chips:
        print("No Developer Chips are installed.")
    else:
        print("\nDeveloper Chips:")
        for chip in dev_chips:
            print(f"- {chip[0]} (Use: {chip[1]}, Aliases: {chip[2]})")


def about_chip(name) -> dict[str, str] | None:
    log_file_path = "installed_chips.txt"

    if not os.path.exists(log_file_path):
        print("No Community Chips are installed.")
        return None

    with open(log_file_path, 'r') as log_file:
        lines = log_file.readlines()

    for i, _ in enumerate(lines):
        if lines[i].startswith("Repo Name:") and lines[i].split(": ")[1].strip() == name:
            module_name = lines[i].split(": ")[1].strip()
            description = lines[i + 1].split(": ")[1].strip()
            html_url = lines[i + 2].split(": ")[1].strip()
            owner = lines[i + 3].split(": ")[1].strip()
            version = lines[i + 4].split(": ")[1].strip()
            installed_files = []

            j = i + 5
            while j < len(lines) and lines[j].strip() != "":
                installed_files.append(lines[j].strip())
                j += 1

            # Check for the latest version
            latest_release = get_latest_release(owner, module_name)
            latest_version = latest_release['tag_name'] if latest_release else "Unknown"

            if latest_version != version:
                print(
                    f"{Fore.GREEN}A later version is available: {latest_version}.{Fore.RESET} To update type {Fore.YELLOW}'chips update {name}'{Fore.RESET}")
            else:
                print("You have the latest version installed.")

            return {
                "name": module_name,
                "description": description,
                "html_url": html_url,
                "owner": owner,
                "version": version,
                "installed_files": installed_files,
                "latest_version": latest_version
            }

    print(f"The Community Chip '{name}' is not installed.")
    return None


def update_chip(chip_name: str) -> None:
    chip_info = about_chip(chip_name)
    if not chip_info:
        print(f"The chip '{chip_name}' is not installed.")
        return

    if chip_info['latest_version'] != chip_info['version']:
        print(f"Updating chip '{chip_name}' to version {chip_info['latest_version']}...")
        uninstall_chip(chip_name, False)
        install_chip(chip_name, False)
        print(f"Chip '{chip_name}' updated successfully. Restarting Navi...")
        restart_navi()


def help_text() -> None:
    navi.print_message("Chip Manager\n"
                       "chips [install | uninstall | search | update] [app/query]\n\n"
                       "List currently installed chips\n"
                       "chips list")


def run(arguments=None) -> None:
    global navi
    navi = navi_internal.navi_instance
    argv = get_parameters(arguments.text)
    argv.pop(0)

    if not argv:
        help_text()
        return

    command = argv[0]

    if command == "list":
        list_installed_chips()
        return

    if command == "search":
        search(argv)
        return

    if len(argv) == 1:
        chip_info = about_chip(argv[0])
        if chip_info:
            print(f"Name: {chip_info['name']}")
            print(f"Description: {chip_info['description']}")
            print(f"URL: {chip_info['html_url']}")
            print(f"Owner: {chip_info['owner']}")
            print(f"Your Version: {chip_info['version']}")
            print(f"Latest Version: {chip_info['latest_version']}")
        return

    if command == "install" and len(argv) > 1:
        install_chip(argv[1])
        return

    if command == "uninstall" and len(argv) > 1:
        uninstall_chip(argv[1])
        return

    if command == "update" and len(argv) > 1:
        update_chip(argv[1])
        return

    help_text()
