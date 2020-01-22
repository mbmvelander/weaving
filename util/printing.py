from util.plotting import COLOURS


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