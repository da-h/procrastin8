from blessed.sequences import SequenceTextWrapper as TextWrapper
from ui.lines.TaskLine import TaskLine
from ui import get_term
from settings import WINDOW_PADDING
term = get_term()

class AbstractTaskGroup:

    def __init__(self, taskline_container):
        self.tasklines = []
        self.taskline_container = taskline_container
        super().__init__()

    def total_height(self):
        return self.height + sum(task.total_height() if isinstance(task, AbstractTaskGroup) else task.height for task in self.tasklines)

    def get_all_tasks(self):
        tasks = []
        for taskline in self.tasklines:
            if isinstance(taskline, AbstractTaskGroup):
                tasks += taskline.get_all_tasks()
            else:
                tasks.append(taskline.task)
        return tasks

    def add_task(self, task, prepend=""):
        if prepend != "":
            wrapper = TextWrapper(width=self.taskline_container.width-2-WINDOW_PADDING*2-len(prepend), initial_indent="",subsequent_indent=" "*self.taskline_container.indent, term=term)
        else:
            wrapper = self.taskline_container.wrapper
        elem = TaskLine(task, prepend=prepend, wrapper=wrapper, parent=self.taskline_container)
        self.taskline_container.add_line(elem)
        self.tasklines.append(elem)
        return elem

    def add_taskgroup(self, task, prepend="", model=None):
        if prepend != "":
            wrapper = TextWrapper(width=self.taskline_container.width-2-WINDOW_PADDING*2-len(prepend), initial_indent="",subsequent_indent=" "*self.taskline_container.indent, term=term)
        else:
            wrapper = self.taskline_container.wrapper
        taskgroup = self.make_subgroup(model, task, prepend=prepend, wrapper=wrapper, parent=self.taskline_container)
        self.taskline_container.add_line(taskgroup)
        self.tasklines.append(taskgroup)
        return taskgroup
