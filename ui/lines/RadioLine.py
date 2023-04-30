from ui.UIElement import UIElement
from ui import get_term
term = get_term()


class RadioLine(UIElement):
    def __init__(self, text, choices, wrapper=None, parent=None):
        super().__init__(parent=parent)
        self.height = 2
        self.text = text
        self.choices = choices
        self.wrapper = wrapper if wrapper is not None else parent
        self.option = 0

    def typeset(self):
        pass

    async def draw(self):
        if e := self.element("main"):
            with e:
                await super().draw()
                # check what highlight it is
                highlight = lambda x: term.ljust(x,width=self.wrapper.width)
                if term.cursor.on_element == self:
                    highlight = lambda x: term.bold_green(term.ljust(x, width=self.wrapper.width))

                self.printAt((0,0), highlight(self.text))
                # self.printAt((3,1), highlight("".join("◢" + term.black_on_white(c) + "◤" if i == self.option else c for i, c in enumerate(self.choices))))

                choice = [term.black_on_green(" "+c+" ") if i == self.option else " "+c+" " for i, c in enumerate(self.choices)]
                choice[self.option] = term.green("◢") + choice[self.option] + term.green("◤")
                choice_text = term.green(term.bold("/")).join(choice[:self.option]) + choice[self.option] + term.green(term.bold("/")).join(choice[self.option+1:])
                if self.option != 0:
                    choice_text = " "+choice_text
                if self.option != len(choice):
                    choice_text += " "
                self.printAt((3,1), choice_text)

    async def onKeyPress(self, val):
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
        return await super().onKeyPress(val)
