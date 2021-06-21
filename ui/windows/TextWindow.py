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
        self.lines = []
        self.content_lines = []
        self.wrapper = TextWrapper(width=width - self.padding[1] - self.padding[3] - WINDOW_PADDING * 2, initial_indent="", subsequent_indent=" " * indent, drop_whitespace=False, term=term)
        self.title = title
        self.overfull_mode = overfull_mode
        self.current_line = 0
        self.empty_lines = 0
        self.allow_cursor_on_title = False
        self.registerProperty("scroll_pos", 0, ["content", "border"])
        self.registerProperty("content_height", 0, ["window"])
        self.registerProperty("height", self.height, ["content"])
        self._el_changed = []
        self._size_changed = []

    async def draw(self):
        max_height = (self.max_height if self.max_height >= 1 else self.parent.height if self.parent else term.height)
        max_inner_height = max_height - self.padding[0] - self.padding[2]

        # re-typeset text (and redo all if height changes anywhere)
        for el in self._el_changed:
            height = el.height
            el.typeset()
            if el.height != height:
                self.element.remove("content")
                self._el_changed = []
                break

        # calculate dynamic height
        # & position lines
        # redraw_content = False
        if e := self.element("content"):
            with e:
                redraw_content = True
                content_height = 0
                for line in self.lines:
                    line.clear()
                    line.rel_pos = np.array((self.padding[3] + WINDOW_PADDING, content_height - self.scroll_pos + self.padding[0]))
                    line.typeset()
                    line.max_height = max(max_inner_height - content_height + self.scroll_pos, 0)
                    if line.rel_pos[1] < self.padding[1]:
                        line.max_height = 0
                    content_height += line.height
                self.content_height = content_height
                self.max_scroll = max(self.content_height - max_inner_height, 0)

        # draw window
        draw_args = {}
        if self.overfull_mode == OverfullMode.SCROLL:
            self.height = min(self.content_height + self.padding[0] + self.padding[2], max_height)
        if self.max_scroll != 0:
            if self.scroll_pos != 0:
                draw_args["top_line"] = "╴"
            if self.scroll_pos != self.max_scroll:
                draw_args["bottom_line"] = "╴"
        await super().draw(**draw_args)

        # draw scroll bar
        if e := self.element.drawn_recently["border"]:
            if self.content_height > max_inner_height:
                max_scroll = self.content_height - max_inner_height
                self.printAt((self.width-WINDOW_PADDING,int(self.scroll_pos/max_scroll*(max_inner_height-1))), term.yellow("┃") if self.active else "┃")

        # draw text
        for line in self.lines:
            await line.draw()

    async def onKeyPress(self, val):
        element = term.cursor.on_element
        max_height = (self.max_height if self.max_height >= 1 else self.parent.height if self.parent else term.height)
        max_inner_height = max_height - self.padding[0] - self.padding[2]

        if val.code == term.KEY_UP or val == 'k':
            if self.current_line == 0:
                await super().onKeyPress(val)
                return

            self.current_line -= 1
            focus_on = self.content_lines[self.current_line]
            await term.cursor.moveTo(focus_on)
            if focus_on.rel_pos[1] < self.padding[1]:
                await self.scroll(max(self.scroll_pos + focus_on.rel_pos[1] - self.padding[1], 0))
        elif val.code == term.KEY_DOWN or val == 'j':
            if self.current_line == len(self.content_lines) - 1:
                await super().onKeyPress(val)
                return

            self.current_line += 1
            focus_on = self.content_lines[self.current_line]
            await term.cursor.moveTo(focus_on)
            if focus_on.rel_pos[1] > max_inner_height:# - focus_on.height:
                await self.scroll(self.scroll_pos + focus_on.rel_pos[1] - element.rel_pos[1] + focus_on.height - 1)
        elif val.code == term.KEY_HOME:
            self.current_line = 0
            await term.cursor.moveTo(self.content_lines[self.current_line])
            return
        elif val.code == term.KEY_END:
            self.current_line = len(self.content_lines)-1
            await term.cursor.moveTo(self.content_lines[self.current_line])
            return
        elif val == term.KEY_CTRL['e']:
            await self.scroll(max(self.scroll_pos - 1, 0))
        elif val == term.KEY_CTRL['y']:
            if self.content_lines[-1].rel_pos[1] > max_inner_height:
                await self.scroll(self.scroll_pos + 1)
        else:
            await super().onKeyPress(val)

    def add_line(self, text, prepend=""):
        if isinstance(text, str):
            if prepend != "":
                wrapper = TextWrapper(width=self.width - self.padding[1] - self.padding[3] - WINDOW_PADDING * 2 - len(prepend), initial_indent="", subsequent_indent=" " * self.indent, drop_whitespace=False, term=term)
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
        self.empty_lines += 1
        self.add_line("")

    async def onContentChange(self, child_src, el_changed):
        if isinstance(child_src, Line):
            self._el_changed.append(child_src)
        await super().onContentChange(child_src, el_changed)
    async def onSizeChange(self, child_src, el_changed):
        self._size_changed.append(child_src)
        await super().onSizeChange(child_src, el_changed)

    async def onFocus(self):
        if len(self.content_lines):
            self.current_line = max(min(len(self.content_lines)-1, self.current_line),0)
            await term.cursor.moveTo(self.content_lines[self.current_line])

    async def scroll(self, pos):
        self.clear("content")
        self.clear("window")
        self.scroll_pos = pos
