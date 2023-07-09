from ui.UIElement import UIElement
from ui import get_term
from blessed.sequences import SequenceTextWrapper as TextWrapper
term = get_term()

class WidgetBar(UIElement):

    def __init__(self, parent):
        super().__init__((0,0), parent=parent)
        self.height = 3
        self.width = term.width - 2
        self.wrapper = TextWrapper(width=self.width - self.padding[1] - self.padding[3], initial_indent="", subsequent_indent=" ", drop_whitespace=False, term=term)
        self.widgets_left = []
        self.widgets_right = []

    async def draw(self):
        draw_args = self.draw_args

        if el := self.element("widgets_left"):
            pos = 1
            for w in self.widgets_left:
                w.rel_pos[1] = 1
                w.rel_pos[0] = pos
                w.typeset()
                pos += w.width + 1
        if el := self.element("widgets_right"):
            pos = self.width
            for w in self.widgets_right:
                w.rel_pos[1] = 1
                w.rel_pos[0] = pos - w.width
                pos -= w.width + 1

        for w in self.widgets_left:
            await w.draw()
        for w in self.widgets_right:
            await w.draw()

    async def onContentChange(self, orig_src, child_src):
        if orig_src in self.widgets_left:
            self.clear("widgets_left")
        if orig_src in self.widgets_right:
            self.clear("widgets_right")
        await super().onContentChange(orig_src, child_src)

