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
            'COLUMN_WIDTH': 40,
            'WINDOW_PADDING': 2,
            'WINDOW_MARGIN': 1,
            'LIST_HIDDEN': True,
            'TAG_HIDDEN': True,
            'SUBTAG_HIDDEN': True,
            'CREATIONDATE_HIDDEN': True,
            'COMPLETIONDATE_HIDDEN': True,
            'DIM_COMPLETE': True,
            'TODO_STYLE': 1,
            'AUTOADD_CREATIONDATE': True,
            'AUTOADD_COMPLETIONDATE': True
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
        self.config['DEFAULT'] = self.default_settings
        self.save_settings()

    def save_settings(self):
        with open(self.config_file, 'w') as f:
            self.config.write(f)

    @classmethod
    def get(cls, key, fallback=None):
        instance = cls()
        instance.load_settings()

        # Determine the type of the value based on the default settings
        if key in instance.default_settings:
            default_value = instance.default_settings[key]
            if type(default_value) is bool:
                value = instance.config.getboolean('DEFAULT', key, fallback=fallback)
            elif type(default_value) is int:
                value = instance.config.getint('DEFAULT', key, fallback=fallback)
            elif type(default_value) is float:
                value = instance.config.getfloat('DEFAULT', key, fallback=fallback)
            else:
                value = instance.config.get('DEFAULT', key, fallback=fallback)
        else:
            value = instance.config.get('DEFAULT', key, fallback=fallback)

        return value

    @classmethod
    def set(cls, key, value):
        instance = cls()
        instance.config.set('DEFAULT', key, str(value))
        instance.save_settings()
