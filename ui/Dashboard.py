import signal
from ui import get_term
from ui.UIElement import UIElement
from ui.WidgetBar import WidgetBar
from ui.widgets.TimeWarriorWidget import TimeWarriorWidget
from ui.DebugWindow import DebugWindow
from ui.windows import TaskWindow
from ui.TaskVisualizer import TaskVisualizer
from ui.windows.Sidebar import Sidebar
from ui.lines.RadioLine import RadioLine
from settings import Settings
import asyncio

term = get_term()


class Dashboard(UIElement):

    def __init__(self, model, filter=".*"):
        super().__init__((0,0))
        self.width = term.width
        self.model = model
        self.continue_loop = True

        self.widgetbar = WidgetBar(parent=self)
        self.timewarriorwidget = TimeWarriorWidget(parent=self.widgetbar)
        self.widgetbar.widgets_left.append(self.timewarriorwidget)
        self.debugwindow = DebugWindow(parent=self, height=10)
        self.height = term.height - self.pos[1]
        self.task_visualizer = TaskVisualizer((0, self.widgetbar.height), self.height - self.debugwindow.height, model, filter, parent=self)
        self.registered_redraw = False
        self.will_redraw_soon = False
        self.sidebar = None

        # signal: resize
        # - ensures that this function is not called on every resize-event
        self.resize_timer = None
        async def resize_finished():
            await asyncio.sleep(0.1)
            self.width = term.width
            self.height = term.height - self.pos[1] - 1
            self.debugwindow.clear()
            await self.reinit_modelview()
            await self.draw()
        async def on_resize():
            if self.resize_timer is not None:
                self.resize_timer.cancel()
            self.resize_timer = asyncio.create_task(resize_finished())
            await self.resize_timer
        loop = asyncio.get_event_loop()
        loop.add_signal_handler(signal.SIGWINCH, lambda: asyncio.ensure_future(on_resize()))

        # registers itself as main window
        term.main_window = self

    async def draw(self):
        # self.registered_redraw = False

        # debug
        # curframe = inspect.currentframe()
        # calframe = inspect.getouterframes(curframe, 2)
        # await term.log('caller name:' + calframe[1][3])

        # check what will be redrawn
        # print(term.clear)

        with term.location():
            self.debugwindow.log_draw_start()

            # self.debugwindow.pos[1] = -1
            await self.widgetbar.draw()
            # await self.debugwindow.draw()
            await self.task_visualizer.draw()

        # if self.registered_redraw:
        #     self.registered_redraw = False
        #     await self.draw()
            # return
        await term.draw()


    async def loop(self, queue):
        with term.fullscreen():
            print(term.home + term.clear)
            await self.draw()
            await term.cursor.moveTo(self)
            await self.draw()
            while self.continue_loop:
                key = await queue.get()
                if key and term.cursor.on_element:
                    self.will_redraw_soon = True
                    await term.cursor.on_element.onKeyPress(key)
                    self.will_redraw_soon = False
                    await self.draw()

    async def onElementClosed(self, el):
        if el == self.sidebar:
            await self.sidebar.clear_area()
            self.children.remove(el)
            self.sidebar = None
            await self.draw()

    async def onContentChange(self, child_src=None, el_changed=None):
        await super().onContentChange(child_src, el_changed)
        if not self.will_redraw_soon:
            await self.draw()

    async def onFocus(self):
        await term.cursor.moveTo(self.task_visualizer)

    async def onKeyPress(self, val):

        # =============== #
        # general actions #
        # =============== #

        # q to exit
        if val == "q":
            term.cursor.show()
            self.continue_loop = False

        # u to undo
        elif val == "u":
            self.model.undo_manager.undo()
            await self.reinit_modelview()
        elif val == "R":
            self.model.undo_manager.redo()
            await self.reinit_modelview()

        # s to open settings window
        elif val == "s":
            if self.sidebar is not None:
                self.sidebar.clear()
                self.sidebar = None
                await self.draw()
            else:
                await self.show_settings_sidebar()

    async def show_settings_sidebar(self):
        self.sidebar = Sidebar(Settings.get('COLUMN_WIDTH'), parent=self)
        await self.sidebar.draw()
        # await term.cursor.moveTo(self.sidebar.lines[0])

    async def reinit_modelview(self, line_offset = 0):
        await self.task_visualizer.reinit_modelview(line_offset)

    async def init_modelview(self):
        await self.task_visualizer.init_modelview()

