from blessed import Terminal
from blessed.sequences import Sequence, SequenceTextWrapper as TextWrapper
import numpy as np

from settings import COLUMN_WIDTH, WINDOW_PADDING
from model import Tag, List, Modifier, ModifierDate

class Cursor:

    def __init__(self):
        self.pos = np.array((3,2))

    def moveTo(self, on_element):
        self.on_element = on_element
        self.pos = self.on_element._ctrl_pos

    def clear(self):
        self.on_element = None

    def draw(self):
        pass
        # print(term.move_xy(self.pos)+"_")


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
        print(term.move_xy(pos+(1+0,0)) + " %s " % term.bold(term.white(title)))


class UIElement:
    def __init__(self, parent=None):
        self.active = False
        self.parent = parent
        self.pos = None
        self._ctrl_pos = None

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

    def formatText(self):
        return str(self.text)

    def draw(self, pos, wrapper):
        super().draw()

        # ensure lines have correct width
        text = wrapper.wrap(self.formatText())
        self.height = len(text)

        # check what highlight it is
        highlight = lambda x: term.ljust(x,width=wrapper.width)
        if pos[1] <= term.cursor.pos[1] and term.cursor.pos[1] < pos[1]+len(text):
            highlight = lambda x: term.bold_white(term.ljust(x, width=wrapper.width))

        # print lines
        for i, t in enumerate(text):
            self.printAt(pos+(0,i),highlight(t))


class TextWindow(UIElement):

    def __init__(self, pos, width, title, indent=2, parent=None):
        super().__init__(parent)
        self.pos = np.array(pos)
        self.width = width
        self.title = title
        self.lines = []
        self.wrapper = TextWrapper(width=width-2-WINDOW_PADDING*2, initial_indent="",subsequent_indent=" "*indent, term=term)
        self.height = 1

    def draw(self):
        super().draw()

        # first draw text
        content_height = 1
        for line in self.lines:
            line.draw(self.pos+(1+WINDOW_PADDING,content_height), self.wrapper)
            content_height += line.height
        content_height += 1
        self.height = content_height

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


class SettingsWindow(TextWindow):

    def __init__(self, width, parent=None):
        pos = ((term.width - width)//2,10)
        super().__init__(pos, width=width, title="Settings", parent=parent)

    # def cursorAction(self, val):
    #     element = term.cursor.on_element
    #
    #     if val.code == term.KEY_UP and element != self.lines[0]:
    #         term.cursor.pos += (0, -1)
    #     elif val.code == term.KEY_DOWN and element != self.lines[-1]:
    #         term.cursor.pos += (0,  element.height)
    #     else:
    #         return super().cursorAction(val)




# ============= #
# Todo Specific #
# ============= #

class TaskLine(Line):

    def formatText(self):
        S = []
        if self.text["complete"]:
            S.append("✗")
        else:
            S.append("·")
        if self.text["priority"] != "M_":
            S.append("(%s)" % self.text["priority"])
        if self.text["completion-date"]:
            S.append(term.bright_white(str(self.text["completion-date"])))
        if self.text["creation-date"]:
            S.append(term.dim+(str(self.text["creation-date"]))+term.normal)
        for t in self.text["text"]:
            if isinstance(t, Tag):
                S.append(term.red(str(t)))
            elif isinstance(t, List):
                S.append(term.bold(term.blue(str(t))))
            elif isinstance(t, Modifier):
                S.append(term.green(str(t)))
            elif isinstance(t, ModifierDate):
                S.append(term.green(str(t)))
            else:
                S.append(t)
        return " ".join([str(s) for s in S])+term.no_dim



