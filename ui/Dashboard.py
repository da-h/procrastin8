import signal
from itertools import chain
from datetime import datetime
import numpy as np
from ui import get_term
from ui.UIElement import UIElement
from ui.windows.Sidebar import Sidebar
from ui.lines.RadioLine import RadioLine
from ui.lines.TaskLine import TaskLine
from ui.util.AbstractTaskGroup import AbstractTaskGroup
from ui.windows import TaskWindow
from settings import COLUMN_WIDTH, WINDOW_MARGIN, TODO_STYLE, AUTOADD_CREATIONDATE, WINDOW_PADDING
from model import Task, Tag, Subtag, List, re_priority
from enum import Enum

term = get_term()


class StackMode(Enum):
    MERGE_SMALLEST = 0
    KEEP_ORDER = 1
class SortMode(Enum):
    FILE = 0
    GROUP_FULL = 1


draw_calls = 0
def redraw():
    return
    global draw_calls
    print(term.move_y(term.height - 4) + term.center('draw() calls: %i' % draw_calls).rstrip(), end='', flush=False)
    print(term.move_y(term.height - 3) + term.center('cursor: '+str(term.cursor.pos)).rstrip(), end='', flush=False)
    print(term.move_y(term.height - 2) + term.center('element: '+str(term.cursor.on_element) if term.cursor.on_element else "").rstrip(), end='', flush=False)
    draw_calls += 1


class Dashboard(UIElement):

    def __init__(self, model, filter=".*"):
        super().__init__((0,0))
        self.width = term.width
        self.height = term.height - self.pos[1]
        self.filter = filter
        self.model = model
        self.overlay = None
        self.continue_loop = True
        self.windows = []
        self.marked = []
        self.current_window = 0
        # self.stackmode = StackMode.MERGE_SMALLEST
        self.stackmode = StackMode.KEEP_ORDER
        # self.sortmode = SortMode.GROUP_FULL
        self.sortmode = SortMode.FILE
        self.init_modelview()

        def on_resize(sig, action):
            print(term.home + term.clear)
            self.width = term.width
            self.height = term.height
            self.elements = []
            self.init_modelview()
        signal.signal(signal.SIGWINCH, on_resize)

    def draw(self):
        with term.location():
            for elem in self.elements:
                if elem != self.overlay:
                    elem.draw()
            for i, elem in enumerate(self.marked):
                # self.printAt(elem.pos - self.pos + (-2,0), term.yellow("┃"), ignore_padding=True)
                # self.printAt(elem.pos - self.pos + (COLUMN_WIDTH-WINDOW_PADDING*2-1,0), term.yellow("┃"), ignore_padding=True)
                self.printAt(elem.pos - self.pos + (-1,0), term.yellow("⯈"), ignore_padding=True)
                self.printAt(elem.pos - self.pos + (COLUMN_WIDTH-WINDOW_PADDING*2-2,0), term.yellow(str(i+1)), ignore_padding=True)
            if self.overlay:
                self.overlay.draw()
        redraw()
        term.draw()

    def loop(self):
        val = ''
        while self.continue_loop:
            val = term.inkey(esc_delay=0)
            if val and term.cursor.on_element:
                term.cursor.on_element.onKeyPress(val)
            self.draw()

    def onFocus(self):
        if len(self.elements):
            term.cursor.moveTo(self.elements[0])

    def onElementClosed(self, elem):
        self.elements.remove(elem)
        if elem == self.overlay:
            self.overlay = None
        self.draw()
        if term.cursor.isOnElement(elem):
            term.cursor.moveTo(self.elements[0])

    def onKeyPress(self, val):
        element = term.cursor.on_element

        # =============== #
        # general actions #
        # =============== #

        # q to exit
        if val == "q":
            term.cursor.show()
            self.continue_loop = False
            return

        # LEFT/RIGHT to move between windows
        elif val.code == term.KEY_RIGHT:
            last_window = self.current_window
            self.current_window = min(self.current_window + 1, len(self.windows)-1)
            if self.current_window != last_window:
                term.cursor.moveTo(self.windows[self.current_window])
            return
        elif val.code == term.KEY_LEFT:
            last_window = self.current_window
            self.current_window = max(self.current_window - 1, 0)
            if self.current_window != last_window:
                term.cursor.moveTo(self.windows[self.current_window])
            return

        # s to open settings window
        elif val == "s" and self.overlay is None:
            # self.overlay = Prompt(COLUMN_WIDTH, parent=self)
            self.overlay = Sidebar(COLUMN_WIDTH, parent=self)
            self.overlay.draw()
            self.rel_pos = (COLUMN_WIDTH,0)
            self.overlay.rel_pos = (-COLUMN_WIDTH,0)
            self.overlay.add_emptyline()
            self.overlay.lines.append(RadioLine("Verbosity",["Small","Medium","Full"], wrapper=self.overlay.wrapper, parent=self.overlay))


            old_elem = term.cursor.moveTo(self.overlay.lines[0])
            redraw()
            return

        # X to Archive done tasks
        elif val == 'X':
            self.model.archive()
            self.elements = []
            self.init_modelview()
            self.draw()
            term.cursor.moveTo(self.elements[0])

        # Ctrl+r to save order of current view
        elif self.sortmode != SortMode.FILE and val == term.KEY_CTRL['r']:
            tasks = list(chain.from_iterable([win.get_all_tasks() for win in self.windows]))
            self.model.save_order(tasks)
            self.init_modelview()

        # Ctrl+r to move marked elements to the top
        elif self.sortmode == SortMode.FILE and val == term.KEY_CTRL['r']:
            all_tasks = list(chain.from_iterable([win.get_all_tasks() for win in self.windows]))
            marked_tasks = [m.task for m in self.marked]
            for t in marked_tasks:
                all_tasks.remove(t)
            tasks = marked_tasks + all_tasks
            self.marked = []
            self.model.save_order(tasks)
            self.init_modelview()

        elif val == term.KEY_CTRL['o']:
            marked_tasks = [m.task for m in self.marked]
            sort_by = ["lists", "tags","subtags","priority"]
            marked_tasks = self.model.query(filter=marked_tasks, sortBy=sort_by)
            self.marked = []
            self.model.save_order(marked_tasks)
            self.init_modelview()

        # space to mark task
        elif val == ' ':
            def mark(elem):
                if isinstance(elem, AbstractTaskGroup):
                    for e in elem.tasklines:
                        mark(e)
                    return

                if elem in self.marked:
                    self.marked.remove(elem)
                else:
                    self.marked.append(elem)
            mark(element)

        # n to create new task
        elif val == 'n':
            if isinstance(element, AbstractTaskGroup):
                element._update_common_tags()
                initial_text = " ".join([str(t) for t in element.common_subtags] + [str(t) for t in element.common_tags] + [str(t) for t in element.common_lists])
            elif isinstance(element, TaskLine):
                initial_text = " ".join([str(t) for t in element.task["subtags"]] + [str(t) for t in element.task["tags"]] + [str(t) for t in element.task["lists"]])
            elif isinstance(element, TaskWindow):
                initial_text = ""

            if AUTOADD_CREATIONDATE:
                initial_text = datetime.now().strftime("%Y-%m-%d") + " " + initial_text

            if isinstance(element, TaskLine) and element.task["priority"] != "M_":
                initial_text = "("+element.task["priority"]+") " + initial_text

            pos = element.task if isinstance(element, TaskLine) and not isinstance(element, AbstractTaskGroup) else -1
            task = self.model.new_task(initial_text, pos=pos)
            task["unsaved"] = True
            self.reinit_modelview(line_offset=+1)
            term.cursor.on_element.set_editmode(True)

        # d to delete current task
        elif val == 'd':
            if not isinstance(element, TaskLine) or isinstance(element, AbstractTaskGroup):
                return

            self.model.remove_task(pos=element.task)
            self.reinit_modelview(line_offset=0)


        # Shift + UP/DOWN to swap tasks up/down
        elif val.code == term.KEY_SDOWN:
            if not isinstance(element, TaskLine) or isinstance(element, AbstractTaskGroup):
                return

            window = self.windows[self.current_window]
            if window.current_line < len(window.content_lines) - 1:
                next_line = list(filter(lambda l: isinstance(l, TaskLine), window.content_lines[window.current_line + 1:]))
                if not next_line:
                    return
                next_line = next_line[0]
            self.model.swap_tasks(pos=element.task, pos2=next_line.task)
            self.reinit_modelview(line_offset=1)
        elif val.code == term.KEY_SUP:
            if not isinstance(element, TaskLine) or isinstance(element, AbstractTaskGroup):
                return

            window = self.windows[self.current_window]
            if window.current_line >= 0:
                next_line = list(filter(lambda l: isinstance(l, TaskLine), window.content_lines[window.current_line - 1:]))
                if not next_line:
                    return
                next_line = next_line[0]
            self.model.swap_tasks(pos=element.task, pos2=next_line.task)
            self.reinit_modelview(line_offset=-1)


        # =================== #
        # cursor on TaskGroup #
        # =================== #
        elif isinstance(element, AbstractTaskGroup):
            if element.edit_mode:

                # ESC to exit editmode & restore previous
                if val.code == term.KEY_ESCAPE:
                    element.task = element.previous_task
                    element.previous_task = None
                    element.set_editmode(False)
                    return

                # ENTER to exit editmode & save for all tasks in group
                elif val.code == term.KEY_ENTER:
                    element.set_editmode(False)
                    new_common_lists = set(element.task["lists"])
                    new_common_tags = set(element.task["tags"])
                    new_common_subtags = set(element.task["subtags"])

                    for task in element.get_all_tasks():
                        lists = set(task["lists"])
                        tags = set(task["tags"])
                        subtags = set(task["subtags"])

                        # remove differences from text
                        for t in element.common_lists.difference(new_common_lists):
                            task["text"].remove(t)
                        for t in element.common_tags.difference(new_common_tags):
                            task["text"].remove(t)
                        for t in element.common_subtags.difference(new_common_subtags):
                            task["text"].remove(t)

                        # add new to text
                        for t in new_common_subtags.difference(element.common_subtags):
                            task["text"].append(t)
                        for t in new_common_tags.difference(element.common_tags):
                            task["text"].append(t)
                        for t in new_common_lists.difference(element.common_lists):
                            task["text"].append(t)

                        # save new state for easier access
                        task["lists"] = list(lists.difference(element.common_lists).union(new_common_lists))
                        task["tags"] = list(tags.difference(element.common_tags).union(new_common_tags))
                        task["subtags"] = list(subtags.difference(element.common_subtags).union(new_common_subtags))

                        # update text-representation
                        task.update_rawtext()
                    self.model.save()
                    self.reinit_modelview(line_offset=-1)

        # ================== #
        # cursor on TaskLine #
        # ================== #
        elif isinstance(element, TaskLine):
            if element.edit_mode:

                # ESC to exit editmode & restore previous
                if val.code == term.KEY_ESCAPE:

                    element.task = element.previous_task
                    element.previous_task = None
                    element.set_editmode(False)
                    if "unsaved" in element.task:
                        element.task.model.remove_task(element.task)
                        window = self.windows[self.current_window]
                        window.lines.remove(element)
                        window.current_line -= 1
                        term.cursor.moveTo(window)
                        self.reinit_modelview(line_offset=0)
                    return

                # ENTER to exit editmode & save
                elif val.code == term.KEY_ENTER:
                    element.set_editmode(False)
                    if "unsaved" in element.task:
                        del element.task["unsaved"]
                    element.task.model.save()

                    self.reinit_modelview(line_offset=0)
                    return

            else:

                # CTRL + p to set priority
                if val == term.KEY_CTRL['p']:
                    element.set_editmode(True, charpos=0)
                    term.cursor.pos = element.pos + (len(element.prepend),0)
                    term.cursor.draw()
                    new_val = term.inkey()
                    if new_val.code == term.KEY_BACKSPACE:
                        element.task["priority"] = "M_"
                    else:
                        new_priority = str(new_val).upper()
                        if re_priority.match(new_priority):
                            element.task["priority"] = new_priority
                    element.set_editmode(False)
                    element.task.model.save()
                    return
        return super().onKeyPress(val)

    def reinit_modelview(self, line_offset = 0):

        # save cursor positions in each window
        win_title_str = lambda win: str(win.title.task) if isinstance(win.title, TaskLine) else win.title
        current_lines_per_window = {
            win_title_str(win): win.current_line for win in self.windows
        }

        self.elements = []
        self.init_modelview()

        # restore cursor positions in each window
        for win in self.windows:
            win.current_line = current_lines_per_window[win_title_str(win)]

        self.draw()
        if len(self.windows) <= self.current_window:
            self.current_window = len(self.windows) - 1
            self.window[self.current_window].current_line = 0
        if len(self.windows) > 0:
            window = self.windows[min(self.current_window, len(self.windows))]
        else:
            window = self.windows[len(self.current_window)-1]

        window.current_line += line_offset
        term.cursor.moveTo(window)

    def init_modelview(self):
        win_pos = 0
        listtag = None
        tag = None
        subtag = None
        new_window = True
        self.windows = []
        task_group = None
        subtask_group = None

        if self.sortmode == SortMode.GROUP_FULL:
            sort_by = ["lists", "tags","subtags","priority"]
        elif self.sortmode == SortMode.FILE:
            sort_by = []
        for l in self.model.query(filter=self.filter, sortBy=sort_by):
            # if "filter-sidebar" in l["raw_text"]:
            #     breakpoint()

            # new listname window
            # if l["lists"]:
            # breakpoint()
            if l["lists"] and listtag not in l["lists"]:
                # break
                listtag = l["lists"][0]
                new_window = True

            if new_window:
                win = TaskWindow((1 + win_pos,1),COLUMN_WIDTH, listtag.name if listtag else "Todos", parent=self)
                win.max_height = self.height - 1
                win_pos += COLUMN_WIDTH + WINDOW_MARGIN
                self.windows.append(win)
                new_window = False
                tag = None
                subtag = None
                task_group = None
                subtask_group = None

            # tag-line
            if l["tags"] and tag not in l["tags"]:
                if tag and TODO_STYLE==1:
                    win.add_emptyline()
                tag = l["tags"][0]
                task_group = win.add_taskgroup(tag, model=self.model)
                subtask_group = None
            elif not l["tags"]:
                task_group = None
                if tag:
                    win.add_emptyline()
                    tag = None
                subtask_group = None

            # subtag-line
            if l["subtags"] and subtag not in l["subtags"]:
                subtag = l["subtags"][0] if l["subtags"] else None
                subtask_group = task_group.add_taskgroup(term.dim+subtag.name, prepend=term.blue("· "), model=self.model)
            elif not l["subtags"]:
                subtag = None
                subtask_group = None

            # actual task
            (subtask_group if subtask_group else task_group if task_group else win).add_task(l, prepend="   " if l["subtags"] else "")

        # create a window if no entries exist
        if new_window:
            win = TaskWindow((1 + win_pos,1),COLUMN_WIDTH, listtag.name if listtag else "Todos", parent=self)
            self.windows.append(win)


        # pack windows if space is not sufficient
        if term.width < win_pos:
            self.draw()
            max_columns = term.width//(COLUMN_WIDTH+WINDOW_MARGIN)
            wins_to_stack = len(self.windows) - max_columns
            win_stacks = [[i] for i in range(len(self.windows))]


            # in this mode, we stack smallest windows until the stack-length equals the maximal number of columns
            if self.stackmode == StackMode.MERGE_SMALLEST:
                while len(win_stacks) > max_columns:
                    stack_heights = [sum(self.windows[i].height for i in stack) for stack in win_stacks]
                    smallest, second_smallest = sorted(np.argpartition(stack_heights, 2)[:2]) if len(stack_heights) > 2 else [0,1]
                    win_stacks[smallest] += win_stacks[second_smallest]
                    del win_stacks[second_smallest]

            # in this mode, we keep the order of the windows, stacking neighbouring windows by specifying the break positions in the window list
            elif self.stackmode == StackMode.KEEP_ORDER:
                win_heights = [w.height for w in self.windows]
                break_positions = [0]
                cumsum_heights = np.cumsum([0] + win_heights)
                target_height =  cumsum_heights[-1] // max_columns
                for i, cumsum in enumerate(cumsum_heights):
                    if cumsum >= cumsum_heights[break_positions[-1]] + target_height:
                        break_positions.append(i)
                break_positions.append(len(self.windows))

                win_stacks = [list(range(s_start,s_end)) for s_start, s_end in zip(break_positions, break_positions[1:])]

            # set positions from stacks
            for stack_i, stack in enumerate(win_stacks):
                current_height = 0
                for win_i in stack:
                    self.windows[win_i].rel_pos = (1+(COLUMN_WIDTH+WINDOW_MARGIN)*stack_i, 1+current_height)
                    current_height += min(self.windows[win_i].height, self.windows[win_i].max_height) if self.windows[win_i].max_height >= 0 else self.windows[win_i].height

                if 1 + current_height < term.height:
                    continue

                # set max-height if height exceeds terminal height
                win_heights = np.array([self.windows[i].height for i in stack])
                while 1 + win_heights.sum() > term.height:
                    win_heights[win_heights == np.max(win_heights)] -= 1
                for win_i, max_height in zip(stack, win_heights):
                    self.windows[win_i].max_height = max_height

                # reposition with new max_height
                current_height = 0
                for win_i in stack:
                    self.windows[win_i].rel_pos = (1+(COLUMN_WIDTH+WINDOW_MARGIN)*stack_i, 1+current_height)
                    current_height += min(self.windows[win_i].height, self.windows[win_i].max_height) if self.windows[win_i].max_height >= 0 else self.windows[win_i].height

            # re order windows based on stacks
            if self.stackmode == StackMode.MERGE_SMALLEST:
                new_window_order = []
                for stack in win_stacks:
                    for win_i in stack:
                        if self.windows[win_i].active:
                            self.current_window = len(new_window_order)
                        new_window_order.append(self.windows[win_i])
                self.windows = new_window_order

            self.draw()

