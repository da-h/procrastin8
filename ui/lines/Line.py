from ui.UIElement import UIElement
from ui import get_term
from blessed.sequences import Sequence
import numpy as np
import asyncio

term = get_term()

class Line(UIElement):

    def __init__(self, text="", rel_pos=None, prepend="", append="", wrapper=None, parent=None, center=False, line_style=""):
        super().__init__(rel_pos=rel_pos, parent=parent)
        if text is not None:
            self.registerProperty("text", text, ["main", "typeset"])
        self.height = 1
        self.wrapper = wrapper if wrapper is not None else parent.wrapper if parent is not None and hasattr(parent, 'wrapper') else parent
        self.registerProperty("prepend", prepend, ["main", "typeset"])
        self.registerProperty("append", append, ["main", "typeset"])
        self.registerProperty("edit_mode", False, ["main"])
        self.registerProperty("edit_charpos", 0, ["main"])
        self.registerProperty("edit_firstchar", 0, ["main"])
        self.registerProperty("line_style", line_style, ["main", "typeset"])
        self.registerProperty("active", prepend, ["main"])
        self.registerProperty("center", center, ["main"])
        self._typeset_text = None

    def formatText(self):
        return str(self.text)

    # ensure lines have correct width
    def typeset(self):
        if el := self.element('typeset'):
            if self.wrapper is None:
                self._typeset_text = [self.formatText()]
                self.height = 1
            else:
                self._typeset_text = self.wrapper.wrap(self.formatText())
                self.height = max(len(self._typeset_text),1)
            if len(self._typeset_text) == 0:
                self._typeset_text = [""]

    async def draw(self):
        if el := self.element("main"):

            # check what highlight it is
            highlight = lambda x: x
            if self.active:
                highlight = lambda x: term.bold(x)

            # print lines
            for i, t in enumerate(self._typeset_text if self._typeset_text else self.text):
                t = Sequence(highlight(t), term)
                t_len = t.length()
                t = self.prepend+term.normal+self.line_style+t+term.normal+self.append
                if self.center:
                    el.printAt(((self.wrapper.width-1)//2 - t_len//2 - 1, 1), " "+t+" ")
                else:
                    el.printAt((0, i), t)

            if self.edit_mode:
                prepend = Sequence(self.prepend, term)
                prepend_len = prepend.length()
                term.cursor.pos = self.pos + (prepend_len, 0) + self._get_pos_in_line()

    def _get_pos_in_line(self):
        total_chars, t_len = 0, 0

        for i, t in enumerate(self._typeset_text):
            t = Sequence(t, term).lstrip()
            t_len = len(t)
            if self.edit_charpos + self.edit_firstchar < total_chars + t_len:
                indent_len = 0 if not self.wrapper else len(self.wrapper.initial_indent) if i == 0 else len(self.wrapper.subsequent_indent)
                return (self.edit_charpos + self.edit_firstchar - total_chars + indent_len, i)
            total_chars += t_len
        indent_len = 0 if not self.wrapper else len(self.wrapper.initial_indent) if i == 0 else len(self.wrapper.subsequent_indent)
        return (t_len + indent_len,i)

    async def set_editmode(self, mode: bool, charpos: int=0, firstchar: int=0):
        self.edit_mode = mode
        self.edit_charpos = charpos
        self.edit_firstchar = firstchar
        if self.edit_mode:
            term.cursor.show()
        else:
            term.cursor.hide()

    async def onKeyPress(self, val, orig_src=None, child_src=None):
        if self.edit_mode:
            if val.code == term.KEY_RIGHT:
                self.edit_charpos = min(self.edit_charpos + 1, len(self.text))
                return
            elif val.code == term.KEY_LEFT:
                self.edit_charpos = max(self.edit_charpos - 1, 0)
                return
            elif val.code == term.KEY_DOWN:
                j, i = self._get_pos_in_line()

                # there is no down in last line
                if i == len(self._typeset_text) - 1:
                    return

                # all but first line skip need to ignore the initial indent
                indent_len = len(self.wrapper.initial_indent) if i != 0 else len(self.wrapper.subsequent_indent)
                self.edit_charpos += len(Sequence(self._typeset_text[i], term).lstrip()) - indent_len
                self.edit_charpos = min(self.edit_charpos , len(self.text))
                return
            elif val.code == term.KEY_UP:
                j, i = self._get_pos_in_line()

                # there is no up in first line
                if i == 0:
                    return

                # all but first line skip need to ignore the initial indent
                indent_len = len(self.wrapper.initial_indent) if i != 1 else len(self.wrapper.subsequent_indent)
                self.edit_charpos -= len(Sequence(self._typeset_text[i-1], term).lstrip()) - indent_len
                self.edit_charpos = max(self.edit_charpos , 0)
                return
            elif val.code == term.KEY_HOME:
                self.edit_charpos = 0
                return
            elif val.code == term.KEY_END:
                self.edit_charpos = len(self.text)
                return
            elif val.code == term.KEY_BACKSPACE:
                if self.edit_charpos > 0:
                    await self._updateText(self.text[:self.edit_charpos-1] + self.text[self.edit_charpos:])
                    self.edit_charpos -= 1
                return
            elif val.code == term.KEY_DELETE:
                await self._updateText(self.text[:self.edit_charpos] + self.text[self.edit_charpos+1:])
                return
            elif val.code == term.KEY_TAB:
                self.edit_charpos += len(self.text[self.edit_charpos:].split(" ")[0]) + 1
                self.edit_charpos = min(self.edit_charpos, len(self.text))
                return
            elif val.code == term.KEY_BTAB:
                at_word_start = self.text[self.edit_charpos-1] == " "
                self.edit_charpos -= len(self.text[:self.edit_charpos].split(" ")[-2 if at_word_start else -1])
                if at_word_start:
                    self.edit_charpos -= 1
                self.edit_charpos = max(self.edit_charpos, 0)
                return
            elif not val.is_sequence:
                await self._updateText(self.text[:self.edit_charpos] + str(val) + self.text[self.edit_charpos:])
                self.edit_charpos += len(val)
                return
        return await super().onKeyPress(val, orig_src=orig_src)

    async def _updateText(self, raw_text):
        if self.edit_mode:
            new_edit_charpos = min(self.edit_charpos, len(raw_text))
            if new_edit_charpos != self.edit_charpos:
                self.edit_charpos = new_edit_charpos
        if self.text != raw_text:
            self.text = raw_text

    async def onEnter(self, orig_src=None, child_src=None):
        self.active = True
        await super().onEnter(orig_src=orig_src)
    async def onLeave(self, orig_src=None, child_src=None):
        self.active = False
        await super().onLeave(orig_src=orig_src)

