import re
import os
from datetime import date
from pathlib import Path


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

    def save(self):
        self.model.save()

    @classmethod
    def from_rawtext(cls, model, t, line_no=None):
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
            "raw_text": m[5],
            "raw_full_text": t,
            "text": text,
            "tags": tags,
            "subtags": subtags,
            "lists": lists,
            "modifier": modifiers,
        })

        if line_no:
            task["#"] = line_no

        return task


class Model():
    def __init__(self, todofile, donefile):
        self.todofile = todofile
        self.donefile = donefile
        self.lists = {}
        self.tags = {}
        self.subtags = {}

        self.todo = []
        with open(self.todofile,"r") as file:
            for line_no, t in enumerate(file):
                if not t.strip():
                    continue

                task = Task.from_rawtext(self, t, line_no=line_no)
                self.todo.append(task)

    def save(self):
        try:
            os.rename(self.todofile, self.todofile+"~")
            with open(self.todofile, "w") as f:
                for t in self.todo:
                    f.writelines(str(t)+"\n")
            os.remove(self.todofile+"~")
        except Exception as  e:
            print("An exception occured. The original file has been moved before modification to '%s'." % self.todofile+"~")
            print(str(e))

    def archive(self):
        todo, done = [], []

        for t in self.todo:
            (done if t["complete"] else todo).append(t)

        self.todo = todo

        try:
            Path(self.donefile).touch()
            os.rename(self.donefile, self.donefile+"~")
            with open(self.donefile, "w") as f:
                for t in done:
                    f.writelines(str(t)+"\n")
            os.remove(self.donefile+"~")
        except Exception as  e:
            print("An exception occured. The original file has been moved before modification to '%s'." % self.donefile+"~")
            print(str(e))

        self.save()

    def query(self, filter=".*", sortBy=[]):

        def sortstr_lineno(x):
            if isinstance(x, str):
                return x
            return [xi.repr_char+("%i" % xi.line_no)+xi.name for xi in x]

        filter_re = re.compile(filter)
        todo = []
        for t in self.todo:
            m = filter_re.match(t["raw_full_text"])
            if m:
                todo.append(t)

        if len(sortBy) == 0:
            return todo

        def sortstr(t):
            return "|".join(
                        ",".join(
                            sortstr_lineno(t[o])
                        ) if t[o] else "0000" for o in sortBy
                    )

        return sorted(todo, key=sortstr)

    def new_task(self, initial_text="", pos=-1):
        if isinstance(pos, Task):
            pos = self.todo.index(pos)
        task = Task.from_rawtext(self,initial_text)
        self.todo.insert(pos+2, task)
        # self.save()
        return task

    def remove_task(self, pos=-1):
        if isinstance(pos, int):
            pos = self.todo[pos]
        self.todo.remove(pos)
        self.save()
