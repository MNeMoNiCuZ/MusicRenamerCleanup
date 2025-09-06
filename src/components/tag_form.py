from PyQt6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QDialogButtonBox, QLabel

class TagForm(QDialog):
    """
    A dialog for batch editing tags of selected tracks.
    """
    def __init__(self, parent=None, tags_to_show=None, initial_data=None):
        super().__init__(parent)
        self.setWindowTitle("Batch Edit Tags")
        
        self.fields = {}
        if tags_to_show is None:
            tags_to_show = ['Artist', 'Album', 'Title', 'Genre', 'Date']

        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # Add a label for shared values
        info_label = QLabel("Fields with different values across selected files are marked with '<multiple values>'.")
        main_layout.addWidget(info_label)

        for tag in tags_to_show:
            self.fields[tag] = QLineEdit()
            form_layout.addRow(f"&{tag}:", self.fields[tag])

        main_layout.addLayout(form_layout)

        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

        self.populate_initial_data(initial_data)

    def populate_initial_data(self, data):
        if not data:
            return
        for tag, value in data.items():
            if tag in self.fields:
                self.fields[tag].setText(value)

    def get_form_data(self):
        """Returns the data entered in the form."""
        data = {}
        for tag, field in self.fields.items():
            text = field.text()
            # Only include fields that the user has actually filled in
            if text and text != '<multiple values>':
                data[tag] = text
        return data
