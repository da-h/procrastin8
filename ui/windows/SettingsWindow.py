from ui.lines.ElemWithLabel import ElemWithLabel
from ui.windows.TextWindow import TextWindow
from ui.UIElement import UIElement
from ui.lines.Line import Line
from ui.lines.HLine import HLine
from ui.lines.Line import Line
from ui.lines.RadioLine import RadioLine
from ui.lines.NumberInput import NumberInput
from ui import get_term
from ui.UIElement import UIElement
from ui.lines.RadioLine import RadioLine
from ui.widgets.TextWidget import TextWidget
from settings import Settings

term = get_term()


class SettingsWindow(TextWindow):
    def __init__(self, width, parent=None):
        width = 50
        super().__init__((term.width // 2 - width//2, 0), width=width, title="Settings", parent=parent)
        self.active_line = 0
        self.layer += 1

        # Dynamically create RadioLines for each setting in Settings.default_settings
        max_len = max(len(key) for key in Settings.default_settings().keys())
        for key, init_value in Settings.default_settings().items():
            value = Settings.get(key)
            if type(init_value) is bool:
                input_el_fn = lambda parent: RadioLine(["True", "False"], option=0 if value else 1, parent=parent)
            elif type(init_value) is int or type(init_value) is float:
                input_el_fn = lambda parent: NumberInput(value, parent=parent)
            else:
                raise ValueError("Not supported")
            space = " "*(max_len - len(key))
            line = ElemWithLabel(key+space, input_el_fn, parent=self)
            line.key = key
            line.type = type(init_value)
            self.lines.append(line)

    async def draw(self):
        with term.location():
            await super().draw()
            v_offset = 1
            for line in self.children:
                line.rel_pos[1] = v_offset
                line.typeset()
                v_offset += line.height
                await line.draw()

    async def onFocus(self):
        await term.cursor.moveTo(self.lines[self.active_line].elem)

    async def onContentChange(self, child_src, el_changed):
        if child_src.type == bool:
            Settings.set(child_src.key, child_src.elem.choices[child_src.elem.option])
        else:
            Settings.set(child_src.key, child_src.elem.value)
        await super().onContentChange(self, el_changed)

    async def onKeyPress(self, val):

        # Handle arrow key presses to navigate RadioLines
        if val.code == term.KEY_UP:
            self.lines[self.active_line].clear()
            self.active_line = (self.active_line - 1) % len(self.lines)
            self.lines[self.active_line].clear()
            await term.cursor.moveTo(self.lines[self.active_line])
            await self.draw()
            return
        elif val.code == term.KEY_DOWN:
            self.lines[self.active_line].clear()
            self.active_line = (self.active_line + 1) % len(self.lines)
            self.lines[self.active_line].clear()
            await term.cursor.moveTo(self.lines[self.active_line])
            await self.draw()
            return

        return await super().onKeyPress(val)
