import json
import os
from utils.user_defaults import DEFAULT_BANNED_WORDS, DEFAULT_TAG_MAPPINGS

class SettingsManager:
    """Handles loading and accessing application settings."""
    def __init__(self, settings_path='src/settings.json'):
        self.settings_path = settings_path
        self.settings = self.load_settings()

    def load_settings(self):
        """Loads settings from the JSON file."""
        if os.path.exists(self.settings_path):
            with open(self.settings_path, 'r') as f:
                settings = json.load(f)
            
            # Migration Logic: Ensure defaults are merged into existing settings
            # We use a config_version to track if we've applied the latest defaults
            current_version = settings.get('config_version', 0)
            LATEST_VERSION = 1
            
            general = settings.setdefault('general', {})
            
            if current_version < LATEST_VERSION:
                # Merge Banned Words (Union)
                current_words = set(general.get('words_to_remove', []))
                merged_words = current_words.union(set(DEFAULT_BANNED_WORDS))
                general['words_to_remove'] = sorted(list(merged_words))
                
                # Merge Tag Mappings (Defaults as base, User overrides)
                current_mappings = general.get('tag_mappings', {})
                merged_mappings = DEFAULT_TAG_MAPPINGS.copy()
                merged_mappings.update(current_mappings)
                general['tag_mappings'] = merged_mappings
                
                # Update Version
                settings['config_version'] = LATEST_VERSION
                
                # Save immediately to persist migration
                # We can't call self.save_settings() here easily because self.settings isn't set yet
                # So we just proceed returning the modified settings object, 
                # relying on the caller or subsequent saves to persist it.
                # However, for robustness, 'main_window' or 'settings_window' saving triggers will handle it.
            
            # Fallback for keys if they somehow don't exist even after migration logic
            if 'words_to_remove' not in general:
                general['words_to_remove'] = DEFAULT_BANNED_WORDS
            if 'tag_mappings' not in general:
                general['tag_mappings'] = DEFAULT_TAG_MAPPINGS
                
            return settings
        # Return a default structure if the file doesn't exist
        return {
            "general": {
                "excluded_folders": [], 
                "special_album_names": [], 
                "words_to_remove": DEFAULT_BANNED_WORDS,
                "tag_mappings": DEFAULT_TAG_MAPPINGS,
                "auto_apply_name_to_title": False 
            },
            "ui": {"highlight_colors": {}},
            "tagging_and_columns": {"default_tags": {"Artist": True, "Album": True, "Title": True}}
        }

    def save_settings(self):
        """Saves the current settings to the JSON file."""
        with open(self.settings_path, 'w') as f:
            json.dump(self.settings, f, indent=4)

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
