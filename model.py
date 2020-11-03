import re
import os
from datetime import date


rdate = "\d{4}-\d{2}-\d{2}"
completion = "x"
priority = "\([A-Z]\)"
ws = "\s*"


re_todo     = re.compile(f"{ws}({completion})?{ws}({priority})?{ws}({rdate})?{ws}({rdate})?{ws}(.*)")
re_modifier_with_date = re.compile(f"(\w+):({rdate})")
re_modifier = re.compile("(\w+):(\w+)")
re_tag = re.compile("\+(\w+)")
re_subtag = re.compile("\+\+(\w+)")
re_list = re.compile("@(\w+)")


class Tag(str):
    def __str__(self):
        return "+"+super().__str__()
    def __repr__(self):
        return "+"+super().__str__()


class Subtag(str):
    def __str__(self):
        return "++"+super().__str__()
    def __repr__(self):
        return "++"+super().__str__()


class List(str):
    def __str__(self):
        return "@"+super().__str__()
    def __repr__(self):
        return "@"+super().__str__()


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
    def from_rawtext(cls, model, t):
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
                tags.append(m2[1])
                text.append(Tag(m2[1]))
                continue

            m2 = re_subtag.match(word)
            if m2:
                subtags.append(m2[1])
                text.append(Subtag(m2[1]))
                continue

            m2 = re_list.match(word)
            if m2:
                lists.append(m2[1])
                text.append(List(m2[1]))
                continue

            text.append(word)

        if m[1] == "x":
            completion_date = m[3]
            creation_date = m[4]
        else:
            completion_date = None
            creation_date = m[3]
            # TODO error when both are specified

        return Task(model, {
            "complete": m[1] == "x",
            "priority": m[2][1:-1] if m[2] else "M_",
            "completion-date": date.fromisoformat(completion_date) if completion_date else None,
            "creation-date": date.fromisoformat(creation_date) if creation_date else None,
            # "raw_text_complete": t,
            "raw_text": m[5],
            "text": text,
            "tags": tags,
            "subtags": subtags,
            "lists": lists,
            "modifier": modifiers,
        })


class Model():
    def __init__(self, filename):
        self.filename = filename

        self.todo = []
        with open(self.filename,"r") as file:
            for line_no, t in enumerate(file):
                if not t.strip():
                    continue

                task = Task.from_rawtext(self, t)
                task["#"] = line_no
                self.todo.append(task)

    def save(self):
        try:
            os.rename(self.filename, self.filename+"~")
            with open(self.filename, "w") as f:
                for t in self.todo:
                    f.writelines(str(t)+"\n")
            os.remove(self.filename+"~")
        except Exception as  e:
            print("An exception occured. The original file has been moved before modification to '%s'." % self.filename+"~")
            print(str(e))


    def sortBy(self, order_list=[]):
        if len(order_list) == 0:
            return self.todo
        return sorted(self.todo, key=lambda t: ["|".join(",".join(t[o]) for o in order_list)])
