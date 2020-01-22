import math


def split_threads(n_threads, n_batches=1, more_in_center=False, divisible_by=1):
    """Split the number of threads into batches

    Take the total number of threads and split it into batches with the requested
    constraints. Applicable e.g. when splitting a warp into several colours or
    several plaits.

    :param n_threads: total number of threads
    :param n_batches: number of batches to split into
    :param more_in_center: if the number of threads cannot be split evenly into
                           batches, place more threads in the middle batches if set
                           to True. Otherwise place more threads in the first and
                           last batches.
    :param divisible_by: ensure batches are divisible by given number
    :return: list of number of threads from batch 0 to batch n_batches-1
    """
    # If x = 1234.5678, then math.modf(x) is (0.5678000000000338, 1234.0)
    floor = int(math.modf(n_threads / n_batches)[1])
    n_per_batch = [floor] * n_batches
    remainder = n_threads % n_batches
    rem_is_odd = remainder % 2 != 0
    n_colours_is_odd = n_batches % 2 != 0
    if rem_is_odd:
        even_remainder = remainder - 1
    else:
        even_remainder = remainder
    batch_range = range(0, int(even_remainder/2), 1)
    if more_in_center:
        batch_range = range(int(even_remainder/2), 0, -1)
    for i in batch_range:
        n_per_batch[i] += 1
        n_per_batch[-(i+1)] += 1
    if rem_is_odd:
        if n_colours_is_odd:
            n_per_batch[int((n_batches - 1) / 2)] += 1
        else:
            n_per_batch[even_remainder/2] += 1
    # Rearrange to ensure batches are evenly divisible by given number
    for i in range(int(n_batches/2)):
        mirrored_i = n_batches - 1
        while n_per_batch[i] % divisible_by != 0:
            n_per_batch[i] -= 1
            n_per_batch[i+1] += 1
        while n_per_batch[mirrored_i] % divisible_by != 0:
            n_per_batch[mirrored_i] -= 1
            n_per_batch[mirrored_i-1] += 1
    return n_per_batch
