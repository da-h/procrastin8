from blessed.sequences import Sequence
from ui.UIElement import UIElement
from ui import get_term
term = get_term()


class HLine(UIElement):
    def __init__(self, text=None, height=1, wrapper=None, center=False, parent=None):
        super().__init__(parent=parent)
        self.wrapper = wrapper if wrapper is not None else (parent.wrapper if parent is not None and hasattr(parent, 'wrapper') else TextWrapper(width=self.width - self.padding[1] - self.padding[3], initial_indent="", subsequent_indent=" ", drop_whitespace=False, term=term))
        self.height = height
        self.text = text
        self.center = center

    def typeset(self):
        pass

    async def draw(self):
        if el := self.element("main"):
            for i in range(self.height-1):
                el.printAt((0,i),          " "*self.wrapper.width)
            el.printAt((0,self.height-1), term.dim+"─"*self.wrapper.width+term.normal)
            if self.text:
                if self.center:
                    el.printAt(((self.wrapper.width-1)//2 - Sequence(self.text, term).length()//2 - 1, self.height - 1), " "+self.text+" ")
                else:
                    el.printAt((0,self.height-1), self.text+" ")
