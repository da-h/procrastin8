from ui.UIElement import UIElement
from ui import get_term
term = get_term()

class SuggestionPopup(UIElement):
    def __init__(self, suggestions=None, rel_pos=None, parent=None):
        super().__init__(rel_pos=rel_pos, parent=parent)
        self.registerProperty("suggestions", suggestions or [], ["main"])
        self.registerProperty("selected", 0, ["main"])

    async def draw(self):
        await super().draw()

        if e := self.element("main"):
            with e:
                for i, suggestion in enumerate(self.suggestions):
                    style = term.bold_black_on_white if i == self.selected else term.black_on_white
                    self.printAt((0, i), f"{style}{suggestion}{term.normal}")

    async def onKeyPress(self, val):
        if val.code == term.KEY_TAB:
            self.selected = max(0, self.selected - 1)
            return True
        elif val.code == term.KEY_BTAB:
            self.selected = min(len(self.suggestions) - 1, self.selected + 1)
            return True
        return False
        # return await super().onKeyPress(val)

    async def update_suggestions(self, suggestions):
        self.suggestions = suggestions
        self.selected = 0
        await self.redraw("main")
