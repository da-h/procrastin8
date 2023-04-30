from ui.windows.TextWindow import TextWindow
from ui.UIElement import UIElement
from ui.lines.Line import Line
from ui.lines.HLine import HLine
from ui.lines.RadioLine import RadioLine
from ui import get_term
from ui.UIElement import UIElement
from ui.lines.RadioLine import RadioLine
from ui.widgets.TextWidget import TextWidget
from settings import Settings

term = get_term()


class Sidebar(UIElement):
    def __init__(self, width, parent=None):
        super().__init__((parent.width - width, 0), parent=parent)
        self.width = width
        self.lines = []
        self.setting_lines = []

        # Dynamically create RadioLines for each setting in Settings.default_settings
        Line("Some Text", parent=self)
        HLine(height=1, parent=self)
        for key in Settings.default_settings().keys():
            self.lines.append(RadioLine(key, ["True", "False"], parent=self))

        self.active_line = 0

    async def draw(self):
        with term.location():
            v_offset = 0
            for line in self.children:
                line.rel_pos = (0, v_offset)
                v_offset += line.height
                line.typeset()
                await line.draw()

    async def onFocus(self):
        await term.cursor.moveTo(self.lines[0])

    async def onKeyPress(self, val):
        await term.log(self.active_line)

        # Handle arrow key presses to navigate RadioLines
        if val.code == term.KEY_UP:
            self.lines[self.active_line].clear()
            self.active_line = (self.active_line - 1) % len(self.lines)
            self.lines[self.active_line].clear()
            await term.cursor.moveTo(self.lines[self.active_line])
            await self.draw()
            return
        elif val.code == term.KEY_DOWN:
            self.lines[self.active_line].clear()
            self.active_line = (self.active_line + 1) % len(self.lines)
            self.lines[self.active_line].clear()
            await term.cursor.moveTo(self.lines[self.active_line])
            await self.draw()
            return
        # elif val.code in [term.KEY_LEFT, term.KEY_RIGHT]:
        #     await self.lines[self.active_line].onKeyPress(val)
        #     await self.draw()
        #     return
        return await super().onKeyPress(val)
