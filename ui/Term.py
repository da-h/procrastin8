from blessed import Terminal
import numpy as np
from heapq import heappush, heappop, heapify
from copy import copy
from time import sleep
import asyncio


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

    async def moveTo(self, on_element):

        # children are equal -> no change/events
        if self.on_element == on_element:
            return

        # Event: onUnfocus
        if self.on_element is not None:
            await self.on_element.onLeave()
            await self.on_element.onUnfocus()

        self.on_element = self.on_element_current = on_element
        self.pos = self.on_element.pos
        # term.location(self.pos[0], self.pos[1])

        # Event: onFocus
        if self.on_element is not None:
            await self.on_element.onEnter()
            await self.on_element.onFocus()

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
        self.current_state = {}
        self.print_buffer = []
        self.continue_loop = True
        self._log_msgs = []

        if not self.dim:
            self.dim = self.bright_black

    async def log(self, msg):
        self._log_msgs = self._log_msgs[-99:] + [msg]

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

    # secure print
    def print(self, pos, seq):
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


    async def draw(self):

        # alternatively: clear whole screen
        # self.print((0,0), term.home + term.clear)

        # remove what is not requested again
        for pos, seq in self.buffered_delete.items():
            self.print(pos," "*seq.length())

        # print all new sequences
        for pos, seq_list in self.buffered_print.items():
            for seq in seq_list:
                self.print(pos, seq)
                self.current_state[pos] = seq

        # flush & draw cursor
        self.print_flush()
        self.buffered_print = {}
        self.buffered_delete = copy(self.current_state)
        await self.cursor.draw()

term = None
def get_term():
    global term
    if not term:
        term = globals()["term"] = WorkitTerminal()
    return term
