#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sys import argv
try:
    from PIL import Image
except:
    from sys import stderr
    stderr.write('[E] PIL not installed')
    exit(1)

from io import BytesIO
import requests
import re
from drawille import Canvas, get_terminal_size


def usage():
    print('Usage: %s <url/id>')
    exit()

if __name__ == '__main__':
    if len(argv) < 2:
        url = 'http://xkcd.com/'
    elif argv[1] in ['-h', '--help']:
        usage()
    elif argv[1].startswith('http'):
        url = argv[1]
    else:
        url = 'http://xkcd.com/%s/' % argv[1]
    c = requests.get(url).text
    img_url = 'https:' + ''.join(re.search('src="(\/\/imgs.xkcd.com\/comics\/.*\.)(jpg|png)"', c).groups())
    i = Image.open(BytesIO(requests.get(img_url).content)).convert('L')
    w, h = i.size
    tw, th = get_terminal_size()
    tw *= 2
    th *= 2
    if tw < w:
        ratio = tw / float(w)
        w = tw
        h = int(h * ratio)
        i = i.resize((w, h), Image.ANTIALIAS)
    can = Canvas()
    x = y = 0

    try:                   i_converted = i.tobytes()
    except AttributeError: i_converted = i.tostring()

    for pix in i_converted:
        if type(pix) is str: pix = ord(pix)
        if pix < 128:
            can.set(x, y)
        x += 1
        if x >= w:
            y += 1
            x = 0
    print(can.frame())
