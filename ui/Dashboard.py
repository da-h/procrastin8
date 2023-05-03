import signal
from ui import get_term
from ui.UIElement import UIElement
from ui.WidgetBar import WidgetBar
from ui.widgets.TimeWarriorWidget import TimeWarriorWidget
from ui.DebugWindow import DebugWindow
from ui.windows import TaskWindow
from ui.TaskVisualizer import TaskVisualizer
from ui.windows.SettingsWindow import SettingsWindow
from ui.lines.RadioLine import RadioLine
from settings import Settings
import asyncio
from ui.windows import TextWindow

term = get_term()


class Dashboard(UIElement):

    def __init__(self, model, filter=".*"):
        super().__init__((0,0))
        self.width = term.width
        self.model = model
        self.continue_loop = True

        self.settingswin = SettingsWindow(Settings.get('appearance.column_width'), parent=self)
        self.settingswin.visible = False
        self.widgetbar = WidgetBar(parent=self)
        self.timewarriorwidget = TimeWarriorWidget(parent=self.widgetbar)
        self.widgetbar.widgets_left.append(self.timewarriorwidget)
        self.debugwindow = DebugWindow(parent=self, height=10)
        self.height = term.height - self.pos[1]
        self.task_visualizer = TaskVisualizer((0, self.widgetbar.height), self.height - self.debugwindow.height, model, filter, parent=self)
        # self.win = TaskWindow((10,20), 45, title="blub", parent=self)
        # # self.win = TextWindow((10,20), 45, title="blub", parent=self)
        # self.win.add_line("l1")
        # self.win.add_line("l2")
        # self.win.add_line("l3")
        # self.win.max_height = 100

        # signal: resize
        # - ensures that this function is not called on every resize-event
        self.resize_timer = None
        async def resize_finished():
            await asyncio.sleep(0.1)
            self.width = term.width
            self.height = term.height - self.pos[1] - 1
            self.debugwindow.clear()
            await self.task_visualizer.reinit_modelview()
            await self.dispatch_draw()
        async def on_resize():
            if self.resize_timer is not None:
                self.resize_timer.cancel()
            self.resize_timer = asyncio.create_task(resize_finished())
            await self.resize_timer
        loop = asyncio.get_event_loop()
        loop.add_signal_handler(signal.SIGWINCH, lambda: asyncio.ensure_future(on_resize()))

        # registers itself as main window
        term.main_window = self


    async def dispatch_draw(self, reason=("Dashboard", )):
        # await term.log(reason)
        await self._draw()
        await term.draw()

    async def loop(self, queue):
        with term.fullscreen():
            print(term.home + term.clear)
            await self.dispatch_draw()
            await term.cursor.moveTo(self)
            while self.continue_loop:
                key = await queue.get()
                if key and term.cursor.on_element:
                    await term.cursor.on_element.onKeyPress(key)
                    # await self.dispatch_draw()

    # async def onContentChange(self, child_src=None, el_changed=None):
    #     if child_src == self.settingswin:
    #         await self.task_visualizer.reinit_modelview()
    #         await term.cursor.moveTo(self.settingswin)
    #         self.clear()
    #         # await self.dispatch_draw()
    #
    #     await super().onContentChange(child_src, el_changed)
    #     # await self.dispatch_draw()

    async def onFocus(self):
        await term.cursor.moveTo(self.children[-1])
    # async def onFocus(self):
    #     await term.cursor.moveTo(self.win)

    async def onKeyPress(self, val):

        # =============== #
        # general actions #
        # =============== #

        # q to exit
        if val == "r":
            import numpy as np
            self.win.rel_pos = np.random.randint(0,50,(2,))


        # q to exit
        if val == "q":
            term.cursor.show()
            self.continue_loop = False

        # u to undo
        elif val == "u":
            self.model.undo_manager.undo()
            await self.task_visualizer.reinit_modelview()
        elif val == "R":
            self.model.undo_manager.redo()
            await self.task_visualizer.reinit_modelview()

        # s to open settings window
        elif val == "s":
            await self.toggle_settings()

    async def toggle_settings(self):
        self.settingswin.visible = not self.settingswin.visible
        if self.settingswin.visible:
            await term.cursor.moveTo(self.settingswin)
            await self.settingswin.draw()
        else:
            self.settingswin.clear()
            await term.cursor.moveTo(self)
            # await self.settingswin.draw()
            # await self.dispatch_draw()
        self.clear()
        # await self.dispatch_draw()

