"""Read firmware's VT100 console; selection colors are more reliable than OCR."""

import re


def console_nodes(data):
    rows, columns = 80, 240
    cells = [[(" ", 44) for _ in range(columns)] for _ in range(rows)]
    row = column = 0
    background = 44
    tokens = re.split(r"(\x1b\[[0-9;?=]*[A-Za-z])", data)
    for token in tokens:
        if token.startswith("\x1b["):
            code, parameters = token[-1], token[2:-1]
            if parameters.startswith(("?", "=")):
                continue
            values = [int(x) if x else 0 for x in parameters.split(";")]
            if code in ("H", "f"):
                row = max(0, min(rows - 1, (values[0] or 1) - 1))
                column = max(0, min(columns - 1, (values[1] if len(values) > 1 else 1) - 1))
            elif code == "J" and values[0] in (2, 3):
                cells = [[(" ", background) for _ in range(columns)] for _ in range(rows)]
            elif code == "m":
                for value in values:
                    if value == 0:
                        background = 44
                    elif 40 <= value <= 47:
                        background = value
            elif code == "t" and len(values) == 3 and values[0] == 8:
                rows, columns = max(1, min(values[1], 200)), max(1, min(values[2], 400))
                cells = [[(" ", background) for _ in range(columns)] for _ in range(rows)]
                row = column = 0
            continue
        for character in token:
            if character == "\r":
                column = 0
            elif character == "\n":
                row = min(rows - 1, row + 1)
            elif character >= " " and character != "\x7f":
                cells[row][column] = (character, background)
                column = min(columns - 1, column + 1)
    result = []
    for index, line in enumerate(cells):
        # Shim puts each menu item on a separate line, inside box-drawing borders.
        text = "".join(character if not "\u2500" <= character <= "\u257f" and character != "|" else " "
                       for character, _ in line).strip()
        if text.strip("+-/\\ "):
            start = next(i for i, (character, _) in enumerate(line) if character.strip()
                         and character != "|" and not "\u2500" <= character <= "\u257f")
            selected = any(color == 40 and character.strip() and character != "|"
                           and not "\u2500" <= character <= "\u257f"
                           for character, color in line)
            result.append({"name": text, "rect": [start, index, len(text), 1],
                           "serial": True, "dark_background": selected})
    return result
