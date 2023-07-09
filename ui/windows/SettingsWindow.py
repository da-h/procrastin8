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
from ui.lines.Line import Line
from settings import Settings

term = get_term()


class SettingsWindow(TextWindow):
    def __init__(self, width, parent=None):
        width = 50
        super().__init__((term.width // 2 - width//2, term.height // 2 - sum(len(category) + 3 for category in Settings.default_settings().values())), width=width, title="Settings", parent=parent)
        self.current_line = 0
        self.layer = self.parent.layer + 1

        # Dynamically create UIElements for each setting in Settings.default_settings
        max_len = max(len(key) for category in Settings.default_settings().values() for key in category.keys())
        for category, settings in Settings.default_settings().items():
            # self.lines.append(HLine(parent=self))
            self.lines.append(Line("", parent=self))
            self.lines.append(Line(category.title(), line_style=term.bold_red, parent=self))
            self.lines.append(HLine(parent=self))
            for key, init_value in settings.items():
                value = Settings.get(f"{category}.{key}")
                if isinstance(init_value, bool):
                    input_el_fn = lambda parent: RadioLine(["True", "False"], option=0 if value else 1, parent=parent)
                elif isinstance(init_value, int) or isinstance(init_value, float):
                    input_el_fn = lambda parent: NumberInput(value, parent=parent)
                else:
                    input_el_fn = lambda parent: Line([str(value)], parent=parent)
                space = " "*(max_len - len(key))
                line = ElemWithLabel(key+space, input_el_fn, parent=self)
                line.key = f"{category}.{key}"
                line.type = type(init_value)
                self.lines.append(line)
                self.content_lines.append(line)
            self.lines.append(Line("", parent=self))

    async def onContentChange(self, orig_src, child_src):
        if child_src.type == bool:
            Settings.set(child_src.key, child_src.elem.choices[child_src.elem.option] == "True")
        else:
            Settings.set(child_src.key, child_src.elem.value)
        await super().onContentChange(self, orig_src)
