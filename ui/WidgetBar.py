from ui.UIElement import UIElement
from ui import get_term
term = get_term()

class WidgetBar(UIElement):

    def __init__(self, parent):
        super().__init__((1,0), parent=parent)
        self.height = 1
        self.width = term.width - 2
        self.widgets_left = [TextWidget("test", parent=self), TextWidget("test2", parent=self), TextWidget("test500", parent=self)]
        self.widgets_right = [TextWidget("test", parent=self), TextWidget("test2", parent=self), TextWidget("test500", parent=self)]

    async def draw(self, **draw_args):
        await super().draw()


        if e := self.element("widgets_left"):
            with e:
                pos = 0
                for w in self.widgets_left:
                    w.rel_pos[0] = pos
                    await w.draw()
                    pos += w.width + 1
        if e := self.element("widgets_right"):
            with e:
                pos = self.width
                for w in self.widgets_right:
                    w.rel_pos[0] = pos - w.width
                    await w.draw()
                    pos -= w.width + 1


class TextWidget(UIElement):
    def __init__(self, text, parent=None):
        super().__init__((0,0), parent=parent)
        self.height = 1
        self.text = text
        self.width = len(self.text)

    async def draw(self, **draw_args):
        await super().draw()
        self.printAt((0,0), term.dim + self.text + term.normal)
