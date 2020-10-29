from ui import term, TaskWindow, TaskLine, COLUMN_WIDTH, SettingsWindow, Line, Cursor
from model import Model


draw_calls = 0
def redraw():
    global draw_calls
    print(term.move_y(term.height - 4) + term.center('draw() calls: %i' % draw_calls).rstrip())
    print(term.move_y(term.height - 3) + term.center('cursor: '+str(term.cursor.pos)).rstrip())
    print(term.move_y(term.height - 2) + term.center('element: '+str(term.cursor.on_element) if term.cursor.on_element else "").rstrip())
    draw_calls += 1

def main():
    draw_calls = 0
    model = Model()
    with term.fullscreen(), term.cbreak(), term.hidden_cursor():

        win = TaskWindow((1,1),COLUMN_WIDTH, "Title")
        for l in model.todo:
            win.add_line(l)

        win.draw()
        term.cursor.finalize()
        win.draw()
        redraw()

        overlay = None

        # set cursor position
        val = ''
        while val.lower() != 'q':
            val = term.inkey()
            if val == "s" and overlay is None:
                overlay = SettingsWindow(COLUMN_WIDTH)
                overlay.draw()
                term.cursor.moveTo(overlay.lines[0])
                redraw()
            elif val:
                term.cursor.on_element.cursorAction(val)

            win.draw()
            if overlay:
                overlay.draw()
            term.cursor.finalize()
            redraw()

if __name__ == "__main__":
    main()
