from copy import copy
from blessed.sequences import Sequence
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

    def __init__(self, text, *args, **kwargs):
        self.task = text
        self.hide_taskbullet = False
        super().__init__(*args, text=None, **kwargs)

    @property
    def text(self):
        return self.task["raw_text"]

    def formatText(self):
        S = []
        default = self.line_style
        if self.task["complete"]:
            default = (term.dim if DIM_COMPLETE else "")

        if self.task["priority"] == "A":
            S.append(term.red(self.task["priority"])+default)
        elif self.task["priority"] == "B":
            S.append(term.yellow(self.task["priority"])+default)
        elif self.task["priority"] == "C":
            S.append(term.green(self.task["priority"])+default)
        elif self.task["priority"] == "D":
            S.append(term.blue(self.task["priority"])+default)
        elif self.task["priority"] == "M_":
            if self.task["complete"]:
                S.append(term.green("✗")+default)
            elif self.hide_taskbullet:
                pass
            else:
                S.append(term.blue("·"))
        else:
            S.append(term.grey(self.task["priority"])+default)

        if not COMPLETIONDATE_HIDDEN and self.task["completion-date"]:
            S.append(term.bright_white(str(self.task["completion-date"])+default))
        if not CREATIONDATE_HIDDEN and self.task["creation-date"]:
            S.append(term.dim+(str(self.task["creation-date"]))+default)

        for t in self.task["text"]:
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
        self.last_line_style = default
        return " ".join([str(s) for s in S])+term.normal

    def onKeyPress(self, val):
        if self.edit_mode:
            # if val.code == term.KEY_ESCAPE:
            #     self.task = Task.from_rawtext(self.task.model, self.previous_text)
            #     self.set_editmode(False)
            #     return
            super().onKeyPress(val)
            return
        else:
            if val == "x":
                self.task["complete"] = not self.task["complete"]
                if AUTOADD_COMPLETIONDATE and self.task["creation-date"]:
                    self.task["completion-date"] = datetime.now().strftime("%Y-%m-%d")
                if self.task["completion-date"] and not self.task["complete"]:
                    self.task["completion-date"] = None
                self.task.save()
                return
            elif val == "i" or val == "e":
                self.set_editmode(True)
                return
            elif val == "I":
                self.set_editmode(True)
                return
            elif val == "A":
                self.set_editmode(True, charpos=len(self.task["raw_text"]) - 1, firstchar=2)
                return
        UIElement.onKeyPress(self, val)

    def _updateText(self, raw_text):
        text_optionals = self.task.__str__(print_description=False)
        leading_spaces = len(raw_text) - len(raw_text.lstrip())
        raw_text = (text_optionals + " " if text_optionals else "") + raw_text
        self.task.update( Task.from_rawtext(self.task.model, raw_text, leading_spaces=leading_spaces ) )

    def set_editmode(self, mode, charpos: int=0, firstchar: int=2):
        if mode:
            self.previous_task = copy(self.task)
        else:
            self.previous_task = None
        super().set_editmode(mode, charpos, firstchar)

    def onEditModeKey(self, val):
        if val.is_sequence:
            return
