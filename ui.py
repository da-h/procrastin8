from blessed.sequences import Sequence, SequenceTextWrapper as TextWrapper
import numpy as np

from settings import COLUMN_WIDTH, WINDOW_PADDING, TAG_HIDDEN, SUBTAG_HIDDEN, DIM_COMPLETE
from model import Tag, Subtag, List, Modifier, ModifierDate
from uiutil import WorkitTerminal


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


class Line(UIElement):

    def __init__(self, text="", rel_pos=None, prepend="", wrapper=None, parent=None):
        super().__init__(rel_pos=rel_pos, parent=parent)
        self.text = text
        self.height = 1
        self.wrapper = wrapper
        self.prepend = prepend
        self.edit_mode = False
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

    def set_editmode(self, mode: bool):
        self.edit_mode = mode
        if self.edit_mode:
            print(term.normal_cursor, end='')
        else:
            print(term.hide_cursor, end='')

    def onKeyPress(self, val):
        if self.edit_mode:
            if val.code == term.KEY_ESCAPE:
                self.set_editmode(False)
            else:
                self.onEditModeKey(val)
            return
        return super().onKeyPress(val)

    def onEditModeKey(self, val):
        pass

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


class RadioLine(UIElement):
    def __init__(self, text, choices, wrapper, parent=None):
        super().__init__(parent=parent)
        self.height = 2
        self.text = text
        self.choices = choices
        self.wrapper = wrapper
        self.active = 0

    def typeset(self):
        pass

    def draw(self, clean=False):
        super().draw(clean)
        # check what highlight it is
        highlight = lambda x: term.ljust(x,width=self.wrapper.width)
        if term.cursor.on_element == self:
            highlight = lambda x: term.bold_green(term.ljust(x, width=self.wrapper.width))

        self.printAt((0,0), highlight(self.text))
        # self.printAt((3,1), highlight("".join("◢" + term.black_on_white(c) + "◤" if i == self.active else c for i, c in enumerate(self.choices))))

        choice = [term.black_on_green(" "+c+" ") if i == self.active else " "+c+" " for i, c in enumerate(self.choices)]
        choice[self.active] = term.green("◢") + choice[self.active] + term.green("◤")
        choice_text = term.green(term.bold("/")).join(choice[:self.active]) + choice[self.active] + term.green(term.bold("/")).join(choice[self.active+1:])
        if self.active != 0:
            choice_text = " "+choice_text
        if self.active != len(choice):
            choice_text += " "
        self.printAt((3,1), choice_text)

    def onKeyPress(self, val):
        if val.code == term.KEY_LEFT:
            self.active = (self.active - 1) % len(self.choices)
            return
        elif val.code == term.KEY_RIGHT:
            self.active = (self.active + 1) % len(self.choices)
            return
        return super().onKeyPress(val)




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

    def onKeyPress(self, val):
        element = term.cursor.on_element
        non_empty_lines = list(filter(lambda l: l.text, self.lines))

        if val.code == term.KEY_UP:
            index = non_empty_lines.index(element)
            if index > 0:
                term.cursor.moveTo(non_empty_lines[index-1])
        elif val.code == term.KEY_DOWN:
            index = non_empty_lines.index(element)
            if index < len(non_empty_lines)-1:
                term.cursor.moveTo(non_empty_lines[index+1])
        else:
            return super().onKeyPress(val)

    def add_line(self, text, prepend=""):
        if prepend != "":
            wrapper = TextWrapper(width=self.width-2-WINDOW_PADDING*2-len(prepend), initial_indent="",subsequent_indent=" "*self.indent, term=term)
        else:
            wrapper = self.wrapper
        elem = Line(text, prepend=prepend, wrapper=wrapper, parent=self)
        self.lines.append(elem)
        self.manage(elem)

    def add_hline(self, text=""):
        elem = HLine(text, wrapper=self.wrapper, parent=self)
        self.lines.append(elem)
        self.manage(elem)

    def add_emptyline(self):
        self.add_line("")

    def onFocus(self):
        if len(self.lines):
            term.cursor.moveTo(self.lines[0])

class TaskWindow(TextWindow):

    def add_task(self, text, prepend=""):
        if prepend != "":
            wrapper = TextWrapper(width=self.width-2-WINDOW_PADDING*2-len(prepend), initial_indent="",subsequent_indent=" "*self.indent, term=term)
        else:
            wrapper = self.wrapper
        elem = TaskLine(text, prepend=prepend, wrapper=wrapper, parent=self)
        self.lines.append(elem)
        self.manage(elem)


class Prompt(TextWindow):

    def __init__(self, width, parent=None):
        rel_pos = ((term.width - width)//2,10)
        super().__init__(rel_pos, width=width, title="Settings", parent=parent)

        self.add_line("Add")
        self.add_line("Remove")
        self.add_line("Tag")
        self.add_line("Lorem")
        self.add_line("Ipsum")

    def onKeyPress(self, val):

        if val == "s":
            self.close()
            return

        return super().onKeyPress(val)


class Sidebar(TextWindow):

    def __init__(self, width, parent=None):
        rel_pos = (0,0)
        super().__init__(rel_pos, width=width, title="Settings", parent=parent)
        self.draw_style = "basic-left-edge"

        self.lines.append(RadioLine("Verbosity",["Small","Medium","Full"], wrapper=self.wrapper, parent=self))
        self.manage(self.lines[-1])
        self.lines.append(RadioLine("Verbosity",["Small","Medium","Full"], wrapper=self.wrapper, parent=self))
        self.manage(self.lines[-1])
        self.lines.append(RadioLine("Verbosity",["Small","Medium","Full"], wrapper=self.wrapper, parent=self))
        self.manage(self.lines[-1])

    def onKeyPress(self, val):

        if val == "s":
            self.parent.rel_pos = (0,0)
            self.close()
            return

        return super().onKeyPress(val)





# ============= #
# Todo Specific #
# ============= #

class TaskLine(Line):

    def formatText(self):
        S = []
        if self.text["complete"]:
            S.append(term.green("✗")+(term.dim if DIM_COMPLETE else ""))
        else:
            S.append(term.blue("·"))
        if self.text["priority"] != "M_":
            S.append("(%s)" % self.text["priority"])
        if self.text["completion-date"]:
            S.append(term.bright_white(str(self.text["completion-date"])))
        if self.text["creation-date"]:
            S.append(term.dim+(str(self.text["creation-date"]))+term.normal)

        SText = []
        for text_i, t in enumerate(self.text["text"]):
            tstr = str(t)
            if text_i != len(self.text["text"]):
                tstr += " "
            if self.edit_mode and self.text_i == text_i:
                # breakpoint()
                tstr = tstr[:self.text_charpos] + term.black_on_white(tstr[self.text_charpos]) + tstr[self.text_charpos+1:]

            if isinstance(t, Tag):
                if not TAG_HIDDEN or self.edit_mode:
                    SText.append(term.red(tstr))
            elif isinstance(t, Subtag):
                if not SUBTAG_HIDDEN or self.edit_mode:
                    SText.append(term.red(term.dim+tstr))
            elif isinstance(t, List):
                SText.append(term.bold(term.blue(tstr)))
            elif isinstance(t, Modifier):
                SText.append(term.green(tstr))
            elif isinstance(t, ModifierDate):
                SText.append(term.green(tstr))
            else:
                SText.append(tstr)
        return " ".join([str(s) for s in S])+" "+"".join(SText)+term.normal

    def onKeyPress(self, val):
        if val == "x":
            self.text["complete"] = not self.text["complete"]
            self.text.save()
        elif val == "i" or val == "e":
            self.set_editmode(True)
            self.text_i = 0
            self.charpos = 0
            self._update_charPos()
        elif val == "I":
            self.set_editmode(True)
            self.text_i = 0
            self.charpos = 0
            self._update_charPos()
        elif val == "A":
            self.set_editmode(True)
            self.text_i = 0
            self.charpos = len(str(self.text)) - 1
            self._update_charPos()
        elif self.edit_mode:
            if val.code == term.KEY_RIGHT:
                self.charpos = min(self.charpos+1,len(str(self.text))-1)
                self._update_charPos()
            elif val.code == term.KEY_LEFT:
                self.charpos = max(self.charpos-1,0)
                self._update_charPos()
            elif not val.is_sequence:
                self.text["text"][self.text_i] = self.text["text"][self.text_i][:self.text_charpos] + str(val) + self.text["text"][self.text_i][self.text_charpos:]
                # TODO
                # self.text.save()
        super().onKeyPress(val)

    def _update_charPos(self):
        text_i = 0
        text_charpos = self.charpos
        # breakpoint()
        while text_i < len(self.text["text"]) and text_charpos >= len(self.text["text"][text_i]):
            text_charpos -= len(self.text["text"][text_i])
            text_i += 1
            text_charpos -= 1

        # normalize
        if text_charpos < 0 and text_i >= len(self.text["text"]):
            text_i = len(self.text["text"]) - 1
            text_charpos = len(self.text["text"][text_i])
        elif text_charpos < 0:# and text_i >= len(self.text["text"]):
            text_i -= 1
            text_charpos = len(self.text["text"][text_i])

        self.text_charpos, self.text_i = text_charpos, text_i

    def onEditModeKey(self, val):
        if val.is_sequence:
            return

        # rel_pos = term.cursor.relativePos()
        # self.charpos = self.wrapper.width * rel_pos[1] + rel_pos[0]




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
        self.continue_loop = True

    def draw(self, clean=False):
        with term.location():
            for elem in self.elements:
                if elem != self.overlay:
                    elem.draw(clean)
            if self.overlay:
                self.overlay.draw(True)
            term.cursor.finalize()
        redraw()

    def loop(self):
        val = ''
        while self.continue_loop:
            val = term.inkey()
            if val and term.cursor.on_element:
                term.cursor.on_element.onKeyPress(val)

            # self.clear()
            self.draw()

    def onFocus(self):
        if len(self.elements):
            term.cursor.moveTo(self.elements[0])

    def onElementClosed(self, elem):
        self.elements.remove(elem)
        if elem == self.overlay:
            self.overlay = None
        self.draw(True)
        if term.cursor.isOnElement(elem):
            term.cursor.moveTo(self.elements[0])

    def onKeyPress(self, val):
        if val == "q":
            self.continue_loop = False
            return
        elif val == "+":
            self.rel_pos += (4,3)
            return
        elif val == "-":
            self.rel_pos += (-4,-3)
            return
        elif val == "s" and self.overlay is None:
            # self.overlay = Prompt(COLUMN_WIDTH, parent=self)
            self.overlay = Sidebar(COLUMN_WIDTH, parent=self)
            self.overlay.draw()
            self.rel_pos = (COLUMN_WIDTH,0)
            self.overlay.rel_pos = (-COLUMN_WIDTH,0)
            self.manage(self.overlay)
            old_elem = term.cursor.moveTo(self.overlay.lines[0])
            redraw()
            return
        return super().onKeyPress(val)
