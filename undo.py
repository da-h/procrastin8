import os
import shutil

class UndoManager:
    def __init__(self, model, undo_directory="undos"):
        self.model = model
        self.undo_directory = undo_directory
        self.undo_counter = 0
        self.redo_counter = 0

        if not os.path.exists(self.undo_directory):
            os.makedirs(self.undo_directory)

    def record_operation(self):
        undo_file = os.path.join(self.undo_directory, f"undo_{self.undo_counter}.txt")

        # Save the current state of the model's todofile to an undo file
        shutil.copy(self.model.todofile, undo_file)

        # Increment the undo counter
        self.undo_counter += 1

        # Reset the redo counter
        self.redo_counter = 0

        # Cleanup unnecessary undo/redo files
        self.cleanup_undo_files()

    def undo(self):
        if self.undo_counter > 0:
            undo_file = os.path.join(self.undo_directory, f"undo_{self.undo_counter - 1}.txt")
            shutil.copy(undo_file, self.model.todofile)
            self.model.reload()
            self.undo_counter -= 1
            self.cleanup_undo_files()
            self.redo_counter += 1

    def redo(self):
        if self.redo_counter == 0:
            # print("No redo operation available.")
            return

        redo_file = os.path.join(self.undo_directory, f"undo_{self.undo_counter}.txt")
        if not os.path.exists(redo_file):
            # print("Redo file not found.")
            return

        # Copy redo_file to the model's todofile
        shutil.copy(redo_file, self.model.todofile)

        # Update the model
        self.model.load_from_file()

        # Update the counters
        self.redo_counter -= 1
        self.undo_counter += 1

    def cleanup_undo_files(self):
        # Remove unnecessary redo files
        for i in range(self.undo_counter + self.redo_counter, self.undo_counter * 2):
            file_path = os.path.join(self.undo_directory, f"undo_{i}.txt")
            if os.path.exists(file_path):
                os.remove(file_path)

        # Reset the redo counter
        self.redo_counter = 0

