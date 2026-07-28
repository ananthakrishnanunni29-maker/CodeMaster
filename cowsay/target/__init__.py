import random

from cowsay.balloon import say as _balloon_say, think as _balloon_think
from cowsay import cows as _cows
from cowsay.faces import faces as _faces


def say(options):
    return _do_it(options, True)


def think(options):
    return _do_it(options, False)


list = _cows.list


def _do_it(options, say_aloud):
    if options.get("r"):
        cows_list = _cows.list_sync()
        cow_file = cows_list[random.randint(0, len(cows_list) - 1)]
    else:
        cow_file = options.get("f") or "default"

    cow = _cows.get(cow_file)
    face = _faces(options)
    face["thoughts"] = "\\" if say_aloud else "o"

    text = options.get("text") or " ".join(options.get("_", []))
    wrap = None if options.get("n") else options.get("W")

    if say_aloud:
        balloon_text = _balloon_say(text, wrap)
    else:
        balloon_text = _balloon_think(text, wrap)

    return balloon_text + "\n" + cow(face)
