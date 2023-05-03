from ui.UIElement import UIElement
from ui import get_term
term = get_term()


class RadioLine(UIElement):
    def __init__(self, text, choices, wrapper, parent=None):
        super().__init__(parent=parent)
        self.height = 2
        self.text = text
        self.choices = choices
        self.wrapper = wrapper
        self.active = 0

    def typeset(self):
        pass

    async def draw(self, children=[]):
        # check what highlight it is
        highlight = lambda x: term.ljust(x,width=self.wrapper.width)
        if term.cursor.on_element == self:
            highlight = lambda x: term.bold_green(term.ljust(x, width=self.wrapper.width))

        if el := self.element("main"):
            el.printAt((0,0), highlight(self.text))
            # el.printAt((3,1), highlight("".join("◢" + term.black_on_white(c) + "◤" if i == self.active else c for i, c in enumerate(self.choices))))

            choice = [term.black_on_green(" "+c+" ") if i == self.active else " "+c+" " for i, c in enumerate(self.choices)]
            choice[self.active] = term.green("◢") + choice[self.active] + term.green("◤")
            choice_text = term.green(term.bold("/")).join(choice[:self.active]) + choice[self.active] + term.green(term.bold("/")).join(choice[self.active+1:])
            if self.active != 0:
                choice_text = " "+choice_text
            if self.active != len(choice):
                choice_text += " "
            el.printAt((3,1), choice_text)

    async def onKeyPress(self, val):
        if val.code == term.KEY_LEFT:
            self.active = (self.active - 1) % len(self.choices)
            return
        elif val.code == term.KEY_RIGHT:
            self.active = (self.active + 1) % len(self.choices)
            return
        return await super().onKeyPress(val)
