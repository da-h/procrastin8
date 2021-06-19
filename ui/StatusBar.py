from ui.UIElement import UIElement
from ui import get_term
from blessed.sequences import Sequence
from time import time
term = get_term()

def current_milli_time():
    return round(time() * 1000)

class StatusBar(UIElement):

    def __init__(self):
        super().__init__((0,0))
        self.height = 10
        self.width = term.width
        self.status = "ok"
        self.draw_calls = 0
        self._redraw_start = current_milli_time()

    def log_draw_start(self):
        self._redraw_start = current_milli_time()

    async def draw(self, **draw_args):
        await super().draw()
        self.draw_calls += 1
        if self.status:
            msg_l = term.dim + "Status " + term.green + self.status + term.normal
            msg_r = term.dim + "Draws: " + term.green + str(self.draw_calls) + term.normal
            cur_time = current_milli_time()
            msg_r += "  " + term.dim + "Redraw Time: " + term.green + str(cur_time - self._redraw_start) + "ms" + term.normal
            msg_r = Sequence(msg_r, term)
            self.printAt((1,0), msg_l)
            self.printAt((self.width - msg_r.length() - 1,0), msg_r)

        if self.height > 2:
            self.printAt((0,1), term.dim + "─"*self.width+term.normal)
        for i, l in enumerate(term._log_msgs):
            self.printAt((0,i+2), term.dim + "   "+str(l)+term.normal)
        self._redraw_start = cur_time
