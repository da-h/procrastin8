from ui.UIElement import UIElement
from blessed.sequences import Sequence
from ui import get_term
from blessed.sequences import SequenceTextWrapper as TextWrapper
term = get_term()


class ElemWithLabel(UIElement):
    def __init__(self, label, elem_fn, wrapper=None, parent=None):
        super().__init__(parent=parent)
        self.height = 1
        self.label = label
        self.elem = elem_fn(self)
        self.wrapper = wrapper if wrapper is not None else (parent.wrapper if parent is not None and hasattr(parent, 'wrapper') else TextWrapper(width=self.width - self.padding[1] - self.padding[3], initial_indent="", subsequent_indent=" ", drop_whitespace=False, term=term))

    def typeset(self):
        pass

    async def onFocus(self):
        await term.cursor.moveTo(self.elem)
    async def onEnter(self):
        self.clear()
    async def onLeave(self):
        self.clear()


    async def draw(self):
        if e := self.element("main"):
            with e:
                await super().draw()

                # check what highlight it is
                highlight = lambda x: term.ljust(x,width=self.wrapper.width)
                if self in term.cursor.elements_under_cursor:
                    highlight = lambda x: term.bold_green(term.ljust(x, width=self.wrapper.width))

                self.printAt((0,0), highlight(self.label))
                # await term.log(Sequence(self.label, term).length())
                self.elem.rel_pos = (Sequence(self.label, term).length() + 3,0)
                await self.elem.draw()

