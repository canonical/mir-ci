#!/usr/bin/env python3
import asyncio
import os
import sys
import time

from mir_ci.virtual_pointer import Button, VirtualPointer

states = {"down": True, "up": False}


def show_help() -> None:
    print(
        f"""
Usage: {os.path.basename(__file__)} [ARGS, COMMANDS...]

Args:
    -h, --help      show this help text
    --wait SECONDS  set time to wait between each command

Commands:
    move X Y        move the pointer, X and Y must be floats between 0 and 1
    pos X Y         position the pointer, X and Y are absolute coordinates
    BUTTON STATE    click or unclick a button
    sleep SECONDS   sleep for the given number of seconds

Buttons: left, right, middle
Button states: up, down
"""
    )


async def main() -> None:
    pointer = VirtualPointer(os.environ["WAYLAND_DISPLAY"])
    wait_time = 0.0
    try:
        args = sys.argv[1:] or ["-h"]
        commands: list = []
        while args:
            arg = args.pop(0)
            if arg == "--help" or arg == "-h":
                show_help()
                exit(0)
            elif arg == "--wait":
                wait_time = float(args.pop(0))
            elif arg == "move":
                commands.append((pointer.move_to_proportional, (float(args.pop(0)), float(args.pop(0)))))
            elif arg == "pos":
                commands.append((pointer.move_to_absolute, (int(args.pop(0)), int(args.pop(0)))))
            elif arg == "left":
                commands.append((pointer.button, (Button.LEFT, states[args.pop(0)])))
            elif arg == "right":
                commands.append((pointer.button, (Button.RIGHT, states[args.pop(0)])))
            elif arg == "middle":
                commands.append((pointer.button, (Button.MIDDLE, states[args.pop(0)])))
            elif arg == "sleep":
                commands.append((time.sleep, (float(args.pop(0)),)))
            else:
                assert False, f"invalid argument: {arg}"
    except Exception as e:
        print("Argument error:", str(e))
        show_help()
        exit(1)
    async with pointer:
        for i, command in enumerate(commands):
            if i and wait_time:
                time.sleep(wait_time)
            print(f'{command[0].__name__}({", ".join(map(str, command[1]))})')
            command[0](*command[1])


if __name__ == "__main__":
    asyncio.run(main())
