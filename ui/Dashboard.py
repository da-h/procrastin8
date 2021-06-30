import signal
from itertools import chain
from datetime import datetime
import numpy as np
from ui import get_term
from ui.UIElement import UIElement
from ui.WidgetBar import WidgetBar
from ui.DebugWindow import DebugWindow
from ui.windows.Sidebar import Sidebar
from ui.lines.RadioLine import RadioLine
from ui.lines.TaskLine import TaskLine
from ui.util.AbstractTaskGroup import AbstractTaskGroup
from ui.windows import TaskWindow
from settings import COLUMN_WIDTH, WINDOW_MARGIN, TODO_STYLE, AUTOADD_CREATIONDATE, WINDOW_PADDING
from model import Task, Tag, Subtag, List, re_priority
from enum import Enum
import asyncio
import inspect

term = get_term()


class StackMode(Enum):
    MERGE_SMALLEST = 0
    KEEP_ORDER = 1
    KEEP_ORDER_EQUAL_SIZES = 2
class SortMode(Enum):
    FILE = 0
    GROUP_FULL = 1


class Dashboard(UIElement):

    def __init__(self, model, filter=".*"):
        super().__init__((0,0))
        self.width = term.width
        self.filter = filter
        self.model = model
        self.continue_loop = True
        self.windows = []
        self.marked = []
        self.current_window = 0
        # self.stackmode = StackMode.MERGE_SMALLEST
        self.stackmode = StackMode.KEEP_ORDER
        # self.stackmode = StackMode.KEEP_ORDER_EQUAL_SIZES
        # self.sortmode = SortMode.GROUP_FULL
        self.sortmode = SortMode.FILE
        self.task_groups = []
        self.subtask_groups = []
        self.tasks = []
        self.widgetbar = WidgetBar(parent=self)
        self.debugwindow = DebugWindow(parent=self, height=10)
        self.height = term.height - self.pos[1] - self.widgetbar.height
        self.inited = False
        self.registered_redraw = False

        # signal: resize
        # - ensures that this function is not called on every resize-event
        self.resize_timer = None
        async def resize_finished():
            await asyncio.sleep(0.1)
            self.width = term.width
            self.height = term.height - self.pos[1] - 1
            self.debugwindow.clear()
            await self.reinit_modelview()
            await self.draw()
        async def on_resize():
            if self.resize_timer is not None:
                self.resize_timer.cancel()
            self.resize_timer = asyncio.create_task(resize_finished())
            await self.resize_timer
        loop = asyncio.get_event_loop()
        loop.add_signal_handler(signal.SIGWINCH, lambda: asyncio.ensure_future(on_resize()))

        # registers itself as main window
        term.main_window = self

    async def redraw(self):
        self.registered_redraw = True

    async def draw(self):
        # self.registered_redraw = False

        # debug
        # curframe = inspect.currentframe()
        # calframe = inspect.getouterframes(curframe, 2)
        # await term.log('caller name:' + calframe[1][3])

        if not self.inited:
            self.inited = True
            await self.init_modelview()

        # check what will be redrawn
        # print(term.clear)

        with term.location():
            self.debugwindow.log_draw_start()

            for elem in self.windows:
                await elem.draw()

            if e := self.element("marked"):
                with e:
                    for i, elem in enumerate(self.marked):
                        self.printAt(elem.pos - self.pos + (-1,0), term.yellow("┃"), ignore_padding=True)
                        str_num = str(i+1)
                        self.printAt(elem.pos - self.pos + (COLUMN_WIDTH-WINDOW_PADDING*2-len(str_num)-1,0), term.bold_yellow(str_num), ignore_padding=True)

            # self.debugwindow.pos[1] = -1
            await self.widgetbar.draw()
            await self.debugwindow.draw()

        # if self.registered_redraw:
        #     self.registered_redraw = False
        #     await self.draw()
            # return
        await term.draw()


    async def loop(self, queue):
        with term.fullscreen():
            print(term.home + term.clear)
            await self.draw()
            await term.cursor.moveTo(self)
            await self.draw()
            while self.continue_loop:
                key = await queue.get()
                if key and term.cursor.on_element:
                    await term.cursor.on_element.onKeyPress(key)
                    await self.draw()

    async def onFocus(self):
        if len(self.windows):
            await term.cursor.moveTo(self.windows[0])

    async def onContentChange(self, child_src=None, el_changed=None):
        if isinstance(child_src, TaskWindow):
            self.clear("marked")
        await super().onContentChange(child_src, el_changed)

    async def onElementClosed(self, elem):
        self.children.remove(elem)
        if elem in self.windows:
            self.windows.remove(elem)
        await self.draw()
        if term.cursor.isOnElement(elem):
            await term.cursor.moveTo(self.windows[0])

    async def onKeyPress(self, val):
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
        # UP/DOWN (window catches this event unless first/last task is under cursor) to move to next/previous task 
        elif val.code == term.KEY_RIGHT or val.code == term.KEY_DOWN or val == 'j':
            last_window = self.current_window
            self.current_window = min(self.current_window + 1, len(self.windows)-1)
            if self.current_window != last_window:
                if val.code == term.KEY_DOWN or val == 'j':
                    self.windows[self.current_window].current_line = 0
                await term.cursor.moveTo(self.windows[self.current_window])
            return
        elif val.code == term.KEY_LEFT or val.code == term.KEY_UP or val == 'k':
            last_window = self.current_window
            self.current_window = max(self.current_window - 1, 0)
            if self.current_window != last_window:
                if val.code == term.KEY_UP or val == 'k':
                    self.windows[self.current_window].current_line = len(self.windows[self.current_window].lines) - 1
                await term.cursor.moveTo(self.windows[self.current_window])
            return

        # s to open settings window
        # elif val == "s" and self.overlay is None:
        #     # self.overlay = Prompt(COLUMN_WIDTH, parent=self)
        #     self.overlay = Sidebar(COLUMN_WIDTH, parent=self)
        #     await self.overlay.draw()
        #     self.rel_pos = (COLUMN_WIDTH,0)
        #     self.overlay.rel_pos = (-COLUMN_WIDTH,0)
        #     self.overlay.add_emptyline()
        #     self.overlay.lines.append(RadioLine("Verbosity",["Small","Medium","Full"], wrapper=self.overlay.wrapper, parent=self.overlay))
        #
        #
        #     old_elem = await term.cursor.moveTo(self.overlay.lines[0])
        #     return

        # X to Archive done tasks
        elif val == 'X':
            self.model.archive()
            await self.reinit_modelview()
            await term.cursor.moveTo(self.windows[0])

        # Ctrl+r to save order of current view
        elif self.sortmode != SortMode.FILE and val == term.KEY_CTRL['r']:
            tasks = list(chain.from_iterable([win.get_all_tasks() for win in self.windows]))
            self.model.save_order(tasks)
            await self.reinit_modelview()

        # Ctrl+r to move marked children to the top
        elif self.sortmode == SortMode.FILE and val == term.KEY_CTRL['r']:
            all_tasks = list(chain.from_iterable([win.get_all_tasks() for win in self.windows]))
            marked_tasks = [m.task for m in self.marked]
            for t in marked_tasks:
                all_tasks.remove(t)
            tasks = marked_tasks + all_tasks
            self.marked = []
            self.clear("marked")
            self.model.save_order(tasks)
            await self.reinit_modelview()

        elif val == term.KEY_CTRL['o']:
            marked_tasks = [m.task for m in self.marked]
            sort_by = ["lists", "tags","subtags","priority"]
            marked_tasks = self.model.query(filter=marked_tasks, sortBy=sort_by)
            self.marked = []
            self.clear("marked")
            self.model.save_order(marked_tasks)
            await self.reinit_modelview()

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
            self.clear("marked")

        # n to create new task
        elif val == 'n' or val == 'N':
            if isinstance(element, AbstractTaskGroup):
                element._update_common_tags()
                if val == 'N':
                    initial_text = " ".join([str(t) for t in element.common_lists])
                else:
                    initial_text = " ".join([str(t) for t in element.common_subtags] + [str(t) for t in element.common_tags] + [str(t) for t in element.common_lists])
            elif isinstance(element, TaskLine):
                if val == 'N':
                    initial_text = " ".join([str(t) for t in element.task["subtags"]] + [str(t) for t in element.task["tags"]] + [str(t) for t in element.task["lists"]])
                else:
                    initial_text = " ".join([str(t) for t in element.task["subtags"]] + [str(t) for t in element.task["tags"]] + [str(t) for t in element.task["lists"]])

            if AUTOADD_CREATIONDATE:
                initial_text = datetime.now().strftime("%Y-%m-%d") + " " + initial_text

            if isinstance(element, TaskLine) and element.task["priority"] != "M_":
                initial_text = "("+element.task["priority"]+") " + initial_text


            pos = element.get_all_tasks()[0] if isinstance(element, AbstractTaskGroup) else element.task
            offset = 0 if val == 'N' or isinstance(element, AbstractTaskGroup) else 1
            task = self.model.new_task(initial_text, pos=pos, offset=offset)
            task["unsaved"] = True
            if isinstance(element, AbstractTaskGroup) and isinstance(element.taskline_container, TaskWindow):
                offset += 1
            await self.reinit_modelview(line_offset=offset if val == 'N' else 1)
            await term.cursor.on_element.set_editmode(True)

        # d to delete current task
        elif val == 'd':
            if not isinstance(element, TaskLine) or isinstance(element, AbstractTaskGroup):
                return

            self.model.remove_task(pos=element.task)
            await self.reinit_modelview(line_offset=0)

        # d to delete current task
        elif (val == 'm' or val == 'M' or val == 'p' or val == 'P') and len(self.marked):

            marked_tasks = [t.task for t in self.marked]
            cursor_tasks = element.get_all_tasks()

            target_task = cursor_tasks[-1 if val == 'p' or val == 'm' else 0]
            before = val == 'P' or val == 'M'
            if target_task in marked_tasks:
                return

            # in case we are pasting into another group (and not moving)
            if val == 'p' or val == 'P':

                # we need to calculate the differences between the old sets and the new sets
                # to adapt the task["text"]
                target_lists = set(target_task["lists"])
                target_tags = set(target_task["tags"])
                target_subtags = set(target_task["subtags"])

                for task in marked_tasks:

                    # save lists/tags/subtags
                    task_lists = set(task["lists"])
                    task_tags = set(task["tags"])
                    task_subtags = set(task["subtags"])

                    # remove differences from text
                    for t in task_lists.difference(target_lists):
                        task["text"].remove(t)
                    for t in task_tags.difference(target_tags):
                        task["text"].remove(t)
                    for t in task_subtags.difference(target_subtags):
                        task["text"].remove(t)

                    # add new to text
                    for t in target_subtags.difference(task_subtags):
                        task["text"].append(t)
                    for t in target_tags.difference(task_tags):
                        task["text"].append(t)
                    for t in target_lists.difference(task_lists):
                        task["text"].append(t)

                    # save new state for easier access
                    task["lists"] = list(target_lists)
                    task["tags"] = list(target_tags)
                    task["subtags"] = list(target_subtags)

                    task.update_rawtext()

            self.model.move_to(marked_tasks, target_task, before=before)
            self.model.save()
            self.marked = []
            self.clear("marked")
            await self.reinit_modelview(line_offset=0)

        elif val.code == term.KEY_ESCAPE and len(self.marked):
            self.marked = []
            self.clear("marked")

        # Shift + UP/DOWN to swap tasks up/down
        elif val.code == term.KEY_SDOWN or val.code == term.KEY_SUP:

            # check what type of element we are on right now
            if isinstance(element, AbstractTaskGroup):
                if element.prepend:
                    # skip subtask groups
                    the_list = self.subtask_groups
                    return
                else:
                    the_list = self.task_groups
            else:
                the_list = self.tasks

            ind = the_list.index(element)

            if val.code == term.KEY_SDOWN:
                if ind == len(the_list) - 1:
                    return
                dir = 1
            else: # KEY_SUP
                if ind == 0:
                    return
                ind -= 1
                dir = -1

            tasks = the_list[ind+1].get_all_tasks() + the_list[ind].get_all_tasks()
            self.model.save_order(tasks)

            window = self.windows[self.current_window]
            await self.reinit_modelview(line_offset=dir*(len(tasks)-1))


        # =================== #
        # cursor on TaskGroup #
        # =================== #
        elif isinstance(element, AbstractTaskGroup):
            if element.edit_mode:

                # ESC to exit editmode & restore previous
                if val.code == term.KEY_ESCAPE:
                    element.task = element.previous_task
                    element.previous_task = None
                    await element.set_editmode(False)
                    return

                # ENTER to exit editmode & save for all tasks in group
                elif val.code == term.KEY_ENTER:
                    await element.set_editmode(False)
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
                    await self.reinit_modelview(line_offset=-1)

        # ================== #
        # cursor on TaskLine #
        # ================== #
        elif isinstance(element, TaskLine):
            if element.edit_mode:

                # ESC to exit editmode & restore previous
                if val.code == term.KEY_ESCAPE:

                    element.task = element.previous_task
                    element.previous_task = None
                    await element.set_editmode(False)
                    if "unsaved" in element.task:
                        element.task.model.remove_task(element.task)
                        window = self.windows[self.current_window]
                        window.lines.remove(element)
                        window.current_line -= 1
                        await term.cursor.moveTo(window)
                        await self.reinit_modelview(line_offset=0)
                    return

                # ENTER to exit editmode & save
                elif val.code == term.KEY_ENTER:
                    await element.set_editmode(False)
                    if "unsaved" in element.task:
                        del element.task["unsaved"]
                    element.task.model.save()

                    await self.reinit_modelview(line_offset=0)
                    return

            else:

                # CTRL + p to set priority
                if val == term.KEY_CTRL['p']:
                    await element.set_editmode(True, charpos=0)
                    term.cursor.pos = element.pos + (len(element.prepend),0)
                    await term.cursor.draw()
                    new_val = term.inkey()
                    if new_val.code == term.KEY_BACKSPACE:
                        element.task["priority"] = "M_"
                    else:
                        new_priority = str(new_val).upper()
                        if re_priority.match(new_priority):
                            element.task["priority"] = new_priority
                    await element.set_editmode(False)
                    element.task.model.save()
                    return
        return await super().onKeyPress(val)

    async def reinit_modelview(self, line_offset = 0):

        # save cursor positions in each window
        win_title_str = lambda win: str(win.title.task) if isinstance(win.title, TaskLine) else win.title
        current_lines_per_window = {
            win_title_str(win): win.current_line for win in self.windows
        }

        self.clear()
        for w in self.windows:
            self.children.remove(w)
        self.windows = []
        await self.init_modelview()

        # restore cursor positions in each window
        for win in self.windows:
            win_title = win_title_str(win)
            if win_title in current_lines_per_window:
                win.current_line = current_lines_per_window[win_title]

        await self.draw()
        if len(self.windows) < self.current_window:
            self.current_window = len(self.windows) - 1
            self.window[self.current_window].current_line = 0
        if len(self.windows) > 0:
            window = self.windows[min(self.current_window, len(self.windows)-1)]
        else:
            window = self.windows[0]

        window.current_line += line_offset
        await term.cursor.moveTo(window)

    async def init_modelview(self):
        win_pos = 0
        listtag = None
        tag = None
        subtag = None
        new_window = True
        self.windows = []
        task_group = None
        subtask_group = None
        level_change = False

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
                win = TaskWindow((1 + win_pos, self.widgetbar.height),COLUMN_WIDTH, listtag.name if listtag else "Todos", parent=self)
                win.max_height = self.height - self.debugwindow.height
                win_pos += COLUMN_WIDTH + WINDOW_MARGIN
                self.windows.append(win)
                new_window = False
                tag = None
                subtag = None
                task_group = None
                subtask_group = None

            # tag-line
            if l["tags"] and tag not in l["tags"]:
                if len(win.lines) > 0 and TODO_STYLE==1:
                    win.add_emptyline()
                tag = l["tags"][0]
                task_group = win.add_taskgroup(tag, model=self.model)
                self.task_groups.append(task_group)
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
                self.subtask_groups.append(subtask_group)
            elif not l["subtags"]:
                subtag = None
                subtask_group = None
                # level_change = True

            # actual task
            task = (subtask_group if subtask_group else task_group if task_group else win).add_task(l, prepend="   " if l["subtags"] else "")
            self.tasks.append(task)

        # create a window if no entries exist
        if new_window:
            win = TaskWindow((1 + win_pos, self.widgetbar.height),COLUMN_WIDTH, listtag.name if listtag else "Todos", parent=self)
            self.windows.append(win)


        # pack windows if space is not sufficient
        if term.width < win_pos:
            await self.draw()
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
            elif self.stackmode == StackMode.KEEP_ORDER or self.stackmode == StackMode.KEEP_ORDER_EQUAL_SIZES:
                win_heights = [w.height for w in self.windows]
                break_positions = [0]
                cumsum_heights = np.cumsum([0] + win_heights)
                if self.stackmode == StackMode.KEEP_ORDER:
                    target_height =  self.height
                else:
                    target_height =  cumsum_heights[-1] // max_columns
                offset = 0
                for i, cumsum in enumerate(cumsum_heights):
                    if cumsum >= cumsum_heights[break_positions[-1]] + target_height - offset:

                        if self.stackmode == StackMode.KEEP_ORDER_EQUAL_SIZES:
                            break_positions.append(i)
                            offset += cumsum - target_height
                        else:
                            break_positions.append(i - 1)

                    if self.stackmode == StackMode.KEEP_ORDER and len(break_positions) == max_columns:
                        break
                break_positions.append(len(self.windows))

                win_stacks = [list(range(s_start,s_end)) for s_start, s_end in zip(break_positions, break_positions[1:])]


            # set positions from stacks
            for stack_i, stack in enumerate(win_stacks):
                current_height = 0
                for win_i in stack:
                    self.windows[win_i].rel_pos = (1+(COLUMN_WIDTH+WINDOW_MARGIN)*stack_i, self.widgetbar.height+current_height)
                    current_height += min(self.windows[win_i].height, self.windows[win_i].max_height) if self.windows[win_i].max_height >= 0 else self.windows[win_i].height

                if 1 + current_height < self.height:
                    continue

                # set max-height if height exceeds terminal height
                win_heights = np.array([self.windows[i].height for i in stack])
                while 1 + win_heights.sum() > self.height:
                    win_heights[win_heights == np.max(win_heights)] -= 1
                for win_i, max_height in zip(stack, win_heights):
                    self.windows[win_i].max_height = max_height

                # reposition with new max_height
                current_height = 0
                for win_i in stack:
                    self.windows[win_i].rel_pos = (1+(COLUMN_WIDTH+WINDOW_MARGIN)*stack_i, self.widgetbar.height+current_height)
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

            await self.draw()



