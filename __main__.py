"""
WireWorld, another cellular automaton with funny consequences:
    http://mathworld.wolfram.com/WireWorld.html

Use metaclasses for implement the singleton pattern.

Need a utf8 compliant terminal, or modify the CHAR_{WIDE,HEAD}
    values, few lines below.

"""
import time

from itertools import product
from collections import defaultdict

# Constants about printing
CHAR_VOID = ' '
CHAR_WIRE = '\N{FULL BLOCK}'
CHAR_HEAD = '\N{MEDIUM SHADE}'
CHAR_TAIL = CHAR_WIRE  # dont show electron tails

# used for parsing input file
CHARS_VOID = CHAR_VOID + '  '
CHARS_WIRE = CHAR_WIRE + '#@%'
CHARS_HEAD = CHAR_HEAD + '+?)>'
CHARS_TAIL = CHAR_TAIL + '-.(<'


class Printable(type):
    """Metaclass for printable classes.
    Each childs can redefine the letter used for print itself when the
    string representation is asked.

    """
    def __new__(cls, name, bases, namespace, letter=CHAR_VOID):
        new_cls = super().__new__(cls, name, bases, namespace)
        new_cls.letter = letter
        return new_cls

    # must be redefined, while a keyword argument is introduced
    def __init__(cls, name, bases, namespace, letter=CHAR_VOID):
        super().__init__(name, bases, namespace)

    def __str__(cls):
        "String representation of the class is its letter"
        return cls.letter


class Void(metaclass=Printable, letter=CHAR_VOID):
    """State 0: nothing, do nothing, acts on nothing"""
    @classmethod
    def next_state(cls, neighbors):
        return cls


class Wire(metaclass=Printable, letter=CHAR_WIRE):
    """State 3: Turn in ElecHead if 1 or 2 neighbors are ElecHead"""
    @classmethod
    def next_state(cls, neighbors):
        if tuple(n is ElecHead for n in neighbors).count(True) in (1, 2):
            return ElecHead
        else:
            return cls

class ElecHead(metaclass=Printable, letter=CHAR_HEAD):
    """State 1: Turn in ElecTail"""
    @staticmethod
    def next_state(neighbors):
        return ElecTail

class ElecTail(metaclass=Printable, letter=CHAR_TAIL):
    """State 2: Turn in Wire"""
    @staticmethod
    def next_state(neighbors):
        return Wire


class World(defaultdict):
    """Get together many Wire and Void references.
    Provides API for manipulate them and compute the next World.

    Provides API for load a world from a file.

    """

    def __init__(self, table={}):
        # make the table a dictionnary
        if not isinstance(table, defaultdict):
            table = World.__tabletodict(table)
        # call super with the dictionnary, with the same factory of default
        super().__init__(table.default_factory, table)
        self.maxcoords = self.__maxcoords()


    def next(world):
        "Return the next world"
        return World(
            defaultdict(lambda: Void, {
                coords: state.next_state(world.neighbors(coords))
                for coords, state in tuple(world.items())
            }))

    def __maxcoords(world):
        "Return the maximal coordinates used by a non-Void object"
        return (
            max(x for x, _ in world.keys()),
            max(y for _, y in world.keys())
        )

    def neighbors(world, center):
        "Return iterable on neighboring states. (Moore neighbors)"""
        x, y = center
        yield from (
            world[x+i, y+j]
            for i, j in product((-1, 0, 1), repeat=2)
            if j != 0 or i != 0
        )


    def __iter__(world):
        "Return iterable of ((x, y), state)"
        maxx, maxy = world.maxcoords
        return (((x, y), world[x, y]) for x, y in product(range(maxx+1), range(maxy+1)))


    def __str__(world):
        maxx, maxy = world.maxcoords
        ret = '—' * (maxy + 2) + '\n|'
        old_x = 0
        for (x, y), state in world:
            if old_x != x:
                ret += '|\n|'
                old_x = x
            ret += str(state)
        return ret + '|\n' + '—' * (maxy + 2) + '\n'

    @property
    def have_current(world):
        "True iff any reference in the world is a ElecHead"
        return any(state is ElecHead for _, state in world)


    @staticmethod
    def read(filename):
        "Return a new World, initialized from given filename"
        wireclass = defaultdict(
            lambda: None,  # manage \n notabily
            {letter: cls for cls, letters in (
                (Wire,      CHARS_WIRE),
                (Void,      CHARS_VOID),
                (ElecHead,  CHARS_HEAD),
                (ElecTail,  CHARS_TAIL),
            ) for letter in letters
            }
        )
        with open(filename) as fd:
            tupleworld = tuple(
                tuple(wireclass[char] for char in line if char in wireclass)
                for line in fd
            )
        return World(tupleworld)

    @staticmethod
    def __tabletodict(table):
        """Convert given table (tuple of tuple of states, preferabily)
        in coords:state dict.

        """
        return defaultdict(
            lambda: Void,
            {(x, y): table[x][y]
             for x in range(len(table))
             for y in range(len(table[x]))}
        )


    @staticmethod
    def gate_or():
        """logical OR gate"""
        return World.read('gate_or.txt')
    @staticmethod
    def gate_xor():
        """logical XOR gate"""
        return World.read('gate_xor.txt')
    @staticmethod
    def gate_and():
        """logical AND gate"""
        return World.read('gate_and.txt')


if __name__ == '__main__':
    for func in (World.gate_or, World.gate_xor, World.gate_and):
        world = func()
        def user_show():
            print('PLAYING: ' + func.__doc__)
            print(world)
            time.sleep(0.3)
        user_show()
        while world.have_current:
            world = world.next()
            user_show()
