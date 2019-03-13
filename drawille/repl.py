# -*- coding: utf-8 -*-

# (C) 2018 Uwe Jugel, @ubunatic
# License: GNU AGPLv3+ (see LICENSE file or http://www.gnu.org/licenses)

"""
This module implements a REPL to run drawille Turtle commands using the
the Turtille syntax, which allows to define simple procedural graphics and
animations to be drawn on the console.

To start this module, run: `turtille` or `python -m drawille`.

The module can also be embedded using the `drawille.Turtille` class.
See the class docu for more details.
"""

from __future__ import unicode_literals, absolute_import, print_function
from builtins import open, super

import re, os, logging, time
import lark
from drawille.turtle import Turtle
from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory
try:
    # required for prompt-toolkit>=2.0.0
    from prompt_toolkit.completion import WordCompleter
except ImportError:
    # legacy import for prompt-toolkit<2.0.0
    from prompt_toolkit.contrib.completers import WordCompleter

from pygments.lexer import RegexLexer, bygroups
from pygments.token import Text, Name, Keyword, Comment, Literal, Number

log = logging.getLogger(__name__)

usage = """
# Copyright: This is Turtille the Turtle REPL (C) Uwe Jugel, @ubunatic
#            running on top of Drawille.      (C) Adam Tauber, asciimoo@gmail.com
#
# License:   GNU AGPLv3 (see LICENSE file or http://www.gnu.org/licenses)

Hi, I am Turtille!

Type 'q' or 'quit' to leave. Type 'forward', 'backward', 'left', or 'right' to move.
You can also chain instructions. For instance, for drawing a rectangle:

    forward right 90  forward right 90  forward right 90  forward right 90

Typing only the first letters of these words also works:

    f r 90  f r 90  f r 90  f r 90

You can give this "program" a name and use it by its name:

    rect -> f r 90  f r 90  f r 90  f r 90   # define program
    rect                                     # run program

You can also repeat commands using 'number * command':

    r3f1 -> r 3 f 1    # define program
    120 * r3f1         # repeat program 120 times

You can easily define programs that make use other programs:

    fr90   -> f r 90
    rect   -> 4 * fr90
    rec45  -> rect r 45
    flower -> clear 8 * rec45

    flower  # enjoy!

Do not forget to save all your programs:

    save

You can also draw animations:

    flower10 -> flower r 10  # draw something + change angle slightly
    animate 5 flower10       # repeat program 5 times
    animate flower10         # repeat program forever (press Ctrl-C to stop)

Other commands are:

    help   # show this help
    reset  # reset Turtille (angle and position)
    clear  # clear the screen (but do not reset angle and position)
    quit   # exit Turtille

"""

class StopTurtille(Exception):  pass
class TurtilleError(Exception): pass


class TurtilleLexer(RegexLexer):
    """TurtilleLexer is a simple RegexLexer,
    required for pygments syntax highlighting."""
    name = 'Turtille'
    aliases = ['turty', 'tur', 'turtille']
    filenames = ['*.tur']
    flags = re.IGNORECASE

    tokens = dict(root=[
        (r'\s+',               Text),
        (r'([0-9]+)(\s*)(\*)', bygroups(Keyword, Text, Keyword)),
        (r'(.*?)(\s*)(->)',    bygroups(Name.Function, Text, Keyword)),
        (r'[0-9]+',            Number),
        (r'[a-z]+',            Literal),
        (r'#.*\n',             Comment),
        (r'.*\n',              Text),
    ])


class DefaultPrinter(object):
    """DefaultPrinter is a Mixin Class for the Turtle VM for printng output to the console.
    All output is handled in this class, the BaseVM class is output agnostic.
    """
    def print_text(tur, *args):
        """print_text prints is the text output function of the Turtle VM,
        for the DefaultPrinter it is used to print the turtles current frame.
        It uses Python's print function."""
        print(*args)

    def print_frame(tur):
        """print_frame prints the turtle's current frame"""
        tur.print_text(tur.turtle.frame())

    def print_func(tur, command):
        """print_func prints the definition of one of turtle's commands"""
        tur.print_text(tur.format_func(command))


class BaseVM(DefaultPrinter):
    """BaseVM is an extentable Turle VM that implements the basic Turtle commands or
    forwards them the it's `turtle`. It can run Turtille programs and print the result.
    Usage Example:

        tur = BaseVM()
        tur.add_func('fr90', [('f',), ('r',90)])
        tur.add_func('rect', [('repeat', 4, 'fr90'])
        tur.run_program([('rect',)])

    """
    def __init__(tur):
        tur.turtle = Turtle()
        tur.funcs = {}
        tur.reserved_commands = set()
        tur.commands = {}
        for k,v in [('left',    tur.turtle.left),
                    ('right',   tur.turtle.right),
                    ('up',      tur.turtle.up),
                    ('down',    tur.turtle.down),
                    ('forward', tur.turtle.forward),
                    ('back',    tur.turtle.back),
                    ('clear',   tur.turtle.clear),
                    ('move',    tur.turtle.move),
                    ('quit',    tur.quit),
                    ('print',   tur.print_func),
                    ('help',    tur.help),
                    ('repeat',  tur.repeat),
                    ('reset',   tur.reset)]:
            tur.add_command(k,v)
        super().__init__()

    def add_command(tur, cmd, fn):
        log.debug("adding command: %s", cmd)
        assert cmd not in tur.commands, "safe overriding commands not supported"
        tur.commands[cmd] = fn
        short = cmd[0]
        if short not in tur.commands:
            log.debug("adding shortcut: %s", short)
            tur.commands[short] = fn
        tur.reserved_commands.add(cmd)
        tur.reserved_commands.add(short)

    def add_func(tur, cmd, commands):
        log.debug("adding func: %s", cmd)
        if cmd in tur.reserved_commands:
            raise ValueError('cannot override builtin command: {}'.format(cmd))
        else:
            program = commands[:]
            def run_function(): tur.run_program(program)
            tur.commands[cmd] = run_function
            tur.funcs[cmd] = program

    def run_program(tur, commands):
        program = []
        errors  = []
        for res in commands:
            cmd, args = res[0], res[1:]
            if cmd not in tur.commands:
                errors.append('invalid function or command: "{}"'.format(cmd))
            else:
                program.append((cmd, args))

        if len(errors) > 0:
            raise ValueError('Program has errors:\n' + '\n'.join(errors))

        for cmd, args in program:
            log.debug('running: %s%s', cmd, tuple(args))
            tur.commands[cmd](*args)

    def repeat(tur, *repeat_args):
        # also accept single list of args instead of implicit *args
        if len(repeat_args) == 1: repeat_args = repeat_args[0]
        ra = repeat_args
        num, cmd, args = ra[0], ra[1], ra[2:]
        if cmd not in tur.commands:
            raise ValueError('cannot repeat invalid function or command: {}'.format(cmd))
        else:
            fn = tur.commands[cmd]
            for i in range(num): fn(*args)

    def run(tur, text): tur.run_program(tur.parse(text))

    def quit(tur): raise StopTurtille("quit")

    def help(tur): tur.print_text(usage)

    def reset(tur):
        tur.turtle.pos_x = 0
        tur.turtle.pos_y = 0
        tur.turtle.rotation = 0
        tur.turtle.clear()

    def format_func(tur, cmd):
        fn = tur.funcs.get(cmd)
        if fn is None: return cmd
        program = [' '.join(str(v) for v in c) for c in fn]
        return '{} -> {}'.format(cmd, ' '.join(program))


class WithAnimate(object):
    """WithAnimate add the `animate` command to the Turtle VM"""
    def __init__(tur):
        super().__init__()
        tur.add_command('animate', tur.animate)

    def clear_screen(tur):
        os.system('cls' if os.name == 'nt' else 'clear')

    def animate(tur, num, cmd):
        if cmd not in tur.funcs:
            raise ValueError('invalid animation function: {}'.format(cmd))
        # since debug logging will destroy the animation, we need to temporary disable it
        level = log.getEffectiveLevel()
        try:
            fn = tur.commands[cmd]
            log.setLevel(logging.INFO)
            # TODO (uj): use curses animate
            # animate(tur.turtle, fn)
            i = 0
            while True:
                fn()
                tur.clear_screen()
                tur.print_text("# press Ctrl-C to stop animation")
                tur.print_frame()
                time.sleep(1.0/24.0)
                if   num is None: continue
                elif i > num:     break
                else:             i += 1
        except KeyboardInterrupt:
            tur.print_text("\n# stopped animation")
        finally:
            log.setLevel(level)


class WithSaveAndLoad(object):
    def __init__(tur):
        super().__init__()
        tur.add_command('save', tur.save)
        tur.add_command('load', tur.load)

    def save(tur, filename='.turtille'):
        # TODO: preserve comments
        with open(filename, 'wb') as f:
            for name in tur.funcs:
                text = tur.format_func(name)
                f.write('    {}\n'.format(text).encode())
                log.debug("saved func: %s", text)
        log.info('saved: %s', list(tur.funcs))

    def load(tur, filename='.turtille', silent=False):
        if silent: info = log.debug
        else:      info = log.info
        program = []
        try:
            with open(filename, 'rb') as f:
                for line in f:
                    program.extend(tur.parse(line.decode()))
            if silent: info = log.debug
            else:      info = log.info
            info('loaded functions from %s', filename)
        except IOError:
            info('nothing to load from %s', filename)
        return program


class Repl(BaseVM):
    """Turtille is a Turtle REPL for interactively running turtille commands and programs"""
    def __init__(tur):
        super().__init__()
        tur.add_command('_',    tur.last)
        tur.add_command('last', tur.last)
        tur.history = InMemoryHistory()
        tur.unaries = 'up down clear quit reset u d c q'.split()
        tur.lino = 1
        tur._last_cmd = None

    def start(tur):
        """start the repl loop"""
        log.debug("starting REPL")
        tur.help()
        while True:
            try: tur.repl(); tur.lino += 1
            except (StopTurtille, EOFError): return True
            except KeyboardInterrupt:        print("Type 'q' or 'quit' to stop Turtille.")
            except Exception as err:         print(err)  # any errors are printed to repl

    def repl(tur):
        """run the repl once: first read input, then execute the program"""
        completer = WordCompleter(list(tur.commands), ignore_case=True)
        text = prompt('Turtille [{}]: '.format(tur.lino),
                      history=tur.history,
                      lexer=TurtilleLexer,
                      completer=completer)
        program = list(tur.parse(text))
        tur.run_program(program)
        if len(program) == 0 or len(program) == 1 and program[0][0] in ('h','help'): return
        tur.last_cmd = program[-1]
        tur.print_frame()

    def parse(tur, text): raise NotImplementedError('initialized VM without a parser class')

    @property
    def last_cmd(tur): return tur._last_cmd

    @last_cmd.setter
    def last_cmd(tur, command):
        cmd = command[0]
        if cmd not in ('_', 'last'): tur._last_cmd = command

    def last(tur):
        cmd = tur.last_cmd
        if cmd is not None: return tur.commands[cmd[0]](*cmd[1:])


class WithDefaultParser(object):

    def parse(tur, text):
        """parse the given `text` to a program and store any defined functions as new commands"""
        text = text.strip()
        tokens = [t.strip() for t in text.split(' ')]
        tokens.reverse()
        program = [t for t in tokens if len(t) > 0]
        return list(tur.parse_program(program))

    def parse_program(tur, tokens):
        while len(tokens) > 0:
            res = tur.parse_command(tokens)
            if res is not None: yield res

    def parse_comment(tur, tokens):
        while len(tokens) > 0 and tokens.pop() != '\n': pass

    def parse_repeat(tur, num, tokens):
        num  = int(num)
        res  = tur.parse_command(tokens)
        cmd  = res[0]
        args = res[1:]
        return ('repeat', num, cmd) + tuple(args)

    def parse_animate(tur, arg, tokens):
        try:               num = int(arg); cmd = tokens.pop()
        except ValueError: num = None;     cmd = arg
        return ('animate', num, cmd)

    def parse_func(tur, name, tokens):
        program = []
        while len(tokens) > 0:
            t = tokens.pop()
            program.append(t)
            if t == '\n': break
        program.reverse()
        log.debug("parse_func:    %s", program)
        commands = list(tur.parse_program(program))
        tur.add_func(name, commands)

    def parse_command(tur, tokens):
        arg1 = tokens.pop()
        if len(tokens) > 0: arg2 = tokens[-1]  # parse look ahead to detect funcs and loops
        else:               arg2 = None

        log.debug("parse_command: %s", tokens[:])

        if   arg1.startswith('#'):       return tur.parse_comment(tokens)
        elif arg2 == '*':  tokens.pop(); return tur.parse_repeat(arg1, tokens)
        elif arg2 == '->': tokens.pop(); return tur.parse_func(arg1, tokens)
        elif arg1 == 'repeat':           return tur.parse_repeat(tokens.pop(), tokens)
        elif arg1 in ('move',    'm'):   return (arg1, float(tokens.pop()), float(tokens.pop()))
        elif arg1 in ('print',   'p'):   return (arg1, tokens.pop())
        elif arg1 in ('animate', 'a'):   return tur.parse_animate(tokens.pop(), tokens)
        elif arg1 in tur.unaries:        return (arg1,)
        elif arg1 in tur.funcs:          return (arg1,)
        else:
            cmd, arg = arg1, None

            log.debug("parse_command: %s (%s,%s) START", tokens[:], cmd, arg)
            if len(tokens) > 1 and tokens[-2] in ['*']: pass  # ignore arg2 since it belongs to the loop
            elif arg2 is not None:
                # parse number parameter and consume it if possible
                try:               arg = float(arg2); tokens.pop()  # use and consume number arg2
                except ValueError: arg = None
            # everything is parsed and consumed now, but we can still add some default
            if arg is None:
                if   cmd in ('r','l','right','left'):       arg = 45  # turn 45 deggree by default
                elif cmd in ('f','b','forward','backward'): arg = 20  # move 20 steps by default

            log.debug("parse_command: %s (%s,%s) END", tokens[:], cmd, arg)
            if arg is None: return (cmd,)
            else:           return (cmd, arg)

class WithLarkParser(object):
    def __init__(tur):
        super().__init__()
        tur._lark_transformer = TurtilleTransformer(tur)
        tur._lark = lark.Lark(r"""
        start: NL? (func nl | run nl | comment nl )* end
        ?end:     func | run
        ?nl:      NL+
        ?func:    name "->" cmds    -> func
        ?run:     cmds              -> run
        ?comment: "#" any*          -> comment
        ?any:     LETTER+ | INT | FLOAT | CNAME

        ?cmds: cmd+

        ?cmd: MOVEMENT [expr]   -> movement
           | GOTO expr expr     -> goto
           | name               -> cmd
           | "repeat" expr name -> repeat
           | expr "*" name      -> repeat
           | name "*" expr      -> repeated

        MOVEMENT: "f"|"b"|"l"|"r"|"forward"|"back"|"backward"|"left"|"right"
        MOVE: "move"|"mv"|"m"
        GOTO: MOVE|"goto"|"g"

        ?expr: factor
            | expr "+" factor  -> add
            | expr "-" factor  -> sub
        ?factor: atom
            | factor "*" atom  -> mul
            | factor "/" atom  -> div
        ?atom: int | float
            | "-" atom         -> neg
            | "(" expr ")"

        ?int:   INT            -> int
        ?float: FLOAT          -> float

        ?name: CNAME           -> name
        ?arg:  CNAME           -> name
        val:   name | expr

        %import common.INT
        %import common.FLOAT
        %import common.LETTER
        %import common.CNAME
        %import common.NEWLINE -> NL
        %import common.WS_INLINE
        %ignore WS_INLINE
        """)

    def parse(tur, text):
        tf = tur._lark_transformer
        tree = tur._lark.parse(text)
        print("CODE:\n", text.strip())
        print("TREE:\n", tree)
        rest = tf.transform(tree)
        print("REST:\n", rest)
        print("AST:")
        for cmd in tf.program:
            print(cmd)
        tur.run_program(tf.program)
        tur.print_frame()

@lark.v_args(inline=True)
class TurtilleTransformer(lark.Transformer):
    from operator import add, sub, mul, truediv as div, neg
    float = float
    int   = int

    def __init__(t, tur):
        t.tur = tur  # type: Turtille
        t.program = []

    def name(t, token):               return token.value
    def comment(t, *tokens):          pass
    def movement(t, token, num=None):
        cmd = token.value[0]
        if num is None:
            if   cmd in ('r','l','right','left'):               num = 45  # turn 45 deggree by default
            elif cmd in ('f','b','forward','backward', 'back'): num = 20  # move 20 steps by default
        return (cmd, num)
    def goto(t, name, x, y):          return (name, x, y)
    def repeat(t, num, name):         return ('repeat', num, name)
    def repeated(t, name, num):       return t.repeat(num, name)
    def cmd(t, name):                 return (name, )
    def cmds(t, *cmds):               return list(cmds)
    def func(t, name, cmds):
        # t.program.append(('func', name, cmds))
        t.tur.add_func(name, cmds)
    def run(t, cmds):
        if   type(cmds) is tuple: t.program.append(cmds)
        elif type(cmds) is list:  t.program.extend(cmds)
        else: raise TypeError('invalid command list type: {}'.format(type(cmds)))

class Lurtille(WithLarkParser, Repl):
    def __init__(tur):
        super().__init__()

class Turtille(WithDefaultParser, WithAnimate, WithSaveAndLoad, Repl):
    """Turtille is a Turtle REPL for interactively running turtille commands and programs.
    It supports `save` and `load` for the currently defined set of user functions and
    can also `animate` a command repeatedly.

    Usage Example:

        tur = Turtille()
        tur.run('fr90 -> f r 90')
        tur.run('rect -> 4 * fr90')
        tur.run('rect')
        tur.print_frame()

    """
    def __init__(tur):
        super().__init__()
        tur.load(silent=True)

