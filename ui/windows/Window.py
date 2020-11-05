from ui.UIElement import UIElement
from ui.window_styles import draw_border, draw_border2
from ui import get_term
term = get_term()

class Window(UIElement):

    def __init__(self, rel_pos, width=1, height=1, title="", parent=None, max_height=-1, inner_offset=(1,1)):
        super().__init__(rel_pos=rel_pos, parent=parent, inner_offset=inner_offset, max_height=max_height)
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
                draw_border(self.pos, (self.width, self.height), self.title)
            elif self.draw_style == "basic-left-edge":
                draw_border2(self.pos, (self.width, self.height), self.title)
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
