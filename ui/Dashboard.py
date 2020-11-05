from blessed.sequences import Sequence
from ui import get_term
from ui.UIElement import UIElement
from ui.windows.Sidebar import Sidebar
from ui.lines.RadioLine import RadioLine
from ui.lines.TaskLine import TaskLine
from ui.windows import TaskWindow
from settings import COLUMN_WIDTH
from model import Tag, Subtag, List

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

    def __init__(self, model):
        super().__init__((0,0))
        self.width = term.width
        self.height = term.height
        self.model = model
        self.overlay = None
        self.continue_loop = True
        self.init_modelview()

    def draw(self, clean=False):
        with term.location():
            for elem in self.elements:
                if elem != self.overlay:
                    elem.draw(clean)
            if self.overlay:
                self.overlay.draw(True)
        redraw()
        term.cursor.finalize(term)

    def loop(self):
        val = ''
        while self.continue_loop:
            val = term.inkey(esc_delay=0)
            if val and term.cursor.on_element:
                term.cursor.on_element.onKeyPress(val)

            # self.clear()
            self.draw()

    def onFocus(self):
        if len(self.elements):
            term.cursor.moveTo(self.elements[0])

    def onElementClosed(self, elem):
        self.elements.remove(elem)
        if elem == self.overlay:
            self.overlay = None
        self.draw(True)
        if term.cursor.isOnElement(elem):
            term.cursor.moveTo(self.elements[0])

    def onKeyPress(self, val):
        if val == "q":
            self.continue_loop = False
            return
        elif val == "+":
            self.rel_pos += (4,3)
            return
        elif val == "-":
            self.rel_pos += (-4,-3)
            return
        elif val == "s" and self.overlay is None:
            # self.overlay = Prompt(COLUMN_WIDTH, parent=self)
            self.overlay = Sidebar(COLUMN_WIDTH, parent=self)
            self.overlay.draw()
            self.rel_pos = (COLUMN_WIDTH,0)
            self.overlay.rel_pos = (-COLUMN_WIDTH,0)
            self.manage(self.overlay)
            self.overlay.add_emptyline()
            self.overlay.lines.append(RadioLine("Verbosity",["Small","Medium","Full"], wrapper=self.overlay.wrapper, parent=self.overlay))
            self.overlay.manage(self.overlay.lines[-1])


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
                initial_text = " ".join([str(Subtag(t)) for t in term.cursor.on_element.text["subtags"]] + [str(Tag(t)) for t in term.cursor.on_element.text["tags"]] + [str(List(t)) for t in term.cursor.on_element.text["lists"]])
            else:
                return

            # get index of cursor
            # TODO: make this nicer & correct
            window_under_cursor = term.cursor.on_element.parent
            non_empty_lines = list(filter(lambda l: l.text, window_under_cursor.lines))
            index = non_empty_lines.index(term.cursor.on_element)
            self.model.new_task(initial_text, pos=term.cursor.on_element.text)
            self.elements = []
            self.init_modelview()
            self.draw()
            window_under_cursor = self.elements[0]
            non_empty_lines = list(filter(lambda l: l.text, window_under_cursor.lines))
            term.cursor.moveTo(non_empty_lines[index+1])
            term.cursor.on_element.set_editmode(True)
        elif val == 'd':
            if isinstance(term.cursor.on_element, TaskLine):
                pass
            else:
                return

            # get index of cursor
            # TODO: make this nicer & correct
            window_under_cursor = term.cursor.on_element.parent
            non_empty_lines = list(filter(lambda l: l.text, window_under_cursor.lines))
            index = non_empty_lines.index(term.cursor.on_element)
            self.model.remove_task(pos=term.cursor.on_element.text)
            self.elements = []
            self.init_modelview()
            self.draw()
            window_under_cursor = self.elements[0]
            non_empty_lines = list(filter(lambda l: l.text, window_under_cursor.lines))
            term.cursor.moveTo(non_empty_lines[min(index,len(self.model.todo))])
        return super().onKeyPress(val)


    def init_modelview(self):
        win = TaskWindow((1,1),COLUMN_WIDTH, "Todos")
        tag = None
        subtag = None
        for l in self.model.query(sortBy=["lists", "tags","subtags"]):

            # tag-line
            if l["tags"] and tag not in l["tags"]:
                # win.add_hline(term.white(tag))
                if tag:
                    win.add_emptyline()
                tag = l["tags"][0]
                win.add_line(term.cyan(tag))

            # subtag-line
            if l["subtags"] and subtag not in l["subtags"]:
                subtag = l["subtags"][0] if l["subtags"] else None
                win.add_line(term.cyan(term.dim+subtag), prepend=term.blue("· "))

            # actual task
            win.add_task(l, prepend="   " if l["subtags"] else "")
        self.manage(win)
