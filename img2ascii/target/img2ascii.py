#!/usr/bin/env python3
"""
img2ascii - JPEG/PNG image to ASCII art converter.
Pure Python port from original C code.
"""

import sys
import ctypes
import getopt
from PIL import Image

GRAYSCALE_FLAG = 1 << 0
REVERSE_FLAG   = 1 << 1
PRINT_FLAG     = 1 << 2
DEBUG_FLAG     = 1 << 3


def show_usage():
    sys.stdout.write(
        "\nUsage: \x1b[1mimg2ascii [options] -i <FILE> [-o <FILE>]\x1b[0m \n\n"
        "A command-line tool for converting images to ASCII art \n\n"
        "Options: \n"
        "   -i, --input  <FILE>     Path of the input image file (required) \n"
        "   -o, --output <FILE>     Path of the output file \n"
        "   -w, --width  <NUMBER>   Width of the output \n"
        "   -c, --chars  <STRING>   Characters to be used for the ASCII image \n"
        "   -p, --print             Print the output to the console \n"
        "   -r, --reverse           Reverse the string of characters \n"
        "   -d, --debug             Print some useful information \n\n"
    )


def process_arguments(argv):
    if len(argv) == 1:
        sys.stdout.write("No input file\n")
        show_usage()
        sys.exit(1)

    input_filepath = None
    output_filepath = None
    characters = "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,\"^`'. "
    desired_width = 0
    flags = 0
    resize_image = False

    short_options = "hi:o:w:c:gprd"
    long_options = [
        "help", "input=", "output=", "width=", "chars=",
        "grayscale", "print", "reverse", "debug"
    ]

    try:
        opts, args_rem = getopt.getopt(argv[1:], short_options, long_options)
    except getopt.GetoptError:
        sys.stdout.write("\nHint: Use the \x1b[1m--help\x1b[0m option to get help about the usage \n\n")
        sys.exit(1)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            show_usage()
            sys.exit(1)
        elif opt in ("-i", "--input"):
            input_filepath = arg
        elif opt in ("-o", "--output"):
            output_filepath = arg
        elif opt in ("-w", "--width"):
            try:
                desired_width = int(arg)
            except ValueError:
                desired_width = 0
            resize_image = True
        elif opt in ("-c", "--chars"):
            if len(arg) != 0:
                characters = arg
        elif opt in ("-g", "--grayscale"):
            flags |= GRAYSCALE_FLAG
        elif opt in ("-p", "--print"):
            flags |= PRINT_FLAG
        elif opt in ("-r", "--reverse"):
            flags |= REVERSE_FLAG
        elif opt in ("-d", "--debug"):
            flags |= DEBUG_FLAG

    if input_filepath is None:
        sys.stdout.write("No input file\n")
        show_usage()
        sys.exit(1)

    if output_filepath is None:
        flags |= PRINT_FLAG

    return input_filepath, output_filepath, characters, desired_width, flags, resize_image


def load_image(input_filepath, desired_width, resize_image):
    try:
        img = Image.open(input_filepath).convert("RGB")
    except Exception:
        sys.stderr.write("Could not load image \n")
        sys.exit(1)

    width, height = img.size

    if resize_image:
        if desired_width <= 0:
            sys.stderr.write("Argument 'width' must be greater than 0 \n")
            sys.exit(1)
        elif desired_width > width:
            sys.stderr.write(f"Argument 'width' can not be greater than the original image width ({width}px) \n")
            sys.exit(1)

        desired_height = int(height / (width / float(desired_width)) / 2)
        img = img.resize((desired_width, desired_height), Image.Resampling.BILINEAR)
    else:
        desired_width = width
        desired_height = height // 2
        img = img.resize((desired_width, desired_height), Image.Resampling.BILINEAR)

    return img, desired_width, desired_height


def get_intensity(r, g, b):
    return int(0.299 * r + 0.587 * g + 0.114 * b + 0.5)


def get_output_grayscale(img, desired_width, desired_height, characters, flags):
    if flags & REVERSE_FLAG:
        characters = characters[::-1]

    characters_count = len(characters)
    denom = ctypes.c_float(255.0 / (characters_count - 1)).value

    pixels = list(img.getdata())
    output_chars = []

    for i, (r, g, b) in enumerate(pixels):
        intensity = get_intensity(r, g, b)
        char_index = int(intensity / denom)
        if char_index >= characters_count:
            char_index = characters_count - 1

        output_chars.append(characters[char_index])

        if (i + 1) % desired_width == 0:
            output_chars.append("\n")

    return "".join(output_chars)


def get_output_rgb(img, width, height, characters, flags):
    if flags & REVERSE_FLAG:
        characters = characters[::-1]

    characters_count = len(characters)
    denom = ctypes.c_float(255.0 / (characters_count - 1)).value

    pixels = list(img.getdata())
    output_parts = []

    r_prev = None
    g_prev = None
    b_prev = None

    for i, (r, g, b) in enumerate(pixels):
        intensity = get_intensity(r, g, b)
        char_index = int(intensity / denom)
        if char_index >= characters_count:
            char_index = characters_count - 1

        if not (r == r_prev and g == g_prev and b == b_prev):
            output_parts.append(f"\x1b[38;2;{r};{g};{b}m")

        r_prev = r
        g_prev = g
        b_prev = b

        output_parts.append(characters[char_index])

        if (i + 1) % width == 0:
            output_parts.append("\n")

    output_parts.append("\x1b[0m")
    return "".join(output_parts)


def write_output(img, input_filepath, output_filepath, characters, width, height, flags):
    if flags & GRAYSCALE_FLAG:
        output = get_output_grayscale(img, width, height, characters, flags)
    else:
        output = get_output_rgb(img, width, height, characters, flags)

    if flags & DEBUG_FLAG:
        out_str = output_filepath if output_filepath is not None else "stdout"
        sys.stdout.write(
            f"Input: {input_filepath} \n"
            f"Output: {out_str} \n"
            f"Resolution: {width}x{height} \n"
            f"Characters ({len(characters)}): \"{characters}\" \n"
        )

    if flags & PRINT_FLAG:
        sys.stdout.write(output)

    if output_filepath is not None:
        try:
            with open(output_filepath, "w", encoding="utf-8") as f:
                f.write(output)
        except Exception as e:
            sys.stderr.write(f"Could not create an output file: {e} \n")
            sys.exit(1)


def main():
    input_filepath, output_filepath, characters, desired_width, flags, resize_image = process_arguments(sys.argv)
    img, width, height = load_image(input_filepath, desired_width, resize_image)
    write_output(img, input_filepath, output_filepath, characters, width, height, flags)


if __name__ == "__main__":
    main()
