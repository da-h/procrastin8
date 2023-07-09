from copy import copy
from blessed.sequences import Sequence
from ui.floating.SuggestionPopup import SuggestionPopup
from datetime import datetime
from model.basemodel import Task, Tag, Subtag, List, Modifier, ModifierDate
from settings import Settings

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
        self.suggestion_popup = SuggestionPopup(["one","two","three"], parent=self)
        self.suggestion_popup.visible = False

    @property
    def text(self):
        return self.task["raw_text"]


    async def draw(self):
        await super().draw()

        if e := self.element("suggestion"):
            if self.suggestion_popup.visible:
                await self.suggestion_popup.draw()




    # ensure lines have correct width
    def typeset(self):
        super().typeset()

        # fix wrong typeset in case first line was to long
        if len(self._typeset_text) > 1:
            indent_len = len(self.wrapper.initial_indent)# if i != 1 else len(self.wrapper.subsequent_indent)
            if Sequence(self._typeset_text[0], term).length() == self.edit_firstchar:
                self._typeset_text[0] += self._typeset_text[1][self.edit_firstchar:]
                del self._typeset_text[1]
                self.height -= 1

    def formatText(self):
        S = []
        default = self.line_style
        if self.task["complete"]:
            default = (term.dim if Settings.get('tasks.dim_complete') else "")

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
            elif not self.hide_taskbullet:
                S.append(term.blue("·"))
        else:
            S.append(term.grey(self.task["priority"])+default)

        if not Settings.get('dates.completiondate_hidden') and self.task["completion-date"]:
            S.append(term.bright_white(str(self.task["completion-date"])+default))
        if not Settings.get('dates.creationdate_hidden') and self.task["creation-date"]:
            S.append(term.dim+(str(self.task["creation-date"]))+default)

        for t in self.task["text"]:
            tstr = str(t)

            if isinstance(t, Tag):
                if not Settings.get('appearance.tag_hidden') or self.edit_mode:
                    S.append(term.red(tstr)+default)
            elif isinstance(t, Subtag):
                if not Settings.get('appearance.subtag_hidden') or self.edit_mode:
                    S.append(term.red(term.dim+tstr)+default)
            elif isinstance(t, List):
                if not Settings.get('appearance.list_hidden') or self.edit_mode:
                    S.append(term.bold(term.blue(tstr))+default)
            elif isinstance(t, Modifier):
                S.append(term.green(tstr)+default)
            elif isinstance(t, ModifierDate):
                S.append(term.green(tstr)+default)
            else:
                S.append(tstr)
        self.line_style = default
        return " ".join([str(s) for s in S])+term.normal

    async def onKeyPress(self, val, orig_src=None, child_src=None):
        if self.edit_mode:
            if self.suggestion_popup.visible:
                if await self.suggestion_popup.onKeyPress(val):
                    return

            await super().onKeyPress(val, orig_src=orig_src)
            return
        else:
            if val == "x":
                self.task.toggle_complete()
                await self.onContentChange()
                return
            elif val == "i" or val == "e":
                await self.set_editmode(True)
                return
            elif val == "S":
                await self.set_editmode(True, charpos=0, firstchar=2)
                await self._updateText("")
                return
            elif val == "I":
                await self.set_editmode(True)
                return
            elif val == "A":
                await self.set_editmode(True, charpos=len(self.task["raw_text"]) - 1, firstchar=2)
                return
        await UIElement.onKeyPress(self, val, orig_src=orig_src)

    async def _updateText(self, raw_text):
        text_optionals = self.task.__str__(print_description=False)
        leading_spaces = len(raw_text) - len(raw_text.lstrip())
        raw_text = (f"{text_optionals} " if text_optionals else "") + raw_text
        self.task.update( Task.from_rawtext(self.task.model, raw_text, leading_spaces=leading_spaces ) )
        if self.text != raw_text:
            self.typeset()
        # if self.edit_mode:
        #     words = raw_text[:self.edit_charpos+1].split(' ')
        #     current_word = words[-1] if len(words) > 0 else None
        #     await self.update_suggestion_popup(current_word)

    async def set_editmode(self, mode, charpos: int=0, firstchar: int=2):
        self.previous_task = copy(self.task) if mode else None
        await super().set_editmode(mode, charpos, firstchar)

    def get_all_tasks(self):
        return [self.task]

    async def update_suggestion_popup(self, current_word):
        if len(current_word.strip()) > 0:
            # suggestions = [current_word, current_word+"blub", current_word+"yeah"]
            suggestions = list(self.task.model.lists.keys()) + list(self.task.model.tags.keys()) + list(self.task.model.subtags.keys())

            self.suggestion_popup.visible = True
            rel_pos = term.cursor.pos - self.pos
            self.suggestion_popup.rel_pos = rel_pos[0], rel_pos[1] + 1
            await self.suggestion_popup.update_suggestions(suggestions)
        else:
            self.suggestion_popup.visible = False
        await self.redraw("suggestion")
