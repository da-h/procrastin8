from blessed import Terminal
import numpy as np

class Cursor:

    def __init__(self):
        self.pos = np.array((3,2))
        self.on_element = None
        self.last_position = (-1,-1)

    def moveTo(self, on_element):

        # elements are equal -> no change/events
        if self.on_element == on_element:
            return

        # Event: onUnfocus
        if self.on_element is not None:
            self.on_element.onUnfocus()

        self.on_element = self.on_element_current = on_element
        self.pos = self.on_element.pos
        # term.location(self.pos[0], self.pos[1])

        # Event: onFocus
        if self.on_element is not None:
            self.on_element.onFocus()

    def clear(self):
        self.on_element = None

    def isOnElement(self, elem):
        onelem = self.on_element
        if onelem == elem:
            return True
        while onelem.parent:
            onelem = onelem.parent
            if onelem == elem:
                return True
        return False

    def relativePos(self):
        if self.on_element is None:
            return self.pos

        return self.pos - self.on_element.pos

    def finalize(self):
        pass
        # changed = any(self.last_position != self.pos)
        # self.last_position = np.copy(self.pos)
        # if changed:
        #     self.on_element = self.on_element_current
        #     self.moveTo(self.on_element)
        #     self.on_element.onFocus()
        # return changed


class WorkitTerminal(Terminal):

    def __init__(self):
        super().__init__()
        self.cursor = Cursor()

    def move_xy(self, x, y=None):
        if type(x) is np.ndarray or isinstance(x, tuple):
            return super().move_xy(x[0],x[1])
        return super().move_xy(x,y)


