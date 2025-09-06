from PyQt6.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QLabel
from PyQt6.QtCore import Qt, pyqtSignal
from tools.filename_generators import generate_filename_from_tags

class TagEditorWidget(QWidget):
    """
    A widget for editing tags directly in the tools panel.
    """
    tags_applied = pyqtSignal() # Custom signal to notify parent to refresh

    def __init__(self, parent=None, settings_manager=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.selected_tracks = []
        self.fields = {}
        self.original_field_values = {}  # Track original values to detect changes

        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()



        # Dynamically create fields based on settings
        self.tags_to_show = [t for t in self.settings_manager.get_visible_columns() if t not in ['Original Name', 'New Name', 'Special Tags']]
        for tag in self.tags_to_show:
            self.fields[tag] = QLineEdit()
            form_layout.addRow(f"&{tag}:", self.fields[tag])

        main_layout.addLayout(form_layout)

        self.apply_button = QPushButton("Update Tags")
        self.apply_button.clicked.connect(self.apply_tags_to_selected)
        main_layout.addWidget(self.apply_button)

        self.set_enabled_state(False)

    def set_selected_tracks(self, tracks):
        self.selected_tracks = tracks
        self.populate_fields()
        self.set_enabled_state(bool(tracks))

    def populate_fields(self):
        # Clear original values at the start of population
        self.original_field_values.clear()

        if not self.selected_tracks:
            for field in self.fields.values():
                field.clear()
            return

        # Common logic for both single and multiple tracks
        for tag in self.tags_to_show:
            tag_key = tag.lower().replace(' ', '')
            
            if tag == '[Suffixes]':
                # Special handling for suffixes
                values = [",".join(t.suffixes) for t in self.selected_tracks]
            else:
                # Standard tag handling
                values = [t.proposed_tags.get(tag_key, t.tags.get(tag_key, '')) for t in self.selected_tracks]

            # Use a set to find unique values
            unique_values = set(values)

            if len(unique_values) == 1:
                # All tracks have the same value
                display_value = unique_values.pop() or ''
                self.fields[tag].setText(str(display_value))
            else:
                # Different values across tracks
                self.fields[tag].setText('<multiple values>')
            
            # Store the initial value for later comparison
            self.original_field_values[tag] = self.fields[tag].text()

    def apply_tags_to_selected(self):
        for track in self.selected_tracks:
            for tag, field in self.fields.items():
                current_value = field.text()
                original_value = self.original_field_values.get(tag)

                # Condition to apply change:
                # 1. The field was changed by the user.
                # 2. The field's current value is NOT '<multiple values>'.
                if current_value != original_value and current_value != '<multiple values>':
                    tag_key = tag.lower().replace(' ', '')

                    if tag == '[Suffixes]':
                        # Handle suffixes separately
                        if not current_value.strip():
                            track.suffixes = []
                        else:
                            track.suffixes = [s.strip() for s in current_value.split(',') if s.strip()]
                        continue

                    # For all other tags:
                    if not current_value.strip():
                        # If the field is cleared, remove the tag from proposed_tags
                        if tag_key in track.proposed_tags:
                            del track.proposed_tags[tag_key]
                        # Also mark it for deletion from original tags if it exists there
                        track.proposed_tags[tag_key] = '' # Sentinel for deletion
                    else:
                        # Set the new value in proposed_tags
                        track.proposed_tags[tag_key] = current_value

            # After processing all fields for a track, regenerate its filename
            if not track.is_manual_rename:
                generate_filename_from_tags(track, self.settings_manager)

        self.tags_applied.emit()

    def set_enabled_state(self, enabled):
        for field in self.fields.values():
            field.setEnabled(enabled)
        self.apply_button.setEnabled(enabled)
