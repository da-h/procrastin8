from blessed import Terminal
from blessed.sequences import Sequence
import numpy as np
from textwrap import TextWrapper

from settings import COLUMN_WIDTH, WINDOW_PADDING

class Cursor:

    def __init__(self):
        self.pos = np.array((3,2))
        self.on_element = None

    def clear(self):
        self.on_element = None

    def draw(self):
        print(term.move_xy(self.pos)+"_")


class WorkitTerminal(Terminal):

    def __init__(self):
        super().__init__()
        self.cursor = Cursor()

    def move_xy(self, x, y=None):
        if type(x) is np.ndarray:
            return super().move_xy(x[0],x[1])
        return super().move_xy(x,y)


term = WorkitTerminal()






# ======== #
# basic ui #
# ======== #

def draw_window(pos, dim, title=None):
    pos = np.array(pos)
    dim = np.array(dim)
    width, height = dim

    # draw border
    border  = term.move_xy(pos) + "┌" + "─" * (width-2) + "┐"
    for i in range(height-2):
        border += term.move_xy(pos+(0,i+1)) + "│"
        border += term.move_xy(pos+(width-1,i+1)) + "│"
    border += term.move_xy(pos+(0,height-1)) + "└" + "─" * (width-2) + "┘"
    print(border)

    # set title
    if title is not None:
        print(term.move_xy(pos+(1+5,0)) + " %s " % title)

class UIElement:
    def __init__(self, parent=None):
        self.active = False
        self.parent = parent
        self.pos = None

    def draw(self):
        self.active = False
        self._ctrl_pos = None

    def printAt(self,pos,*args):
        if self._ctrl_pos is None:
            self._ctrl_pos = pos

        seq = Sequence(*args,term)
        if pos[1] == term.cursor.pos[1] and pos[0] <= term.cursor.pos[0] and term.cursor.pos[0] <= pos[0] + len(seq):
            term.cursor.on_element = self
            term.cursor.pos = self._ctrl_pos
        print(term.move_xy(pos)+seq)

    # pass event to parent if nothing happens
    def cursorAction(self, val):
        if self.parent is not None:
            self.parent.cursorAction(val)

class Line(UIElement):

    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.text = text
        self.height = 1

    def draw(self, pos, wrapper):
        super().draw()

        # ensure lines have correct width
        text = str(self.text)
        text = wrapper.wrap(text)
        self.height = len(text)

        # check what highlight it is
        highlight = lambda x: term.ljust(x,width=wrapper.width)
        if pos[1] <= term.cursor.pos[1] and term.cursor.pos[1] < pos[1]+len(text):
            highlight = lambda x: term.black_on_darkkhaki(term.ljust(x, width=wrapper.width))

        # print lines
        for i, t in enumerate(text):
            self.printAt(pos+(0,i),highlight(t))


class Window(UIElement):

    def __init__(self, pos, width, title, indent=4, parent=None):
        super().__init__(parent)
        self.pos = np.array(pos)
        self.width = width
        self.title = title
        self.lines = []
        self.wrapper = TextWrapper(width=width-2-WINDOW_PADDING*2, initial_indent="",subsequent_indent=" "*indent)

    def draw(self):
        super().draw()

        # first draw text
        content_height = 1
        for line in self.lines:
            line.draw(self.pos+(1+WINDOW_PADDING,content_height), self.wrapper)
            content_height += line.height
        content_height += 1

        # now draw border
        draw_window(self.pos, (self.width, content_height), self.title)

    def cursorAction(self, val):
        element = term.cursor.on_element

        if val.code == term.KEY_UP and element != self.lines[0]:
            term.cursor.pos += (0, -1)
        elif val.code == term.KEY_DOWN and element != self.lines[-1]:
            term.cursor.pos += (0,  element.height)
        else:
            return super().cursorAction(val)



