# -*- coding: utf-8 -*-

# (C) 2019, Uwe Jugel, @ubunatic
# License: GNU AGPL (see LICENSE file or http://www.gnu.org/licenses)

from drawille.repl import Turtille, StopTurtille
import argparse, logging, sys

def main():
    p = argparse.ArgumentParser(); add = p.add_argument
    add("--debug",       help='enable debug logs', action='store_true')
    add("--print", "-p", help='print the turtle frame on exit', action='store_true', dest='_print')
    add("--run",   "-c", help='turtille program code', nargs='+', default=None, metavar='PROGRAM')
    add("turfile",       help='turtille code file',    nargs='?',               metavar='TURFILE')
    args = p.parse_args()

    level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=level)

    tur = Turtille()
    try:
        if args.run is not None:
            tur.run(' '.join(args.run))
        elif args.turfile:
            program = tur.load(args.turfile)
            tur.run_program(program)
        else:
            tur.start()
    except StopTurtille: pass
    if args._print: tur.print_frame()
    sys.exit(0)
