from ui import get_term
from ui.windows import TaskWindow
from ui import Dashboard
from settings import COLUMN_WIDTH
from model import Model, Tag

term = get_term()


def main():
    draw_calls = 0

    # init
    model = Model("TODO.md")
    dash = Dashboard(model)

    win = TaskWindow((1,1),COLUMN_WIDTH, "Title")
    tag = None
    subtag = None
    for l in model.sortBy(["tags","subtags"]):

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
    dash.manage(win)

    with term.fullscreen(), term.cbreak():#, term.hidden_cursor():
        dash.draw()
        term.cursor.moveTo(dash)
        dash.draw()
        dash.loop()

if __name__ == "__main__":
    main()
