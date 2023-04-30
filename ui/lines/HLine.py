from blessed.sequences import Sequence
from ui.UIElement import UIElement
from ui import get_term
term = get_term()


class HLine(UIElement):
    def __init__(self, text=None, height=2, wrapper=None, center=False, parent=None):
        super().__init__(parent=parent)
        self.wrapper = wrapper if wrapper is not None else parent
        self.height = height
        self.text = text
        self.center = center

    def typeset(self):
        pass

    async def draw(self):
        await super().draw()
        for i in range(self.height-1):
            self.printAt((0,i),          " "*self.wrapper.width)
        self.printAt((0,self.height-1), term.dim+"─"*self.wrapper.width+term.normal)
        if self.text:
            if self.center:
                self.printAt(((self.wrapper.width-1)//2 - Sequence(self.text, term).length()//2 - 1, self.height - 1), " "+self.text+" ")
            else:
                self.printAt((0,self.height-1), self.text+" ")
