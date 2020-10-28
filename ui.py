from blessed import Terminal
from blessed.sequences import Sequence, SequenceTextWrapper as TextWrapper
import numpy as np

from settings import COLUMN_WIDTH, WINDOW_PADDING
from model import Tag, List, Modifier, ModifierDate

class Cursor:

    def __init__(self):
        self.pos = np.array((3,2))
        self.on_element = None
        self.last_position = (-1,-1)

    def moveTo(self, on_element):
        self.on_element = on_element
        self.pos = self.on_element.pos

    def clear(self):
        self.on_element = None

    def finalize(self):
        changed = any(self.last_position != self.pos)
        self.last_position = np.copy(self.pos)
        if changed:
            self.on_element = self.on_element_current
            self.on_element.onHoverEvent()
            self.moveTo(self.on_element)
            term.redraw = True
        return changed
            # if term.cursor.changedPosition() and term.cursor.on_element != self:
            #     term.cursor.on_element = self
            #     self.onHoverEvent()
            #     term.cursor.pos = self.pos


class WorkitTerminal(Terminal):

    def __init__(self):
        super().__init__()
        self.cursor = Cursor()
        self.redraw = True

    def move_xy(self, x, y=None):
        if type(x) is np.ndarray:
            return super().move_xy(x[0],x[1])
        return super().move_xy(x,y)


term = WorkitTerminal()






# ======== #
# basic ui #
# ======== #

def draw_border(pos, dim, title=None):
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
    def __init__(self, pos=None, parent=None):
        if not pos and not parent:
            raise ValueError("Either position or parent have to be specified")
        self.parent = parent
        self.pos = pos
        self.last_print = {}

    def draw(self):
        pass

    def close(self):
        for key, val in self.last_print.items():
            print(term.move_xy(key)+" "*len(Sequence(val)))

    def printAt(self, rel_pos, *args):
        seq = Sequence(*args,term)
        pos = self.pos + rel_pos
        if pos[1] == term.cursor.pos[1] and pos[0] <= term.cursor.pos[0] and term.cursor.pos[0] < pos[0] + len(seq):
            term.cursor.on_element_current = self

        new_print = term.move_xy(pos)+seq
        if rel_pos not in self.last_print or self.last_print[rel_pos] != new_print:
            print(new_print)
            self.last_print[rel_pos] = new_print

    # pass event to parent if nothing happens
    def cursorAction(self, val):
        if self.parent is not None:
            self.parent.cursorAction(val)

    def onHoverEvent(self):
        pass


class Line(UIElement):

    def __init__(self, text, pos=None, wrapper=None, parent=None):
        super().__init__(pos, parent)
        self.text = text
        self.height = 1
        self.wrapper = wrapper
        self._typeset_text = None

    def formatText(self):
        return str(self.text)

    # ensure lines have correct width
    def typeset(self):
        if self.wrapper is None:
            self._typeset_text = self.text
            self.height = 1
        else:
            self._typeset_text = self.wrapper.wrap(self.formatText())
            self.height = len(self._typeset_text)

    def draw(self):
        super().draw()

        # check what highlight it is
        highlight = lambda x: term.ljust(x,width=self.wrapper.width)
        # if self.pos[1] <= term.cursor.pos[1] and term.cursor.pos[1] < self.pos[1]+self.height:
        if term.cursor.on_element == self:
            highlight = lambda x: term.bold_white(term.ljust(x, width=self.wrapper.width))

        # print lines
        for i, t in enumerate(self._typeset_text):
            self.printAt((0,i),highlight(t))

    def onHoverEvent(self):
        term.redraw = True

class PlainWindow(UIElement):

    def __init__(self, pos, width=1, height=1, title="", parent=None):
        super().__init__(pos, parent)
        self.width = width
        self.height = height
        self.title = title
        self.last_width = None
        self.last_height = None
        self.last_title = None

    def draw(self):
        if self.last_width != self.width or self.height != self.height or self.title != self.title:
            draw_border(self.pos, (self.width, self.height), self.title)
            self.last_width = self.width
            self.last_height = self.height
            self.last_title = self.title

    def close(self):
        clean  = term.move_xy(self.pos) + " " + " " * (self.width-2) + " "
        for i in range(self.height-2):
            clean += term.move_xy(self.pos+(0,i+1)) + " "*self.width
        clean += term.move_xy(self.pos+(0,self.height-1)) + " " + " " * (self.width-2) + " "
        print(clean)
        term.redraw = True



class TextWindow(PlainWindow):

    def __init__(self, pos, width, title, indent=2, parent=None):
        super().__init__(pos, parent)
        self.pos = np.array(pos)
        self.width = width
        self.title = title
        self.lines = []
        self.wrapper = TextWrapper(width=width-2-WINDOW_PADDING*2, initial_indent="",subsequent_indent=" "*indent, term=term)
        self.height = 1

    def draw(self):

        # calculate dynamic height
        # & position lines
        content_height = 1
        for line in self.lines:
            line.pos = self.pos+(1+WINDOW_PADDING,content_height)
            line.typeset()
            content_height += line.height
        content_height += 1

        # draw window
        self.height = content_height
        super().draw()

        # draw text
        for line in self.lines:
            line.draw()


    def cursorAction(self, val):
        element = term.cursor.on_element

        if val.code == term.KEY_UP and element != self.lines[0]:
            term.cursor.pos += (0, -1)
            term.redraw = True
        elif val.code == term.KEY_DOWN and element != self.lines[-1]:
            term.cursor.pos += (0,  element.height)
            term.redraw = True
        else:
            return super().cursorAction(val)

    def add_line(self, text):
        self.lines.append( Line(text, wrapper=self.wrapper, parent=self) )


class TaskWindow(TextWindow):

    def add_line(self, text):
        self.lines.append( TaskLine(text, wrapper=self.wrapper, parent=self) )


class SettingsWindow(TextWindow):

    def __init__(self, width, parent=None):
        pos = ((term.width - width)//2,10)
        super().__init__(pos, width=width, title="Settings", parent=parent)

        self.add_line("Add")
        self.add_line("Remove")
        self.add_line("Tag")
        self.add_line("Lorem")
        self.add_line("Ipsum")

    def cursorAction(self, val):

        if val == "s":
            self.close()
            return

        return super().cursorAction(val)




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



