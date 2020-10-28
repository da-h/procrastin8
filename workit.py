from blessed import Terminal
from blessed.sequences import Sequence
import numpy as np
from textwrap import TextWrapper

COLUMN_WIDTH = 40
term = Terminal()

class Cursor:

    def __init__(self):
        self.pos = np.array((3,2))
        self.on_element = None

    def clear(self):
        self.on_element = None

    def draw(self):
        print(term.move_xy(self.pos)+"_")


cursor = Cursor()


todo = """
2019-01-27 Review @iflow +planing rec:3m due:2019-04-27 t:2019-04-27
(C) 2018-11-02 Universal Correspondence Network +iFlow @papers
(D) 2017-07-21 Universal Programming +iFlow @papers
(D) 2018-11-02 Joshua Tennbaum A Rational Analysis of Rule-based Concept Learning +iFlow @papers
2019-08-19 kanban note Weight gradients by histogram @iflow +infn
2020-10-03 Tidy up kanban +planing @iflow
2020-10-03 Move entval todos to kanban +planing @iflow
2020-10-03 move notes from scribble to kanban +planing @iflow
2020-10-08 Check fanstanstic 3 channel for related work and todos +entval @iflow
2020-07-12 kanban note Relaxation for big Vektors. Instead of having 1000000 weights, use 100 times 20 weights (to have a distribution over combinations) +planing @iflow
2020-10-08 Check information flow channel for related work +entval @iflow
2020-10-06 Go through informationflow channel for relatedwork +entval @iflow
2020-10-08 One Paper read @iflow rec:1b t:2020-10-09
2020-10-03 Clear iflow code from Saturn +oldcode @iflow
2020-10-03 Clear iflow code from sirius +oldcode @iflow
""".strip()


# ====== #
# helper #
# ====== #

term_move_xy = term.move_xy
def move_xy(x,y=None):
    if type(x) is np.ndarray:
        return term_move_xy(x[0],x[1])
    return term_move_xy(x,y)
term.move_xy = move_xy

wrapper = TextWrapper(width=COLUMN_WIDTH,initial_indent="",subsequent_indent="   ")


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
        if pos[1] == cursor.pos[1] and pos[0] <= cursor.pos[0] and cursor.pos[0] <= pos[0] + len(seq):
            cursor.on_element = self
            cursor.pos = self._ctrl_pos
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
        text = wrapper.wrap(self.text)
        self.height = len(text)

        # check what highlight it is
        highlight = lambda x: term.ljust(x,width=wrapper.width)
        if pos[1] <= cursor.pos[1] and cursor.pos[1] < pos[1]+len(text):
            highlight = lambda x: term.black_on_darkkhaki(term.ljust(x, width=wrapper.width))
            # cursor.active_line = self

        # print lines
        for i, t in enumerate(text):
            self.printAt(pos+(0,i),highlight(t))


WINDOW_PADDING = 1
class Window(UIElement):

    def __init__(self, pos, width, title, indent=4, parent=None):
        super().__init__(parent)
        self.pos = np.array(pos)
        self.width = width
        self.title = title
        self.lines = [Line(l,parent=self) for l in todo.split("\n")]
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
        element = cursor.on_element

        if val.code == term.KEY_UP and element != self.lines[0]:
            cursor.pos += (0, -1)
        elif val.code == term.KEY_DOWN and element != self.lines[-1]:
            cursor.pos += (0,  element.height)
        else:
            return super().cursorAction(val)



with term.fullscreen(), term.cbreak(), term.hidden_cursor():
    print(term.move_y(term.height // 2) + term.center('press any key').rstrip())

    win = Window((1,1),COLUMN_WIDTH, "title")
    win.draw()

    # set cursor position
    val = ''
    while val.lower() != 'q':
        val = term.inkey(timeout=3)
        if val:
            cursor.on_element.cursorAction(val)

        cursor.clear()

        win.draw()
        cursor.draw()
