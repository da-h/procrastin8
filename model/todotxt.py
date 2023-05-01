from __future__ import annotations
import re
import os
from pathlib import Path
from undo import UndoManager
from typing import List, Union
from model.basemodel import Task, List


class TodotxtModel:
    """
    A class representing the todo manager's model.

    Manages tasks, tags, subtags, and lists, and provides methods for loading, saving, and querying tasks.
    """

    def __init__(self, todofile: str, donefile: str):
        self.todofile = todofile
        self.donefile = donefile
        self.undo_manager = UndoManager(self)

        self.lists = {}
        self.tags = {}
        self.subtags = {}

        self.load_from_file()

        self.lists = {}
        self.tags = {}
        self.subtags = {}


    def load_from_file(self) -> None:
        """
        Load tasks from the todofile into the model's task list.
        """
        self.todo = []
        with open(self.todofile, "r") as file:
            for line_no, t in enumerate(file):
                if not t.strip():
                    continue

                task = Task.from_rawtext(self, t, line_no=line_no)
                self.todo.append(task)

    def save(self) -> None:
        """
        Save the model's tasks to the todofile.
        """
        self.undo_manager.record_operation()
        try:
            os.rename(self.todofile, self.todofile+"~")
            with open(self.todofile, "w") as f:
                for t in self.todo:
                    f.writelines(str(t)+"\n")
            os.remove(self.todofile+"~")
        except Exception as  e:
            print("An exception occured. The original file has been moved before modification to '%s'." % self.todofile+"~")
            print(str(e))


    def archive(self) -> None:
        """
        Archive completed tasks to the donefile and remove them from the model's task list.
        """
        todo, done = [], []

        for t in self.todo:
            (done if t["complete"] else todo).append(t)

        self.todo = todo

        try:
            Path(self.donefile).touch()
            with open(self.donefile, "a") as f:
                for t in done:
                    f.writelines(str(t)+"\n")
        except Exception as  e:
            print("An exception occured. The original file has been moved before modification to '%s'." % self.donefile+"~")
            print(str(e))

        self.save()

    def query(self, filter: Union[str, List[Task]] = "", sortBy: List[str] = []) -> List[Task]:
        """
        Query tasks in the model based on a filter and sort order.

        Args:
            filter (Union[str, List[Task]], optional): A string or list of tasks to filter the query by. Defaults to "".
            sortBy (List[str], optional): A list of fields to sort the query results by. Defaults to [].

        Returns:
            List[Task]: A list of tasks that match the query.
        """

        def sortstr_lineno(x):
            if isinstance(x, str):
                return x
            return [xi.repr_char+("%i" % xi.line_no)+xi.name for xi in x]

        if isinstance(filter, list):
            todo = filter
        elif filter:
            filter_re = re.compile(".*("+filter+").*")
            todo = []
            for t in self.todo:
                m = filter_re.match(t["raw_full_text"])
                if m:
                    todo.append(t)
        else:
            todo = self.todo

        if len(sortBy) == 0:
            return todo

        def sortstr(t):
            return "|".join(
                        ",".join(
                            sortstr_lineno(t[o])
                        ) if t[o] else "0000" for o in sortBy
                    )

        return sorted(todo, key=sortstr)

    def new_task(self, initial_text: str = "", pos: Union[int, Task] = -1, offset: int = 1) -> Task:
        """
        Create a new task in the model.

        Args:
            initial_text (str, optional): The initial text of the task. Defaults to "".
            pos (Union[int, Task], optional): The position or task to insert the new task after. Defaults to -1.
            offset (int, optional): The offset from the pos to insert the new task. Defaults to 1.

        Returns:
            Task: A new Task instance.
        """
        if isinstance(pos, Task):
            pos = self.todo.index(pos)

        if pos == -1:
            pos = len(self.todo) - offset

        task = Task.from_rawtext(self, initial_text)
        self.todo.insert(pos + offset, task)
        # self.save()
        return task

    def remove_task_at_pos(self, pos: int) -> None:
        task = self.todo[pos]
        return self.remove_task(task)

    def remove_task(self, task: Task) -> None:
        """
        Remove a task from the model.

        Args:
            task (Task): The task to remove from the model.
        """
        self.todo.remove(task)
        self.save()

    def change_task(self, task: Task, new_text: str) -> None:
        """
        Change the text of a task in the model.

        Args:
            task (Task): The task to change the text of.
            new_text (str): The new text for the task.
        """
        task.update_rawtext(new_text)
        self.save()

    def save_order(self, tasks):
        task_pos = [self.todo.index(t) for t in tasks]
        task_pos_sorted = sorted(task_pos)
        for new_pos, task in zip(task_pos_sorted, tasks):
            self.todo[new_pos] = task
        self.save()

    def move_to(self, tasks, task, before=True):
        for t in tasks:
            self.todo.remove(t)
        pos = self.todo.index(task)
        if before:
            self.todo = self.todo[:pos] + tasks + self.todo[pos:]
        else:
            self.todo = self.todo[:pos+1] + tasks + self.todo[pos+1:]
        self.save()

    def reload(self):
        self.todo = []
        with open(self.todofile, "r") as file:
            for line_no, t in enumerate(file):
                if not t.strip():
                    continue

                task = Task.from_rawtext(self, t, line_no=line_no)
                self.todo.append(task)
