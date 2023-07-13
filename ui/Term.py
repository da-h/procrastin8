from blessed import Terminal as BlessedTerminal
import numpy as np
from pathlib import Path


class Cursor:
    def __init__(self):
        self.visible = False
        self.pos = np.array((3, 2))
        self.last_position = (-1, -1)
        self.elements_under_cursor = []

    def show(self):
        self.visible = True

    def hide(self):
        self.visible = False

    @property
    def on_element(self):
        if not self.elements_under_cursor:
            return None
        return self.elements_under_cursor[0]

    async def moveTo(self, on_element):
        # Children are equal -> no change/events
        if self.on_element == on_element:
            return

        parents_source = [self.on_element] + self.on_element.get_parents() if self.on_element else [None]
        parents_target = [on_element] + on_element.get_parents() if on_element else [None]

        self.elements_under_cursor_before = parents_source
        self.elements_under_cursor_after = parents_target

        # Event: onUnfocus
        if parents_source[0] is not None:
            if parents_source[0] not in parents_target:
                await parents_source[0].onLeave()
            await parents_source[0].onUnfocus()

        self.elements_under_cursor = parents_target
        self.pos = self.on_element.pos

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

    async def draw(self, term):
        if self.visible:
            print(term.move_xy(*self.pos) + term.normal_cursor, end='', flush=True)
        else:
            print(term.move_xy(*self.pos) + term.hide_cursor, end='', flush=True)


class Terminal(BlessedTerminal):
    def __init__(self):
        super().__init__()
        self.cursor = Cursor()
        self.KEY_CTRL = {"e": "\x19", "y": "\x05", "r": "\x12", "p": "\x10", "o": "\x0f"}
        self.buffered_print = [{}]
        self.buffered_delete = [{}]
        self.print_buffer = []
        self.continue_loop = True
        self._log_msgs = []
        self.silent_draw = False

        self.log_file = Path("/tmp/procrastin8.log")
        if self.log_file.exists():
            self.log_file.unlink()

        if not self.dim:
            self.dim = self.bright_black

    async def log(self, *msg):
        if self.log_file is not None:
            with self.log_file.open("a") as l:
                l.write(" - ".join([str(m) for m in msg]) + "\n")
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

    def removeAt(self, pos, seq, layer=0):
        pos = (pos[0], pos[1])

        # ensure correct length
        for _ in range(len(self.buffered_delete), layer + 1):
            self.buffered_delete.append({})
            self.buffered_print.append({})

        # register deletion of new sequence
        if pos in self.buffered_delete[layer]:
            self.buffered_delete[layer][pos] = max(self.buffered_delete[layer][pos], seq.length())
        else:
            self.buffered_delete[layer][pos] = seq.length()

    def printAt(self, pos, seq, layer=0):
        pos = (pos[0], pos[1])

        # ensure correct length
        for _ in range(len(self.buffered_delete), layer + 1):
            self.buffered_delete.append({})
            self.buffered_print.append({})

        # register print of new sequence
        if pos in self.buffered_print[layer]:
            self.buffered_print[layer][pos].append(seq)
        else:
            self.buffered_print[layer][pos] = [seq]

    # secure print
    def _print(self, pos, seq):
        if self.height <= pos[1]:
            return
        if self.width <= pos[0]:
            return
        if pos[0] < 0:
            pos = (self.width - pos[0], pos[1])
        if pos[1] < 0:
            pos = (pos[0], self.height - pos[1])

        # Truncate the sequence if it would appear outside the terminal window
        seq_length = len(seq) if isinstance(seq, str) else seq.length()
        if pos[0] + seq_length > self.width:
            seq = seq[:self.width - pos[0]]

        self.print_buffer.append((pos, seq))

    def print_flush(self):
        # Flush the print buffer to the screen
        print("".join([self.move_xy(pos) + seq for pos, seq in self.print_buffer]), end="", flush=True)

        # Reset print_buffer and buffered_print & buffered_delete dictionaries
        self.print_buffer = []
        self.buffered_print = [{} for _ in range(len(self.buffered_print))]
        self.buffered_delete = [{} for _ in range(len(self.buffered_delete))]

    async def draw(self, skip_clear=False):
        if self.silent_draw:
            self.print_flush()
            return

        for layer in range(len(self.buffered_delete)):

            # Remove what is not requested again
            if not skip_clear:
                for pos, length in self.buffered_delete[layer].items():
                    self._print(pos, " " * length)

            # Print all new sequences
            for pos, seq_list in self.buffered_print[layer].items():
                for seq in seq_list:
                    self._print(pos, seq)

        # Flush & draw cursor
        # for i in self.buffered_print[0].values():
        #     await self.log("flush:", i)
        self.print_flush()
        await self.cursor.draw(self)

term = None

def get_term():
    global term
    if not term:
        term = globals()["term"] = Terminal()
    return term
