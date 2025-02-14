#!/bin/python3
import platform
import socket
from datetime import datetime

import psutil
import requests

import navi_internal

# Navi Command System Variables
command = "navi_specs"
use = "Prints out system information"
aliases = ['--nspecs', 'nspecs']

# global variables
breakline = "======="


def get_system_info():
    return {
        'Platform': platform.system(),
        'Release': platform.release(),
        'Version': platform.version(),
        'Machine': platform.machine(),
        'Processor': platform.processor()
    }


def get_memory_info():
    memory = psutil.virtual_memory()
    return {
        'Total Memory': f"{memory.total / (1024 * 1024)} MB",
        'Available Memory': f"{memory.available / (1024 * 1024)} MB"
    }


def get_disk_info():
    disk = psutil.disk_usage('/')
    return {
        'Total Disk Space': f"{disk.total / (1024 * 1024 * 1024)} GB",
        'Used Disk Space': f"{disk.used / (1024 * 1024 * 1024)} GB",
        'Free Disk Space': f"{disk.free / (1024 * 1024 * 1024)} GB"
    }


def get_uptime_info():
    boot_time = psutil.boot_time()
    uptime = datetime.now() - datetime.fromtimestamp(boot_time)
    return {
        'Uptime': str(uptime).split('.')[0]
    }


def get_public_ip():
    response = requests.get('https://api.ipify.org')
    return response.text.strip()


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # Use port 80 instead of 0
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except OSError as e:
        print(f"Error: {e}")
        return None


def run(arguments=None):
    navi_instance = navi_internal.navi_instance
    # setup variables
    local_ip = get_local_ip()
    system_info = get_system_info()
    memory_info = get_memory_info()
    disk_info = get_disk_info()
    uptime_info = get_uptime_info()

    # Main functions
    response_message = navi_instance.llm_chat(
        "Give me a really simple quip about getting my systems specs. Dont include commands or references to operating systems.",
        True)
    clean_text = str(response_message).replace("(", "").replace(")", "").replace(", 200", "").replace("\"", "").replace(
        "\\n", "")
    output = clean_text + "\n"
    output += breakline
    output += "System Information:\n"
    for key, value in system_info.items():
        output += f"{key}: {value}\n"

    output += breakline
    output += "Memory Information:\n"
    for key, value in memory_info.items():
        output += f"{key}: {value}\n"

    output += breakline
    output += "Disk Space Information:\n"
    for key, value in disk_info.items():
        output += f"{key}: {value}\n"

    output += breakline
    output += "Uptime Information:\n"
    for key, value in uptime_info.items():
        output += f"{key}: {value}\n"
    output += breakline
    output += "Network Information: \n"
    output += f"Your local ip is: {local_ip}\n"
    output += "Your public ip is: redacted -- Nice try\n"
    navi_instance.print_message(output)
