from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTabWidget, QWidget, QFormLayout, QLineEdit, QCheckBox, QPushButton, QDialogButtonBox, QHBoxLayout, QFileDialog

class SettingsWindow(QDialog):
    """
    A dialog for managing application settings.
    """
    def __init__(self, parent=None, settings_manager=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.settings_manager = settings_manager
        self.setMinimumSize(500, 400)

        main_layout = QVBoxLayout(self)
        tab_widget = QTabWidget()

        # Create tabs
        self.general_tab = QWidget()
        self.columns_tab = QWidget()
        self.ui_tab = QWidget()

        tab_widget.addTab(self.general_tab, "General")
        tab_widget.addTab(self.columns_tab, "Columns")
        tab_widget.addTab(self.ui_tab, "UI")

        # Populate tabs
        self.create_general_tab()
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

        # Words to Remove
        words_to_remove_str = ", ".join(self.settings_manager.get('general', {}).get('words_to_remove', []))
        self.words_to_remove_field = QLineEdit(words_to_remove_str)
        layout.addRow("Words to Remove (comma-separated):", self.words_to_remove_field)
        # Quick Folder Path
        quick_folder_path = self.settings_manager.get('general', {}).get('quick_folder_path', '')
        self.quick_folder_field = QLineEdit(quick_folder_path)
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_quick_folder)
        quick_folder_layout = QHBoxLayout()
        quick_folder_layout.addWidget(self.quick_folder_field)
        quick_folder_layout.addWidget(browse_button)
        layout.addRow("Quick Folder Path:", quick_folder_layout)


    def create_columns_tab(self):
        layout = QVBoxLayout(self.columns_tab)
        self.column_checkboxes = {}
        
        tag_settings = self.settings_manager.get('tagging_and_columns', {}).get('default_tags', {})
        for tag, is_visible in tag_settings.items():
            self.column_checkboxes[tag] = QCheckBox(tag)
            self.column_checkboxes[tag].setChecked(is_visible)
            layout.addWidget(self.column_checkboxes[tag])

    def browse_quick_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Select Quick Folder")
        if path:
            self.quick_folder_field.setText(path)

    

    def save_settings(self):
        # Save general settings
        excluded_folders = [folder.strip() for folder in self.excluded_folders_field.text().split(',') if folder.strip()]
        self.settings_manager.settings['general']['excluded_folders'] = excluded_folders

        words_to_remove = [word.strip() for word in self.words_to_remove_field.text().split(',') if word.strip()]
        self.settings_manager.settings['general']['words_to_remove'] = words_to_remove
        quick_folder_path = self.quick_folder_field.text().strip()
        self.settings_manager.settings['general']['quick_folder_path'] = quick_folder_path


        # Save column visibility settings
        for tag, checkbox in self.column_checkboxes.items():
            self.settings_manager.settings['tagging_and_columns']['default_tags'][tag] = checkbox.isChecked()

        

        # Persist to file
        with open(self.settings_manager.settings_path, 'w') as f:
            import json
            json.dump(self.settings_manager.settings, f, indent=4)
        
        self.accept()
