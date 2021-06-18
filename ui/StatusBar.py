from ui.UIElement import UIElement
from ui import get_term
term = get_term()

class StatusBar(UIElement):

    def __init__(self):
        super().__init__((0,0))
        self.height = 1
        self.width = term.width
        self.status = "ok"

    def draw(self, **draw_args):
        super().draw()
        color = ""
        top_line = ""
        # self.printAt((0,0), color+"┌" + top_line * (self.width-2) + "┐", ignore_padding=True)
        if self.status:
            self.printAt((0,0), term.dim + "Status " + term.green + self.status)
