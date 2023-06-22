import os
import random

breakline = "+===================================================+"

# The cover art:
art = f"""{breakline}
|               _   __            _                 |
|              / | / /___ __   __(_)                |
|             /  |/ / __ `/ | / / /                 |
|            / /|  / /_/ /| |/ / /                  |
|           /_/ |_/\__,_/ |___/_/ v0.0.6            |
|   Type '/help' for help or '/stop' to exit        |
{breakline}
"""
vbusterArt = f"""{breakline}
|         _    ______             __                |           
|        | |  / / __ )__  _______/ /____  _____     |
|        | | / / __  / / / / ___/ __/ _ \/ ___/     |
|        | |/ / /_/ / /_/ (__  ) /_/  __/ /         |
|        |___/_____/\__,_/____/\__/\___/_/          |
|                Powered by ClamAV                  |
{breakline}

"""
reconArt = f"""{breakline}
|         ____                                      |                     
|        / __ \___  _________  ____                 |
|       / /_/ / _ \/ ___/ __ \/ __ \\                |
|      / _, _/  __/ /__/ /_/ / / / /                |
|     /_/ |_|\___/\___/\____/_/ /_/                 |                                
{breakline}
"""

vthuntArt= f"""{breakline}
|       _    __________  __            __           | 
|      | |  / /_  __/ / / /_  ______  / /_          |
|      | | / / / / / /_/ / / / / __ \/ __/          |
|      | |/ / / / / __  / /_/ / / / / /_            | 
|      |___/ /_/ /_/ /_/\__,_/_/ /_/\__/            | 
|          Code contributed by Wyrd                 |   
{breakline}
"""

# Clear Screen Code
def clearScreen():
  os.system('cls' if os.name == 'nt' else 'clear')

## Nmap Commands
nMapCommands = """Before you pick your options here are some nmap example's to work with.
1. nmap -sV (service version detection) IpAddress/URLHere
2. nmap -sS (TCP SYN scan) IpAddress/URLHere
3. nmap --top-ports (scan top ports) IpAddress/URLHere
4. nmap -O (operating system detection) IpAddress/URLHere
5. nmap -A (aggressive scan) IpAddress/URLHere

Navi> [\u2713] - for example you can chain these: nmap -sSV IpAddress/URLHere 
"""
