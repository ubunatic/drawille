from drawille.repl import Turtille
import logging

def test_repl():
    repl = Turtille()

    # test new lines
    repl.parse("\n\n\nprint")
    repl.parse("print\n\n\n")

    # test math and functions
    code = """
    l 1 * 2 + 3  # -> 6
    r 4 + 5 * 6  # -> 34
    clear

    f2r10 -> f 2 r 11 - 1
    f2r10
    clear

    repeat 10 f2r10 f 1 r 10
    10 * f2r10
    f2r10 * 10
    """
    program = repl.parse(code)
    repl.print_func('f2r10')
    repl.run_program(program)
    repl.print_frame()

    # test animate and comments
    repl.parse("""
    animate f r
    animate 10 f r
    animate 10 f r ; text
    f 1 r 1;text
    ; text.
    # text.
    -- text.
    r 1 - 2  -- `q1` 'q2' \"q3\".
    """)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    test_repl()
