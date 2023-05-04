import re
from datetime import date
from settings import Settings

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

    def toggle_complete(self):
        if "actions" in self:
            if self["complete"] and "undone" in self["actions"]:
                self["actions"]["undone"]()
            elif not self["complete"] and "done" in self["actions"]:
                self["actions"]["done"]()

        self["complete"] = not self["complete"]
        if Settings.get('dates.autoadd_completiondate') and self["creation-date"]:
            self["completion-date"] = datetime.now().strftime("%Y-%m-%d")
        if self["completion-date"] and not self["complete"]:
            self["completion-date"] = None

        if not "actions" in self:
            self.save()


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


