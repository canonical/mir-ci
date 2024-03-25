# Copyright 2024 Canonical Ltd.
# Written by:
#   Paolo Gentili <paolo.gentili@canonical.com>
#   Michał Sawicz <michal.sawicz@canonical.com>
# pylint:   disable=C0103
"""
This module provides a robot-library for accessing Zapper HID capabilities.
"""
import math
import time
from typing import List

from robot.api.deco import keyword

from zapper.config import load_config
from zapper.hid import translator
from zapper.hid.hid_codes import HidKey, HidModifier
from zapper.robot.libraries.ZapperProxy import send_zapper_command

MOUSE_STEP = 127


def _get_resolution():
    res = load_config()["hdmi"]["resolution"].split("x")
    assert len(res) == 2, f"Failed to parse resolution: {res}"
    return tuple(int(v) for v in res)


class ZapperHid:
    """
    This library provides access to Zapper HID capabilities.
    """

    ROBOT_LIBRARY_SCOPE = "TEST"

    mouse_position = None
    mouse_moves = 0
    pressed_buttons = None

    @keyword
    def keys_combo(self, combo: List[str]):
        """Press and release a combination of keys using Zapper HID."""

        keys = []
        for key in combo:
            if key in HidKey:
                keys.append(HidKey[key])
            elif key in HidModifier:
                keys.append(HidModifier[key])
            else:
                raise ValueError(f"Characted {key} is not supported.")

        actions = translator.generate_actions_for_key_combo(keys)
        send_zapper_command("handle_hid_actions", actions)

    @keyword
    def type_string(self, string: str):
        """Type a given string using Zapper HID."""
        actions = translator.generate_actions_for_typing(string)
        send_zapper_command("handle_hid_actions", actions)

    def _init_mouse(self) -> None:
        # TODO: drop this once stylus support is in (ZAP-660)
        # Reset button state and move to (0, 0) in increments of MOUSE_STEP
        if self.pressed_buttons is None:
            self.pressed_buttons = set()
        if self.mouse_position is None:
            for _i in range(
                0, math.ceil(max(*_get_resolution()) / MOUSE_STEP)
            ):
                send_zapper_command(
                    "hid_mouse",
                    tuple(self.pressed_buttons),
                    -MOUSE_STEP,
                    -MOUSE_STEP,
                    0,
                )
            self.mouse_moves = 0
            self.mouse_position = [0, 0]

    def _move_mouse(self, x, y) -> None:
        self._init_mouse()
        self.mouse_position[0] += x
        self.mouse_position[1] += y
        send_zapper_command("hid_mouse", tuple(self.pressed_buttons), x, y, 0)
        self.mouse_moves += 1

    @keyword
    def press_pointer_button(self, button: str) -> None:
        """Press the (LEFT|MIDDLE|RIGHT) mouse button"""
        self._init_mouse()
        self.pressed_buttons.add(button)
        send_zapper_command("hid_mouse", tuple(self.pressed_buttons), 0, 0, 0)

    @keyword
    def release_pointer_button(self, button: str) -> None:
        """Release the (LEFT|MIDDLE|RIGHT) mouse button"""
        self._init_mouse()
        try:
            self.pressed_buttons.remove(button)
        except KeyError:
            pass
        else:
            send_zapper_command(
                "hid_mouse", tuple(self.pressed_buttons), 0, 0, 0
            )

    @keyword
    def release_buttons(self) -> None:
        """Release all pointer buttons"""
        self._init_mouse()
        self.pressed_buttons.clear()
        send_zapper_command("hid_mouse", 0, 0, 0, 0)

    @keyword
    def click_pointer_button(self, button: str) -> None:
        """Click the (LEFT|MIDDLE|RIGHT) mouse button"""
        send_zapper_command("mouse_click", (button,))
        # To avoid bounce inhibition
        time.sleep(0.05)

    @keyword
    def walk_pointer_to_absolute(self, x: int, y: int, step_distance: int, delay: float) -> None:
        """
        Walk the virtual pointer to an absolute position within the output, maximum `step_distance`
        at a time, with `delay` seconds in between.
        """
        assert isinstance(x, int) and isinstance(
            y, int
        ), "Coordinates must be integers"

        resolution = _get_resolution()
        assert 0 <= x <= resolution[0], "X coordinate outside of screen"
        assert 0 <= y <= resolution[1], "Y coordinate outside of screen"

        step = min(step_distance, MOUSE_STEP)

        self._init_mouse()
        while self.mouse_position != [x, y]:
            dist_x = x - self.mouse_position[0]
            dist_y = y - self.mouse_position[1]
            step_x = min(abs(dist_x), step) * (dist_x < 0 and -1 or 1)
            step_y = min(abs(dist_y), step) * (dist_y < 0 and -1 or 1)
            self._move_mouse(step_x, step_y)
            time.sleep(delay)

    @keyword
    def walk_pointer_to_proportional(
        self, x: float, y: float, step_distance: int, delay: float
    ) -> tuple[int, int]:
        """
        Move the virtual pointer to a position proportional to the size
        of the output.
        """
        assert 0 <= x <= 1, "x not in range 0..1"
        assert 0 <= y <= 1, "y not in range 0..1"

        resolution = _get_resolution()
        return self.walk_pointer_to_absolute(
            int(resolution[0] * x), int(resolution[1] * y), step_distance, delay
        )

    @keyword
    def move_pointer_to_absolute(self, x: int, y: int) -> None:
        """
        Move the virtual pointer to an absolute position within the output.

        TODO: this should be done with a stylus HID device (ZAP-660) instead
        """
        self.walk_pointer_to_absolute(x, y, MOUSE_STEP, 0)

    @keyword
    def move_pointer_to_proportional(self, x: float, y: float) -> None:
        """
        Move the virtual pointer to a position proportional to the size
        of the output.

        TODO: this should be done with a stylus HID device (ZAP-660) instead
        """
        self.walk_pointer_to_proportional(x, y, MOUSE_STEP, 0)
