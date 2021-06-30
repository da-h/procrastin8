from blessed import Terminal
import numpy as np
from copy import copy
from time import sleep
import asyncio


class Cursor:

    def __init__(self):
        self.pos = np.array((3,2))
        self.last_position = (-1,-1)
        self.visible = False
        self.elements_under_cursor = []

    def show(self):
        self.visible = True

    def hide(self):
        self.visible = False

    @property
    def on_element(self):
        if len(self.elements_under_cursor) == 0:
            return None
        return self.elements_under_cursor[0]

    async def moveTo(self, on_element):

        # children are equal -> no change/events
        if self.on_element == on_element:
            return

        parents_source = [self.on_element] + self.on_element.get_parents() if self.on_element else [None]
        parents_target = [     on_element] +      on_element.get_parents() if      on_element else [None]

        self.elements_under_cursor_before = parents_source
        self.elements_under_cursor_after = parents_target

        # Event: onUnfocus
        if parents_source[0] is not None:
            if parents_source[0] not in parents_target:
                await parents_source[0].onLeave()
            await parents_source[0].onUnfocus()

        self.elements_under_cursor = parents_target
        self.pos = self.on_element.pos
        # term.location(self.pos[0], self.pos[1])

        # Event: onFocus
        if parents_target[0] is not None:
            if parents_target[0] not in parents_source:
                await on_element.onEnter()
            await on_element.onFocus()

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

    async def draw(self):
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
            "r": "\x12",
            "p": "\x10",
            "o": "\x0f"
        }
        self.buffered_print = {}
        self.buffered_delete = {}
        self.print_buffer = []
        self.continue_loop = True
        self._log_msgs = []

        if not self.dim:
            self.dim = self.bright_black

    async def log(self, *msg):
        self._log_msgs = self._log_msgs[-99:] + [" ".join([str(m) for m in msg])]

    # listen for keypresses (to be run in a seperate thread)
    def threaded_inkey(self, queue):
        stop = False
        while not stop:
            with self.cbreak():
                val = self.inkey(esc_delay=0)
                queue.put_nowait(val)
                if val == "q":
                    stop = True
            queue._loop._write_to_self()

    def move_xy(self, x, y=None):
        if type(x) is np.ndarray or isinstance(x, tuple):
            return super().move_xy(x[0],x[1])
        return super().move_xy(x,y)


    def removeAt(self, pos, seq):
        pos = (pos[0], pos[1])

        # register deletion of new sequence
        if pos in self.buffered_delete:
            self.buffered_delete[pos] = max(self.buffered_delete[pos], seq.length())
        else:
            self.buffered_delete[pos] = seq.length()


    def printAt(self, pos, seq):
        pos = (pos[0], pos[1])

        # register print of new sequence
        if pos in self.buffered_print:
            self.buffered_print[pos].append(seq)
        else:
            self.buffered_print[pos] = [seq]

    # secure print
    def _print(self, pos, seq):
        if self.height <= pos[1]:
            return
        if pos[0] < 0:
            pos = (term.width - pos[0], pos[1])
        if pos[1] < 0:
            pos = (pos[0], term.height - pos[1])
        self.print_buffer.append(term.move_xy(pos)+seq)


    def print_flush(self):
        print("".join(self.print_buffer), end="")
        self.print_buffer = []
        self.buffered_print = {}
        self.buffered_delete = {}

    async def draw(self):

        # remove what is not requested again
        for pos, len in self.buffered_delete.items():
            self._print(pos," "*len)

        # print all new sequences
        for pos, seq_list in self.buffered_print.items():
            for seq in seq_list:
                self._print(pos, seq)

        # flush & draw cursor
        self.print_flush()
        await self.cursor.draw()

term = None
def get_term():
    global term
    if not term:
        term = globals()["term"] = WorkitTerminal()
    return term
