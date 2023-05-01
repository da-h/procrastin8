from copy import copy
from blessed.keyboard import Keystroke
from ui.lines.TaskLine import TaskLine
from ui.util.AbstractTaskGroup import AbstractTaskGroup
from settings import Settings
from ui import get_term
from model.basemodel import Tag, Subtag, List, re_priority, Task
term = get_term()

class TaskGroup(AbstractTaskGroup, TaskLine):

    def __init__(self, model, text, *args, **kwargs):
        self.model = model
        self.raw_text = str(text)
        task = Task.from_rawtext(model, str(text))
        TaskLine.__init__(self, *args, text=task, **kwargs)
        AbstractTaskGroup.__init__(self, taskline_container=self.parent)
        if Settings.get('tasks.todo_style') == 1:
            self.height = 1
            self.center = False
        elif Settings.get('tasks.todo_style') == 2:
            self.height = 3
            self.center = True

        self.hide_taskbullet = True
        self.line_style = term.cyan
        self.registerProperty("active", False, ["highlightborder", "grouptitle", "main"])
        self.registerProperty("overwrite_height", 0, "highlightborder")

    def typeset(self):
        super().typeset()

        if self.edit_mode:
            return

        if Settings.get('tasks.todo_style') == 1:
            self._typeset_text = [str(self.text)]
        elif Settings.get('tasks.todo_style') == 2:
            self._typeset_text = ["",str(self.text)]

    async def draw(self):

        if e := self.element("highlightborder"):
            with e:
                if self.active:
                    total_height = self.total_height() - 1 if self.overwrite_height == 0 else self.overwrite_height
                    self.printAt((-Settings.get('appearance.window_padding'),0), term.blue_bold("┏"*1))
                    self.printAt((len(self.prepend) + self.wrapper.width + Settings.get('appearance.window_padding') - 1 + len(self.append),0), term.blue_bold("┓"*1))
                    for i in range(1, total_height):
                        self.printAt((-Settings.get('appearance.window_padding'),i), term.blue_bold("┃"*1))
                        self.printAt((len(self.prepend) + self.wrapper.width + Settings.get('appearance.window_padding') - 1 + len(self.append),i), term.blue_bold("┃"*1))
                    self.printAt((-Settings.get('appearance.window_padding'),total_height), term.blue_bold("┗"*1))
                    self.printAt((len(self.prepend) + self.wrapper.width + Settings.get('appearance.window_padding') - 1 + len(self.append),total_height), term.blue_bold("┛"*1))

        if e := self.element("grouptitle"):
            with e:
                if Settings.get('tasks.todo_style') == 1:
                    await super().draw()
                    return
                if Settings.get('tasks.todo_style') == 2:
                    self.printAt((0,0),          " "*self.wrapper.width)
                    self.printAt((0,1), term.dim+"─"*self.wrapper.width+term.normal)
                    await super().draw()
                    return

        await super().draw()

    def make_subgroup(self, *args, **kwargs):
        return TaskGroup(*args, **kwargs)

    async def onFocus(self):
        self.active = True
        await self.onContentChange()
        return await super().onFocus()
    async def onLeave(self):
        self.active = False
        await self.onContentChange()
        return await super().onLeave()
    async def onKeyPress(self, val):
        if not self.edit_mode:
            if val == 'i' or val == 'e':
                await self.set_editmode(True, firstchar=0)

                self.previous_task = copy(self.task)
                self._update_common_tags()
                self.raw_text = " ".join(str(t) for t in self.common_lists.union(self.common_tags).union(self.common_subtags))

                self.task = Task.from_rawtext(self.model, self.raw_text)
                return
        await super().onKeyPress(val)

    def _update_common_tags(self):
        all_tasks = self.get_all_tasks()

        # determine common lists/tags/subtags of children
        self.common_lists = set(all_tasks[0]["lists"])
        self.common_tags = set(all_tasks[0]["tags"])
        self.common_subtags = set(all_tasks[0]["subtags"])

        for task in all_tasks[1:]:
            self.common_lists = self.common_lists.intersection(task["lists"])
            self.common_tags = self.common_tags.intersection(task["tags"])
            self.common_subtags = self.common_subtags.intersection(task["subtags"])
