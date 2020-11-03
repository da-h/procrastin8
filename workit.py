from ui import get_term
from ui import Dashboard
from model import Model
import sys
from os.path import dirname, join

term = get_term()


def main():
    draw_calls = 0

    # init
    if len(sys.argv) == 1:
        todofile = "TODO.md"
        donefile = "DONE.md"
    else:
        todofile = sys.argv[-1]
        donefile = join(dirname(todofile), "done.md")
    model = Model("TODO.md", "DONE.md")
    dash = Dashboard(model)

    with term.fullscreen(), term.cbreak():#, term.hidden_cursor():
        dash.draw()
        term.cursor.moveTo(dash)
        dash.draw()
        dash.loop()

if __name__ == "__main__":
    main()
