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
        self.last_width = None
        self.last_height = None
        self.last_title = None
        self.draw_style = "basic"

    def draw(self, clean=False):
        super().draw(clean)
        if clean or self.last_width != self.width or self.last_height != self.height or self.last_title != self.title or any(self.last_pos != self.pos):
            if self.draw_style == "basic":
                self.draw_border(self.pos, (self.width, self.height), self.title)
            elif self.draw_style == "basic-left-edge":
                self.draw_border2(self.pos, (self.width, self.height), self.title)

            if self.last_height and self.last_height > self.height:
                for i in range(self.last_height - self.height):
                    self.printAt((0,i+self.height), " "*self.width, ignore_padding=True)

            self.last_width = self.width
            self.last_height = self.height
            self.last_title = self.title
            self.last_pos = self.pos

    def clear(self):
        clean = ""
        for i in range(self.height):
            clean += term.move_xy(self.pos+(0,i)) + " "*self.width
        print(clean, end='', flush=False)
        super().clear()

    def close(self):
        self.clear()
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
