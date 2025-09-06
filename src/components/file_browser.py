from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QAbstractScrollArea, QMenu
from PyQt6.QtGui import QAction, QBrush, QColor, QFont
from PyQt6.QtCore import Qt, pyqtSignal, QItemSelection, QItemSelectionModel
import os
import sys
import subprocess
import re
from utils.color_utils import get_contrasting_text_color
from tools.filename_generators import generate_filename_from_tags

class FileBrowser(QTableWidget):
    """
    A widget to display audio files and their metadata in a table.
    Handles displaying proposed changes and manual edits.
    """
    selection_changed_count = pyqtSignal(int)
    has_invalid_rows = pyqtSignal(bool)

    def __init__(self, parent=None, settings_manager=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.setSortingEnabled(False)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setVisible(False)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.track_map = {}
        self.album_row_map = {}
        self.is_handling_change = False
        self.highlight_rules = None
        self.has_duplicates = False

        self.setStyleSheet("""
            QHeaderView::section {
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 3px 5px; /* Add padding to all cells */
            }
            QTableWidget QLineEdit {
                selection-background-color: black;
                selection-color: white;
            }
        """)

        self.itemChanged.connect(self.handle_item_changed)
        self.itemSelectionChanged.connect(self._emit_selection_count)

    def wheelEvent(self, event):
        """Overrides the default wheel event to prevent selection on scroll."""
        QAbstractScrollArea.wheelEvent(self, event)

    def _emit_selection_count(self):
        """Internal slot to emit the count of selected tracks."""
        count = len(self.selectionModel().selectedRows())
        self.selection_changed_count.emit(count)

    def set_columns(self, columns):
        self.columns = columns
        self.setColumnCount(len(columns))
        self.setHorizontalHeaderLabels([col.upper() for col in columns])
        for i, col in enumerate(columns):
            if col.upper() == 'OTHER':
                # Set a fixed width and prevent it from being resized.
                self.setColumnWidth(i, 30)
                self.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
            else:
                # Allow other columns to be resized interactively.
                self.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)

    def populate_files(self, tracks, highlight_rules=None):
        self.is_handling_change = True
        self.highlight_rules = highlight_rules
        self.setRowCount(0)
        self.track_map.clear()
        self.album_row_map.clear()
        self.has_duplicates = False
        if not tracks:
            self.is_handling_change = False
            return

        row_count = 0
        albums = {}
        for track in tracks:
            album_path = os.path.dirname(track.path)
            if album_path not in albums:
                albums[album_path] = []
            albums[album_path].append(track)

        for album_path in sorted(albums.keys()):
            album_tracks = albums[album_path]
            self.insertRow(row_count)
            self.setRowHeight(row_count, 30)
            album_name = os.path.basename(album_path)
            header_item = QTableWidgetItem(album_name)
            header_font = QFont(); header_font.setBold(True); header_font.setPointSize(12)
            header_item.setFont(header_font)
            header_item.setFlags(header_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.setItem(row_count, 0, header_item)
            self.setSpan(row_count, 0, 1, len(self.columns))
            self.album_row_map[row_count] = []
            album_header_row = row_count
            row_count += 1

            # Check for duplicate names in this album
            for t in album_tracks:
                t.has_duplicate = False
            name_counts = {}
            for t in album_tracks:
                new_name = t.proposed_filename or t.filename
                name_counts[new_name] = name_counts.get(new_name, 0) + 1
            for t in album_tracks:
                new_name = t.proposed_filename or t.filename
                t.has_duplicate = name_counts[new_name] > 1
            self.has_duplicates = self.has_duplicates or any(t.has_duplicate for t in album_tracks)

            for track in sorted(album_tracks, key=lambda t: t.filename):
                self.insertRow(row_count)
                self.track_map[row_count] = track
                self.album_row_map[album_header_row].append(row_count)
                
                for col_idx, col_name in enumerate(self.columns):
                    item = self.create_table_item(track, col_name)
                    self.setItem(row_count, col_idx, item)
                
                self._style_row_items(row_count)
                row_count += 1
        
        # --- Column Sizing Logic ---
        # 1. Temporarily set resize mode to content-based to get ideal widths
        for i in range(self.columnCount()):
            self.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

        # 2. Calculate available width, accounting for the vertical scrollbar
        available_width = self.viewport().width()
        if self.verticalScrollBar().isVisible():
            available_width -= self.verticalScrollBar().width()

        # 3. Get the total width of all content
        total_content_width = sum(self.horizontalHeader().sectionSize(i) for i in range(self.columnCount()))

        # 4. Distribute extra space if the content is narrower than the viewport
        if total_content_width < available_width and self.columnCount() > 0:
            # Exclude fixed columns from space distribution
            interactive_columns = [i for i, col in enumerate(self.columns) if col.upper() != 'OTHER']
            if interactive_columns:
                extra_space = available_width - total_content_width
                space_per_column = extra_space / len(interactive_columns)
                for i in interactive_columns:
                    self.setColumnWidth(i, self.horizontalHeader().sectionSize(i) + int(space_per_column))
        
        # 5. Set the resize mode back to interactive for the user
        for i in range(self.columnCount()):
            self.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)

        self.is_handling_change = False
        self.validate_rows()

    def get_row_color(self, track, highlight_rules):
        if not highlight_rules: return None

        if not track.tags.get('title'):
            missing_title_color = highlight_rules.get("missing_title_highlight", {}).get("color")
            if missing_title_color:
                return QColor(missing_title_color)

        for rule_name, rule_data in highlight_rules.items():
            if rule_name == "missing_title_highlight":
                continue
            color = rule_data.get("color")
            keywords = rule_data.get("keywords", [])
            
            if any(keyword.lower() in track.filename.lower() for keyword in keywords) or \
               (track.proposed_filename and any(keyword.lower() in track.proposed_filename.lower() for keyword in keywords)):
                return QColor(color)
        return None

    def create_table_item(self, track, col_name):
        cell_value, font, background_color = "", QFont(), None
        is_proposed = False
        tag_key = col_name.lower().replace(' ', '')

        # Normalize column name for comparison
        upper_col_name = col_name.upper()

        if upper_col_name == 'ORIGINAL NAME':
            cell_value = f"    {track.filename}"
        elif upper_col_name == 'NEW NAME':
            cell_value = track.proposed_filename or track.filename
            #print(f"[DEBUG] New Name for {track.filename}: '{cell_value}'")
            if track.is_manual_rename:
                font.setBold(True); font.setItalic(True)
                bg_settings = self.settings_manager.get('ui', {}).get('manual_edit_highlight', {})
                background_color = QColor(bg_settings.get('background', '#FFFF99'))
            elif cell_value and cell_value != track.filename:
                is_proposed = True
        elif upper_col_name == 'TITLE RAW':
            cell_value = str(track.tags.get('title', ''))
        elif upper_col_name == 'TITLE':
            base_title = str(track.proposed_tags.get('title', track.clean_title))
            suffixes = "".join(track.suffixes)
            cell_value = f"{base_title}{suffixes}"
            raw_title = str(track.tags.get('title', ''))

            # Use normalized comparison to check for proposed changes
            normalized_cell = re.sub(r'[\s\[\]\(\)]', '', cell_value).lower()
            normalized_raw = re.sub(r'[\s\[\]\(\)]', '', raw_title).lower()
            if normalized_cell != normalized_raw:
                is_proposed = True
        elif upper_col_name == '[SUFFIXES]':
            cell_value = "".join(track.suffixes)
        elif upper_col_name == 'OTHER':
            standard_tags = {'artist', 'album', 'title', 'genre', 'date', 'tracknumber', 'albumartist', 'lyrics'}
            extra_tags = {k: v for k, v in track.tags.items() if k.lower() not in standard_tags and v}
            cell_value = str(len(extra_tags))
            tooltip_text = "\n".join([f"{k}: {v}" for k, v in extra_tags.items()])
            item = QTableWidgetItem(cell_value)
            item.setToolTip(tooltip_text)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            return item
        else: # Generic tag columns
            proposed_value = track.proposed_tags.get(tag_key)
            original_value = track.tags.get(tag_key, '')
            
            if proposed_value is not None:
                cell_value = str(proposed_value)
                if str(proposed_value) != str(original_value):
                    is_proposed = True
            else:
                cell_value = str(original_value)

        if is_proposed:
            font.setBold(True)

        item = QTableWidgetItem(cell_value)
        item.setFont(font)
        if background_color:
            item.setBackground(background_color)
            item.setForeground(get_contrasting_text_color(background_color))
        elif track.has_error:
            item.setForeground(QColor('yellow'))

        if upper_col_name in ['ORIGINAL NAME', 'TITLE RAW']:
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        
        return item

    def _style_row_items(self, row):
        track = self.track_map.get(row)
        if not track:
            return

        row_color = self.get_row_color(track, self.highlight_rules)
        title = track.proposed_tags.get('title', track.tags.get('title', ''))
        is_invalid = not title.strip()

        for col_idx, col_name in enumerate(self.columns):
            item = self.item(row, col_idx)
            if not item:
                continue

            # Apply row background color, respecting manual edit highlight
            if row_color and not (col_name.upper() == 'NEW NAME' and track.is_manual_rename):
                item.setBackground(row_color)

            # Apply text color based on status
            if is_invalid:
                item.setForeground(QColor("red"))
            elif track.has_duplicate:
                item.setForeground(QColor("#FFC0CB"))
            elif row_color:
                item.setForeground(get_contrasting_text_color(row_color))

    def _check_duplicates_for_album(self, track):
        album_path = os.path.dirname(track.path)
        album_tracks = [t for t in self.track_map.values() if os.path.dirname(t.path) == album_path]

        # Clear duplicates for album
        for t in album_tracks:
            t.has_duplicate = False

        # Check duplicates
        name_counts = {}
        for t in album_tracks:
            new_name = t.proposed_filename or t.filename
            name_counts[new_name] = name_counts.get(new_name, 0) + 1

        for t in album_tracks:
            new_name = t.proposed_filename or t.filename
            t.has_duplicate = name_counts[new_name] > 1

        self.has_duplicates = any(t.has_duplicate for t in self.track_map.values())

    def validate_rows(self):
        """Checks all tracks for validation errors and emits a signal."""
        has_missing_title = False
        for track in self.track_map.values():
            title = track.proposed_tags.get('title', track.tags.get('title', ''))
            if not title.strip():
                has_missing_title = True
                break
        self.has_invalid_rows.emit(has_missing_title or self.has_duplicates)

    def handle_item_changed(self, item):
        if self.is_handling_change: return
        row, col = item.row(), item.column()
        if row not in self.track_map: return
        
        track = self.track_map[row]
        col_name = self.columns[col]
        new_value = item.text().strip()

        self.is_handling_change = True
        upper_col_name = col_name.upper()
        if upper_col_name == 'NEW NAME':
            track.proposed_filename = new_value
            track.is_manual_rename = True
            bg_settings = self.settings_manager.get('ui', {}).get('manual_edit_highlight', {})
            background_color = QColor(bg_settings.get('background', '#FFFF99'))
            item.setBackground(background_color)
            item.setForeground(get_contrasting_text_color(background_color))
            self._check_duplicates_for_album(track)
        elif upper_col_name == '[SUFFIXES]':
            track.suffixes = [s.strip() for s in new_value.split(',') if s.strip()]
            if not track.is_manual_rename:
                generate_filename_from_tags(track, self.settings_manager)
        else:
            tag_key = col_name.lower().replace(' ', '')
            track.proposed_tags[tag_key] = new_value
            if tag_key == 'title':
                track.clean_title = new_value  # Update clean_title to reflect manual title change
                if not track.is_manual_rename:
                    generate_filename_from_tags(track, self.settings_manager)
                    self._check_duplicates_for_album(track)
        
        self.is_handling_change = False
        
        self.refresh_row(row)
        self.validate_rows()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            item = self.itemAt(event.pos())
            if item:
                row = item.row()
                if row in self.album_row_map:
                    selection_model = self.selectionModel()
                    
                    if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                        selection_flag = QItemSelectionModel.SelectionFlag.Toggle | QItemSelectionModel.SelectionFlag.Rows
                    else:
                        selection_model.clearSelection()
                        selection_flag = QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows

                    selection = QItemSelection()
                    for track_row in self.album_row_map[row]:
                        index = self.model().index(track_row, 0)
                        selection.select(index, index)
                    
                    selection_model.select(selection, selection_flag)
                    
                    event.accept()
                    return
        super().mousePressEvent(event)

    def get_selected_tracks(self):
        selected_tracks = []
        selected_rows = {index.row() for index in self.selectionModel().selectedRows()}
        for row in selected_rows:
            if row in self.track_map:
                selected_tracks.append(self.track_map[row])
        return selected_tracks

    def select_tracks_by_path(self, track_paths_to_select):
        """Selects rows in the table based on a list of track file paths."""
        selection_model = self.selectionModel()
        selection = QItemSelection()
        
        path_to_row_map = {track.path: row for row, track in self.track_map.items()}

        for path in track_paths_to_select:
            row = path_to_row_map.get(path)
            if row is not None:
                start_index = self.model().index(row, 0)
                end_index = self.model().index(row, self.columnCount() - 1)
                selection.select(start_index, end_index)
        
        selection_model.select(selection, QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows)

    def refresh_row(self, row):
        """Refreshes a single row in the table to reflect updated track data."""
        if row not in self.track_map:
            return

        self.is_handling_change = True
        track = self.track_map[row]
        for col_idx, col_name in enumerate(self.columns):
            item = self.create_table_item(track, col_name)
            self.setItem(row, col_idx, item)
        
        self._style_row_items(row)
        self._check_duplicates_for_album(track)
        self.is_handling_change = False

    def contextMenuEvent(self, event):
        item = self.itemAt(event.pos())
        if not item:
            return

        row = item.row()
        if row in self.track_map:
            right_clicked_track = self.track_map[row]
            folder_path = os.path.dirname(right_clicked_track.path)
            selected_tracks = self.get_selected_tracks()
            
            is_right_clicked_selected = any(t.path == right_clicked_track.path for t in selected_tracks)

            if is_right_clicked_selected:
                tracks_in_folder = [t for t in selected_tracks if os.path.dirname(t.path) == folder_path]
            else:
                tracks_in_folder = [right_clicked_track]

            menu = QMenu(self)
            action_text = "Reveal in Folder" if len(tracks_in_folder) == 1 else "Open Containing Folder"
            open_action = QAction(action_text, self)

            def perform_open():
                try:
                    if sys.platform == "win32":
                        if len(tracks_in_folder) == 1:
                            subprocess.run(['explorer', '/select,', tracks_in_folder[0].path.replace('/', '\\')])
                        else:
                            os.startfile(folder_path)
                    elif sys.platform == "darwin":
                        if len(tracks_in_folder) == 1:
                            subprocess.run(['open', '-R', tracks_in_folder[0].path])
                        else:
                            subprocess.call(["open", folder_path])
                    else: # Linux
                        subprocess.call(["xdg-open", folder_path])
                except Exception as e:
                    print(f"Error opening/revealing path: {e}")

            open_action.triggered.connect(perform_open)
            menu.addAction(open_action)

            # Add "Open Files" action for selected tracks
            if selected_tracks:
                plural = "s" if len(selected_tracks) > 1 else ""
                open_files_action = QAction(f"Open {len(selected_tracks)} File{plural}", self)
                def perform_open_files():
                    for track in selected_tracks:
                        try:
                            if sys.platform == "win32":
                                os.startfile(track.path)
                            elif sys.platform == "darwin":
                                subprocess.call(["open", track.path])
                            else:
                                subprocess.call(["xdg-open", track.path])
                        except Exception as e:
                            print(f"Error opening file {track.path}: {e}")
                open_files_action.triggered.connect(perform_open_files)
                menu.addAction(open_files_action)
            menu.exec(event.globalPos())
        else:
            super().contextMenuEvent(event)

    def handle_item_double_clicked(self, item):
        """Opens a file or folder on double click."""
        row = item.row()
        path = None
        if row in self.track_map:
            # It's a track
            track = self.track_map[row]
            path = track.path
        elif row in self.album_row_map:
            # It's an album header
            track_rows = self.album_row_map[row]
            if track_rows and track_rows[0] in self.track_map:
                track = self.track_map[track_rows[0]]
                path = os.path.dirname(track.path)

        if path:
            try:
                if sys.platform == "win32":
                    os.startfile(path)
                elif sys.platform == "darwin":
                    subprocess.call(["open", path])
                else:
                    subprocess.call(["xdg-open", path])
            except Exception as e:
                print(f"Error opening path: {e}")