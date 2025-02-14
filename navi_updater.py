import os
import shutil
import subprocess  # nosec
import sys
import zipfile
from typing import Any

import requests

global prime_navi_version
navi_version_path = ".navi_version"


def get_navi_version() -> str:
    if not os.path.exists(navi_version_path):
        return "Unknown"
    with open(navi_version_path, 'r') as version_file:
        return version_file.read()


def check_version(edge: bool = False) -> str:
    repo_owner = "SaintsSec"
    repo_name = "Navi"

    version = get_navi_version()

    result, download_url = check_for_new_release(version, repo_owner, repo_name, edge)
    print(result)

    return download_url


def get_latest_release(repo_owner: str, repo_name: str, edge: bool = False) -> dict[str, Any] | None:
    if edge:
        api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases"
    else:
        api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"

    response = requests.get(api_url)

    if response.status_code == 200:
        data = response.json()
        if edge:
            for release in data:
                if release['prerelease']:
                    return {
                        'tag_name': release.get('tag_name'),
                        'release_name': release.get('name'),
                        'html_url': release.get('zipball_url')
                    }
        else:
            return {
                'tag_name': data.get('tag_name'),
                'release_name': data.get('name'),
                'html_url': data.get('zipball_url')
            }
    return None


def is_new_release(current_version: str, latest_version: str) -> bool:
    return current_version < latest_version


def update_version_number(version: str) -> None:
    with open(".navi_version", 'w') as version_file:
        version_file.write(version)


def check_for_new_release(current_version: str, repo_owner: str, repo_name: str, edge: bool = False) -> tuple[
    str, str | None]:
    latest_release = get_latest_release(repo_owner, repo_name, edge)
    if current_version == "Unknown" or (latest_release and is_new_release(current_version, latest_release['tag_name'])):
        global prime_navi_version
        prime_navi_version = latest_release['tag_name']
        return f"New release available!!\n{latest_release['release_name']} ({latest_release['tag_name']})\nURL: {latest_release['html_url']}\n", \
            latest_release['html_url']
    else:
        return "You are running the latest version", None


def update_script(download_url: str) -> None:
    print("Updating the script...")
    try:
        # Download the latest version
        response = requests.get(download_url)
        zip_path = "latest_version.zip"

        with open(zip_path, 'wb') as file:
            file.write(response.content)

        # Unzip the downloaded file
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall("latest_version")

        # Find the path of the current script
        current_script_path = os.path.abspath(sys.argv[0])
        print(f"Current script path: {current_script_path}")

        # Copy all files from the extracted archive to the current directory
        extracted_dir = os.path.join("latest_version", os.listdir("latest_version")[0])
        for item in os.listdir(extracted_dir):
            s = os.path.join(extracted_dir, item)
            d = os.path.join(os.getcwd(), item)
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)

        # Clean up
        shutil.rmtree("latest_version")
        os.remove(zip_path)

        print("Installing any new packages...")

        # Install new packages from requirements.txt
        requirements_path = os.path.join("install", "requirements.txt")
        if os.path.exists(requirements_path):
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_path])  # nosec

        global prime_navi_version
        update_version_number(prime_navi_version)
        print("Update successful. Restarting the script...")

        from navi_shell import restart_navi
        restart_navi()

    except Exception as e:
        print(f"Update failed: {e}")
