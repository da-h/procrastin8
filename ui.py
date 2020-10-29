from blessed import Terminal
from blessed.sequences import Sequence, SequenceTextWrapper as TextWrapper
import numpy as np

from settings import COLUMN_WIDTH, WINDOW_PADDING, TAG_HIDDEN, SUBTAG_HIDDEN
from model import Tag, Subtag, List, Modifier, ModifierDate

class Cursor:

    def __init__(self):
        self.pos = np.array((3,2))
        self.on_element = None
        self.last_position = (-1,-1)

    def moveTo(self, on_element):
        if self.on_element != on_element:
            old_elem = self.on_element
        self.on_element = self.on_element_current = on_element
        self.pos = self.on_element.pos
        self.on_element.onHoverEvent()
        return old_elem

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

    def finalize(self):
        pass
        # changed = any(self.last_position != self.pos)
        # self.last_position = np.copy(self.pos)
        # if changed:
        #     self.on_element = self.on_element_current
        #     self.moveTo(self.on_element)
        #     self.on_element.onHoverEvent()
        # return changed


class WorkitTerminal(Terminal):

    def __init__(self):
        super().__init__()
        self.cursor = Cursor()

    def move_xy(self, x, y=None):
        if type(x) is np.ndarray or isinstance(x, tuple):
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
        border += term.move_xy(pos+(0,i+1)) + "│ "
        border += term.move_xy(pos+(width-2,i+1)) + " │"
    border += term.move_xy(pos+(0,height-1)) + "└" + "─" * (width-2) + "┘"
    print(border)

    # set title
    if title is not None:
        print(term.move_xy(pos+(1+0,0)) + " %s " % term.bold(term.white(title)))

def draw_border2(pos, dim, title=None):
    pos = np.array(pos)
    dim = np.array(dim)
    width, height = dim

    # draw border
    border  = term.move_xy(pos) + " " + " " * (width-2) + "│"
    for i in range(height-2):
        border += term.move_xy(pos+(0,i+1)) + "  "
        border += term.move_xy(pos+(width-2,i+1)) + " │"
    border += term.move_xy(pos+(0,height-1)) + " " + " " * (width-2) + "│"
    print(border)

    # set title
    if title is not None:
        print(term.move_xy(pos+(1+0,0)) + " %s " % term.bold(term.white(title)))



class UIElement:
    def __init__(self, rel_pos=None, parent=None):
        if not rel_pos and not parent:
            raise ValueError("Either position or parent have to be specified")
        self.parent = parent
        self.elements = []
        self._rel_pos = np.array(rel_pos)
        self._last_rel_pos = np.copy(rel_pos)
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
            print(term.move_xy(key)+" "*len(Sequence(val, term)))
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
        if rel_pos not in self.last_print or self.last_print[rel_pos] != new_print:
            print(new_print)
            self.last_print[rel_pos] = new_print

    # pass event to parent if nothing happens
    def cursorAction(self, val):
        if self.parent is not None:
            self.parent.cursorAction(val)

    def onHoverEvent(self):
        pass
    def onElementClosed(self, elem):
        pass


class Line(UIElement):

    def __init__(self, text="", rel_pos=None, prepend="", wrapper=None, parent=None):
        super().__init__(rel_pos=rel_pos, parent=parent)
        self.text = text
        self.height = 1
        self.wrapper = wrapper
        self.prepend = prepend
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
            self.height = max(len(self._typeset_text),1)

    def draw(self, clean=False):
        super().draw(clean)

        # check what highlight it is
        highlight = lambda x: term.ljust(x,width=self.wrapper.width)
        if term.cursor.on_element == self:
            highlight = lambda x: term.bold_white(term.ljust(x, width=self.wrapper.width))

        # print lines
        for i, t in enumerate(self._typeset_text):
            self.printAt((0,i),self.prepend+highlight(t))


class HLine(UIElement):
    def __init__(self, text, wrapper, center=False, parent=None):
        super().__init__(parent=parent)
        self.wrapper = wrapper
        self.height = 2
        self.text = text
        self.center = center

    def typeset(self):
        pass

    def draw(self, clean=False):
        super().draw(clean)
        self.printAt((0,0),          " "*self.wrapper.width)
        self.printAt((0,1), term.dim+"─"*self.wrapper.width+term.normal)
        if self.text:
            if self.center:
                self.printAt((0,1), term.center(self.text, width=self.wrapper.width))
            else:
                self.printAt((0,1), self.text+" ")



class PlainWindow(UIElement):

    def __init__(self, rel_pos, width=1, height=1, title="", parent=None):
        super().__init__(rel_pos=rel_pos, parent=parent)
        self.width = width
        self.height = height
        self.title = title
        self.last_width = None
        self.last_height = None
        self.last_title = None
        self.draw_style = "basic"

    def draw(self, clean=False):
        super().draw(clean)
        if clean or self.last_width != self.width or self.last_height != self.height or self.last_title != self.title or any(self.last_pos != self.pos):
            if self.draw_style == "basic":
                draw_border(self.pos, (self.width, self.height), self.title)
            elif self.draw_style == "basic-left-edge":
                draw_border2(self.pos, (self.width, self.height), self.title)
            self.last_width = self.width
            self.last_height = self.height
            self.last_title = self.title
            self.last_pos = self.pos

    def clear(self):
        clean = ""
        for i in range(self.height):
            clean += term.move_xy(self.pos+(0,i)) + " "*self.width
        print(clean)
        super().clear()

    def close(self):
        self.clear()
        super().close()


class TextWindow(PlainWindow):

    def __init__(self, rel_pos, width, title, indent=2, parent=None):
        super().__init__(rel_pos=rel_pos, parent=parent)
        self.width = width
        self.indent = indent
        self.title = title
        self.lines = []
        self.wrapper = TextWrapper(width=width-2-WINDOW_PADDING*2, initial_indent="",subsequent_indent=" "*indent, term=term)
        self.height = 1

    def draw(self, clean=False):

        # calculate dynamic height
        # & position lines
        content_height = 1
        for line in self.lines:
            line.rel_pos = (1+WINDOW_PADDING,content_height)
            line.typeset()
            content_height += line.height
        content_height += 1

        # draw window
        self.height = content_height
        super().draw(clean)

        # draw text
        for line in self.lines:
            line.draw(clean)


    def cursorAction(self, val):
        element = term.cursor.on_element

        if val.code == term.KEY_UP and element != self.lines[0]:
            term.cursor.moveTo(self.lines[self.lines.index(element)-1])
        elif val.code == term.KEY_DOWN and element != self.lines[-1]:
            term.cursor.moveTo(self.lines[self.lines.index(element)+1])
        else:
            return super().cursorAction(val)

    def add_line(self, text, prepend=""):
        elem = Line(text, prepend=prepend, wrapper=self.wrapper, parent=self)
        self.lines.append(elem)
        self.manage(elem)

    def add_hline(self, text=""):
        elem = HLine(text, wrapper=self.wrapper, parent=self)
        self.lines.append(elem)
        self.manage(elem)

    def onHoverEvent(self):
        if len(self.lines):
            term.cursor.moveTo(self.lines[0])

class TaskWindow(TextWindow):

    def add_task(self, text, prepend=""):
        if prepend != "":
            wrapper = TextWrapper(width=self.width-2-WINDOW_PADDING*2, initial_indent="",subsequent_indent=" "*self.indent, term=term)
        elem = TaskLine(text, prepend=prepend, wrapper=self.wrapper, parent=self)
        self.lines.append(elem)
        self.manage(elem)


class CenteredWindow(TextWindow):

    def __init__(self, width, parent=None):
        rel_pos = ((term.width - width)//2,10)
        super().__init__(rel_pos, width=width, title="Settings", parent=parent)

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


class Sidebar(TextWindow):

    def __init__(self, width, parent=None):
        rel_pos = (0,0)
        super().__init__(rel_pos, width=width, title="Settings", parent=parent)
        self.draw_style = "basic-left-edge"

        self.add_line("Add")
        self.add_line("Remove")
        self.add_line("Tag")
        self.add_line("Lorem")
        self.add_line("Ipsum")

    def cursorAction(self, val):

        if val == "s":
            self.parent.rel_pos = (0,0)
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
                if not TAG_HIDDEN:
                    S.append(term.red(str(t)))
            elif isinstance(t, Subtag):
                if not SUBTAG_HIDDEN:
                    S.append(term.red(term.dim+str(t)))
            elif isinstance(t, List):
                S.append(term.bold(term.blue(str(t))))
            elif isinstance(t, Modifier):
                S.append(term.green(str(t)))
            elif isinstance(t, ModifierDate):
                S.append(term.green(str(t)))
            else:
                S.append(t)
        return " ".join([str(s) for s in S])+term.no_dim

    def cursorAction(self, val):
        if val == "x":
            self.text["complete"] = not self.text["complete"]
            self.text.save()
        super().cursorAction(val)



# ========= #
# Dashboard #
# ========= #

draw_calls = 0
def redraw():
    global draw_calls
    print(term.move_y(term.height - 4) + term.center('draw() calls: %i' % draw_calls).rstrip())
    print(term.move_y(term.height - 3) + term.center('cursor: '+str(term.cursor.pos)).rstrip())
    print(term.move_y(term.height - 2) + term.center('element: '+str(term.cursor.on_element) if term.cursor.on_element else "").rstrip())
    draw_calls += 1

class Dashboard(UIElement):

    def __init__(self, model):
        super().__init__((0,0))
        self.model = model
        self.overlay = None

    def draw(self, clean=False):
        for elem in self.elements:
            if elem != self.overlay:
                elem.draw(clean)
        if self.overlay:
            self.overlay.draw(True)
        term.cursor.finalize()
        redraw()

    def loop(self):
        val = ''
        while val.lower() != 'q':
            val = term.inkey()
            if val == "+":
                self.rel_pos += (4,3)
            elif val == "-":
                self.rel_pos += (-4,-3)
            elif val == "s" and self.overlay is None:
                # self.overlay = CenteredWindow(COLUMN_WIDTH, parent=self)
                self.overlay = Sidebar(COLUMN_WIDTH, parent=self)
                self.overlay.draw()
                self.rel_pos = (COLUMN_WIDTH,0)
                self.overlay.rel_pos = (-COLUMN_WIDTH,0)
                self.manage(self.overlay)
                old_elem = term.cursor.moveTo(self.overlay.lines[0])
                redraw()
            elif val and term.cursor.on_element:
                term.cursor.on_element.cursorAction(val)

            # self.clear()
            self.draw()

    def onHoverEvent(self):
        if len(self.elements):
            term.cursor.moveTo(self.elements[0])

    def onElementClosed(self, elem):
        self.elements.remove(elem)
        if elem == self.overlay:
            self.overlay = None
        self.draw(True)
        if term.cursor.isOnElement(elem):
            term.cursor.moveTo(self.elements[0])

