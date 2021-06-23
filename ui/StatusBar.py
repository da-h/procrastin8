from ui.UIElement import UIElement
from ui import get_term
from blessed.sequences import Sequence
from time import time
from asyncio import sleep, Lock, create_task
term = get_term()

def current_milli_time():
    return round(time() * 1000)

class StatusBar(UIElement):

    def __init__(self):
        super().__init__((0,0))
        self.height = 1
        self.width = term.width
        self.status = ""
        self.redraw_info = True
        self.draw_calls = 0
        self._redraw_start = current_milli_time()
        self.status_lock = Lock()
        self.status_clear_timer = None

    def log_draw_start(self):
        self._redraw_start = current_milli_time()

    async def clear_status(self, *msg):
        await sleep(2.5)
        await self.status_lock.acquire()
        self.status = " ".join([str(m) for m in msg])
        await term.main_window.draw()
        self.status_lock.release()
    async def _show_status(self, *msg):
        await self.status_lock.acquire()
        if self.status_clear_timer is not None:
            self.status_clear_timer.cancel()
        self.status = " ".join([str(m) for m in msg])
        await sleep(0.05)
        await term.main_window.draw()
        self.status_lock.release()
        self.status_clear_timer = create_task(self.clear_status())
    async def show_status(self, *msg):
        create_task(self._show_status(*msg))

    async def draw(self, **draw_args):
        await super().draw()
        self.draw_calls += 1
        cur_time = current_milli_time()

        self.clear("statusinfo")
        if e := self.element("statusinfo"):
            with e:
                if self.status:
                    msg_l = term.dim + "Status " + term.green + self.status + term.normal
                    self.printAt((1,0), msg_l)

        # we want the redraw_info to redraw every time
        if self.redraw_info:
            self.clear("redraw_info")
            if e := self.element("redraw_info"):
                with e:
                    msg_r = term.dim + "Draws: " + term.green + str(self.draw_calls) + term.normal
                    msg_r += term.dim + " (" + \
                                term.green + "+"+str(len(term.buffered_print)) + term.normal + "/" + \
                                term.red + "-"+str(len(term.buffered_delete)) + term.normal + ")"
                    msg_r += "  " + term.dim + "Redraw Time: " + term.green + str(cur_time - self._redraw_start) + "ms" + term.normal
                    msg_r = Sequence(msg_r, term)
                    self.printAt((self.width - msg_r.length() - 1,0), msg_r)

        if self.height > 2:
            self.printAt((0,1), term.dim + "─"*self.width+term.normal)
        for i in range(self.height):
            self.printAt((0,i+2), " "*term.width)
        for i, l in enumerate(term._log_msgs[-self.height+3:]):
        # for i, l in enumerate(list(term.buffered_print.values())[-2*self.height:-3-self.height]):
            self.printAt((0,i+2), term.dim + "   "+str(l)[:self.width-5]+term.normal)
        self._redraw_start = cur_time
