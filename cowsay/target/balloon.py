from wcwidth import wcswidth


def say(text, wrap):
    delimiters = {
        "first": ["/", "\\"],
        "middle": ["|", "|"],
        "last": ["\\", "/"],
        "only": ["<", ">"]
    }

    return _format(text, wrap, delimiters)


def think(text, wrap):
    delimiters = {
        "first": ["(", ")"],
        "middle": ["(", ")"],
        "last": ["(", ")"],
        "only": ["(", ")"]
    }

    return _format(text, wrap, delimiters)


def _string_width(text):
    return wcswidth(text) or len(text)


def _format(text, wrap, delimiters):
    lines = _split(text, wrap)
    max_length = _max_length(lines)

    if len(lines) == 1:
        balloon = [
            " " + _top(max_length),
            delimiters["only"][0] + " " + lines[0] + " " + delimiters["only"][1],
            " " + _bottom(max_length)
        ]
    else:
        balloon = [" " + _top(max_length)]

        for i, line in enumerate(lines):
            if i == 0:
                delimiter = delimiters["first"]
            elif i == len(lines) - 1:
                delimiter = delimiters["last"]
            else:
                delimiter = delimiters["middle"]

            balloon.append(delimiter[0] + " " + _pad(line, max_length) + " " + delimiter[1])

        balloon.append(" " + _bottom(max_length))

    return "\n".join(balloon)


def _split(text, wrap):
    import re
    text = re.sub(r'\r\n?|[\n\u2028\u2029]', '\n', text)
    text = re.sub(r'^\uFEFF', '', text)
    text = text.replace('\t', '        ')

    lines = []
    if not wrap:
        lines = text.split("\n")
    else:
        start = 0
        while start < len(text):
            next_new_line = text.find("\n", start)

            if next_new_line == -1:
                wrap_at = min(start + wrap, len(text))
            else:
                wrap_at = min(start + wrap, next_new_line)

            lines.append(text[start:wrap_at])
            start = wrap_at

            if start < len(text) and text[start] == "\n":
                start += 1

    return lines


def _max_length(lines):
    max_len = 0
    for line in lines:
        w = _string_width(line)
        if w > max_len:
            max_len = w
    return max_len


def _pad(text, length):
    return text + " " * (length - _string_width(text))


def _top(length):
    return "_" * (length + 2)


def _bottom(length):
    return "-" * (length + 2)
