from blessed import Terminal
import numpy as np
from heapq import heappush, heappop, heapify
from copy import copy


class Cursor:

    def __init__(self):
        self.pos = np.array((3,2))
        self.on_element = None
        self.last_position = (-1,-1)
        self.visible = False

    def show(self):
        self.visible = True

    def hide(self):
        self.visible = False

    def moveTo(self, on_element):

        # elements are equal -> no change/events
        if self.on_element == on_element:
            return

        # Event: onUnfocus
        if self.on_element is not None:
            self.on_element.onUnfocus()

        self.on_element = self.on_element_current = on_element
        self.pos = self.on_element.pos
        # term.location(self.pos[0], self.pos[1])

        # Event: onFocus
        if self.on_element is not None:
            self.on_element.onFocus()

    def clear(self):
        self.on_element = None

    def isOnElement(self, elem):
        onelem = self.on_element
        if onelem == elem:
            return True
        while onelem.parent:
            onelem = onelem.parent
            if onelem == elem:
                return True
        return False

    def relativePos(self):
        if self.on_element is None:
            return self.pos

        return self.pos - self.on_element.pos

    def draw(self):
        if self.visible:
            print(term.move_xy(*self.pos)+term.normal_cursor, end='', flush=True)
        else:
            print(term.move_xy(*self.pos)+term.hide_cursor, end='', flush=True)


class WorkitTerminal(Terminal):

    def __init__(self):
        super().__init__()
        self.cursor = Cursor()
        self.KEY_CTRL = {
            "e": "\x19",
            "y": "\x05",
            "p": "\x10"
        }
        self.buffered_print = {}
        self.buffered_delete = {}
        self.current_state = {}

    def move_xy(self, x, y=None):
        if type(x) is np.ndarray or isinstance(x, tuple):
            return super().move_xy(x[0],x[1])
        return super().move_xy(x,y)

    def printAt(self, pos, seq):
        pos = (pos[0], pos[1])

        # unregister removal on window in case
        # - same sequence should be printed at same position
        # - new sequence is at least longer
        if pos in self.current_state and (self.current_state[pos] == seq or self.current_state[pos].length() <= seq.length()):
            if pos in self.buffered_delete:
                del self.buffered_delete[pos]

        # register print of new sequence
        if pos in self.buffered_print:
            self.buffered_print[pos].append(seq)
        else:
            self.buffered_print[pos] = [seq]

    def draw(self):

        # remove what is not requested again
        for pos, seq in self.buffered_delete.items():
            print(term.move_xy(pos)+" "*seq.length(), end='', flush=False)

        # print all new sequences
        for pos, seq_list in self.buffered_print.items():
            for seq in seq_list:
                print(term.move_xy(pos)+seq, end='', flush=False)
                self.current_state[pos] = seq

        # flush & draw cursor
        self.buffered_print = {}
        self.buffered_delete = copy(self.current_state)
        self.cursor.draw()

term = None
def get_term():
    global term
    if not term:
        term = globals()["term"] = WorkitTerminal()
    return term
