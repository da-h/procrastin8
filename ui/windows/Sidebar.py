from ui.windows.TextWindow import TextWindow
from ui.UIElement import UIElement
from ui.lines.RadioLine import RadioLine
from ui import get_term
from ui.UIElement import UIElement
from ui.lines.RadioLine import RadioLine
from ui.widgets.TextWidget import TextWidget
from settings import Settings

term = get_term()

class SettingsWidget(UIElement):
    def __init__(self, parent=None):
        super().__init__((0, 0), parent=parent)

        # Sample settings content for each category
        self.general = TextWidget("General settings:\n- Setting 1\n- Setting 2", parent=self)
        self.projects = TextWidget("Projects settings:\n- Setting 1\n- Setting 2", parent=self)
        self.notifications = TextWidget("Notifications settings:\n- Setting 1\n- Setting 2", parent=self)

    async def draw(self):
        with term.location():
            await self.general.draw()
            await self.projects.draw()
            await self.notifications.draw()


class Sidebar(UIElement):
    def __init__(self, width, parent=None):
        super().__init__((parent.width - width, 0), parent=parent)
        self.width = width
        self.settings_widget = SettingsWidget(parent=self)
        self.lines = [
            RadioLine("General", ["On", "Off"], parent=self),
            RadioLine("Projects", ["On", "Off"], parent=self),
            RadioLine("Notifications", ["On", "Off"], parent=self)
        ]
        self.active_line = 0
        self.lines[self.active_line].selected = True

    async def draw(self):
        with term.location():
            v_offset = 0
            for line in self.lines:
                line.rel_pos = (0, v_offset)
                v_offset += line.height
                await line.draw()

    async def onKeyPress(self, val):
        # s to close the sidebar
        if val == "s":
            await self.close()
            self.parent.sidebar = None
            await self.parent.draw()
        else:
            await super().onKeyPress(val)

            # Handle arrow key presses to navigate RadioLines
            if val.code == term.KEY_UP:
                self.active_line = (self.active_line - 1) % len(self.radio_lines)
                for line in self.radio_lines:
                    line.selected = False
                self.radio_lines[self.active_line].selected = True
                await self.draw()
            elif val.code == term.KEY_DOWN:
                self.active_line = (self.active_line + 1) % len(self.radio_lines)
                for line in self.radio_lines:
                    line.selected = False
                self.radio_lines[self.active_line].selected = True
                await self.draw()
            elif val.code in [term.KEY_LEFT, term.KEY_RIGHT]:
                await self.radio_lines[self.active_line].onKeyPress(val)
                await self.draw()
