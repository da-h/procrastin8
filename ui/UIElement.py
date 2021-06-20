import numpy as np
from blessed.sequences import Sequence
from ui import get_term

term = get_term()


class UIElementTerminalBridge(object):

    def __init__(self):
        self.history = []
        self.elements = {} # low-level drawing units

    @property
    def name(self):
        if len(self.history):
            return self.history[-1]
        return "main"

    def __call__(self, name):
        if name in self.elements:
            return False
        self.elements[name] = []
        self.history.append(name)
        return self
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        del self.history[-1]

    # tell terminal what to print
    # (it remembers all calls under the name of the with-statement)
    def printAt(self, pos, seq):
        if self.name not in self.elements:
            self.elements[self.name] = []
        self.elements[self.name].append(((pos[0],pos[1]), seq))
        term.printAt(pos, seq)

    # tell terminal what element to delete
    def remove(self, element):
        if element not in self.elements:
            return
        for pos, seq in self.elements[element]:
            term.removeAt(pos, seq)
        del self.elements[element]
    def removeAll(self):
        for e in list(self.elements.keys()):
            self.remove(e)

    def redraw(self, element):
        if element in self.elements:
            del self.elements[element]


class UIElement(object):
    __initialized = False
    def __init__(self, rel_pos=None, parent=None, max_height=-1, padding=(0,0,0,0)):
        if not rel_pos and not parent:
            raise ValueError("Either position or parent have to be specified")
        if parent:
            parent.children.append(self)
        self.parent = parent
        self.padding = padding
        self.max_height = max_height
        self._rel_pos = np.array(rel_pos) if rel_pos else np.array((0,0))
        self.pos_changed = False

        self.children = [] # true uielements
        self.element = UIElementTerminalBridge() # remembers all printed low-level drawing units

        self._prop_elem_connections = {}
        self._prop_vals = {}
        self.__initialized = True

    def registerProperty(self, name, value, elements):
        if name in self._prop_vals:
            self._prop_elem_connections[name] += elements
        else:
            self._prop_elem_connections[name] = elements
        self._prop_vals[name] = value

    def __getattr__(self, name):
        if name in self._prop_vals.keys():
            return self._prop_vals[name]
        return self.__dict__[name]
    def __setattr__(self, name, value):
        if self.__initialized and name in self._prop_vals.keys():
            els = self._prop_elem_connections[name]
            if len(els) == 0:
                self.element.removeAll()
            else:
                for el in els:
                    self.element.remove(el)
            self._prop_vals[name] = value
            return
        object.__setattr__(self, name, value)

    @property
    def pos(self):
        if self.parent:
            return self.parent.pos + self.rel_pos
        return self.rel_pos

    @property
    def rel_pos(self):
        return self._rel_pos
    @rel_pos.setter
    def rel_pos(self, a):
        if (a[0], a[1]) != (self._rel_pos[0], self._rel_pos[1]):
            self.pos_changed = True
        self._rel_pos = np.array(a)

    async def redraw(self, element=None):
        if element:
            self.element.redraw(element)
        if self.parent:
            await self.parent.redraw()

    async def draw(self):
        if self.pos_changed:
            self.clear()
            self.pos_changed = False

    def clear(self, elements=[]):
        if len(elements) == 0:
            self.element.removeAll()
        for e in elements:
            self.element.remove(e)

    async def close(self):
        if self.parent:
            await self.parent.onElementClosed(self)

    def printAt(self, rel_pos, *args, ignore_padding=False):
        seq = Sequence(*args,term)
        pos = self.pos + rel_pos + (0 if ignore_padding else (self.padding[0],self.padding[2]))

        if self.max_height == 0:
            return
        if self.max_height > 0 and (rel_pos[1] if ignore_padding else rel_pos[1] + self.padding[0] + self.padding[2]) >= self.max_height:
            return

        self.element.printAt(pos, seq)

    def get_parents(self):
        parents = []
        n = self
        while n.parent:
            n = n.parent
            parents.append(n)
        return parents


    # ------ #
    # Events #
    # ------ #
    async def onKeyPress(self, val):
        if self.parent is not None:
            await self.parent.onKeyPress(val)

    async def onFocus(self):
        pass

    async def onUnfocus(self):
        pass

    async def onSizeChange(self, child_src=None, el_changed=[]):
        if self.parent:
            await self.parent.onSizeChange(self, el_changed + [self])

    async def onContentChange(self, child_src=None, el_changed=None):
        if self.parent:
            await self.parent.onContentChange(self, el_changed)

    async def onEnter(self):
        # await term.log("enter"+str(self))
        if self.parent and self.parent not in term.cursor.elements_under_cursor_before:
            await self.parent.onEnter()

    async def onLeave(self):
        # await term.log("leave"+str(self))
        if self.parent and self.parent not in term.cursor.elements_under_cursor_after:
            await self.parent.onLeave()

    async def onElementClosed(self, elem):
        if self.parent is not None:
            await self.parent.onElementClosed(elem)
