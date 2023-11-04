import configparser
from PySide6 import QtWidgets
import sys


class Configuration:
    def __init__(self, config_file):
        self.config = configparser.ConfigParser()
        self.config.read(config_file)

    def get_api_key(self):
        api_key = self.config.get("API", "key", fallback=None)
        if not api_key:
            api_key = self.prompt_for_api_key()
            self.save_api_key(api_key)
        return api_key

    def prompt_for_api_key(self):
        api_key, ok = QtWidgets.QInputDialog.getText(
            None,
            "OpenAI API Key",
            "Enter your OpenAI API key:"
        )
        if ok and api_key:
            return api_key
        else:
            sys.exit("API key is required to continue.")

    def save_api_key(self, api_key):
        self.config["API"] = {"key": api_key}
        with open("config.ini", "w") as configfile:
            self.config.write(configfile)
