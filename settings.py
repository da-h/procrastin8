import configparser
from pathlib import Path

class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

class Settings(metaclass=Singleton):
    def __init__(self):
        self.config = configparser.ConfigParser()

        # Default settings
        self.default_settings = {
            'appearance': {
                'column_width': 40,
                'window_padding': 2,
                'window_margin': 1,
                'list_hidden': True,
                'tag_hidden': True,
                'subtag_hidden': True,
            },
            'dates': {
                'creationdate_hidden': True,
                'completiondate_hidden': True,
                'autoadd_creationdate': True,
                'autoadd_completiondate': True,
            },
            'tasks': {
                'dim_complete': True,
                'todo_style': 1,
            },
            'jira': {
                'instance': "",
                'jql': "",
                'username': "",
                'api_token': "",
            }
        }

        # Create the config directory if it does not exist
        config_dir = Path.home() / '.config' / 'procastin8'
        config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = config_dir / 'settings.ini'

        # Load settings from the config file or use default settings
        if self.config_file.exists():
            self.load_settings()
        else:
            self.reset_settings()

    def load_settings(self):
        self.config.read(self.config_file)

    def reset_settings(self):
        # Set default values for missing keys
        for category, settings in self.default_settings.items():
            if not self.config.has_section(category):
                self.config.add_section(category)
            for key, value in settings.items():
                if not self.config.has_option(category, key):
                    self.config.set(category, key, str(value))
        self.save_settings()

    def save_settings(self):
        with open(self.config_file, 'w') as f:
            self.config.write(f)

    @classmethod
    def get(cls, key, fallback=None):
        instance = cls()
        if key == "default_settings":
            return instance.default_settings

        category, _, setting = key.partition('.')
        if not instance.config.has_section(category):
            instance.config.add_section(category)
        if setting not in instance.config.options(category):
            default_value = fallback
        else:
            default_value = instance.default_settings[category][setting]
        value = instance.config.get(category, setting, fallback=default_value)

        # Determine the type of the value based on the default settings
        if isinstance(default_value, bool):
            value = instance.config.getboolean(category, setting, fallback=default_value)
        elif isinstance(default_value, int):
            value = instance.config.getint(category, setting, fallback=default_value)
        elif isinstance(default_value, float):
            value = instance.config.getfloat(category, setting, fallback=default_value)

        return value

    @classmethod
    def set(cls, key, value):
        instance = cls()

        category, _, setting = key.partition('.')
        if not instance.config.has_section(category):
            instance.config.add_section(category)
        instance.config.set(category, setting, str(value))

        instance.save_settings()

    @classmethod
    def default_settings(cls):
        return cls().default_settings

