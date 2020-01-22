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
        colour = COLOURS[ord(t) - 65]
        # PIL (to memory for saving to file)
        draw.line((x, y0, x, y1), colour)
        x += 1

    # PIL image can be saved as .png .jpg .gif or .bmp file
    filename = "warp.jpg"
    image.save(filename)
