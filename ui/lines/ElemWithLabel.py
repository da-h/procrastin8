from ui.UIElement import UIElement
from blessed.sequences import Sequence
from ui import get_term
term = get_term()


class ElemWithLabel(UIElement):
    def __init__(self, label, elem_fn, wrapper=None, parent=None):
        super().__init__(parent=parent)
        self.height = 1
        self.label = label
        self.elem = elem_fn(self)
        self.wrapper = wrapper if wrapper is not None else parent

    def typeset(self):
        pass

    async def onFocus(self):
        await term.cursor.moveTo(self.elem)

    async def draw(self):
        if e := self.element("main"):
            with e:
                await super().draw()

                # check what highlight it is
                highlight = lambda x: term.ljust(x,width=self.wrapper.width-4)
                if self in term.cursor.elements_under_cursor:
                    highlight = lambda x: term.bold_green(term.ljust(x, width=self.wrapper.width-4))

                self.printAt((0,0), highlight(self.label))
                # await term.log(Sequence(self.label, term).length())
                self.elem.rel_pos = (Sequence(self.label, term).length() + 3,0)
                await self.elem.draw()

