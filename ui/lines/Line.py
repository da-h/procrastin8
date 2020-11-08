from ui.UIElement import UIElement
from ui import get_term
from blessed.sequences import Sequence
import numpy as np

term = get_term()

class Line(UIElement):

    def __init__(self, text="", rel_pos=None, prepend="", wrapper=None, parent=None):
        super().__init__(rel_pos=rel_pos, parent=parent)
        self.text = text
        self.height = 1
        self.wrapper = wrapper
        self.prepend = prepend
        self.edit_mode = False
        self.edit_charpos = 0
        self.edit_firstchar = 0
        self._typeset_text = None
        self.line_style = ""

    def formatText(self):
        return str(self.text)

    # ensure lines have correct width
    def typeset(self):
        if self.wrapper is None:
            self._typeset_text = self.formatText()
            self.height = 1
        else:
            self._typeset_text = self.wrapper.wrap(self.formatText())
            self.height = max(len(self._typeset_text),1)
        if self.text == "":
            self._typeset_text = [""]

    def draw(self):
        super().draw()

        # check what highlight it is
        highlight = lambda x: term.ljust(x,width=self.wrapper.width)
        if term.cursor.on_element == self:
            highlight = lambda x: term.bold(term.ljust(x, width=self.wrapper.width))

        # print lines
        for i, t in enumerate(self._typeset_text):
            t = Sequence(highlight(t), term)
            self.printAt((0, i), self.prepend+self.line_style+t)

        if self.edit_mode:
            # self.edit_charpos = 34
            prepend = Sequence(self.prepend, term)
            prepend_len = prepend.length()
            term.cursor.pos = self.pos + (prepend_len, 0) + self._get_pos_in_line()

    def _get_pos_in_line(self):
        total_chars = 0

        for i, t in enumerate(self._typeset_text):
            t = Sequence(t, term).lstrip()
            t_len = len(t)
            if total_chars <= self.edit_charpos + self.edit_firstchar and self.edit_charpos  + self.edit_firstchar < total_chars + t_len + 1:
                indent_len = len(self.wrapper.initial_indent) if i == 0 else len(self.wrapper.subsequent_indent)
                return (self.edit_charpos + self.edit_firstchar - total_chars + indent_len, i)
            total_chars += t_len + 1
        return (0,0)

    def set_editmode(self, mode: bool, charpos: int=0, firstchar: int=0):
        self.edit_mode = mode
        self.edit_charpos = charpos
        self.edit_firstchar = firstchar
        if self.edit_mode:
            term.cursor.show()
        else:
            term.cursor.hide()

    def onKeyPress(self, val):
        if self.edit_mode:
            self.onEditModeKey(val)
            if val.code == term.KEY_ESCAPE:
                self.set_editmode(False)
            return
        return super().onKeyPress(val)

    def onEditModeKey(self, val):
        pass
