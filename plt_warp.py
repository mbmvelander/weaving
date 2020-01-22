import sys
from util import calc
from util.plotting import draw_plot
from util.printing import latex_print_string

N_BRAIDS = 4
N_PER_LANG_PAIR = 5


def read_threads():
    data = sys.stdin.readlines()
    threads = []
    for thread in data[0].split(","):
        threads.append(thread.strip())
    return threads


def get_braids(threads_in, n_braids):
    threads = threads_in
    n_threads = len(threads)
    n_threads_per_braid = calc.split_threads(n_threads, n_braids, more_in_center=True, divisible_by=N_PER_LANG_PAIR)
    braids = []
    for n_threads_in_braid in n_threads_per_braid:
        braid = []
        for j in range(n_threads_in_braid):
            braid.append(threads.pop(0))
        braids.append(list(braid))
    return braids


def main():
    threads = read_threads()
    if len(threads) % N_PER_LANG_PAIR != 0:
        print('Warning: the total number of threads is not evenly divisible into lang pairs (%i/%i).\n\r         One braid will have an incomplete lang pair.' % (len(threads), N_PER_LANG_PAIR))
    draw_plot(threads)
    braids = get_braids(threads, N_BRAIDS)
    for i in range(N_BRAIDS):
        print("Braid " + str(i+1) + ": " + str(len(braids[i])))
        with open('braid' + str(i+1) + '.tex', 'w') as f:
            f.write(latex_print_string(braids[i]))


if __name__ == "__main__":
    main()
