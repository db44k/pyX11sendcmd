# pyX11sendcmd

## Overview
`pyX11sendcmd` is a Python-based tool for sending (nearly) arbitrary keystrokes
to a remote (Open?) X Display System. At heart, it is a re-implementation of
Metasploit's `unix/x11/x11_keyboard_exec` module with a few added features.
Namely, `pyX11sendcmd` allows the caller to specify whether commands are to be
sent through the remote system's QuickLaunch menu (as the Metasploit module
does) but also allows the user to specify a window directly by window ID
(presumably ascertained from alternative sources like `xwininfo`).

In 'root' mode, `pyX11sendcmd` sends the hotkeys to open up a quicklaunch menu
on Ubuntu (ALT+F2) then sends a command specified on the command-line by `-C` or
`--desktop_command`. It then sends a command specified by `-c` or `--window_command`
to the window that currently has focus (ideally the one that was just opened by
the desktop command). There are two delays: `-D` or `--desktop_delay` is the
amount of time to wait for the remote desktop to react to hotkeys and the
desktop command (that is- opening the quicklaunch menu and launching a
terminal). Then `--keyboard_delay` or `-K` is the amount of time to wait between
sending subsequent keystrokes to the active window. This introduces latency
tolerance not seen in the corresponding Metasploit module. Because this mode is
tied to the Ubuntu quicklaunch shortcut it has not been tested outside of
Ubuntu 14, 16, and 18.

Ubuntu 18 will show a desktop popup after the quicklaunch menu is used to
display to the user that the requested application is ready. This can cause
some instability if the application isn't already in use as it will steal the
input focus from the recently-opened window.

In 'window' mode, `pyX11sendcmd` takes a user command specified on the command
line by `-c` or `--window_command` and sends it directly to an already-open X
Window, specified by `-w` or `--window`. (The `xwininfo` command can be used to
identify good targets.) Once specified, `pyX11sendcmd` changes focus to that
window, delivers the command's keystrokes (separated timewise by the value
specified in the `--keyboard_delay` or `-K` parameter) then sends the 'Return' key
and returns window focus to the original. This method requires a terminal to
already be open in the display, but because it doesn't rely on the quicklaunch
shortcuts it can target other Unix-based operating systems in addition to
Ubuntu. (Tested on CentOS 6 and 7. Solaris and FreeBSD coming soon?)

## Usage

```sh
python3 pyX11sendcmd.py -h
usage: pyX11sendcmd.py [-h] [-t TARGET] [-d DISPLAY] [-c WINDOW_COMMAND] [-C DESKTOP_COMMAND] [-w WINDOW] [-R] [-K KEYBOARD_DELAY] [-D DESKTOP_DELAY] [-v]

options:
  -h, --help            show this help message and exit
  -t TARGET, --target TARGET
                        target URL or IP address to throw against
  -d DISPLAY, --display DISPLAY
                        display number to target (default = 0)
  -c WINDOW_COMMAND, --window_command WINDOW_COMMAND
                        command to send to the remote window (default = sleep 10)
  -C DESKTOP_COMMAND, --desktop_command DESKTOP_COMMAND
                        command to send to the desktop launch option (default = xterm)
  -w WINDOW, --window WINDOW
                        window ID to target (cannot be used with --root)
  -R, --root            target the root display (cannot be used with --window)
  -K KEYBOARD_DELAY, --keyboard_delay KEYBOARD_DELAY
                        time (seconds; supports decimals) between simulated keystrokes
  -D DESKTOP_DELAY, --desktop_delay DESKTOP_DELAY
                        time (seconds; supports decimals) between desktop input events
  -v, --verbose         increase output verbosity (not currently implemented)
```

## Example

Send a remote command to the specified window:
```sh
python3 pyX11sendcmd.py -t <TARGET_IP> -d <DISPLAY_NO> -w <WINDOW_ID> -c 'sleep 10'
```

## References
- Metasploit x11_keyboard_exec module - <https://github.com/rapid7/metasploit-framework/blob/master/documentation/modules/exploit/unix/x11/x11_keyboard_exec.md>
- Scorpion Labs Blog - <https://www.klogixsecurity.com/scorpion-labs-blog/>