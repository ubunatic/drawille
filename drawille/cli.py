from drawille.repl import Turtille
import argparse, logging, sys

def main():
    p = argparse.ArgumentParser(); add = p.add_argument
    add("--debug", action='store_true')
    add("--run",   help='turtille program code', nargs='+', default=None, metavar='PROGRAM')
    add("turfile", help='turtille code file',    nargs='?',               metavar='TURFILE')
    args = p.parse_args()

    level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=level)

    tur = Turtille()
    if args.run is not None:
        tur.run(' '.join(args.run))
    elif args.turfile:
        program = tur.load(args.turfile)
        tur.run_program(program)
    else:
        tur.start()
        sys.exit(0)
    tur.print_frame()
