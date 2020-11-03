from ui.windows.Window import Window
from ui.lines.Line import Line
from ui.lines.HLine import HLine
from blessed.sequences import SequenceTextWrapper as TextWrapper
from settings import WINDOW_PADDING
from ui import get_term
term = get_term()


class TextWindow(Window):

    def __init__(self, rel_pos, width, title, indent=2, parent=None):
        super().__init__(rel_pos=rel_pos, parent=parent)
        self.width = width
        self.indent = indent
        self.title = title
        self.lines = []
        self.wrapper = TextWrapper(width=width - 2 - WINDOW_PADDING * 2, initial_indent="", subsequent_indent=" " * indent, term=term)
        self.height = 1

    def draw(self, clean=False):

        # calculate dynamic height
        # & position lines
        content_height = 1
        for line in self.lines:
            line.rel_pos = (1 + WINDOW_PADDING, content_height)
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

        if val.code == term.KEY_UP or val == 'k':
            index = non_empty_lines.index(element)
            if index > 0:
                term.cursor.moveTo(non_empty_lines[index - 1])
        elif val.code == term.KEY_DOWN or val == 'j':
            index = non_empty_lines.index(element)
            if index < len(non_empty_lines) - 1:
                term.cursor.moveTo(non_empty_lines[index + 1])
        else:
            super().onKeyPress(val)

    def add_line(self, text, prepend=""):
        if prepend != "":
            wrapper = TextWrapper(width=self.width - 2 - WINDOW_PADDING * 2 - len(prepend), initial_indent="", subsequent_indent=" " * self.indent, term=term)
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
