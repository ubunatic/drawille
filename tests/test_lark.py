from drawille.repl import Lurtille

def test_repl():
    repl = Lurtille()
    code = """\n\n\n
    f 2 * 10 + 1
    r 3 + 4  * 5
    # comment 123

    fr90 -> f r 90
    fr90

    repeat 10 fr90 f 10
    10 * fr90
    fr90 * 10"""
    repl.parse(code)

if __name__ == '__main__': test_repl()
