from ui.windows.TextWindow import TextWindow
from ui.lines.RadioLine import RadioLine
from ui import get_term
term = get_term()


class Sidebar(TextWindow):

    def __init__(self, width, parent=None):
        rel_pos = (0,0)
        super().__init__(rel_pos, width=width, title="Settings", parent=parent)
        self.draw_style = "basic-left-edge"

        self.lines.append(RadioLine("Verbosity",["Small","Medium","Full"], wrapper=self.wrapper, parent=self))
        # self.lines.append(RadioLine("Verbosity",["Small","Medium","Full"], wrapper=self.wrapper, parent=self))
        # self.lines.append(RadioLine("Verbosity",["Small","Medium","Full"], wrapper=self.wrapper, parent=self))

    async def onKeyPress(self, val):

        if val == "s":
            self.parent.rel_pos = (0,0)
            await self.close()
            return

        return await super().onKeyPress(val)
