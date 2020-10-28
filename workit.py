from ui import term, Window, COLUMN_WIDTH, cursor




with term.fullscreen(), term.cbreak(), term.hidden_cursor():
    print(term.move_y(term.height // 2) + term.center('press any key').rstrip())

    win = Window((1,1),COLUMN_WIDTH, "title")
    win.draw()

    # set cursor position
    val = ''
    while val.lower() != 'q':
        val = term.inkey(timeout=3)
        if val:
            cursor.on_element.cursorAction(val)

        cursor.clear()

        win.draw()
        cursor.draw()
