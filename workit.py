from ui import term, TaskWindow, COLUMN_WIDTH, Dashboard
from model import Model, Tag


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
            tag = l["tags"][0]
            # win.add_hline(term.white(tag))
            win.add_line("")
            win.add_line(term.white(tag))

        # subtag-line
        if l["subtags"] and subtag not in l["subtags"]:
            subtag = l["subtags"][0] if l["subtags"] else None
            win.add_line(term.underline(term.white(term.dim+subtag)), prepend="  ")

        # actual task
        win.add_task(l, prepend="   " if l["subtags"] else "")
    dash.manage(win)

    with term.fullscreen(), term.cbreak(), term.hidden_cursor():
        dash.draw()
        term.cursor.moveTo(dash)
        dash.draw()
        dash.loop()

if __name__ == "__main__":
    main()
