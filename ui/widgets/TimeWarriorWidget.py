import asyncio
from ui.UIElement import UIElement
from ui.lines.Line import Line
from ui import get_term
term = get_term()


async def run(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()

    if stdout:
        stdout = stdout.decode()
    if stderr:
        stderr = stderr.decode()

    return stdout, stderr



class TimeWarriorWidget(Line):
    def __init__(self, parent=None):
        super().__init__("…", rel_pos=(0,0), parent=parent)
        self.height = 1
        self.width = len(self.text)
        self.line_style = term.blue+term.dim
        self.active = False
        self.prepend = "  "
        self.periodic_check = None
        self.timer = ""
        async def start_periodic_check():
            self.periodic_check = asyncio.create_task(self._update_tasks(1))
        asyncio.ensure_future(start_periodic_check())

    async def _update_tasks(self, every_seconds):
        while True:
            await self._update_tasks_now()

            # check this periodically
            await asyncio.sleep(every_seconds)

    def _clear_timer(self):
        self.timer = ""
        self.append = ""

    async def _update_tasks_now(self):
        if not self.edit_mode:
            last_append = self.append

            # check what tasks are currently worked on
            stdout, stderr = await run("timew")
            if stdout == "There is no active time tracking.\n":
                stdout = ""
                self._clear_timer()
            else:
                stdout_lines = stdout.split("\n")
                if len(stdout_lines) > 2:
                    self.timer = stdout_lines[3].split()[-1]
                    if self.active:
                        self.append = term.orange+term.dim+" (%s)" % self.timer
                    else:
                        self.append = ""
                else:
                    self._clear_timer()
                stdout = " ".join(stdout_lines[0].split(" ")[1:])

            # if the current tasks changed, set the new text
            if stdout != self.text and not self.edit_mode or last_append != self.append:
                await self._updateText(stdout)

    async def onKeyPress(self, val, orig_src=None, child_src=None):
        if self.edit_mode:
            if val.code == term.KEY_ESCAPE:
                await self._updateText(self.saved_text)
                await self.set_editmode(False)
                await term.cursor.moveTo(self.parent.parent)
                return
            elif val.code == term.KEY_ENTER:
                cmd = self.text + " "
                if cmd.strip().split(" ")[0] == "cont":
                    await run("timew cont")
                elif cmd.strip().split(" ")[0] == "":
                    await run("timew stop")
                else:
                    await run("timew start "+cmd)
                await self._update_tasks_now()
                await self.set_editmode(False)
                await term.cursor.moveTo(self.parent.parent)
                return
        else:
            if val == "i" or val == "e":
                self._clear_timer()
                await self.set_editmode(True)
                return
            elif val == "I":
                self._clear_timer()
                await self.set_editmode(True)
                return
            elif val == "A":
                self._clear_timer()
                await self.set_editmode(True, charpos=len(self.text), firstchar=2)
                return
            elif val == "S":
                self._clear_timer()
                await self._updateText("")
                await self.set_editmode(True, charpos=len(self.text), firstchar=2)
                return
            elif val == "x":
                self._clear_timer()
                await self._updateText("")
                await run("timew stop")
                return
            elif val == "d":
                self._clear_timer()
                await self._updateText("")
                await run("timew delete @1")
                return
        return await super().onKeyPress(val, orig_src=orig_src)

    async def set_editmode(self, mode: bool, charpos: int=0, firstchar: int=0):
        self.timer = ""
        if mode:
            self.saved_text = self.text
            self.prepend = term.black_on_blue("›")+term.normal+" "
            if self.periodic_check:
                self.periodic_check.cancel()
        else:
            self.saved_text = None
            self.prepend = "  "
            self.periodic_check = asyncio.create_task(self._update_tasks(2))
        await super().set_editmode(mode, charpos, firstchar)

    async def onFocus(self, orig_src=None, child_src=None):
        if child_src is None:
            self.active = True
            self.line_style = term.yellow
            if not self.edit_mode:
                self.prepend = term.orange("›")+term.normal+" "
                if self.timer:
                    self.append = term.orange+term.dim+" (%s)" % self.timer
        await super().onFocus(orig_src=orig_src)

    async def onUnfocus(self, orig_src=None, child_src=None):
        if child_src is None:
            self.active = False
            self.line_style = term.blue+term.dim
            self.prepend = "  "
            self._clear_timer()
            self.clear() # removing what has been appended needs a complete refresh
        await super().onFocus(orig_src=orig_src)
