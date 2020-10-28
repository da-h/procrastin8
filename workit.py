from ui import term, Window, Line, COLUMN_WIDTH
from model import Model


def main():
    model = Model()
    with term.fullscreen(), term.cbreak(), term.hidden_cursor():
        print(term.move_y(term.height // 2) + term.center('press any key').rstrip())

        win = Window((1,1),COLUMN_WIDTH, "title")
        win.lines = [Line(l, parent=win) for l in model.todo]
        win.draw()

        # set cursor position
        val = ''
        while val.lower() != 'q':
            val = term.inkey(timeout=3)
            if val:
                term.cursor.on_element.cursorAction(val)
            term.cursor.clear()
            win.draw()
            term.cursor.draw()


if __name__ == "__main__":
    main()
