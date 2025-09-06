from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QDialogButtonBox, QLabel

class FindReplaceDialog(QDialog):
    """
    A dialog to get 'find' and 'replace' strings from the user.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Find and Replace in Title")
        
        self.layout = QVBoxLayout(self)
        
        self.find_label = QLabel("Find:")
        self.find_input = QLineEdit(self)
        self.layout.addWidget(self.find_label)
        self.layout.addWidget(self.find_input)
        
        self.replace_label = QLabel("Replace with:")
        self.replace_input = QLineEdit(self)
        self.layout.addWidget(self.replace_label)
        self.layout.addWidget(self.replace_input)
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        
        self.layout.addWidget(self.button_box)

    def get_values(self):
        """Returns the find and replace strings."""
        return self.find_input.text(), self.replace_input.text()