import numpy as np
from ui.UIElement import UIElement
from ui import get_term
term = get_term()

class Window(UIElement):

    def __init__(self, rel_pos, width=1, height=1, title="", parent=None, max_height=-1, padding=(1,1,1,1)):
        super().__init__(rel_pos=rel_pos, parent=parent, padding=padding, max_height=max_height)
        self.width = width
        self.height = height
        self.title = title
        self.draw_style = "basic"
        self.active = False

    async def draw(self, **draw_args):
        await super().draw()
        if e := self.element("border"):
            with e:
                if self.draw_style == "basic":
                    self.draw_border(self.pos, (self.width, self.height), self.title, color=term.yellow if self.active else term.dim, **draw_args)
                elif self.draw_style == "basic-left-edge":
                    self.draw_border2(self.pos, (self.width, self.height), self.title, color=term.normal if self.active else term.dim, **draw_args)

    async def close(self):
        await super().close()

    def draw_border(self, pos, dim, title=None, color=term.normal, top_line="─", bottom_line="─"):
        pos = np.array(pos)
        dim = np.array(dim)
        width, height = dim

        # draw border
        self.printAt((0,0), color+"┌" + top_line * (width-2) + "┐", ignore_padding=True)
        for i in range(height-2):
            self.printAt((0,i+1), color+"│  ", ignore_padding=True)
            self.printAt((width-2,i+1), color+" │", ignore_padding=True)
        self.printAt((0,height-1), color+"└" + bottom_line * (width-2) + "┘", ignore_padding=True)

        # set title
        if title is not None:
            if isinstance(title, str):
                self.printAt((1+0,0), color+" %s " % term.bold(term.white(title)), ignore_padding=True)

    def draw_border2(self, pos, dim, title=None, color=term.normal):
        pos = np.array(pos)
        dim = np.array(dim)
        width, height = dim

        # draw border
        self.printAt((0,0), color+" " + " " * (width-2) + "│", ignore_padding=True)
        for i in range(height-2):
            self.printAt((0,i+1), color+"  ", ignore_padding=True)
            self.printAt((width-2,i+1), color+" │", ignore_padding=True)
        self.printAt((0,height-1), color+" " + " " * (width-2) + "│", ignore_padding=True)

        # set title
        if title is not None:
            self.printAt((1+0,0), color+" %s " % term.bold(term.white(title)), ignore_padding=True)

    async def onEnter(self):
        self.active = True
        await super().onEnter()
        await self.redraw("border")
    async def onLeave(self):
        self.active = False
        await super().onEnter()
        await self.redraw("border")
