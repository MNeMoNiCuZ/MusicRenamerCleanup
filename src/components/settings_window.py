from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTabWidget, QWidget, QFormLayout, QLineEdit, QCheckBox, QPushButton, QDialogButtonBox, QHBoxLayout, QFileDialog, QPlainTextEdit, QLabel

class SettingsWindow(QDialog):
    """
    A dialog for managing application settings.
    """
    def __init__(self, parent=None, settings_manager=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.settings_manager = settings_manager
        self.setMinimumSize(600, 500)

        main_layout = QVBoxLayout(self)
        tab_widget = QTabWidget()

        # Create tabs
        self.general_tab = QWidget()
        self.blocklist_tab = QWidget()
        self.tags_tab = QWidget()
        self.columns_tab = QWidget()

        tab_widget.addTab(self.general_tab, "General")
        tab_widget.addTab(self.blocklist_tab, "Blocklist")
        tab_widget.addTab(self.tags_tab, "Tags")
        tab_widget.addTab(self.columns_tab, "Columns")

        # Populate tabs
        self.create_general_tab()
        self.create_blocklist_tab()
        self.create_tags_tab()
        self.create_columns_tab()
        
        main_layout.addWidget(tab_widget)

        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.save_settings)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    def create_general_tab(self):
        layout = QFormLayout(self.general_tab)
        
        # Excluded Folders
        excluded_folders_str = ", ".join(self.settings_manager.get('general', {}).get('excluded_folders', []))
        self.excluded_folders_field = QLineEdit(excluded_folders_str)
        layout.addRow("Excluded Folders (comma-separated):", self.excluded_folders_field)

        # Auto-apply Name > Title setting
        self.auto_apply_check = QCheckBox("Auto-apply 'Name > Title' if >80% of tracks have missing titles")
        is_auto_apply = self.settings_manager.get('general', {}).get('auto_apply_name_to_title', False)
        self.auto_apply_check.setChecked(is_auto_apply)
        layout.addRow(self.auto_apply_check)

    def create_blocklist_tab(self):
        layout = QVBoxLayout(self.blocklist_tab)
        
        layout.addWidget(QLabel("Words/Phrases to Remove (One per line)"))
        
        # Use QPlainTextEdit for multi-line support
        words_to_remove_list = self.settings_manager.get('general', {}).get('words_to_remove', [])
        # Join with ACTUAL newlines for display in text edit
        words_to_remove_str = "\n".join(words_to_remove_list)
        self.words_to_remove_field = QPlainTextEdit(words_to_remove_str)
        self.words_to_remove_field.setPlaceholderText("Bonus Track\nRemastered\nOfficial Video")
        layout.addWidget(self.words_to_remove_field)

    def create_tags_tab(self):
        layout = QVBoxLayout(self.tags_tab)
        
        layout.addWidget(QLabel("Tag Rules (One per line)"))
        layout.addWidget(QLabel("Format: 'Keyword = [Tag]' OR just 'TagWord' (implies TagWord = [TagWord])"))
        
        tag_mappings = self.settings_manager.get('general', {}).get('tag_mappings', {})
        # Convert dict to string "Key = Value"
        mappings_str = ""
        for pattern, tag in tag_mappings.items():
            mappings_str += f"{pattern} = {tag}\n"
            
        self.tag_mappings_field = QPlainTextEdit(mappings_str.strip())
        self.tag_mappings_field.setPlaceholderText("(acoustic) = [Acoustic]\nInstrumental = [Instrumental]\nLive")
        layout.addWidget(self.tag_mappings_field)

    def create_columns_tab(self):
        layout = QVBoxLayout(self.columns_tab)
        self.column_checkboxes = {}
        
        tag_settings = self.settings_manager.get('tagging_and_columns', {}).get('default_tags', {})
        for tag, is_visible in tag_settings.items():
            self.column_checkboxes[tag] = QCheckBox(tag)
            self.column_checkboxes[tag].setChecked(is_visible)
            layout.addWidget(self.column_checkboxes[tag])

    def save_settings(self):
        # Save general settings
        excluded_folders = [folder.strip() for folder in self.excluded_folders_field.text().split(',') if folder.strip()]
        self.settings_manager.settings['general']['excluded_folders'] = excluded_folders
        
        # Save auto-apply setting
        self.settings_manager.settings['general']['auto_apply_name_to_title'] = self.auto_apply_check.isChecked()

        # Save words to remove (split by newline)
        words_text = self.words_to_remove_field.toPlainText()
        words_to_remove = [line.strip() for line in words_text.split('\n') if line.strip()]
        self.settings_manager.settings['general']['words_to_remove'] = words_to_remove
        
        # Save tag mappings
        mappings_text = self.tag_mappings_field.toPlainText()
        new_mappings = {}
        for line in mappings_text.split('\n'):
            line = line.strip()
            if not line: continue
            
            if '=' in line:
                parts = line.split('=', 1)
                pattern = parts[0].strip()
                tag = parts[1].strip()
                if pattern and tag:
                    new_mappings[pattern] = tag
            else:
                # Simple keyword case: "Live" -> "[Live]"
                # Use the line as the keyword, and capitalize it for the tag
                keyword = line
                # Simple Title Case for the generated tag content
                tag_content = keyword.title() 
                new_mappings[keyword] = f"[{tag_content}]"
                
        self.settings_manager.settings['general']['tag_mappings'] = new_mappings

        # Remove legacy quick_folder_path if it exists
        if 'quick_folder_path' in self.settings_manager.settings['general']:
            del self.settings_manager.settings['general']['quick_folder_path']

        # Save column visibility settings
        for tag, checkbox in self.column_checkboxes.items():
            self.settings_manager.settings['tagging_and_columns']['default_tags'][tag] = checkbox.isChecked()

        # Persist to file
        with open(self.settings_manager.settings_path, 'w') as f:
            import json
            json.dump(self.settings_manager.settings, f, indent=4)
        
        self.accept()
