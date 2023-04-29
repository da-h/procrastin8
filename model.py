from __future__ import annotations
import re
import os
from datetime import date
from pathlib import Path
from undo import UndoManager
from typing import List, Union


rdate = "\d{4}-\d{2}-\d{2}"
completion = "x"
priority = "\([A-Z]\)"
ws = "\s*"


re_priority = re.compile("[A-Z]")
re_todo     = re.compile(f"{ws}({completion})?{ws}({priority})?{ws}({rdate})?{ws}({rdate})?{ws}(.*)")
re_modifier_with_date = re.compile(f"(\w+):({rdate})")
re_modifier = re.compile("(\w+):(\w+)")
re_tag = re.compile("\+(\w+)")
re_subtag = re.compile("\+\+(\w+)")
re_list = re.compile("@(\w+)")


class MetaTag:
    def __init__(self, name, line_no=None):
        self.line_no = line_no if line_no is not None else -1
        self.name = name
        self.repr_char = ""
    def __str__(self):
        return self.repr_char+self.name
    def __repr__(self):
        return self.repr_char+self.name


class Tag(MetaTag):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.repr_char = "+"


class Subtag(MetaTag):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.repr_char = "++"


class List(MetaTag):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.repr_char = "@"


class Modifier(tuple):
    def __str__(self):
        return self[0]+":"+self[1]
    def __repr__(self):
        return self[0]+":"+self[1]


class ModifierDate(tuple):
    def __str__(self):
        return self[0]+":"+str(self[1])
    def __repr__(self):
        return self[0]+":"+str(self[1])


class CompletionDate(date):
    pass


class CreationDateCompletionDate(date):
    pass


class Task(dict):
    """
    A class representing a task in the todo manager.

    Inherits from dict and extends it with methods for manipulating and saving tasks.
    """

    def __init__(self, model, d):
        super().__init__(d)
        self.model = model

    def __str__(self, print_optionals=True, print_description=True):
        S = []
        if print_optionals:
            if self["complete"]:
                S.append("x")
            if self["priority"] != "M_":
                S.append("(%s)" % self["priority"])
            if self["completion-date"]:
                S.append(str(self["completion-date"]))
            if self["creation-date"]:
                S.append(str(self["creation-date"]))
        if print_description:
            S += self["text"]
        return " ".join(str(s) for s in S)

    def update_rawtext(self):
        self["raw_text"] = Task.__str__(self, print_optionals=False)
        self["raw_full_text"] = Task.__str__(self)

    def save(self):
        self.model.save()


    @classmethod
    def from_rawtext(cls, model, t: str, line_no: int = None, leading_spaces: int = 0) -> 'Task':
        """
        Create a Task instance from the raw text of a task entry.

        Args:
            model (Model): The model instance.
            t (str): The raw text of the task entry.
            line_no (int, optional): The line number of the task entry in the file. Defaults to None.
            leading_spaces (int, optional): The number of leading spaces in the task entry. Defaults to 0.

        Returns:
            Task: A Task instance created from the raw text.
        """
        modifiers = {}
        tags = []
        subtags = []
        lists = []

        # match agains todo.txt
        m = re_todo.match(t)
        if m is None:
            raise ValueError("does not match against todoregex")

        # extract tags & modifiers from raw-text
        raw_text = m[5]
        text = []
        if leading_spaces > 0:
            text.append(" "*(leading_spaces-1))
        for word in raw_text.split(" "):

            m2 = re_modifier_with_date.match(word)
            if m2:
                modifiers[m2[1]] = date.fromisoformat(m2[2])
                text.append(ModifierDate((m2[1], modifiers[m2[1]])))
                continue

            m2 = re_modifier.match(word)
            if m2:
                modifiers[m2[1]] = m2[2]
                text.append(Modifier((m2[1], m2[2])))
                continue

            m2 = re_tag.match(word)
            if m2:
                if m2[1] in model.tags:
                    tag = model.tags[m2[1]]
                else:
                    tag = model.tags[m2[1]] = Tag(m2[1], line_no=line_no)
                tags.append(tag)
                text.append(tag)
                continue

            m2 = re_subtag.match(word)
            if m2:
                if m2[1] in model.subtags:
                    subtag = model.subtags[m2[1]]
                else:
                    subtag = model.subtags[m2[1]] = Subtag(m2[1], line_no=line_no)
                subtags.append(subtag)
                text.append(subtag)
                continue

            m2 = re_list.match(word)
            if m2:
                if m2[1] in model.lists:
                    list = model.lists[m2[1]]
                else:
                    list = model.lists[m2[1]] = List(m2[1], line_no=line_no)
                lists.append(list)
                text.append(list)
                continue

            text.append(word)

        if m[1] == "x":
            completion_date = m[3]
            creation_date = m[4]
        else:
            completion_date = None
            creation_date = m[3]
            # TODO error when both are specified

        task = Task(model, {
            "complete": m[1] == "x",
            "priority": m[2][1:-1] if m[2] else "M_",
            "completion-date": date.fromisoformat(completion_date) if completion_date else None,
            "creation-date": date.fromisoformat(creation_date) if creation_date else None,
            # "raw_text_complete": t,
            "raw_text": " "*leading_spaces+m[5],
            "raw_full_text": m[0],
            "text": text,
            "tags": tags,
            "subtags": subtags,
            "lists": lists,
            "modifier": modifiers,
        })

        if line_no:
            task["#"] = line_no

        return task



class Model:
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
