import sys
import math
from PIL import Image, ImageDraw


white = (255, 255, 255)
black = (0, 0, 0)

COLOURS = [
    (65, 60, 90),
    (180, 140, 175),
    (225, 190, 200),
    (250, 250, 225),
    (250, 245, 155)
]

N_PLAITS = 4
N_PER_LANG_PAIR = 2


def read_threads():
    data = sys.stdin.readlines()
    threads = []
    for thread in data[0].split(","):
        threads.append(thread.strip())
    return threads


def draw_plot(threads_in):
    threads = threads_in
    width = len(threads)
    height = int(width/5)
    image = Image.new("RGB", (width, height), black)
    draw = ImageDraw.Draw(image)

    y0 = 0
    y1 = height
    x = 0
    for t in threads:
        colour = COLOURS[ord(t)-65]
        # PIL (to memory for saving to file)
        draw.line((x, y0, x, y1), colour)
        x += 1

    # PIL image can be saved as .png .jpg .gif or .bmp file
    filename = "warp.jpg"
    image.save(filename)


def latex_header():
    return '\n'.join([r'\documentclass[landscape,a4paper,ms,12pt]{memoir}',
                      r'\usepackage[margin=1cm]{geometry}',
                      r'\renewcommand{\baselinestretch}{2.5}',
                      r'\usepackage{xcolor}',
                      r'\usepackage[T1]{fontenc}',
                      r'\def\rangeRGB{255}',
                      r'\DeclareFontShape{OT1}{cmtt}{bx}{n}{<5><6><7><8><9><10><10.95><12><14.4><17.28><20.74><24.88>cmttb10}{}',
                      r'\renewcommand{\seriesdefault}{bx}',
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


def latex_print_string(threads_in):
    threads = threads_in
    strings = []
    count = 0
    while len(threads) > 0:
        t = threads.pop(0)
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


def get_plaits(threads_in, n_plaits):
    threads = threads_in
    n_threads = len(threads)
    n_threads_per_plait = get_n_threads_per_plait(n_threads, n_plaits)
    plaits = []
    for n_threads_in_plait in n_threads_per_plait:
        plait = []
        for j in xrange(n_threads_in_plait):
            plait.append(threads.pop(0))
        plaits.append(list(plait))
    return plaits


# If cannot split evenly, the plaits on the edges will be slightly narrower
# than the central one(s)
def get_n_threads_per_plait(n_threads, n_plaits):
    # If x = 1234.5678, then math.modf(x) is (0.5678000000000338, 1234.0)
    floor = int(math.modf(n_threads/n_plaits)[1])
    n_threads_per_plait = [floor] * n_plaits
    remainder = n_threads % n_plaits
    rem_is_odd = remainder % 2 != 0
    n_plaits_is_odd = n_plaits % 2 != 0
    if rem_is_odd:
        even_remainder = remainder - 1
    else:
        even_remainder = remainder
    for i in range(even_remainder/2, 0, -1):
        n_threads_per_plait[i] += 1
        n_threads_per_plait[-(i+1)] += 1
    if rem_is_odd:
        if n_plaits_is_odd:
            n_threads_per_plait[int((n_plaits-1)/2)] += 1
        else:
            n_threads_per_plait[even_remainder/2] += 1
    # Rearrange to fit the number of threads in a lang pair
    for i in xrange(n_plaits/2):
        mirrored_i = n_plaits - 1
        while n_threads_per_plait[i] % N_PER_LANG_PAIR != 0:
            n_threads_per_plait[i] -= 1
            n_threads_per_plait[i+1] += 1
        while n_threads_per_plait[mirrored_i] % N_PER_LANG_PAIR != 0:
            n_threads_per_plait[mirrored_i] -= 1
            n_threads_per_plait[mirrored_i-1] += 1
    return n_threads_per_plait


def main():
    threads = read_threads()
    draw_plot(threads)
    plaits = get_plaits(threads, N_PLAITS)
    for i in xrange(N_PLAITS):
        print("Plait " + str(i+1) + ": " + str(len(plaits[i])))
        with open('plait' + str(i+1) + '.tex', 'w') as f:
            f.write(latex_print_string(plaits[i]))


if __name__ == "__main__":
    main()
