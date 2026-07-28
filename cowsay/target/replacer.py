import re


def replacer(cow, variables):
    eyes = variables.get("eyes", "")
    eye_l = eyes[0] if eyes else ""
    eye_r = eyes[1] if len(eyes) > 1 else ""
    tongue = variables.get("tongue", "")

    if "$the_cow" in cow:
        cow = _extract_the_cow(cow)

    cow = cow.replace("$thoughts", variables.get("thoughts", ""))
    cow = cow.replace("$eyes", eyes)
    cow = cow.replace("$tongue", tongue)
    cow = cow.replace("${eyes}", eyes)
    cow = cow.replace("$eye", eye_l, 1)
    cow = cow.replace("$eye", eye_r, 1)
    cow = cow.replace("${tongue}", tongue)

    return cow


def _extract_the_cow(cow):
    cow = re.sub(r'\r\n?|[\n\u2028\u2029]', '\n', cow)
    cow = re.sub(r'^\uFEFF', '', cow)
    match = re.search(r'\$the_cow\s*=\s*<<"*EOC"*;*\n([\s\S]+)\nEOC\n', cow)

    if not match:
        import sys
        print("Cannot parse cow file\n", cow, file=sys.stderr)
        return cow
    else:
        result = match.group(1)
        result = result.replace("\\\\", "\\")
        result = result.replace("\\@", "@")
        result = result.replace("\\$", "$")
        return result
