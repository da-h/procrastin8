from copy import copy
from blessed.sequences import SequenceTextWrapper as TextWrapper
from blessed.keyboard import Keystroke
from ui.lines.TaskLine import TaskLine
from ui.util.AbstractTaskGroup import AbstractTaskGroup
from settings import TODO_STYLE, WINDOW_PADDING
from ui import get_term
from model import Tag, Subtag, List, re_priority, Task
term = get_term()

class TaskGroup(TaskLine, AbstractTaskGroup):

    def __init__(self, model, text, *args, **kwargs):
        self.model = model
        self.raw_text = str(text)
        task = Task.from_rawtext(model, str(text))
        self.hide_taskbullet = True
        if TODO_STYLE == 1:
            self.height = 1
            self.center = False
        elif TODO_STYLE == 2:
            self.height = 3
            self.center = True
        self.active = False

        TaskLine.__init__(self, *args, text=task, **kwargs)
        AbstractTaskGroup.__init__(self, taskline_container=self.parent)

    def typeset(self):
        if self.edit_mode:

            super().typeset()

        else:
            if TODO_STYLE == 1:
                self._typeset_text = [term.cyan(str(self.text))]
            elif TODO_STYLE == 2:
                self._typeset_text = ["",term.cyan(str(self.text))]

    def draw(self):
        if self.active:
            total_height = self.total_height() - 1
            self.printAt((-WINDOW_PADDING,0), term.blue_bold("┏"*1))
            self.printAt((len(self.prepend) + self.wrapper.width + WINDOW_PADDING - 1,0), term.blue_bold("┓"*1))
            for i in range(1, total_height):
                self.printAt((-WINDOW_PADDING,i), term.blue_bold("┃"*1))
                self.printAt((len(self.prepend) + self.wrapper.width + WINDOW_PADDING - 1,i), term.blue_bold("┃"*1))
            self.printAt((-WINDOW_PADDING,total_height), term.blue_bold("┗"*1))
            self.printAt((len(self.prepend) + self.wrapper.width + WINDOW_PADDING - 1,total_height), term.blue_bold("┛"*1))

        if TODO_STYLE == 1:
            super().draw()
            return
        if TODO_STYLE == 2:
            self.printAt((0,0),          " "*self.wrapper.width)
            self.printAt((0,1), term.dim+"─"*self.wrapper.width+term.normal)
            super().draw()
            return

    def make_subgroup(self, *args, **kwargs):
        return TaskGroup(*args, **kwargs)

    def onFocus(self):
        self.active = True
        return super().onFocus()
    def onLeave(self):
        self.active = False
        return super().onLeave()
    def onKeyPress(self, val):
        if not self.edit_mode:
            if val == "e":
                self.previous_task = copy(self.task)
                self._update_common_tags()
                self.raw_text = " ".join(str(t) for t in self.common_lists.union(self.common_tags).union(self.common_subtags))

                self.task = Task.from_rawtext(self.model, self.raw_text)
                self.set_editmode(True, firstchar=0)
                return
        super().onKeyPress(val)

    def _update_common_tags(self):
        all_tasks = self.get_all_tasks()

        # determine common lists/tags/subtags of children
        self.common_lists = set(all_tasks[0]["lists"])
        self.common_tags = set(all_tasks[0]["tags"])
        self.common_subtags = set(all_tasks[0]["subtags"])

        for task in all_tasks[1:]:
            self.common_lists.intersection(task["lists"])
            self.common_tags.intersection(task["tags"])
            self.common_subtags.intersection(task["subtags"])
