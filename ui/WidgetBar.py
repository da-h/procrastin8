from ui.UIElement import UIElement
from ui import get_term
term = get_term()

class WidgetBar(UIElement):

    def __init__(self, parent):
        super().__init__((0,0), parent=parent)
        self.height = 3
        self.width = term.width - 2
        self.widgets_left = []
        self.widgets_right = []

    async def draw(self, **draw_args):
        await super().draw()

        if e := self.element("widgets_left"):
            with e:
                pos = 1
                for w in self.widgets_left:
                    w.rel_pos[1] = 1
                    w.rel_pos[0] = pos
                    w.typeset()
                    pos += w.width + 1
        if e := self.element("widgets_right"):
            with e:
                pos = self.width
                for w in self.widgets_right:
                    w.rel_pos[1] = 1
                    w.rel_pos[0] = pos - w.width
                    pos -= w.width + 1

        for w in self.widgets_left:
            await w.draw()
        for w in self.widgets_right:
            await w.draw()

    async def onContentChange(self, child_src, el_changed):
        if el_changed in self.widgets_left:
            self.clear("widgets_left")
        if el_changed in self.widgets_right:
            self.clear("widgets_right")
        await super().onContentChange(child_src, el_changed)

