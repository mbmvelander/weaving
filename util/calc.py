

def split_threads(n_threads, n_batches=1, peak_at_center=False, divisible_by=1):
    """Split the number of threads into batches

    Take the total number of threads and split it into batches with the requested
    constraints. Applicable e.g. when splitting a warp into several colours or
    several plaits.

    Example problem:
      I want to create a warp of 379 threads but that warp is too wide to do all at
      once so I want to split it into five batches. These batches should be split
      according to the following needs:
        - as equal in size as possible
        - if not equal in size, make the central batches wider than the outer ones
        - divisible by two in as many of the batches as possible, with any extra threads
          placed all in one batch

      Call:
        batches = split_threads(379, n_batches=5, peak_at_center=True, divisible_by=2)

      Expected outcome:
        batches = [76, 76, 77, 76, 74]

    :param n_threads: total number of threads
    :param n_batches: number of batches to split into
    :param peak_at_center: if the number of threads cannot be split evenly into
                           batches, place more threads in the middle batch(es) if set
                           to True. Otherwise place more threads in the first and
                           last batch(es).
    :param divisible_by: ensure batches are divisible by given number, with a maximum
                         of one batch breaking this constraint
    :return: list of number of threads from batch 0 to batch n_batches-1
    """
    # Find the largest number divisible by both n_batches and divisible_by
    number_to_split = largest_divisible_by_all(n_threads, [divisible_by, n_batches])

    # Evenly distribute this number across batches
    n_per_batch = [int(number_to_split/n_batches)] * n_batches

    # Figure out how many threads are left over after the initial split, and how best
    # to split those remaining threads
    remainder = n_threads - number_to_split
    final_remainder = remainder % divisible_by
    evenly_distributable_remainder = remainder - final_remainder
    n_remainder_batches = int(evenly_distributable_remainder / divisible_by)

    # To best distribute the remaining threads, we need to know if the user prefers
    # them to be distributed with a peak at the middle, or rather on the edges,
    # e.g. [1, 2, 2, 1] vs [2, 1, 1, 2]
    # If central peak is preferred, placement is done like this (N is divisible_by):
    #   [0, 0, 0, 0, 0]
    #   [0, N, N, N, 0] ==> done
    # Conversely, if we prefer edges then we place in this order:
    #   [0, 0, 0, 0, 0]
    #   [N, 0, 0, 0, 0]
    #   [N, 0, 0, N, N] ==> done
    # If there are any threads remaining now, we add it to the middle batch (or
    # one of the two middle batches if n_batches is odd) if wanting central peak,
    # or the the last batch if larger edges are preferred.
    n_add_none = n_batches - n_remainder_batches
    if peak_at_center:
        for i in range(int(n_add_none/2), int(n_add_none/2) + n_remainder_batches, 1):
            n_per_batch[i] += divisible_by
        if final_remainder > 0:
            n_per_batch[int(n_batches/2)] += final_remainder
    else:
        for i in range(0, int(n_remainder_batches/2), 1):
            n_per_batch[i] += divisible_by
        for i in range(int(n_remainder_batches/2)+n_add_none, n_batches, 1):
            n_per_batch[i] += divisible_by
        if final_remainder > 0:
            n_per_batch[-1] += final_remainder
    return n_per_batch


def largest_divisible_by_all(number, divisible_by):
    """Figure out the largest integer N<=number which is divisible by all given integers

    :param number: the number returned has to be smaller than or equal to this
    :param divisible_by: list of integers to check for
    :return: the largest integer evenly divisible by all in divisible_by list
    """
    # Sort elements largest first; there is no point in checking smaller numbers if the
    # test number is not divisible by the largest number in the list, and logic is
    # extended to check numbers largest to smallest
    if isinstance(divisible_by, list):
        divisible_by_cp = divisible_by.copy()
    else:
        divisible_by_cp = [divisible_by]
    divisible_by_cp.sort(reverse=True)
    largest_in_list = divisible_by_cp[0]
    number_to_test = number - (number % largest_in_list)
    while True:
        # Step down by the largest number in the divisible_by list
        number_to_test -= largest_in_list
        div_by_all = True
        for test_num in divisible_by_cp[1:]:
            div_by_all = div_by_all and (number_to_test % test_num == 0)
            if not div_by_all:
                break
        if div_by_all:
            return number_to_test
