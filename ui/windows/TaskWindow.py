from ui.windows.TextWindow import TextWindow
from ui.util.AbstractTaskGroup import AbstractTaskGroup
from ui.TaskGroup import TaskGroup
from blessed.sequences import SequenceTextWrapper as TextWrapper
from settings import WINDOW_PADDING
from ui import get_term
term = get_term()


class TaskWindow(TextWindow, AbstractTaskGroup):

    def __init__(self, *args, **kwargs):
        TextWindow.__init__(self, *args, **kwargs)
        AbstractTaskGroup.__init__(self, taskline_container=self)

    def make_subgroup(self, *args, **kwargs):
        return TaskGroup(*args, **kwargs)

    def total_height(self):
        return self.height
