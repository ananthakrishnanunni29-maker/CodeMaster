def faces(options):
    modes = {
        "b": {"eyes": "==", "tongue": "  "},
        "d": {"eyes": "xx", "tongue": "U "},
        "g": {"eyes": "$$", "tongue": "  "},
        "p": {"eyes": "@@", "tongue": "  "},
        "s": {"eyes": "**", "tongue": "U "},
        "t": {"eyes": "--", "tongue": "  "},
        "w": {"eyes": "OO", "tongue": "  "},
        "y": {"eyes": "..", "tongue": "  "}
    }

    for mode_key in modes:
        if options.get(mode_key) is True:
            return modes[mode_key]

    return {
        "eyes": options.get("e") or "oo",
        "tongue": options.get("T") or "  "
    }
