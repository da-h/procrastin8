from ui.windows.TextWindow import TextWindow
from ui.lines.TaskLine import TaskLine
from ui.TaskGroup import TaskGroup
from blessed.sequences import SequenceTextWrapper as TextWrapper
from settings import WINDOW_PADDING
from ui import get_term
term = get_term()


class TaskWindow(TextWindow):

    def add_task(self, text, prepend=""):
        if prepend != "":
            wrapper = TextWrapper(width=self.width-2-WINDOW_PADDING*2-len(prepend), initial_indent="",subsequent_indent=" "*self.indent, term=term)
        else:
            wrapper = self.wrapper
        elem = TaskLine(text, prepend=prepend, wrapper=wrapper, parent=self)
        self.add_line(elem)
        return elem

    def add_taskgroup(self, text, prepend="", model=None):
        if prepend != "":
            wrapper = TextWrapper(width=self.width-2-WINDOW_PADDING*2-len(prepend), initial_indent="",subsequent_indent=" "*self.indent, term=term)
        else:
            wrapper = self.wrapper
        taskgroup = TaskGroup(model, text, prepend=prepend, wrapper=wrapper, parent=self)
        self.add_line(taskgroup)
        return taskgroup
