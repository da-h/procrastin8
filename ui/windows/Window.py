import numpy as np
from ui.UIElement import UIElement
from ui import get_term
term = get_term()

class Window(UIElement):

    def __init__(self, rel_pos, width=1, height=1, title="", parent=None, max_height=-1, padding=(1,1,1,1)):
        super().__init__(rel_pos=rel_pos, parent=parent, padding=padding, max_height=max_height)
        self.registerProperty("width", width, ["border"], instant_draw=False)
        self.registerProperty("height", height, ["border"], instant_draw=False)
        self.registerProperty("title", title, ["border"])
        self.registerProperty("border_color", term.dim, ["border"])
        self.registerProperty("draw_style", "basic", ["border"], instant_draw=False)
        self.addPropertyElements("max_height", ["clearbg", "border"])

    async def draw(self, **draw_args):
        if self.layer > 0:
            if el := self.element("clearbg"):
                for i in range(self.height):
                    el.printAt((0,i), " "*self.width, ignore_padding=True)

        if el := self.element("border"):
            if self.draw_style == "basic":
                self.draw_border(el, self.pos, (self.width, self.height), self.title, color=self.border_color, **draw_args)
            elif self.draw_style == "basic-left-edge":
                self.draw_border2(el, self.pos, (self.width, self.height), self.title, color=self.border_color, **draw_args)

    async def close(self):
        await super().close()

    def draw_border(self, el, pos, dim, title=None, color=term.normal, top_line="─", bottom_line="─"):
        pos = np.array(pos)
        dim = np.array(dim)
        width, height = dim

        # draw border
        el.printAt((0,0), color+"┌" + top_line * (width-2) + "┐", ignore_padding=True)
        for i in range(height-2):
            el.printAt((0,i+1), color+"│ ", ignore_padding=True)
            el.printAt((width-2,i+1), color+" │", ignore_padding=True)
        el.printAt((0,height-1), color+"└" + bottom_line * (width-2) + "┘", ignore_padding=True)

        # set title
        if title is not None and isinstance(title, str):
            el.printAt((1+0,0), color+" %s " % term.bold(term.white(title)), ignore_padding=True)

    def draw_border2(self, el, pos, dim, title=None, color=term.normal):
        pos = np.array(pos)
        dim = np.array(dim)
        width, height = dim

        # draw border
        el.printAt((0,0), color+" " + " " * (width-2) + "│", ignore_padding=True)
        for i in range(height-2):
            el.printAt((0,i+1), color+"  ", ignore_padding=True)
            el.printAt((width-2,i+1), color+" │", ignore_padding=True)
        el.printAt((0,height-1), color+" " + " " * (width-2) + "│", ignore_padding=True)

        # set title
        if title is not None and isinstance(title, str):
            el.printAt((1+0,0), color+" %s " % term.bold(term.white(title)), ignore_padding=True)
