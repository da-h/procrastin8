from jira import JIRA
from typing import List, Union
from model.basemodel import Task
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

            raw_text = f"{story_name} @{epic_name}"
            task = Task.from_rawtext(self, raw_text, line_no=None)
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


    def query(self, filter: Union[str, List[Task]] = "", sortBy: List[str] = []) -> List[Task]:
        return self.todo
        # Reuse the query function from the Model class
        return TodotxtModel.query(self, filter, sortBy)

    # Other functions from the Model class can be reused without modification, 
    # just remove the ones related to the todofile and donefile
