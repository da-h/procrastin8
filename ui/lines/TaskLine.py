from model import Task, Tag, Subtag, List, Modifier, ModifierDate
from settings import WINDOW_PADDING, COLUMN_WIDTH, TAG_HIDDEN, SUBTAG_HIDDEN, DIM_COMPLETE

from ui import get_term
from ui.lines.Line import Line
term = get_term()



# ============= #
# Todo Specific #
# ============= #

class TaskLine(Line):

    def formatText(self):
        S = []
        if self.text["complete"]:
            S.append(term.green("✗")+(term.dim if DIM_COMPLETE else ""))
        else:
            S.append(term.blue("·"))
        if self.text["priority"] != "M_":
            S.append("(%s)" % self.text["priority"])
        if self.text["completion-date"]:
            S.append(term.bright_white(str(self.text["completion-date"])))
        if self.text["creation-date"]:
            S.append(term.dim+(str(self.text["creation-date"]))+term.normal)

        for t in self.text["text"]:
            tstr = str(t)

            if isinstance(t, Tag):
                if not TAG_HIDDEN or self.edit_mode:
                    S.append(term.red(tstr))
            elif isinstance(t, Subtag):
                if not SUBTAG_HIDDEN or self.edit_mode:
                    S.append(term.red(term.dim+tstr))
            elif isinstance(t, List):
                S.append(term.bold(term.blue(tstr)))
            elif isinstance(t, Modifier):
                S.append(term.green(tstr))
            elif isinstance(t, ModifierDate):
                S.append(term.green(tstr))
            else:
                S.append(tstr)
        return " ".join([str(s) for s in S])+term.normal

    def onKeyPress(self, val):
        if not self.edit_mode:
            if val == "x":
                self.text["complete"] = not self.text["complete"]
                self.text.save()
                return
            elif val == "i" or val == "e":
                self.set_editmode(True)
                return
            elif val == "I":
                self.set_editmode(True)
                return
            elif val == "A":
                self.set_editmode(True, charpos=len(self.text["raw_text"]) - 1, firstchar=2)
                return
        elif self.edit_mode:
            if val.code == term.KEY_RIGHT:
                self.edit_charpos = min(self.edit_charpos+1,len(self.text["raw_text"]))
                return
            elif val.code == term.KEY_LEFT:
                self.edit_charpos = max(self.edit_charpos-1,0)
                return
            elif val.code == term.KEY_DOWN:
                self.edit_charpos = min(self.edit_charpos+self.wrapper.width-len(self.prepend)-self.edit_firstchar, len(self.text["raw_text"]))
                return
            elif val.code == term.KEY_UP:
                self.edit_charpos = min(self.edit_charpos-self.wrapper.width+len(self.prepend)+self.edit_firstchar, len(self.text["raw_text"]))
                return
            elif val.code == term.KEY_HOME:
                self.edit_charpos = 0
                return
            elif val.code == term.KEY_END:
                self.edit_charpos = len(self.text["raw_text"])
                return
            elif val.code == term.KEY_BACKSPACE:
                self._updateText(self.text["raw_text"][:self.edit_charpos-1] + self.text["raw_text"][self.edit_charpos:])
                self.edit_charpos -= 1
                return
            elif val.code == term.KEY_DELETE:
                self._updateText(self.text["raw_text"][:self.edit_charpos] + self.text["raw_text"][self.edit_charpos+1:])
                return
            elif val.code == term.KEY_ESCAPE:
                self.set_editmode(False)
                self.text.save()
                return
            elif not val.is_sequence:
                self._updateText(self.text["raw_text"][:self.edit_charpos] + str(val) + self.text["raw_text"][self.edit_charpos:])
                self.edit_charpos += 1
                return
        super().onKeyPress(val)

    def _updateText(self, raw_text):
        text_optionals = self.text.__str__(print_description=False)
        raw_text = (text_optionals + " " if text_optionals else "") + raw_text
        self.text.update( Task.from_rawtext(self.text.model, raw_text ) )

    def set_editmode(self, mode, charpos: int=0, firstchar: int=2):
        super().set_editmode(mode, charpos, firstchar)

    def onEditModeKey(self, val):
        if val.is_sequence:
            return
