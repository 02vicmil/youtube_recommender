import pathlib
import os
import platform
import importlib
import sys
import shutil
import fnmatch
import hashlib
import string
import random
import time
from typing import List, Dict
sys.path.append(str(pathlib.Path(__file__).resolve().parents[0]))

def get_directory_path(__file__in, up_directories=0):
    return str(pathlib.Path(__file__in).parents[up_directories].resolve()).replace("\\", "/")


def run_command(command: str) -> None:
    """Run a command in the terminal"""
    if platform.system() == "Windows": # Windows
        win_command = None
        if command[0] != '"':
            win_command = f'powershell; {command}'
        else:
            win_command = f'powershell; &{command}'

        print("running command: ", f'{win_command}')
        os.system(win_command)
    else:
        print("running command: ", f'{command}')
        os.system(command)


def python_virtual_environment(env_directory_path):
    # Setup a python virtual environmet
    os.makedirs(env_directory_path, exist_ok=True) # Ensure directory exists
    run_command(f'"{sys.executable}" -m venv "{env_directory_path}"')


def get_venv_site_packages_path(venv_path):
    """Returns the site-packages path for a given virtual environment."""
    python_version = f"python{sys.version_info.major}.{sys.version_info.minor}"
    
    # Construct the expected site-packages path
    if platform.system() == "Windows": # Windows
        # The site package path may vary on windows, so we check for both
        site_packages_path = os.path.join(venv_path, "Lib", "site-packages")
        if not os.path.exists(site_packages_path):
            site_packages_path = os.path.join(venv_path, "lib", python_version, "site-packages")
    else:  # macOS/Linux
        site_packages_path = os.path.join(venv_path, "lib", python_version, "site-packages")

    return site_packages_path if os.path.exists(site_packages_path) else None


def get_venv_pip_path(env_directory_path):
    if platform.system() == "Windows":
        # The path may vary on windows, so we need to check for both the scripts path and the bin path
        script_path = f'{env_directory_path}/Scripts/pip.exe'
        print("script_path", script_path)
        if os.path.exists(script_path):
            return script_path
        bin_path = f'{env_directory_path}/bin/pip'
        return bin_path
    else:
        return f'{env_directory_path}/bin/pip'


def pip_install_packages_in_virtual_environment(env_directory_path, packages):
    if not os.path.exists(env_directory_path):
        print("Invalid path")
        raise Exception("Invalid path")
    
    for package in packages:
        run_command(f'"{get_venv_pip_path(env_directory_path)}" install {package}')


def try_import_module(module_name: str) -> bool:
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False
    

def module_installed_in_virtual_environment(venv_path: str, module_name: str):
    module_path = get_venv_site_packages_path(venv_path=venv_path) + "/" + module_name
    return os.path.exists(module_path)
    

def include_other_venv(other_venv_path: str):
    site_package_path = get_venv_site_packages_path(other_venv_path)
    if not other_venv_path in sys.path:
        print("Updating sys.path with other venv", site_package_path)
        sys.path.append(site_package_path)  # Add other venv's site-packages to sys.path


def parse_requirements(file_path):
    requirements = []
    with open(file_path, 'r') as f:
        for line in f:
            # Strip whitespace and ignore comments or empty lines
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            # Remove inline comments
            line = line.split('#')[0].strip()

            requirements.append(line)

    return requirements


def open_webbrowser(url: str):
    import webbrowser
    webbrowser.open(url, new=0, autoraise=True)


def serve_html_page(html_file_path: str):
    import webbrowser
    """ Start the webbrowser if not already open and launch the html page

    Parameters
    ----------
        html_file_path (str): The path to the html file that should be shown in the browser

    Returns
    -------
        None
    """
    os.chdir(get_directory_path(html_file_path, 0))
    if not (os.path.exists(html_file_path)):
        print("html file does not exist!")
        return
    
    file_name: str = html_file_path.replace("\\", "/").rsplit("/", maxsplit=1)[-1]
    webbrowser.open("http://localhost:8000/" + file_name, new=0, autoraise=True)

    try:
        run_command(f'"{sys.executable}" -m http.server --bind localhost')
    except Exception as e:
        pass

    
import subprocess
def invoke_python_file_using_subprocess(python_env_path: str, file_path: str, logfile_path: str = None) -> subprocess.Popen:
    if not os.path.exists(python_env_path):
        print(f"invalid path: {python_env_path}")

    if not os.path.exists(file_path):
        print(f"invalid path: {file_path}")

    current_directory = str(pathlib.Path(file_path).parents[0].resolve()).replace("\\", "/")
    os.chdir(current_directory) # Set active directory to the current directory

    command = ""
    my_os = platform.system()
    if logfile_path:
        if my_os == "Windows":
            command = f'powershell; &"{python_env_path}/Scripts/python" -u "{file_path}" > "{logfile_path}"'
        else:
            command = f'"{python_env_path}/bin/python" -u "{file_path}" > "{logfile_path}"'
    else:
        if my_os == "Windows":
            command = f'powershell; &"{python_env_path}/Scripts/python" -u "{file_path}"'
        else:
            command = f'"{python_env_path}/bin/python" -u "{file_path}"'

    new_process = subprocess.Popen(command, shell=True)
    return new_process


def ensure_package_installed_in_virtual_environment(venv_path: str, module_name: str):
    if not module_installed_in_virtual_environment(venv_path=venv_path, module_name=module_name):
        print(f"installing {module_name}")
        pip_install_packages_in_virtual_environment(venv_path, [module_name])
    else:
        print(f"{module_name} already installed")


def start_file(start_file_path, pip_package_names, venv_path = get_directory_path(__file__) + "/venv"):
    # Setup virtual environment with the required packages
    if not os.path.exists(venv_path):
        python_virtual_environment(venv_path)
    
    for pip_package in pip_package_names:
        ensure_package_installed_in_virtual_environment(venv_path=venv_path, module_name=pip_package)

    new_process = None
    try:
        new_process = invoke_python_file_using_subprocess(venv_path, start_file_path)
        while True:
            time.sleep(1)
    finally:
        if new_process:
            new_process.kill()


if __name__ == "__main__":
    start_file_path = get_directory_path(__file__) + "/app.py"

    open_webbrowser("http://127.0.0.1:5005/videos")

    start_file(start_file_path, ["flask", "SQLAlchemy", "google-api-python-client"])

    
        