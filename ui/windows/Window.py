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

    def draw(self):
        super().draw()
        if self.draw_style == "basic":
            self.draw_border(self.pos, (self.width, self.height), self.title)
        elif self.draw_style == "basic-left-edge":
            self.draw_border2(self.pos, (self.width, self.height), self.title)

    def close(self):
        super().close()

    def draw_border(self, pos, dim, title=None):
        pos = np.array(pos)
        dim = np.array(dim)
        width, height = dim

        # draw border
        self.printAt((0,0), "┌" + "─" * (width-2) + "┐", ignore_padding=True)
        for i in range(height-2):
            self.printAt((0,i+1), "│  ", ignore_padding=True)
            self.printAt((width-2,i+1), " │", ignore_padding=True)
        self.printAt((0,height-1), "└" + "─" * (width-2) + "┘", ignore_padding=True)

        # set title
        if title is not None:
            self.printAt((1+0,0), " %s " % term.bold(term.white(title)), ignore_padding=True)

    def draw_border2(self, pos, dim, title=None):
        pos = np.array(pos)
        dim = np.array(dim)
        width, height = dim

        # draw border
        self.printAt((0,0), " " + " " * (width-2) + "│", ignore_padding=True)
        for i in range(height-2):
            self.printAt((0,i+1), "  ", ignore_padding=True)
            self.printAt((width-2,i+1), " │", ignore_padding=True)
        self.printAt((0,height-1), " " + " " * (width-2) + "│", ignore_padding=True)

        # set title
        if title is not None:
            self.printAt((1+0,0), " %s " % term.bold(term.white(title)), ignore_padding=True)
