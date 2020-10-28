import re
from datetime import date

todo = """
2019-01-27 Review @iflow +planing rec:3m due:2019-04-27 t:2019-04-27
(C) 2018-11-02 Universal Correspondence Network +iFlow @papers
(D) 2017-07-21 Universal Programming +iFlow @papers
(D) 2018-11-02 Joshua Tennbaum A Rational Analysis of Rule-based Concept Learning +iFlow @papers
2019-08-19 kanban note Weight gradients by histogram @iflow +infn
2020-10-03 Tidy up kanban +planing @iflow
2020-10-03 Move entval todos to kanban +planing @iflow
2020-10-03 move notes from scribble to kanban +planing @iflow
2020-10-08 Check fanstanstic 3 channel for related work and todos +entval @iflow
2020-07-12 kanban note Relaxation for big Vektors. Instead of having 1000000 weights, use 100 times 20 weights (to have a distribution over combinations) +planing @iflow
2020-10-08 Check information flow channel for related work +entval @iflow
2020-10-06 Go through informationflow channel for relatedwork +entval @iflow
x (A) 2020-10-12 2020-10-08 One +Paper read @iflow rec:1b t:2020-10-09
2020-10-03 Clear iflow code from Saturn +oldcode @iflow
2020-10-03 Clear iflow code from sirius +oldcode @iflow
""".strip()


rdate = "\d{4}-\d{2}-\d{2}"
completion = "x"
priority = "\([A-Z]\)"
ws = "\s*"

re_todo     = re.compile(f"{ws}({completion})?{ws}({priority})?{ws}({rdate})?{ws}({rdate})?{ws}(.*)")
re_modifier_with_date = re.compile(f"(\w+):({rdate})")
re_modifier = re.compile("(\w+):(\w+)")
re_tag = re.compile("\+(\w+)")
re_list = re.compile("@(\w+)")

class Tag(str):
    def __str__(self):
        return "+"+super().__str__()
    def __repr__(self):
        return "+"+super().__str__()

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
    def __str__(self):
        S = []
        if self["complete"]:
            S.append("x")
        if self["priority"] != "M_":
            S.append("(%s)" % self["priority"])
        if self["completion-date"]:
            S.append(str(self["completion-date"]))
        if self["creation-date"]:
            S.append(str(self["creation-date"]))
        S += self["text"]
        return " ".join(str(s) for s in S)

class Model():
    def __init__(self):

        self.todo = []
        for t in todo.split("\n"):
            modifiers = {}
            tags = []
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

                m2 = re_list.match(word)
                if m2:
                    lists.append(m2[1])
                    text.append(List(m2[1]))
                    continue

                text.append(word)

            self.todo.append(Task({
                "complete": m[1] == "x",
                "priority": m[2][1:-1] if m[2] else "M_",
                "completion-date": date.fromisoformat(m[3]) if m[3] else None,
                "creation-date": date.fromisoformat(m[4]) if m[4] else None,
                "raw_text": t,
                "text": text,
                "tags": tags,
                "lists": lists,
                "modifier": modifiers
            }))
