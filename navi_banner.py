from navi_updater import get_navi_version

breakline = "+===================================================+"

versionNum = get_navi_version()

# The cover art:
art = rf"""{breakline}
|               _   __            _                 |
|              / | / /___ __   __(_)                |
|             /  |/ / __ `/ | / / /                 |
|            / /|  / /_/ /| |/ / /                  |
|           /_/ |_/\__,_/ |___/_/ v{versionNum}            |
|===================================================|
|  Disclaimer: Saints Security Group LLC does not   |
|  condone or support illegal activity and assumes  |
|  no responsibility for damages caused through     |
|  the use of Navi. --nhelp for more information    |
{breakline}
"""
three_b_art = rf"""{breakline}
|          _   __            _ _____ __             |    
|         / | / /___ __   __(_)__  // /_            |
|        /  |/ / __ `/ | / / / /_ </ __ \           |
|       / /|  / /_/ /| |/ / /___/ / /_/ /           |
|      /_/ |_/\__,_/ |___/_//____/_.___/v{versionNum}      |
|===================================================|
|  Disclaimer: Saints Security Group LLC does not   |
|  condone or support illegal activity and assumes  |
|  no responsibility for damages caused through     |
|  the use of Navi. --nhelp for more information    |
{breakline}
"""

helpArt = rf"""{breakline}
      _   __            _    __  __     __
     / | / /___ __   __(_)  / / / /__  / /___
    /  |/ / __ `/ | / / /  / /_/ / _ \/ / __ \\
   / /|  / /_/ /| |/ / /  / __  /  __/ / /_/ /
  /_/ |_/\__,_/ |___/_/  /_/ /_/\___/_/ .___/
                                     /_/
{breakline}
"""
