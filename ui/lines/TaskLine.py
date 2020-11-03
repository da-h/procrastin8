from model import Tag, Subtag, List, Modifier, ModifierDate
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

        for text_i, t in enumerate(self.text["text"]):
            tstr = str(t)
            # if text_i != len(self.text["text"]):
            #     tstr += " "
            # if self.edit_mode and self.text_i == text_i:
            #     # breakpoint()
            #     tstr = tstr[:self.text_charpos] + term.black_on_white(tstr[self.text_charpos]) + tstr[self.text_charpos+1:]
            # term.location(self.pos[0], self.pos[1])

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
                # TODO merge all this into set_editmode
                self.set_editmode(True)
                self.text_i = 0
                self.edit_charpos = 0
                self.edit_firstchar = 2
                self._update_charPos()
                return
            elif val == "I":
                self.set_editmode(True)
                self.text_i = 0
                self.edit_charpos = 0
                self.edit_firstchar = 2
                self._update_charPos()
                return
            elif val == "A":
                self.set_editmode(True)
                self.text_i = 0
                self.edit_charpos = len(str(self.text)) - 1
                self.edit_firstchar = 2
                self._update_charPos()
                return
        elif self.edit_mode:
            if val.code == term.KEY_RIGHT:
                self.edit_charpos = min(self.edit_charpos+1,len(str(self.text))-1)
                self._update_charPos()
                return
            elif val.code == term.KEY_LEFT:
                self.edit_charpos = max(self.edit_charpos-1,0)
                self._update_charPos()
                return
            elif not val.is_sequence:
                # TODO: better make raw?
                self.text["text"][self.text_i] = self.text["text"][self.text_i][:self.text_charpos] + str(val) + self.text["text"][self.text_i][self.text_charpos:]
                self.edit_charpos += 1
                self._update_charPos()
                return
        super().onKeyPress(val)

    # TODO: can this be removed now with the cursor inplace?
    def _update_charPos(self):
        text_i = 0
        text_charpos = self.edit_charpos
        # breakpoint()
        while text_i < len(self.text["text"]) and text_charpos >= len(self.text["text"][text_i]):
            text_charpos -= len(self.text["text"][text_i])
            text_i += 1
            text_charpos -= 1

        # normalize
        if text_charpos < 0 and text_i >= len(self.text["text"]):
            text_i = len(self.text["text"]) - 1
            text_charpos = len(self.text["text"][text_i])
        elif text_charpos < 0:# and text_i >= len(self.text["text"]):
            text_i -= 1
            text_charpos = len(self.text["text"][text_i])

        self.text_charpos, self.text_i = text_charpos, text_i

    def onEditModeKey(self, val):
        if val.is_sequence:
            return

        # rel_pos = term.cursor.relativePos()
        # self.edit_charpos = self.wrapper.width * rel_pos[1] + rel_pos[0]



