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
        self._is_draw_in_progress = False
        self._draw_semaphore = asyncio.Semaphore(1)
        self._more_draws_event = asyncio.Event()
        self._draw_task = None

        self.settingswin = SettingsWindow(Settings.get('appearance.column_width'), parent=self)
        self.settingswin.visible = False
        self.widgetbar = WidgetBar(parent=self)
        self.timewarriorwidget = TimeWarriorWidget(parent=self.widgetbar)
        self.widgetbar.widgets_left.append(self.timewarriorwidget)
        self.debugwindow = DebugWindow(parent=self, height=10)
        self.height = term.height - self.pos[1]
        self.task_visualizer = TaskVisualizer((0, self.widgetbar.height), self.height - self.debugwindow.height, model, filter, parent=self)

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

        term.main_window = self


    async def _dispatch_draw(self, reason=("Dashboard", )):
        await self._draw()
        await term.draw()



    async def dispatch_draw(self, reason=("Dashboard", )):
        if self._draw_semaphore.locked():
            # If a draw is in progress, just set the event
            self._more_draws_event.set()
        else:
            # Start the draw task if it's not already running
            self._draw_task = await asyncio.create_task(self._draw_after_delay())

    async def _draw_after_delay(self):
        while True:
            async with self._draw_semaphore:
                self._more_draws_event.clear()
                await self._dispatch_draw()

            await asyncio.sleep(0.01)  # Throttling

            # If no more draws, exit the loop
            if not self._more_draws_event.is_set():
                break

    async def loop(self, queue):
        with term.fullscreen():
            print(term.home + term.clear)
            await self.dispatch_draw()
            await term.cursor.moveTo(self)
            while self.continue_loop:
                key = await queue.get()
                if key and term.cursor.on_element:
                    await term.cursor.on_element.onKeyPress(key)

    async def onFocus(self):
        await term.cursor.moveTo(self.children[-1])

    async def onKeyPress(self, val):
        if val == "r":
            import numpy as np
            self.win.rel_pos = np.random.randint(0,50,(2,))

        if val == "q":
            term.cursor.show()
            self.continue_loop = False

        elif val == "u":
            self.model.undo_manager.undo()
            await self.task_visualizer.reinit_modelview()
        elif val == "R":
            self.model.undo_manager.redo()
            await self.task_visualizer.reinit_modelview()

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
        self.clear()

