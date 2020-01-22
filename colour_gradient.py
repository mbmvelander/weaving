import numpy.random
from util import calc


n_threads = 1532
n_colours = 5
sigma = 120.0
max_jump = 50
max_tries = 1000
pattern_size = 108.0
max_per_line = 30.0
PREFER_EDGES = False
COLOURS = [
    (65, 60, 90),
    (180, 140, 175),
    (225, 190, 200),
    (250, 250, 225),
    (250, 245, 155)
]


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


def place_one_thread(colour, n_threads_per_colour, colour_count_in,
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


def place_threads(n_threads_per_colour, colour_centers, prefer_edges=False):
    placement = [None] * n_threads
    colour_count = [0] * n_colours
    n_tries = 0
    edge_offset = 0
    if prefer_edges:
        for i in range(0, int(n_colours/2.0)):
            while colour_count[i] < n_threads_per_colour[i] or colour_count[-1-i] < n_threads_per_colour[-1-i]:
                for colour in [i, n_colours - 1 - i]:
                    placement, colour_count, n_tries = place_one_thread(colour,
                                                                        n_threads_per_colour,
                                                                        colour_count,
                                                                        colour_centers,
                                                                        placement,
                                                                        n_tries)
        edge_offset = 1
    while sum(x is None for x in placement) > 0:
        for colour in range(0+edge_offset, len(n_threads_per_colour)-edge_offset, 1):
            placement, colour_count, n_tries = place_one_thread(colour,
                                                                n_threads_per_colour,
                                                                colour_count,
                                                                colour_centers,
                                                                placement,
                                                                n_tries)
    return placement


def main():
    n_threads_per_colour = calc.split_threads(n_threads, n_colours)
    colour_centers = get_colour_centers(n_threads_per_colour)
    placement = place_threads(n_threads_per_colour, colour_centers, PREFER_EDGES)
    print(",".join(str(x) for x in placement))


if __name__ == "__main__":
    main()
