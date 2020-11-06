from datetime import datetime
from model import Task, Tag, Subtag, List, Modifier, ModifierDate
from settings import WINDOW_PADDING, COLUMN_WIDTH, LIST_HIDDEN, TAG_HIDDEN, SUBTAG_HIDDEN, DIM_COMPLETE, COMPLETIONDATE_HIDDEN, CREATIONDATE_HIDDEN, AUTOADD_COMPLETIONDATE

from ui import get_term
from ui.UIElement import UIElement
from ui.lines.Line import Line
term = get_term()



# ============= #
# Todo Specific #
# ============= #

class TaskLine(Line):

    def formatText(self):
        S = []
        default = "" #term.normal
        if self.text["complete"]:
            default = (term.dim if DIM_COMPLETE else "")

        if self.text["priority"] == "A":
            S.append(term.red(self.text["priority"])+default)
        elif self.text["priority"] == "B":
            S.append(term.yellow(self.text["priority"])+default)
        elif self.text["priority"] == "C":
            S.append(term.green(self.text["priority"])+default)
        elif self.text["priority"] == "D":
            S.append(term.blue(self.text["priority"])+default)
        elif self.text["priority"] == "M_":
            if self.text["complete"]:
                S.append(term.green("✗")+default)
            else:
                S.append(term.blue("·"))
        else:
            S.append(term.grey(self.text["priority"])+default)

        if not COMPLETIONDATE_HIDDEN and self.text["completion-date"]:
            S.append(term.bright_white(str(self.text["completion-date"])+default))
        if not CREATIONDATE_HIDDEN and self.text["creation-date"]:
            S.append(term.dim+(str(self.text["creation-date"]))+default)

        for t in self.text["text"]:
            tstr = str(t)

            if isinstance(t, Tag):
                if not TAG_HIDDEN or self.edit_mode:
                    S.append(term.red(tstr)+default)
            elif isinstance(t, Subtag):
                if not SUBTAG_HIDDEN or self.edit_mode:
                    S.append(term.red(term.dim+tstr)+default)
            elif isinstance(t, List):
                if not LIST_HIDDEN or self.edit_mode:
                    S.append(term.bold(term.blue(tstr))+default)
            elif isinstance(t, Modifier):
                S.append(term.green(tstr)+default)
            elif isinstance(t, ModifierDate):
                S.append(term.green(tstr)+default)
            else:
                S.append(tstr)
        self.line_style = default
        return " ".join([str(s) for s in S])+term.normal

    def onKeyPress(self, val):
        if not self.edit_mode:
            if val == "x" or val == " ":
                self.text["complete"] = not self.text["complete"]
                if AUTOADD_COMPLETIONDATE and self.text["creation-date"]:
                    self.text["completion-date"] = datetime.now().strftime("%Y-%m-%d")
                if self.text["completion-date"] and not self.text["complete"]:
                    self.text["completion-date"] = None
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
                if self.edit_charpos > 0:
                    self._updateText(self.text["raw_text"][:self.edit_charpos-1] + self.text["raw_text"][self.edit_charpos:])
                    self.edit_charpos -= 1
                return
            elif val.code == term.KEY_DELETE:
                self._updateText(self.text["raw_text"][:self.edit_charpos] + self.text["raw_text"][self.edit_charpos+1:])
                return
            elif val.code == term.KEY_RIGHT:
                self._updateText(self.text["raw_text"][:self.edit_charpos] + self.text["raw_text"][self.edit_charpos+1:])
                return
            elif val.code == term.KEY_TAB:
                self.edit_charpos += len(self.text["raw_text"][self.edit_charpos:].split(" ")[0]) + 1
                self.edit_charpos = min(self.edit_charpos, len(self.text["raw_text"]))
            elif val.code == term.KEY_BTAB:
                at_word_start = self.text["raw_text"][self.edit_charpos-1] == " "
                self.edit_charpos -= len(self.text["raw_text"][:self.edit_charpos].split(" ")[-2 if at_word_start else -1])
                if at_word_start:
                    self.edit_charpos -= 1
                self.edit_charpos = max(self.edit_charpos, 0)
            elif not val.is_sequence:
                self._updateText(self.text["raw_text"][:self.edit_charpos] + str(val) + self.text["raw_text"][self.edit_charpos:])
                self.edit_charpos += 1
                return
        UIElement.onKeyPress(self, val)

    def _updateText(self, raw_text):
        text_optionals = self.text.__str__(print_description=False)
        leading_spaces = len(raw_text) - len(raw_text.lstrip())
        raw_text = (text_optionals + " " if text_optionals else "") + raw_text
        self.text.update( Task.from_rawtext(self.text.model, raw_text, leading_spaces=leading_spaces ) )

    def set_editmode(self, mode, charpos: int=0, firstchar: int=2):
        super().set_editmode(mode, charpos, firstchar)

    def onEditModeKey(self, val):
        if val.is_sequence:
            return
