import os
from cowsay.replacer import replacer as _replacer

_text_cache = {}
_cows_path = os.path.join(os.path.dirname(__file__), "cows")


def _cow_names_from_files(files):
    result = []
    for cow in files:
        name, _ = os.path.splitext(os.path.basename(cow))
        result.append(name)
    return result


def get(cow):
    text = _text_cache.get(cow)

    if text is None:
        if "\\" in cow or "/" in cow:
            file_path = cow
        else:
            file_path = os.path.join(_cows_path, cow) + ".cow"

        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        _text_cache[cow] = text

    def render(options):
        return _replacer(text, options)

    return render


def list(callback=None):
    try:
        files = os.listdir(_cows_path)
        names = _cow_names_from_files(files)
        if callback:
            try:
                callback(None, names)
            except Exception:
                pass
        return names
    except Exception as e:
        if callback:
            try:
                callback(e, None)
            except Exception:
                pass
        raise


def list_sync():
    files = os.listdir(_cows_path)
    return _cow_names_from_files(files)
