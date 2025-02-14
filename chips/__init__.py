"""Init commands."""
import importlib
import logging
import os
import sys
from os.path import dirname, join, exists
from pathlib import Path

package_dir = Path(__file__).parent

# Add the parent directory to the Python path
sys.path.append(dirname(dirname(__file__)))

# Ensure the logs directory exists
logs_dir = join(dirname(dirname(__file__)), 'logs')
if not exists(logs_dir):
    os.makedirs(logs_dir)

# Initialize an empty dictionary for modules, alias-to-command mapping, and command usage
modules = {}
alias_to_command = {}
command_usage = {}


def load_module(name):
    """Load module with the given name."""
    try:
        module = importlib.import_module(f".{name}", 'chips')
    except ModuleNotFoundError as e:
        print(f"Module '{name}' not found: {e}")
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s %(levelname)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            filename=join(logs_dir, "error.log"),
        )
        logging.error(f"Chip '{name}' not found: {e}")
    except Exception as generic:
        logging.error(f"Issue loading Chip '{name}': {generic}")
        return
    else:
        return module


def module_name_from_path(f):
    rel_path = f.relative_to(package_dir).with_suffix('')
    module_name = '.'.join(rel_path.parts)
    return module_name


# List all .py files in the current directory and subdirectories, excluding __init__.py
__all__ = [
    module_name_from_path(f)
    for f in package_dir.rglob('*.py')
    if f.is_file() and f.name != '__init__.py'
]

# Load each module found in __all__
for module_name in __all__:
    mod = load_module(module_name)
    if mod:
        if hasattr(mod, 'command'):
            modules[mod.command] = mod
            alias_to_command[mod.command] = mod.command  # Map the command to itself
            aliases = getattr(mod, 'aliases', [])  # Safely get the aliases attribute, default to an empty list
            for alias in aliases:
                alias_to_command[alias] = mod.command  # Map each alias to the main command
            use = getattr(mod, 'use', None)  # Safely get the use attribute, default to None
            if use:
                command_usage[mod.command] = use
        else:
            print(f"Warning: The Chip '{module_name}' is not installed correctly. Ignoring module.")
    else:
        print(f"Chip '{module_name}' could not be loaded.")

# Export modules, alias_to_command, and command_usage for use in other scripts
__all__.extend(['modules', 'alias_to_command', 'command_usage'])
