from ui import term, TaskWindow, TaskLine, COLUMN_WIDTH, SettingsWindow, Line, Cursor
from model import Model


draw_calls = 0
def redraw():
    global draw_calls
    print(term.move_y(term.height // 2) + term.center('draw() calls: %i' % draw_calls).rstrip())
    draw_calls += 1

def main():
    draw_calls = 0
    model = Model()
    with term.fullscreen(), term.cbreak(), term.hidden_cursor():
        print(term.move_y(term.height // 2) + term.center('press any key').rstrip())

        win = TaskWindow((1,1),COLUMN_WIDTH, "Title")
        for l in model.todo:
            win.add_line(l)

        while term.redraw:
            term.redraw = False
            win.draw()
            redraw()

        overlay = None

        # set cursor position
        val = ''
        while val.lower() != 'q':
            val = term.inkey()
            if val == "s":
                overlay = SettingsWindow(COLUMN_WIDTH)
                overlay.draw()
                term.cursor.moveTo(overlay.lines[0])
            if val:
                term.cursor.on_element.cursorAction(val)

            while term.redraw:
                term.redraw = False
                win.draw()
                redraw()

if __name__ == "__main__":
    main()
