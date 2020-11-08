import numpy as np
from blessed.sequences import Sequence
from ui import get_term

term = get_term()

class UIElement:
    def __init__(self, rel_pos=None, parent=None, max_height=-1, padding=(0,0,0,0)):
        if not rel_pos and not parent:
            raise ValueError("Either position or parent have to be specified")
        if parent:
            parent.elements.append(self)
        self.parent = parent
        self.padding = padding
        self.max_height = max_height
        self.elements = []
        self._rel_pos = np.array(rel_pos) if rel_pos else np.array((0,0))
        self.last_print = {}

    @property
    def pos(self):
        if self.parent:
            return self.parent.pos + self.rel_pos
        return self.rel_pos

    @property
    def rel_pos(self):
        return self._rel_pos
    @rel_pos.setter
    def rel_pos(self, a):
        self._rel_pos = np.array(a)

    def draw(self):
        pass

    def close(self):
        if self.parent:
            self.parent.onElementClosed(self)

    def printAt(self, rel_pos, *args, ignore_padding=False):
        seq = Sequence(*args,term)
        pos = self.pos + rel_pos + (0 if ignore_padding else (self.padding[0],self.padding[2]))
        if pos[1] == term.cursor.pos[1] and pos[0] <= term.cursor.pos[0] and term.cursor.pos[0] < pos[0] + len(seq):
            term.cursor.on_element_current = self

        if self.max_height == 0:
            return
        if self.max_height > 0 and (rel_pos[1] if ignore_padding else rel_pos[1] + self.padding[0] + self.padding[2]) >= self.max_height:
            return

        term.printAt(pos, seq)

    # ------ #
    # Events #
    # ------ #
    def onKeyPress(self, val):
        if self.parent is not None:
            self.parent.onKeyPress(val)

    def onFocus(self):
        pass

    def onUnfocus(self):
        pass

    def onEnter(self):
        if self.parent:
            self.parent.onEnter()

    def onLeave(self):
        if self.parent:
            self.parent.onLeave()

    def onElementClosed(self, elem):
        if self.parent is not None:
            self.parent.onElementClosed(elem)
