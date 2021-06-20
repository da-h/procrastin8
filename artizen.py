from ui import get_term
from ui import Dashboard
from model import Model
import sys
from os.path import dirname, join
import asyncio
from asyncio import Queue
import threading

term = get_term()

def main():

    # init
    if len(sys.argv) == 1:
        todofile = "todo.txt"
        donefile = "done.txt"
    elif len(sys.argv) >= 2:
        todofile = sys.argv[1]
        donefile = join(dirname(todofile), "done.txt")

    if len(sys.argv) == 3:
        filter = sys.argv[-1]
    else:
        filter = ".*"
    model = Model(todofile, donefile)
    dash = Dashboard(model, filter)

    loop = asyncio.get_event_loop()

    queue = Queue()
    t = threading.Thread(target=term.threaded_inkey, args=[queue])
    t.start()
    loop.run_until_complete(dash.loop(queue))

if __name__ == "__main__":
    main()
