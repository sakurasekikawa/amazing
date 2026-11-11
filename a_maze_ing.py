"""
parse
↓
dict
"""


def parse_coord(value: str) -> tuple[int, int]:
    return tuple(map(int, value.split(",")))


PARSERS = {
    "WIDTH": int,
    "HEIGHT": int,
    "EXIT": parse_coord,
    "PLAYER": parse_coord,
}


def read_config(config.txt: str) -> dict:
    config = {}

    with open(filename, "r", encoding="utf-8") as file:
        for line in file:
            key, value = line.strip().split("=", 1)

            if key in PARSERS:
                config[key] = PARSERS[key](value)

    return config
