from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QGroupBox, QSizePolicy, QLabel
from PyQt6.QtCore import Qt
from components.tag_editor_widget import TagEditorWidget

class ToolsPanel(QWidget):
    """
    A panel containing buttons for file and folder operations.
    """
    def __init__(self, parent=None, settings_manager=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)

        # --- Tags Editor --- #
        self.tags_group = QGroupBox("Tags")
        tags_layout = QVBoxLayout(self.tags_group)
        self.tag_editor_widget = TagEditorWidget(self, settings_manager=self.settings_manager)
        tags_layout.addWidget(self.tag_editor_widget)
        main_layout.addWidget(self.tags_group)

        # --- Tools --- #
        self.tools_group = QGroupBox("Tools")
        tools_layout = QVBoxLayout(self.tools_group)
        self.tools_group.setMinimumWidth(88)

        self.btn_name_to_title = QPushButton("Name > Title")
        self.btn_name_to_title.setToolTip("Generate Title from filename.")

        self.btn_camel_case = QPushButton("Camel Case")
        self.btn_camel_case.setToolTip("Apply camel case to the Title tag. (F4)")

        self.btn_find_replace = QPushButton("Find/Replace")
        self.btn_find_replace.setToolTip("Find and replace text in the Title tag.")

        self.btn_clear_hidden_tags = QPushButton("Clear Hidden")
        self.btn_clear_hidden_tags.setToolTip("Clear all tags not shown as columns. (F3)")

        all_buttons = [
            self.btn_name_to_title,
            self.btn_camel_case,
            self.btn_find_replace,
            self.btn_clear_hidden_tags
        ]

        for btn in all_buttons:
            btn.setFixedHeight(50)
            btn.setStyleSheet("font-size: 20px; font-weight: bold;")
            tools_layout.addWidget(btn)

        main_layout.addWidget(self.tools_group)

        # Selected Files Status Bar
        self.selected_files_label = QLabel("Selected: 0 files")
        self.selected_files_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        main_layout.addWidget(self.selected_files_label)

        # Save Changes Button
        self.btn_save_changes = QPushButton("Save Changes")
        self.btn_save_changes.setToolTip("Save all changes to files. (Ctrl+S or F5)")
        self.btn_save_changes.setFixedHeight(50) # Make it big
        self.btn_save_changes.setStyleSheet("font-size: 20px; font-weight: bold;") # Make it bold and larger font
        main_layout.addWidget(self.btn_save_changes)

        self.btn_revert = QPushButton("Revert")
        self.btn_revert.setFixedHeight(25)
        self.btn_revert.setStyleSheet("font-size: 14px;")
        main_layout.addWidget(self.btn_revert)

        # Status Label for Save operation
        self.save_status_label = QLabel("")
        self.save_status_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        main_layout.addWidget(self.save_status_label)

        

        main_layout.addStretch() # Pushes everything to the top

        # Set initial state to disabled
        self.tools_group.setEnabled(False)
        self.tags_group.setEnabled(False)
