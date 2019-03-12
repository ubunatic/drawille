from drawille import Turtille
from drawille.repl import StopTurtille

import os, logging

def tur_path(tur_name):
    here = os.path.dirname(__file__)
    return os.path.join(here, tur_name)

def test_imports():
    # This test ensures that all modules can be loaded without errors
    import drawille                        # noqa: F401
    import drawille.repl                   # noqa: F401
    from drawille import Turtle, Turtille  # noqa: F401
    from drawille.turtle import Turtle     # noqa: F401,F811
    from drawille.repl import Turtille     # noqa: F401,F811

def test_run_command():
    logging.basicConfig(level=logging.DEBUG)

    tur = Turtille()
    print("funcs:", list(tur.funcs))
    assert 'rect' in tur.funcs

    tur.run('myfunc -> rect')
    tur.run('myfunc')
    tur.run('r 60 f')
    tur.run('l 60 f r 60 b')
    tur.print_frame()  # output: "swing door/window": [\]\
    try: tur.run('c q'); assert False, "quit must raise StopTurtille"
    except StopTurtille: pass
    tur.print_func('rect')
    tur.turtle.clear()
    tur.reset()

    program = tur.load(tur_path('test.tur'))
    assert program == [('testrect',)]
    tur.run_program(program)
    for k in tur.funcs: tur.print_func(k)
    assert 'testrect' in tur.funcs
    tur.run('f 10 testrect')
    tur.print_frame()  # output: two rects: [][]


if __name__ == '__main__': test_run_command()
