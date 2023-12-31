from ui.windows.TextWindow import TextWindow
from ui import get_term
term = get_term()


class Prompt(TextWindow):

    def __init__(self, width, parent=None):
        rel_pos = ((term.width - width)//2,10)
        super().__init__(rel_pos, width=width, title="Settings", parent=parent)

        self.add_line("Add")
        self.add_line("Remove")
        self.add_line("Tag")
        self.add_line("Lorem")
        self.add_line("Ipsum")

    async def onKeyPress(self, val, orig_src=None, child_src=None):

        if val == "s":
            await self.close()
            return

        return await super().onKeyPress(val, orig_src=orig_src)
