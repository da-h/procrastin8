import numpy as np
from blessed.sequences import Sequence
from ui import get_term
import asyncio

term = get_term()


class UIElementTerminalBridge(object):

    def __init__(self, uiel, element_label):
        self.uiel = uiel
        self.subelements = [] # low-level drawing units
        self.label = element_label
        self.dirty = True
        self.always_dirty = False

    def printAt(self, rel_pos, *args, ignore_padding=False):
        if not self.uiel.visible:
            return
        seq = Sequence(*args, term)
        pos = self.uiel.pos + rel_pos + (0 if ignore_padding else (self.uiel.padding[0],self.uiel.padding[2]))

        if self.uiel.max_height == 0:
            return
        if self.uiel.max_height > 0 and (rel_pos[1] if ignore_padding else rel_pos[1] + self.uiel.padding[0] + self.uiel.padding[2]) >= self.uiel.max_height:
            return

        # tell terminal what to print
        # (it remembers all calls under the name of the with-statement)
        self.subelements.append(((pos[0],pos[1]), seq))
        term.printAt(pos, seq, self.uiel.layer)

    # tell terminal what element to delete
    def clear(self):
        for pos, seq in self.subelements:
            term.removeAt(pos, seq, layer=self.uiel.layer)
        self.subelements = []
        self.dirty = True


class UIElement(object):
    __initialized = False
    def __init__(self, rel_pos=None, parent=None, max_height=-1, padding=(0,0,0,0), layer=None):
        if not rel_pos and not parent:
            raise ValueError("Either position or parent have to be specified")
        if parent:
            parent.children.append(self)
        self.visible = True
        self.parent = parent
        self.padding = padding
        self.max_height = max_height
        self._rel_pos = np.array(rel_pos) if rel_pos else np.array((0,0))
        self.layer = parent.layer + 1 if layer is None and parent is not None else 0
        self.dirty = True

        self.children = [] # true uielements

        self._elements = {}
        self._prop_elem_connections = {}
        self._prop_vals = {}
        self.__initialized = True

    def registerProperty(self, name, value, element_labels):
        if isinstance(element_labels, str):
            element_labels = [element_labels]
        if name in self._prop_vals:
            self._prop_elem_connections[name] += element_labels
        else:
            self._prop_elem_connections[name] = element_labels
        self._prop_vals[name] = value

    def chainProperty(self, src_element_label, element_labels):
        if isinstance(element_labels, str):
            element_labels = [element_labels]
        for name in self._prop_vals:
            if src_element_label in self._prop_elem_connections[name]:
                self._prop_elem_connections[name] += element_labels

    def __getattr__(self, name):
        if name in self._prop_vals.keys():
            return self._prop_vals[name]
        if name in self.__dict__:
            return self.__dict__[name]
        return False
    def __setattr__(self, name, value):
        if self.__initialized and name in self._prop_vals.keys():
            if self._prop_vals[name] == value:
                return
            labels = self._prop_elem_connections[name]
            for label in labels:
                self.element(label, getalways=True).clear()
            self._prop_vals[name] = value
            asyncio.create_task(self.mark_dirty((self, name, value)))
            return
        object.__setattr__(self, name, value)

    async def mark_dirty(self, reason=None, layer=None):
        if layer is None:
            layer = self.layer
        self.dirty = True
        if self.parent is not None:
            if not self.parent.dirty:
                if self.parent.layer <= layer:
                    self.parent.clear()
                await self.parent.mark_dirty(reason, layer)
        else:
            await self.dispatch_draw(reason)

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
        if a[0] != self._rel_pos[0] and a[1] != self._rel_pos[1]:
            if self.__initialized:
                self.clear()
                asyncio.create_task(self.mark_dirty((self, "rel_pos")))
        self._rel_pos = np.array(a)

    def element(self, element_label, getalways=False):
        if element_label in self._elements:
            if not getalways:
                if not self._elements[element_label].dirty:
                    return False
                self._elements[element_label].dirty = False
            return self._elements[element_label]
        element = UIElementTerminalBridge(self, element_label)
        self._elements[element_label] = element
        return element

    async def _draw(self):
        if (not self.dirty and not self.always_dirty) or not self.visible:
            return
        self.__initialized = True

        await self.draw()
        self.dirty = False

        for child in self.children:
            await child._draw()

    async def draw(self):
        pass

    def clear(self, element_labels=[]):
        if isinstance(element_labels, str):
            element_labels = [element_labels]
        if len(element_labels) == 0:
            element_labels = self._elements.keys()
        for label in element_labels:
            self.element(label, getalways=True).clear()
        self.dirty = True
        for c in self.children:
            c.clear()

    async def close(self):
        if self.parent:
            await self.parent.onElementClosed(self)

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
        await self.onChildFocused()

    async def onChildFocused(self, child_src=None, el_focused=None):
        if el_focused is None:
            el_focused = self
        if self.parent:
            await self.parent.onChildFocused(self, el_focused)

    async def onUnfocus(self):
        await self.onChildUnfocused()

    async def onChildUnfocused(self, child_src=None, el_unfocused=None):
        if el_unfocused is None:
            el_unfocused = self
        if self.parent:
            await self.parent.onChildUnfocused(self, el_unfocused)

    async def onSizeChange(self, child_src=None, el_changed=[]):
        if self.parent:
            await self.parent.onSizeChange(self, el_changed + [self])

    async def onContentChange(self, child_src=None, el_changed=None):
        await self.mark_dirty((self, "onContentChange"))
        if el_changed is None:
            el_changed = self
        if self.parent:
            await self.parent.onContentChange(self, el_changed)

    async def onEnter(self):
        if self.parent and self.parent not in term.cursor.elements_under_cursor_before:
            await self.parent.onEnter()

    async def onLeave(self):
        if self.parent and self.parent not in term.cursor.elements_under_cursor_after:
            await self.parent.onLeave()

    async def onElementClosed(self, elem):
        if self.parent is not None:
            await self.parent.onElementClosed(elem)
