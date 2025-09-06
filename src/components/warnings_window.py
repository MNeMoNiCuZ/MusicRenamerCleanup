from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QDialogButtonBox

class WarningsWindow(QDialog):
    """
    A dialog for displaying structural warnings found in the library.
    """
    def __init__(self, parent=None, warnings_text=""):
        super().__init__(parent)
        self.setWindowTitle("Library Warnings")
        self.setMinimumSize(960, 400)

        layout = QVBoxLayout(self)
        
        text_area = QTextEdit()
        text_area.setReadOnly(True)
        text_area.setText(warnings_text)
        layout.addWidget(text_area)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)
