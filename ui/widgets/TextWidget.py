from ui.UIElement import UIElement
from ui import get_term
term = get_term()

class TextWidget(UIElement):
    def __init__(self, text, parent=None):
        super().__init__((0,0), parent=parent)
        self.height = 1
        self.text = text
        self.width = len(self.text)

    async def draw(self, **draw_args):
        await super().draw()
        self.printAt((0,0), term.dim + self.text + term.normal)
