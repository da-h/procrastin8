from ui.UIElement import UIElement
from ui import get_term
from blessed.sequences import Sequence
import numpy as np

term = get_term()

class Line(UIElement):

    def __init__(self, text="", rel_pos=None, prepend="", append="", wrapper=None, parent=None, center=False):
        super().__init__(rel_pos=rel_pos, parent=parent)
        if text is not None:
            self.registerProperty("text", text, ["main"])
        self.height = 1
        self.wrapper = wrapper
        self.prepend = prepend
        self.append = append
        self.registerProperty("edit_mode", False, ["main"])
        self.registerProperty("edit_charpos", 0, ["main"])
        self.registerProperty("edit_firstchar", 0, ["main"])
        self._typeset_text = None
        self.line_style = ""
        self.last_line_style = ""
        self.center = center
        self.text_changed = False

    def formatText(self):
        return str(self.text)

    # ensure lines have correct width
    def typeset(self):
        if self.text_changed:
            self.clear("main")
            self.text_changed = False
        else:
            self.element.redraw("main")
        if self.wrapper is None:
            self._typeset_text = [self.formatText()]
            self.height = 1
        else:
            self._typeset_text = self.wrapper.wrap(self.formatText())
            self.height = max(len(self._typeset_text),1)
        if len(self._typeset_text) == 0:
            self._typeset_text = [""]

    async def draw(self):
        await super().draw()

        if e := self.element("main"):
            with e:

                # check what highlight it is
                highlight = lambda x: x
                if term.cursor.on_element == self:
                    highlight = lambda x: term.bold(x)

                # print lines
                for i, t in enumerate(self._typeset_text):
                    t = Sequence(highlight(t), term)
                    t_len = t.length()
                    t = self.prepend+term.normal+self.line_style+t+term.normal+self.append
                    if self.center:
                        self.printAt(((self.wrapper.width-1)//2 - t_len//2 - 1, 1), " "+t+" ")
                    else:
                        self.printAt((0, i), t)

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
        await self.onContentChange()

    async def onKeyPress(self, val):
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
        return await super().onKeyPress(val)

    async def _updateText(self, raw_text, call_onContentChange=True):
        if self.text != raw_text:
            self.text_changed = True
        self.text = raw_text
        if self.edit_mode:
            self.edit_charpos = min(self.edit_charpos, len(self.text))
        await self.onContentChange()

    async def onEnter(self):
        await super().onEnter()
        await self.redraw("main")
    async def onLeave(self):
        await super().onLeave()
        await self.redraw("main")
