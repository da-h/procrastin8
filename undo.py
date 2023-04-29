import os
import shutil
from pathlib import Path


class UndoManager:
    def __init__(self, model, undo_directory="undos"):
        self.model = model
        self.undo_directory = undo_directory
        self.undo_counter = 0
        Path(self.undo_directory).mkdir(parents=True, exist_ok=True)

    def record_operation(self):
        undo_file = os.path.join(self.undo_directory, f"undo_{self.undo_counter}.txt")
        shutil.copy(self.model.todofile, undo_file)
        self.undo_counter += 1

    def undo(self):
        if self.undo_counter > 0:
            self.undo_counter -= 1
            undo_file = os.path.join(self.undo_directory, f"undo_{self.undo_counter}.txt")
            shutil.copy(undo_file, self.model.todofile)
            self.model.reload()
            os.remove(undo_file)
