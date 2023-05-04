from jira import JIRA
from typing import List as ListType, Union
from model.basemodel import Task, List
from model.todotxt import TodotxtModel

class JiraModel:
    """
    A class representing the JIRA model.

    Manages tasks, tags, subtags, and lists, and provides methods for loading, saving, and querying tasks.
    """

    def __init__(self, jira_instance: str, username: str, api_token: str, jql: int):
        self.jira_instance = jira_instance
        self.username = username
        self.api_token = api_token
        self.jql = jql
        self.jira_client = JIRA(self.jira_instance, basic_auth=(self.username, self.api_token))

        self.lists = {}
        self.tags = {}
        self.subtags = {}

        self.load_from_jira()

    def load_from_jira(self) -> None:
        """
        Load tasks from the JIRA board into the model's task list.
        """
        self.todo = []
        self.stories = self.jira_client.search_issues(f"{self.jql}", maxResults=25)
        
        for issue in self.stories:
            epic = issue.fields.parent
            story_name = issue.fields.summary
            epic_name = ""
            if epic:
                epic_name = epic.fields.summary

            card = List(story_name)

            if issue.fields.subtasks:
                done_transition = [t for t in self.jira_client.transitions(issue.fields.subtasks[0]) if t['name'].lower() == "done"][0]
                todo_transition = [t for t in self.jira_client.transitions(issue.fields.subtasks[0]) if t['name'].lower() == "to do"][0]

            for subtask in issue.fields.subtasks:
                task = Task(self, {
                    "complete": subtask.fields.status.name.lower() == "done",
                    "priority": "M_",
                    "completion-date": None,
                    "creation-date": None,
                    # "raw_text_complete": t,
                    "raw_text": None,
                    "raw_full_text": None,
                    "text": [subtask.fields.summary],
                    "tags": [],
                    "subtags": [],
                    "lists": [card],
                    "modifier": [],
                    "actions": {
                        "done": lambda: self.jira_client.transition_issue(subtask, done_transition['id']),
                        "undone": lambda: self.jira_client.transition_issue(subtask, todo_transition['id']),
                    }
                })
                self.todo.append(task)

            # Set the Task attributes
            # task = Task("", "")
            # task.raw_full_text = f"summary +{story_name} @{epic_name}"
            # task.text = f"summary +{story_name} @{epic_name}"
            # task.projects = [epic_name] if epic_name else []
            # task.contexts = []
            # task.completed = False
            # task.priority = None
            # task.creation_date = issue.fields.created
            # self.todo.append(task)


    def query(self, filter: Union[str, ListType[Task]] = "", sortBy: ListType[str] = []) -> ListType[Task]:
        return self.todo
        # Reuse the query function from the Model class
        return TodotxtModel.query(self, filter, sortBy)

    # Other functions from the Model class can be reused without modification, 
    # just remove the ones related to the todofile and donefile
