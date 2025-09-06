import json
import os

class SettingsManager:
    """Handles loading and accessing application settings."""
    def __init__(self, settings_path='src/settings.json'):
        self.settings_path = settings_path
        self.settings = self.load_settings()

    def load_settings(self):
        """Loads settings from the JSON file."""
        if os.path.exists(self.settings_path):
            with open(self.settings_path, 'r') as f:
                return json.load(f)
        # Return a default structure if the file doesn't exist
        return {
            "general": {"excluded_folders": [], "special_album_names": [], "words_to_remove": [], "quick_folder_path": ""},
            "ui": {"highlight_colors": {}},
            "tagging_and_columns": {"default_tags": {"Artist": True, "Album": True, "Title": True}}
        }

    def get(self, key, default=None):
        """Gets a value from the settings."""
        return self.settings.get(key, default)

    def get_visible_columns(self):
        """Gets the list of columns to display in the file browser."""
        tag_settings = self.get('tagging_and_columns', {})
        default_tags = tag_settings.get('default_tags', {})
        
        columns = ['Original Name', 'New Name']
        for tag, is_visible in default_tags.items():
            if is_visible:
                columns.append(tag)
        columns.append('[Suffixes]') # Always include Suffixes
        return columns
