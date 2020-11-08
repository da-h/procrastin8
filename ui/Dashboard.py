from datetime import datetime
from ui import get_term
from ui.UIElement import UIElement
from ui.windows.Sidebar import Sidebar
from ui.lines.RadioLine import RadioLine
from ui.lines.TaskLine import TaskLine
from ui.windows import TaskWindow
from settings import COLUMN_WIDTH, WINDOW_MARGIN, TODO_STYLE, AUTOADD_CREATIONDATE
from model import Tag, Subtag, List, re_priority

term = get_term()


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
        self.height = term.height
        self.filter = filter
        self.model = model
        self.overlay = None
        self.continue_loop = True
        self.windows = []
        self.current_window = 0
        self.init_modelview()

    def draw(self):
        with term.location():
            for elem in self.elements:
                if elem != self.overlay:
                    elem.draw()
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

        if val == "q":
            term.cursor.show()
            self.continue_loop = False
            return
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
        elif val == 'X':
            self.model.archive()
            self.elements = []
            self.init_modelview()
            self.draw()
            term.cursor.moveTo(self.elements[0])
        elif val == 'n':
            if isinstance(term.cursor.on_element, TaskLine):
                initial_text = " ".join([str(t) for t in term.cursor.on_element.text["subtags"]] + [str(t) for t in term.cursor.on_element.text["tags"]] + [str(t) for t in term.cursor.on_element.text["lists"]])
            elif isinstance(term.cursor.on_element, TaskWindow):
                initial_text = ""

            if AUTOADD_CREATIONDATE:
                initial_text = datetime.now().strftime("%Y-%m-%d") + initial_text

            if isinstance(term.cursor.on_element, TaskLine) and term.cursor.on_element.text["priority"] != "M_":
                initial_text = "("+term.cursor.on_element.text["priority"]+") " + initial_text

            task = self.model.new_task(initial_text, pos=term.cursor.on_element.text if isinstance(term.cursor.on_element, TaskLine) else 0)
            task["unsaved"] = True
            self.reinit_modelview(line_offset=+1)
            term.cursor.on_element.set_editmode(True)
        elif val == 'd':
            if not isinstance(term.cursor.on_element, TaskLine):
                return

            self.model.remove_task(pos=term.cursor.on_element.text)
            self.reinit_modelview(line_offset=0)
        elif val.code == term.KEY_SDOWN:
            if not isinstance(term.cursor.on_element, TaskLine):
                return

            window = self.windows[self.current_window]
            non_empty_lines = list(filter(lambda l: l.text, window.lines))
            if window.current_line < len(non_empty_lines) - 1:
                next_line = list(filter(lambda l: isinstance(l, TaskLine), non_empty_lines[window.current_line + 1:]))
                if not next_line:
                    return
                next_line = next_line[0]
            self.model.swap_tasks(pos=term.cursor.on_element.text, pos2=next_line.text)
            self.reinit_modelview(line_offset=1)
        elif val.code == term.KEY_SUP:
            if not isinstance(term.cursor.on_element, TaskLine):
                return

            window = self.windows[self.current_window]
            non_empty_lines = list(filter(lambda l: l.text, window.lines))
            if window.current_line >= 0:
                next_line = list(filter(lambda l: isinstance(l, TaskLine), non_empty_lines[window.current_line - 1:]))
                if not next_line:
                    return
                next_line = next_line[0]
            self.model.swap_tasks(pos=term.cursor.on_element.text, pos2=next_line.text)
            self.reinit_modelview(line_offset=-1)

        elif isinstance(element, TaskLine):
            if element.edit_mode:
                if val.code == term.KEY_ESCAPE:
                    element.set_editmode(False)
                    if "unsaved" in element.text:
                        element.text.model.remove_task(term.cursor.on_element.text)
                        window = self.windows[self.current_window]
                        window.lines.remove(term.cursor.on_element)
                        window.current_line -= 1
                        term.cursor.moveTo(window)
                    return
                elif val.code == term.KEY_ENTER:
                    element.set_editmode(False)
                    if "unsaved" in element.text:
                        del element.text["unsaved"]
                    element.text.model.save()

                    self.reinit_modelview(line_offset=0)
                    return
            else:
                if val == term.KEY_CTRL['p']:
                    element.set_editmode(True, charpos=0)
                    term.cursor.pos = element.pos + (len(element.prepend),0)
                    term.cursor.draw()
                    new_val = term.inkey()
                    if new_val.code == term.KEY_BACKSPACE:
                        element.text["priority"] = "M_"
                    else:
                        new_priority = str(new_val).upper()
                        if re_priority.match(new_priority):
                            element.text["priority"] = new_priority
                    element.set_editmode(False)
                    element.text.model.save()
                    return
        return super().onKeyPress(val)

    def reinit_modelview(self, line_offset = 0):
        current_line = self.windows[self.current_window].current_line
        self.elements = []
        self.init_modelview()
        self.draw()
        if len(self.windows) <= self.current_window:
            self.current_window = len(self.windows) - 1
            current_line = 0
        if len(self.windows) > 0:
            window = self.windows[min(self.current_window, len(self.windows))]
        else:
            window = self.windows[len(self.current_window)-1]
        window.current_line = current_line + line_offset
        term.cursor.moveTo(window)

    def init_modelview(self):
        win_pos = 0
        list = None
        tag = None
        subtag = None
        new_window = True
        self.windows = []
        for l in self.model.query(filter=self.filter, sortBy=["lists", "tags","subtags","priority"]):

            # new list window
            # if l["lists"]:
            # breakpoint()
            if l["lists"] and list not in l["lists"]:
                # break
                list = l["lists"][0]
                new_window = True

            if new_window:
                win = TaskWindow((1 + win_pos,1),COLUMN_WIDTH, list.name if list else "Todos", parent=self)
                win_pos += COLUMN_WIDTH + WINDOW_MARGIN
                self.windows.append(win)
                new_window = False
                tag = None
                subtag = None

            # tag-line
            if l["tags"] and tag not in l["tags"]:
                if tag and TODO_STYLE==1:
                    win.add_emptyline()
                tag = l["tags"][0]
                if TODO_STYLE == 2:
                    win.add_hline(term.cyan(tag.name), center=True)
                    win.add_emptyline()
                elif TODO_STYLE == 1:
                    win.add_line(term.cyan(tag.name))

            # subtag-line
            if l["subtags"] and subtag not in l["subtags"]:
                subtag = l["subtags"][0] if l["subtags"] else None
                win.add_line(term.cyan(term.dim+subtag.name), prepend=term.blue("· "))

            # actual task
            win.add_task(l, prepend="   " if l["subtags"] else "")

        # create a window if no entries exist
        if new_window:
            win = TaskWindow((1 + win_pos,1),COLUMN_WIDTH, list.name if list else "Todos", parent=self)
            self.windows.append(win)
