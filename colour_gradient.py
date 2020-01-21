#!/bin/python

import math
import numpy.random


n_threads = 1532
n_colours = 5
sigma = 120.0
max_jump = 50
max_tries = 1000
pattern_size = 108.0
max_per_line = 30.0
prefer_edges = False
COLOURS = [
    (65, 60, 90),
    (180, 140, 175),
    (225, 190, 200),
    (250, 250, 225),
    (250, 245, 155)
]


def get_n_threads_per_colour(n_threads, n_colours):
    # If x = 1234.5678, then math.modf(x) is (0.5678000000000338, 1234.0)
    floor = int(math.modf(n_threads/n_colours)[1])
    n_threads_per_colour = [floor] * n_colours
    remainder = n_threads % n_colours
    rem_is_odd = remainder % 2 != 0
    n_colours_is_odd = n_colours % 2 != 0
    if rem_is_odd:
        even_remainder = remainder - 1
    else:
        even_remainder = remainder
    for i in range(0, even_remainder/2, 1):
        n_threads_per_colour[i] += 1
        n_threads_per_colour[-(i+1)] += 1
    if rem_is_odd:
        if n_colours_is_odd:
            n_threads_per_colour[int((n_colours-1)/2)] += 1
        else:
            n_threads_per_colour[even_remainder/2] += 1
    return n_threads_per_colour


def get_colour_centers(n_threads_per_colour):
    colour_centers = [0]
    moving_point = n_threads_per_colour[0]
    for colour_n_threads in n_threads_per_colour[1:-1]:
        colour_centers.append(moving_point + int(colour_n_threads/2.0))
        moving_point += colour_n_threads
    colour_centers.append(n_threads)
    return colour_centers


def find_closest_point(suggestion, max_jump, placement):
    # Check backwards and forwards
    closest_left = None
    closest_right = None
    for i in range(suggestion, max(0, suggestion - max_jump), -1):
        if placement[i] is None:
            closest_left = i
            break
    for i in range(suggestion, min(len(placement),
                                   suggestion + max_jump), 1):
        if placement[i] is None:
            closest_right = i
            break
    if closest_left is None and closest_right is None:
        # If we have used up the threads for the colour closest
        # to the empty spot(s), then it'll be unlikely we fill
        # them. Just use up the remaining threads if it comes
        # to that, using colour order to place "original" colour
        return None
    elif closest_left is None:
        return closest_right
    elif closest_right is None:
        return closest_left
    elif abs(closest_left - suggestion) <= abs(closest_right
                                               - suggestion):
        return closest_left
    else:
        return closest_right


def fill_remaining(placement_in, colour_count, n_threads_per_colour):
    # If we have used up the threads for the colour closest
    # to the empty spot(s), then it'll be unlikely we fill
    # them. Just use up the remaining threads if it comes
    # to that, using colour order to place "original" colour
    placement = placement_in
    while sum(x is None for x in placement) > 0:
        for c in range(len(colour_count)):
            colour_char = chr(65 + c)
            while colour_count[c] < n_threads_per_colour[c]:
                for p in range(len(placement)):
                    if placement[p] is None:
                        placement[p] = colour_char
                        colour_count[c] += 1
                        break
    return placement


def place_a_thread(colour, n_threads_per_colour, colour_count_in,
                   colour_centers, placement_in, n_tries_in):
    colour_count = colour_count_in
    placement = placement_in
    n_tries = n_tries_in
    colour_char = chr(65 + colour)
    if colour_count[colour] == n_threads_per_colour[colour]:
        return placement, colour_count, n_tries
    mu = colour_centers[colour]
    suggestion = -1
    while suggestion < 0 or suggestion >= n_threads:
        suggestion = int(numpy.random.normal(mu, sigma, 1))
    if placement[suggestion] is None:
        placement[suggestion] = colour_char
    else:
        closest_point = find_closest_point(suggestion, max_jump,
                                           placement)
        if closest_point is None:
            # If we have used up the threads for the colour closest
            # to the empty spot(s), then it'll be unlikely we fill
            # them. Just use up the remaining threads if it comes
            # to that, using colour order to place "original" colour
            n_tries += 1
            if n_tries > max_tries:
                placement = fill_remaining(placement, colour_count,
                                           n_threads_per_colour)
            return placement, colour_count, n_tries
        placement[closest_point] = colour_char
    n_tries = 0
    colour_count[colour] += 1
    return placement, colour_count, n_tries


def place_threads_no_preference(n_threads_per_colour, colour_centers):
    placement = [None] * n_threads
    colour_count = [0] * n_colours
    n_tries = 0
    while sum(x is None for x in placement) > 0:
        for colour in range(0, len(n_threads_per_colour), 1):
            placement, colour_count, n_tries = place_a_thread(colour,
                                                              n_threads_per_colour,
                                                              colour_count,
                                                              colour_centers,
                                                              placement,
                                                              n_tries)
    return placement


def place_threads_prefer_edges(n_threads_per_colour, colour_centers):
    placement = [None] * n_threads
    colour_count = [0] * n_colours
    n_tries = 0
    for i in range(0, int(n_colours/2.0)):
        while colour_count[i] < n_threads_per_colour[i] or colour_count[-1-i] < n_threads_per_colour[-1-i]:
            for colour in [i, n_colours - 1 - i]:
                placement, colour_count, n_tries = place_a_thread(colour,
                                                                  n_threads_per_colour,
                                                                  colour_count,
                                                                  colour_centers,
                                                                  placement,
                                                                  n_tries)
    while sum(x is None for x in placement) > 0:
        for colour in range(1, len(n_threads_per_colour)-1, 1):
            placement, colour_count, n_tries = place_a_thread(colour,
                                                              n_threads_per_colour,
                                                              colour_count,
                                                              colour_centers,
                                                              placement,
                                                              n_tries)
    return placement


def print_string_separator():
    return "-" * 25


def print_string_tens(placement_in):
    placement = placement_in[:]
    print_string = ""
    count = 0
    while len(placement) > 0:
        print_string += str(placement.pop(0)) + "   "
        count += 1
        if count % 30 == 0:
            print_string += "\n"
            continue
        if count % 10 == 0:
            print_string += "|   "
    return print_string


def print_string_pattern(placement_in):
    placement = placement_in[:]
    n_lines = int(pattern_size/max_per_line + 0.5)
    n_per_line = int(max_per_line)
    print_string = ""
    count = 0
    while len(placement) > 0:
        pattern_count = 0
        for i in range(n_lines):
            for j in range(n_per_line):
                print_string += str(placement.pop(0)) + "   "
                count += 1
                pattern_count += 1
                if count % 10 == 0:
                    print_string += "|   "
                if pattern_count == pattern_size:
                    print_string += "\n"
                    break
            if len(placement) == 0:
                break
            print_string += "\n"
    return print_string


def latex_header():
    return '\n'.join([r'\documentclass[landscape,a4paper,ms,12pt]{memoir}',
                      r'\usepackage[margin=1cm]{geometry}',
                      r'\renewcommand{\baselinestretch}{2.5}',
                      r'\usepackage{xcolor}',
                      r'\usepackage[T1]{fontenc}',
                      r'\def\rangeRGB{255}',
                      r'\renewcommand{\seriesdefault}{\bfdefault}',
                      r'\setlength\parindent{0pt}',
                      r'\pagenumbering{gobble}',
                      r'\begin{document}',
                      r'\begin{Large}',
                      ])


def latex_footer():
    return '\n'.join([
        r'\end{Large}',
        r'\end{document}',
    ])


def latex_print_string(placement_in):
    placement = placement_in
    strings = []
    count = 0
    while len(placement) > 0:
        t = placement.pop(0)
        colour = COLOURS[ord(t)-65]
        strings.append(r'\colorbox[RGB]{' + ','.join(str(x) for x in colour) + r'}{' + str(t) + r'}')
        count += 1
        if count % 30 == 0:
            strings.append(r'\newline')
            continue
        if count % 10 == 0:
            strings.append(r'|')
    main_string = "\n".join(strings)
    return '\n'.join([latex_header(),
                      main_string,
                      latex_footer()])


def main():
    n_threads_per_colour = get_n_threads_per_colour(n_threads, n_colours)
    colour_centers = get_colour_centers(n_threads_per_colour)

    if prefer_edges:
        placement = place_threads_prefer_edges(n_threads_per_colour,
                                               colour_centers)
    else:
        placement = place_threads_no_preference(n_threads_per_colour,
                                                colour_centers)

    print(",".join(str(x) for x in placement))
    # print(print_string_separator())
    # print(print_string_tens(placement))
    # print(print_string_separator())
    # print(print_string_pattern(placement))
    # print(latex_print_string(placement))


if __name__ == "__main__":
    main()
