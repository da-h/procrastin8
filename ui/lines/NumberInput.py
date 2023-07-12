from ui.UIElement import UIElement
from ui import get_term
term = get_term()

class NumberInput(UIElement):
    def __init__(self, default_val, min_val=None, max_val=None, wrapper=None, parent=None):
        super().__init__(parent=parent)
        self.height = 1
        self.default_val = default_val
        self.min_val = min_val
        self.max_val = max_val
        self.wrapper = wrapper if wrapper is not None else parent
        self.value = default_val
        self.editing = False

    def typeset(self):
        pass

    async def draw(self):
        if el := self.element("main"):
            # check what highlight it is
            is_active = term.cursor.on_element == self
            el.printAt((0, 0), f"{self.value}")
            if self.editing:
                el.printAt((len(str(self.value)), 0), term.blink("_"))

    async def onKeyPress(self, val, orig_src=None, child_src=None):
        if self.editing:
            if val.code == term.KEY_ENTER:
                self.editing = False
                self.initial_value = self.value
            elif val.code == term.KEY_ESCAPE:
                self.editing = False
                self.value = self.initial_value
            elif val.code == term.KEY_BACKSPACE:
                self.value //= 10
            elif val in ["0","1","2","3","4","5","6","7","8","9"]:
                digit = int(val)
                self.value = self.value * 10 + digit
            self.clear()
            await self.draw()
        else:
            if val.code == term.KEY_LEFT:
                self.clear()
                await self.draw()
                return
            elif val.code == term.KEY_ENTER:
                self.editing = True
                self.clear()
                await self.draw()
                return
        return await super().onKeyPress(val, orig_src=orig_src)
