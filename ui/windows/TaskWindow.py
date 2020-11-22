from model import Task
from ui.lines.TaskLine import TaskLine
from ui.windows.TextWindow import TextWindow
from ui.util.AbstractTaskGroup import AbstractTaskGroup
from ui.TaskGroup import TaskGroup
from blessed.sequences import SequenceTextWrapper as TextWrapper
from settings import WINDOW_PADDING
from ui import get_term
term = get_term()


class TaskWindow(TextWindow, AbstractTaskGroup):

    def __init__(self, rel_pos, width, title, *args, **kwargs):
        TextWindow.__init__(self, rel_pos, width, title, *args, **kwargs)
        AbstractTaskGroup.__init__(self, taskline_container=self)

        self.title = TaskGroup(self.parent.model, title, prepend=" ", append=" ", wrapper=self.wrapper, parent=self)
        self.title.tasklines = self.tasklines
        # self.title = TaskLine(Task.from_rawtext(self.parent.model, title), prepend=" ", append=" ", wrapper=self.wrapper, parent=self)
        self.title.hide_taskbullet = True
        self.title.line_style = term.bold_white

    def make_subgroup(self, *args, **kwargs):
        return TaskGroup(*args, **kwargs)

    def total_height(self):
        return self.height

    def draw(self):
        super().draw()

        # title
        if isinstance(self.title, TaskLine):
            self.title.typeset()
            self.title.rel_pos = (2,0)
            self.title.height = 2 + self.empty_lines
            self.title.draw()


    def onKeyPress(self, val):
        element = term.cursor.on_element

        if val.code == term.KEY_UP or val == 'k':
            if self.current_line <= 0:
                term.cursor.moveTo(self.title)
                self.title.line_style = term.bold_black_on_white
                self.current_line = -1
                return
        if val.code == term.KEY_DOWN or val == 'j':
            if self.current_line == -1:
                self.title.line_style = term.bold_white
        super().onKeyPress(val)


    def onLeave(self):
        self.title.line_style = term.bold_white
        super().onLeave()
