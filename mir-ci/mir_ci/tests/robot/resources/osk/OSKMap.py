from typing import Literal, Mapping

from robot.api.deco import keyword, library

LETTER_ROWS = {
    "qwertyuiop": (0, 1 / 8, 0),
    "asdfghjkl": (0.05, 3 / 8, 0.05),
    "zxcvbnm": (0.15, 5 / 8, 0.15),
}

# ROWS and KEYS values below are proportional to the size of the OSK region
# This is {layout: {characters: (left_margin, y_offset, right_margin)}}
ROWS: Mapping[str, Mapping[str, tuple[float, float, float]]] = {
    "default": {
        **LETTER_ROWS,
        **{k.upper(): v for k, v in LETTER_ROWS.items()},
        "1234567890": (0, 1 / 8, 0),
        "@#$%&-_+()": (0, 3 / 8, 0),
        ",\"':;!?": (0.15, 5 / 8, 0.15),
    },
    "emoji": {
        "😀😁😅😂😊😇🙃": (0, 1 / 8, 0),
        "😍😘😋😜😎🥳😔": (0, 3 / 8, 0),
        "😢😭😡😱🤔😬🙄": (0, 5 / 8, 0),
    },
}

# This is {layout: {character: (x_offset, y_offset)}}
KEYS: Mapping[str, Mapping[str, tuple[float, float]]] = {
    "default": {
        "shift": (0.075, 5 / 8),
        "backspace": (0.925, 5 / 8),
        "123": (0.1, 7 / 8),
        "ABC": (0.1, 7 / 8),
        "layouts": (0.25, 7 / 8),
        "space": (0.5, 7 / 8),
        "dot": (0.75, 7 / 8),
        "enter": (0.9, 7 / 8),
    },
    "emoji": {
        "layouts": (0.05, 7 / 8),
        "backspace": (0.95, 7 / 8),
    },
}


@library(scope="GLOBAL")
class OSKMap:
    @keyword
    def get_point_for_key(
        self, layout: str, region: Mapping[Literal["left", "top", "right", "bottom"], int], key
    ) -> tuple[int, int]:
        try:
            osk_width = region["right"] - region["left"]
            osk_height = region["bottom"] - region["top"]
            for row, offsets in ROWS[layout].items():
                if key in tuple(row):
                    x_offset = region["left"] + offsets[0] * osk_width
                    key_width = (osk_width - (osk_width * (offsets[0] + offsets[2]))) / len(row)
                    return (
                        round(x_offset + row.index(key) * key_width + key_width / 2),
                        round(region["top"] + offsets[1] * osk_height),
                    )

            return (
                round(region["left"] + KEYS[layout][key][0] * osk_width),
                round(region["top"] + KEYS[layout][key][1] * osk_height),
            )
        except KeyError:
            raise KeyError(f"Failed to find {key} in layout '{layout}'")
