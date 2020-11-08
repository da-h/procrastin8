import numpy as np
from ui.windows.Window import Window
from ui.lines.Line import Line
from ui.lines.HLine import HLine
from blessed.sequences import SequenceTextWrapper as TextWrapper
from settings import WINDOW_PADDING
from ui import get_term
from enum import Enum
term = get_term()

class OverfullMode(Enum):
    SCROLL = 1


class TextWindow(Window):

    def __init__(self, rel_pos, width, title, indent=2, parent=None, overfull_mode=OverfullMode.SCROLL, padding=(1,1,1,1), max_height=-1):
        super().__init__(rel_pos=rel_pos, parent=parent, padding=padding, max_height=max_height)
        self.width = width
        self.height = 1
        self.indent = indent
        self.title = title
        self.lines = []
        self.content_lines = []
        self.wrapper = TextWrapper(width=width - self.padding[1] - self.padding[3] - WINDOW_PADDING * 2, initial_indent="", subsequent_indent=" " * indent, term=term)
        self.overfull_mode = overfull_mode
        self.scroll_pos = 0
        self.current_line = 0

    def draw(self):
        max_height = (self.max_height if self.max_height >= 1 else self.parent.height if self.parent else term.height) - self.rel_pos[1]
        max_inner_height = max_height - self.padding[0] - self.padding[2]

        # calculate dynamic height
        # & position lines
        content_height = 0
        for line in self.lines:
            line.rel_pos = np.array((self.padding[3] + WINDOW_PADDING, content_height - self.scroll_pos + self.padding[0]))
            line.typeset()
            line.max_height = max(max_inner_height - content_height + self.scroll_pos, 0)
            if line.rel_pos[1] < self.padding[1]:
                line.max_height = 0
            content_height += line.height

        # draw window
        if self.overfull_mode == OverfullMode.SCROLL:
            self.height = min(content_height + self.padding[0] + self.padding[2], max_height)
        super().draw()

        # draw text
        for line in self.lines:
            line.draw()

    def onKeyPress(self, val):
        element = term.cursor.on_element
        max_height = (self.max_height if self.max_height >= 1 else self.parent.height if self.parent else term.height) - self.rel_pos[1]
        max_inner_height = max_height - self.padding[0] - self.padding[2]

        if val.code == term.KEY_UP or val == 'k':
            if self.current_line == 0:
                return
            elif self.current_line is None:
                term.cursor.moveTo(self.content_lines[self.current_line])

            self.current_line -= 1
            focus_on = self.content_lines[self.current_line]
            term.cursor.moveTo(focus_on)
            if focus_on.rel_pos[1] < self.padding[1]:
                self.scroll_pos = max(self.scroll_pos + focus_on.rel_pos[1] - self.padding[1], 0)
        elif val.code == term.KEY_DOWN or val == 'j':
            if self.current_line == len(self.content_lines) - 1:
                return
            elif self.current_line is None:
                term.cursor.moveTo(self.content_lines[self.current_line])

            self.current_line += 1
            focus_on = self.content_lines[self.current_line]
            term.cursor.moveTo(focus_on)
            if focus_on.rel_pos[1] > max_inner_height:# - focus_on.height:
                self.scroll_pos += focus_on.rel_pos[1] - element.rel_pos[1] + focus_on.height - 1
        elif val.code == term.KEY_HOME:
            self.current_line = 0
            term.cursor.moveTo(self.content_lines[self.current_line])
            return
        elif val.code == term.KEY_END:
            self.current_line = len(self.content_lines)-1
            term.cursor.moveTo(self.content_lines[self.current_line])
            return
        elif val == term.KEY_CTRL['e']:
            self.scroll_pos = max(self.scroll_pos - 1, 0)
        elif val == term.KEY_CTRL['y']:
            if self.content_lines[-1].rel_pos[1] > max_inner_height:
                self.scroll_pos = self.scroll_pos + 1
        else:
            super().onKeyPress(val)

    def add_line(self, text, prepend=""):
        if isinstance(text, str):
            if prepend != "":
                wrapper = TextWrapper(width=self.width - self.padding[1] - self.padding[3] - WINDOW_PADDING * 2 - len(prepend), initial_indent="", subsequent_indent=" " * self.indent, term=term)
            else:
                wrapper = self.wrapper
            elem = Line(text, prepend=prepend, wrapper=wrapper, parent=self)
        else:
            elem = text
        self.lines.append(elem)
        if not isinstance(text, str) or text:
            self.content_lines.append(elem)

    def add_hline(self, text="", center=False):
        elem = HLine(text, wrapper=self.wrapper, center=center, parent=self)
        self.lines.append(elem)
        self.content_lines.append(elem)

    def add_emptyline(self):
        self.add_line("")

    def onFocus(self):
        if len(self.content_lines):
            self.current_line = max(min(len(self.content_lines)-1, self.current_line),0)
            term.cursor.moveTo(self.content_lines[self.current_line])
