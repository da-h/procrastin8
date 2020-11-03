from ui.UIElement import UIElement
from ui import get_term
term = get_term()


class HLine(UIElement):
    def __init__(self, text, wrapper, center=False, parent=None):
        super().__init__(parent=parent)
        self.wrapper = wrapper
        self.height = 2
        self.text = text
        self.center = center

    def typeset(self):
        pass

    def draw(self, clean=False):
        super().draw(clean)
        self.printAt((0,0),          " "*self.wrapper.width)
        self.printAt((0,1), term.dim+"─"*self.wrapper.width+term.normal)
        if self.text:
            if self.center:
                self.printAt((0,1), term.center(self.text, width=self.wrapper.width))
            else:
                self.printAt((0,1), self.text+" ")


