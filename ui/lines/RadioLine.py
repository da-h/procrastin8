from ui.UIElement import UIElement
from ui import get_term
term = get_term()


class RadioLine(UIElement):
    def __init__(self, choices, option=0, wrapper=None, parent=None):
        super().__init__(parent=parent)
        self.height = 1
        self.choices = choices
        self.wrapper = wrapper if wrapper is not None else parent
        self.option = option

    def typeset(self):
        pass

    async def draw(self):
        if el := self.element("main"):
            is_active = term.cursor.on_element == self
            choice = [term.black_on_green(" "+c+" ") if i == self.option else " "+c+" " for i, c in enumerate(self.choices)]
            # choice[self.option] = term.green("◢") + choice[self.option] + term.green("◤")
            choice[self.option] = term.green("▒") + choice[self.option] + term.green("▒")
            choice_text = term.green(term.bold("/")).join(choice[:self.option]) + choice[self.option] + term.green(term.bold("/")).join(choice[self.option+1:])
            if self.option != 0:
                choice_text = " "+choice_text
            if self.option != len(choice):
                choice_text += " "
            el.printAt((0,0), choice_text)

    async def onKeyPress(self, val, orig_src=None, child_src=None):
        if val.code == term.KEY_LEFT:
            self.option = (self.option - 1) % len(self.choices)
            self.clear()
            await self.draw()
            return
        elif val.code == term.KEY_RIGHT:
            self.option = (self.option + 1) % len(self.choices)
            self.clear()
            await self.draw()
            return
        return await super().onKeyPress(val, orig_src=orig_src)
