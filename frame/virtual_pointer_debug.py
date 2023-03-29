#!/usr/bin/env python3
from virtual_pointer import VirtualPointer, Button
import os
import sys
import time

states = {'down': True, 'up': False}

def show_help() -> None:
    print(f'''
Usage: {os.path.basename(__file__)} [COMMANDS...]

Commands:
    move X Y        move the pointer, X and Y must be floats between 0 and 1
    BUTTON STATE    click or unclick a button
    sleep SECONDS   sleep for the given number of seconds

Buttons: left, right, middle
Button states: up, down
''')

def run() -> None:
    pointer = VirtualPointer(os.environ['WAYLAND_DISPLAY'])
    args = sys.argv[1:]
    commands: list = []
    while args:
        arg = args.pop(0)
        if arg == '--help' or arg == '-h':
            show_help()
            exit(0)
        elif arg == 'move':
            commands.append((pointer.move_to_proportional, (float(args.pop(0)), float(args.pop(0)))))
        elif arg == 'left':
            commands.append((pointer.button, (Button.LEFT, states[args.pop(0)])))
        elif arg == 'right':
            commands.append((pointer.button, (Button.RIGHT, states[args.pop(0)])))
        elif arg == 'middle':
            commands.append((pointer.button, (Button.MIDDLE, states[args.pop(0)])))
        elif arg == 'sleep':
            commands.append((time.sleep, (float(args.pop(0)),)))
        else:
            assert False, f'invalid argument: {arg}'
    with pointer:
        for command in commands:
            print(f'{command[0].__name__}({", ".join(map(str, command[1]))})')
            command[0](*command[1])

if __name__ == '__main__':
    run()
