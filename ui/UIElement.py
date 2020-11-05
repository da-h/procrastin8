import numpy as np
from blessed.sequences import Sequence
from ui import get_term

term = get_term()

class UIElement:
    def __init__(self, rel_pos=None, parent=None):
        if not rel_pos and not parent:
            raise ValueError("Either position or parent have to be specified")
        self.parent = parent
        self.elements = []
        self._rel_pos = np.array(rel_pos) if rel_pos else np.array((0,0))
        self._last_rel_pos = np.copy(rel_pos) if rel_pos else np.array((0,0))
        self.last_print = {}

    @property
    def rel_pos(self):
        return self._rel_pos
    @rel_pos.setter
    def rel_pos(self,a):
        if any(a != self._last_rel_pos):
            self._rel_pos = self._last_rel_pos
            self.clear()
        self._rel_pos = np.copy(a)
        self._last_rel_pos = np.copy(a)

    @property
    def pos(self):
        if self.parent:
            return self.parent.pos + self.rel_pos
        return self.rel_pos

    def manage(self, elem):
        self.elements.append(elem)
        elem.parent = self

    def draw(self, clean=False):
        if clean:
            self.clear()

    def clear(self):
        for key, val in self.last_print.items():
            print(term.move_xy(key)+" "*len(Sequence(val, term)), end='', flush=False)
        self.last_print = {}
        for e in self.elements:
            e.clear()

    def close(self):
        self.clear()
        if self.parent:
            self.parent.onElementClosed(self)

    def printAt(self, rel_pos, *args):
        seq = Sequence(*args,term)
        pos = self.pos + rel_pos
        if pos[1] == term.cursor.pos[1] and pos[0] <= term.cursor.pos[0] and term.cursor.pos[0] < pos[0] + len(seq):
            term.cursor.on_element_current = self

        new_print = term.move_xy(pos)+seq
        pos = (*pos,)
        if pos not in self.last_print or self.last_print[pos] != new_print:
            print(new_print, end='', flush=False)
            self.last_print[pos] = new_print

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

    def onElementClosed(self, elem):
        if self.parent is not None:
            self.parent.onElementClosed(elem)
