import argparse
import os
import sys

import cowsay


def main():
    parser = argparse.ArgumentParser(
        prog=os.path.basename(sys.argv[0]),
        usage="""%(prog)s [-e eye_string] [-f cowfile] [-h] [-l] [-n] [-T tongue_string] [-W column] [-bdgpstwy] text

If any command-line arguments are left over after all switches have been processed, they become the cow's message.

If the program is invoked as cowthink then the cow will think its message instead of saying it.
""",
        add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("-e", default="oo", help="Select the appearance of the cow's eyes.")
    parser.add_argument("-T", default="  ", help="The tongue is configurable similarly to the eyes through -T and tongue_string.")
    parser.add_argument("-W", default=40, type=int, help="Specifies roughly where the message should be wrapped. The default is equivalent to -W 40 i.e. wrap words at or before the 40th column.")
    parser.add_argument("-f", default="default", help="Specifies a cow picture file (''cowfile'') to use. It can be either a path to a cow file or the name of one of cows included in the package.")
    parser.add_argument("--think", action="store_true", help="Think the message instead of saying it aloud.")

    parser.add_argument("-b", action="store_true", help="Mode: Borg")
    parser.add_argument("-d", action="store_true", help="Mode: Dead")
    parser.add_argument("-g", action="store_true", help="Mode: Greedy")
    parser.add_argument("-p", action="store_true", help="Mode: Paranoia")
    parser.add_argument("-s", action="store_true", help="Mode: Stoned")
    parser.add_argument("-t", action="store_true", help="Mode: Tired")
    parser.add_argument("-w", action="store_true", help="Mode: Wired")
    parser.add_argument("-y", action="store_true", help="Mode: Youthful")

    parser.add_argument("-n", action="store_true", help="If it is specified, the given message will not be word-wrapped.")
    parser.add_argument("-h", "--help", action="store_true", help="Display this help message")
    parser.add_argument("-r", action="store_true", help="Select a random cow")
    parser.add_argument("-l", action="store_true", help="List all cowfiles included in this package.")

    parser.add_argument("text", nargs="*", help="Message for the cow to say")

    args = parser.parse_args()

    if args.help:
        parser.print_help()
        return

    if args.l:
        _list_cows()
        return

    if args.text:
        argv = _build_argv(args)
        _say(argv)
        return

    data = sys.stdin.read()
    if data:
        data = _strip_final_newline(data)
        argv = _build_argv(args)
        argv["text"] = data
        argv["_"] = [data]
        _say(argv)
        return

    parser.print_help()


def _build_argv(args):
    argv = {
        "e": args.e,
        "T": args.T,
        "W": args.W,
        "f": args.f,
        "b": args.b,
        "d": args.d,
        "g": args.g,
        "p": args.p,
        "s": args.s,
        "t": args.t,
        "w": args.w,
        "y": args.y,
        "n": args.n,
        "r": args.r,
        "l": args.l,
        "think": args.think,
        "_": args.text,
    }
    return argv


def _strip_final_newline(s):
    if s.endswith("\n"):
        return s[:-1]
    return s


def _say(argv):
    think_mode = argv.get("think") or os.path.basename(sys.argv[0]).endswith("think")
    argv["$0"] = sys.argv[0]

    if think_mode:
        output = cowsay.think(argv)
    else:
        output = cowsay.say(argv)

    print(output)


def _list_cows():
    def callback(err, cow_list):
        if err:
            raise Exception(err)
        print("  ".join(cow_list))

    cowsay.list(callback)


if __name__ == "__main__":
    main()
