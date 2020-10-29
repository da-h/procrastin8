from ui import term, TaskWindow, TaskLine, COLUMN_WIDTH, SettingsWindow, Line, Cursor, Dashboard
from model import Model


def main():
    draw_calls = 0

    # init
    model = Model()
    dash = Dashboard(model)

    win = TaskWindow((1,1),COLUMN_WIDTH, "Title")
    for l in model.todo:
        win.add_line(l)

    dash.manage(win)
    with term.fullscreen(), term.cbreak(), term.hidden_cursor():
        dash.draw()
        term.cursor.moveTo(dash)
        dash.draw()
        dash.loop()

if __name__ == "__main__":
    main()
