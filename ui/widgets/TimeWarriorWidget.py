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
        self.prepend = "  "
        self.periodic_check = None
        async def start_periodic_check():
            self.periodic_check = asyncio.create_task(self._update_tasks(2))
        asyncio.ensure_future(start_periodic_check())

    async def _update_tasks(self, every_seconds):
        while True:
            await self._update_tasks_now()

            # check this periodically
            await asyncio.sleep(every_seconds)

    async def _update_tasks_now(self):
        if not self.edit_mode:

            # check what tasks are currently worked on
            stdout, stderr = await run("timew")
            if stdout == "There is no active time tracking.\n":
                stdout = ""
            else:
                stdout = " ".join(stdout.split("\n")[0].split(" ")[1:])

            # if the current tasks changed, set the new text
            if stdout != self.text and not self.edit_mode:
                await self._updateText(stdout)
                await self.onContentChange()

    async def onKeyPress(self, val):
        if self.edit_mode:
            if val.code == term.KEY_ESCAPE:
                await self._updateText(self.saved_text, call_onContentChange=False)
                await self.set_editmode(False)
                await term.cursor.moveTo(self.parent.parent)
                await self.onContentChange()
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
                await self.set_editmode(True)
                return
            elif val == "I":
                await self.set_editmode(True)
                return
            elif val == "A":
                await self.set_editmode(True, charpos=len(self.text), firstchar=2)
                return
            elif val == "S":
                await self._updateText("")
                await self.set_editmode(True, charpos=len(self.text), firstchar=2)
                return
            elif val == "x":
                await self._updateText("")
                await run("timew stop")
                return
            elif val == "d":
                await self._updateText("")
                await run("timew delete @1")
                return
        return await super().onKeyPress(val)

    async def set_editmode(self, mode: bool, charpos: int=0, firstchar: int=0):
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

    async def onFocus(self):
        if not self.edit_mode:
            self.prepend = term.blue("›")+term.normal+" "
            await self.onContentChange()
        await super().onFocus()

    async def onUnfocus(self):
        self.prepend = "  "
        await self.onContentChange()
        await super().onFocus()
