from ui.windows.TextWindow import TextWindow
from ui.UIElement import UIElement
from ui.lines.RadioLine import RadioLine
from ui import get_term
term = get_term()


# class Sidebar(TextWindow):
#
#     def __init__(self, width, parent=None):
#         rel_pos = (0,0)
#         super().__init__(rel_pos, width=width, title="Settings", parent=parent)
#         self.draw_style = "basic-left-edge"
#
#         self.lines.append(RadioLine("Verbosity",["Small","Medium","Full"], wrapper=self.wrapper, parent=self))
#         # self.lines.append(RadioLine("Verbosity",["Small","Medium","Full"], wrapper=self.wrapper, parent=self))
#         # self.lines.append(RadioLine("Verbosity",["Small","Medium","Full"], wrapper=self.wrapper, parent=self))
#
#     async def onKeyPress(self, val):
#         if val == "s":
#             await self.close()
#             return
#         return await super().onKeyPress(val)
#
#
#

from ui.UIElement import UIElement
from ui.lines.RadioLine import RadioLine
from ui.widgets.TextWidget import TextWidget

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
            RadioLine("General", ["On", "Off"], self.settings_widget.general, parent=self),
            RadioLine("Projects", ["On", "Off"], self.settings_widget.projects, parent=self),
            RadioLine("Notifications", ["On", "Off"], self.settings_widget.notifications, parent=self)
        ]
        self.active_line = 0
        self.lines[self.active_line].selected = True

    async def draw(self):
        with term.location():
            for line in self.lines:
                await line.draw()

    async def onKeyPress(self, val):
        # s to close the sidebar
        if val == "s":
            await self.close()
            self.parent.sidebar = None
            await self.parent.draw()
        else:
            await super().onKeyPress(val)
