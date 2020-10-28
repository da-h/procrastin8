from ui import term, TextWindow, TaskLine, COLUMN_WIDTH, SettingsWindow, Line, Cursor
from model import Model


def main():
    model = Model()
    with term.fullscreen(), term.cbreak(), term.hidden_cursor():
        print(term.move_y(term.height // 2) + term.center('press any key').rstrip())

        win = TextWindow((1,1),COLUMN_WIDTH, "Title")
        win.lines = [TaskLine(l, parent=win) for l in model.todo]
        win.draw()

        overlay = None

        # set cursor position
        val = ''
        while val.lower() != 'q':
            val = term.inkey()
            if val == "s":
                overlay = SettingsWindow(COLUMN_WIDTH)
                overlay.lines = [Line("blub"),Line("bla")]
            if val:
                term.cursor.on_element.cursorAction(val)
            term.cursor.clear()

            if term.cursor.on_element:
                term.cursor.on_element.draw()
            win.draw()
            # if overlay:
            #     overlay.draw()
            # term.cursor.draw()


if __name__ == "__main__":
    main()
