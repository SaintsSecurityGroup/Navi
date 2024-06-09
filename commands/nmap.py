#!/bin/python3
import re
import os
from typing import List
from navi_shell import tr

command = "nmap"
use = "Port scanning"


def run_nmap_scan(target, ports=None, arguments=None):
    # Initialize the nmap command
    command = ['nmap']
    if ports:
        command.extend(['-p', ','.join(ports)])  # Join the ports list into a single string
    if arguments:
        command.extend(arguments)
    command.append(target)

    # Run the nmap command
    result = os.system(" ".join(command))
    return result


def run(arguments=None):
    ip_address = None
    hostname = None

    port_numbers: List[str] = []
    if arguments:
        for token in arguments:
            # Find IP address using regex match
            if re.match(r'(\d{1,3}\.){3}\d{1,3}', token.text):
                ip_address = token.text
            # Find hostname using regex match
            elif re.match(r'[a-zA-Z0-9\-]+\.[a-zA-Z]{2,3}', token.text):
                hostname = token.text

        # Find multiple port numbers
        ports_pattern = re.compile(r'\bports?\s+([\d\s,]+(?:\s*(?:and|,)\s*[\d\s,]*)*)', re.IGNORECASE)
        for match in ports_pattern.finditer(arguments.text):
            ports_text = match.group(1)
            # Split ports by 'and', commas, and spaces to handle multiple ports
            for port in re.split(r'\s*,\s*|\s+and\s+|\s+', ports_text):
                if port.isdigit():
                    port_numbers.append(port)
    if ip_address is None and hostname is None:
        tr("Sorry, you need to provide a valid IP address or hostname")
    else:
        tr("Running... hang tight!\n")
        target = ip_address if ip_address is not None else hostname
        nmap_construction = f"nmap {'-p ' + ','.join(port_numbers) + ' ' if port_numbers else ''}{target}"
        pattern = re.compile(r"""
        -p\s*[\d,-]+|                       # Match -p followed by digits, commas, or hyphens (port ranges)
        -[A-Za-z0-9]{1,2}(?:\s|$)|          # Match short flags (e.g., -A, -sV) followed by a space or end of string
        --\w+(?:=\S+)?|                     # Match long flags and their arguments (e.g., --script, --version-intensity=5)
        \b-T[0-5]\b                         # Match timing templates (e.g., -T0 to -T5)
    """, re.VERBOSE)

        # Find all matches in the command string
        matches = pattern.findall(arguments.text)
        stdout = run_nmap_scan(target, port_numbers, matches)
