import numpy as np
from ui.windows.Window import Window
from ui.lines.Line import Line
from ui.lines.HLine import HLine
from blessed.sequences import SequenceTextWrapper as TextWrapper
from settings import Settings
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
        self.wrapper = TextWrapper(width=width - self.padding[1] - self.padding[3] - Settings.get('appearance.window_padding') * 2, initial_indent="", subsequent_indent=" " * indent, drop_whitespace=False, term=term)
        self.title = title
        self.overfull_mode = overfull_mode
        self.current_line = 0
        self.empty_lines = 0
        self.registerProperty("scroll_pos", 0, ["content", "border", "scroll_indicator"], instant_draw=False)
        self.registerProperty("content_height", 0, ["window"])
        self.registerProperty("height", self.height, ["content"])
        self._el_changed = []
        self._size_changed = []

    async def draw(self):
        max_height = (self.max_height if self.max_height >= 1 else self.parent.height if self.parent else term.height)
        self.max_inner_height = max_height - self.padding[0] - self.padding[2]

        # re-typeset text (and redo all if height changes anywhere)
        for el in self._el_changed:
            height = el.height
            el.typeset()
            if el.height != height:
                self.clear("content")
                self._el_changed = []
                break

        # calculate dynamic height
        # & position lines
        # redraw_content = False
        if el := self.element("content"):
            redraw_content = True
            content_height = 0
            self.line_cum_heights = []
            for line in self.lines:
                line.clear()
                line.rel_pos = np.array((self.padding[3] + Settings.get('appearance.window_padding'), content_height - self.scroll_pos + self.padding[0]))
                line.typeset()
                line.max_height = max(self.max_inner_height - content_height + self.scroll_pos, 0)
                if line.rel_pos[1] < self.padding[1]:
                    line.max_height = 0
                content_height += line.height
                self.line_cum_heights.append(content_height)
            self.content_height = content_height
            self.max_scroll = max(self.content_height - self.max_inner_height, 0)

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
        if el := self.element("scroll_indicator"):
            if self.content_height > self.max_inner_height:
                max_scroll = self.content_height - self.max_inner_height
                el.printAt((self.width-Settings.get('appearance.window_padding'),int(self.scroll_pos/max_scroll*(self.max_inner_height-1))), term.yellow("┃") if self.active else "┃")

        # draw text
        # for line in self.lines:
        #     await line.draw()

    async def onKeyPress(self, val, orig_src=None, child_src=None):
        element = term.cursor.on_element
        max_height = (self.max_height if self.max_height >= 1 else self.parent.height if self.parent else term.height)
        if val.code == term.KEY_UP or val == 'k':
            if self.current_line == 0:
                await super().onKeyPress(val)
                return
            await term.cursor.moveTo(self.content_lines[self.current_line - 1])

        elif val.code == term.KEY_DOWN or val == 'j':
            if self.current_line == len(self.content_lines) - 1:
                await super().onKeyPress(val)
                return
            await term.cursor.moveTo(self.content_lines[self.current_line + 1])

        elif val.code == term.KEY_HOME:
            await term.cursor.moveTo(self.content_lines[0])
            return
        elif val.code == term.KEY_END:
            await term.cursor.moveTo(self.content_lines[-1])
            return
        elif val == term.KEY_CTRL['e']:
            await self.scroll(max(self.scroll_pos - 1, 0))
        elif val == term.KEY_CTRL['y']:
            if self.content_lines[-1].rel_pos[1] > self.max_inner_height:
                await self.scroll(self.scroll_pos + 1)
        else:
            await super().onKeyPress(val, orig_src=orig_src)

    def add_line(self, text, prepend=""):
        if isinstance(text, str):
            if prepend != "":
                wrapper = TextWrapper(width=self.width - self.padding[1] - self.padding[3] - Settings.get('appearance.window_padding') * 2 - len(prepend), initial_indent="", subsequent_indent=" " * self.indent, drop_whitespace=False, term=term)
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

    async def onSizeChange(self, orig_src, child_src):
        self._size_changed.append(child_src)
        await super().onSizeChange(orig_src)

    async def onFocus(self, orig_src=None, child_src=None):

        if child_src is None:
            if len(self.content_lines):
                self.current_line = max(min(len(self.content_lines)-1, self.current_line),0)
                # self.current_line = len(self.content_lines)//2
                await term.cursor.moveTo(self.content_lines[self.current_line])
            await super().onFocus(orig_src=orig_src)

        else:

            try:
                current_line = self.lines.index(child_src)
                current_content_line = self.content_lines.index(child_src)
                if current_line < 0 or current_content_line < 0:
                    return
            except ValueError:
                return

            self.current_line = current_content_line

            # no need to scroll in case window is big enough
            if self.max_scroll == 0:
                return

            if current_line == len(self.lines) - 1:
                await self.scroll(-1)
            else:
                await self.scroll(int(round(current_line / len(self.lines) * self.max_scroll)))

            # await term.log(self.scroll_pos, self.max_scroll, len(self.lines) - self.height)
            # await term.log("content",current_content_line, "line", current_line)

            # up
            # if focus_on.rel_pos[1] < self.padding[1]:
            #     await self.scroll(max(self.scroll_pos + focus_on.rel_pos[1] - self.padding[1], 0))

            # down
            # if focus_on.rel_pos[1] > max_inner_height:# - focus_on.height:
            #     await self.scroll(self.scroll_pos + focus_on.rel_pos[1] - element.rel_pos[1] + focus_on.height - 1)

    async def scroll(self, pos):
        for l in self.lines:
            l.clear()
        if pos >= 0:
            self.scroll_pos = pos
        else:
            self.scroll_pos = self.max_scroll + pos + 1
