
import sys
import os
import re
import mutagen
import copy
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QSplitter, QToolBar, QFileDialog, QTreeWidgetItem, QMessageBox
)
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import Qt

from components.folder_browser import FolderBrowser
from components.file_browser import FileBrowser
from components.tools_panel import ToolsPanel
from components.settings_window import SettingsWindow
from components.warnings_window import WarningsWindow
from utils.settings_manager import SettingsManager
from utils.data_models import Track, Album, Artist
from utils.file_operations import save_track_changes
from tools.tag_generators import generate_tags_from_filename
from tools.filename_generators import generate_filename_from_tags
from tools.preview_utils import clear_preview
from tools.special_cleaner import extract_suffixes, normalize_apostrophes
from tools.clear_hidden_tags import clear_hidden_tags
from tools.camel_case import camel_case
from tools.find_replace import find_replace_in_title
from tools.name_to_tags import name_to_title
from components.find_replace_dialog import FindReplaceDialog

class MainWindow(QMainWindow):
    """
    The main application window.

    Manages the main UI components, data models, and user interactions.
    Connects UI signals to the appropriate handler functions for processing.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Music Renamer")
        self.setGeometry(100, 100, 1600, 900)

        # Set the window icon
        icon_path = os.path.join(os.path.dirname(__file__), 'icon.ico')
        self.setWindowIcon(QIcon(icon_path))

        # Application state
        self.root_path = None
        self.library = {}
        self.current_tracks_in_view = []
        self.is_highlighting_active = False
        self.warnings = []
        self.side_panels_visible = True
        self.last_splitter_sizes = [126, 1000, 88]

        # Managers and Components
        self.settings_manager = SettingsManager()
        self.create_toolbar()
        self.setup_central_widget()

    def setup_central_widget(self):
        """Initializes the main three-column layout with splitters."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)

        self.folder_browser = FolderBrowser()
        self.folder_browser.itemSelectionChanged.connect(self.on_folder_selected)
        self.folder_browser.itemSelectionChanged.connect(self.update_tools_state)
        self.main_splitter.addWidget(self.folder_browser)

        self.file_browser = FileBrowser(settings_manager=self.settings_manager)
        self.file_browser.itemSelectionChanged.connect(self.update_tools_state)
        self.file_browser.selection_changed_count.connect(self.update_selected_files_count) # Connect new signal
        self.file_browser.itemSelectionChanged.connect(self.update_tags_panel_with_selected_tracks) # New connection for tags panel
        self.file_browser.has_invalid_rows.connect(self.set_save_button_enabled)
        self.update_file_browser_columns()
        self.main_splitter.addWidget(self.file_browser)

        self.tools_panel = ToolsPanel(settings_manager=self.settings_manager)
        self.connect_tool_buttons()
        self.main_splitter.addWidget(self.tools_panel)

        self.main_splitter.setSizes([126, 1000, 88])
        main_layout.addWidget(self.main_splitter)

    def create_toolbar(self):
        """Creates the main toolbar and its actions."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        load_action = QAction("Load Folder", self)
        load_action.triggered.connect(self.load_folder)
        toolbar.addAction(load_action)

        refresh_action = QAction("Refresh", self)
        refresh_action.triggered.connect(self.handle_refresh)
        toolbar.addAction(refresh_action)

        save_action = QAction("Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.handle_save_changes)
        toolbar.addAction(save_action)

        

        self.warnings_action = QAction("Warnings (0)", self)
        self.warnings_action.triggered.connect(self.handle_show_warnings)
        toolbar.addAction(self.warnings_action)

        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.handle_open_settings)
        toolbar.addAction(settings_action)

        # Debug Action
        debug_load_action = QAction("Load Quick Folder", self)
        debug_load_action.triggered.connect(self.handle_debug_load_folder)
        debug_load_action.setToolTip("Load the folder specified in Settings (General) > Quick Folder Path")
        toolbar.addAction(debug_load_action)

    def update_selected_files_count(self, count):
        """Updates the label in the tools panel with the number of selected files."""
        if count == 0 and self.current_tracks_in_view:
            self.tools_panel.selected_files_label.setText(f"Selected: All {len(self.current_tracks_in_view)} files")
        else:
            self.tools_panel.selected_files_label.setText(f"Selected: {count} files")

    def update_tags_panel_with_selected_tracks(self):
        """Updates the tags panel with the currently selected tracks from the file browser,
        or all tracks in view if none are explicitly selected."""
        selected_tracks = self.file_browser.get_selected_tracks()
        if not selected_tracks and self.current_tracks_in_view:
            # If no tracks are explicitly selected, act on all tracks in the current view
            tracks_for_panel = self.current_tracks_in_view
        else:
            tracks_for_panel = selected_tracks
        self.tools_panel.tag_editor_widget.set_selected_tracks(tracks_for_panel)

    def connect_tool_buttons(self):
        """Connects signals from the ToolsPanel to handler methods."""
        self.tools_panel.btn_name_to_title.clicked.connect(self.handle_name_to_title)
        self.tools_panel.btn_camel_case.clicked.connect(self.handle_camel_case_title)
        self.tools_panel.btn_find_replace.clicked.connect(self.handle_find_replace)

        self.tools_panel.tag_editor_widget.tags_applied.connect(self.refresh_file_browser)
        self.tools_panel.btn_save_changes.clicked.connect(self.handle_save_changes)
        self.tools_panel.btn_revert.clicked.connect(self.handle_revert_changes)
        self.tools_panel.btn_clear_hidden_tags.clicked.connect(self.handle_clear_hidden_tags)

    # --- MAJOR UI ACTIONS ---
    def load_folder(self):
        """Opens a dialog to select the root music folder and scans the library."""
        path = QFileDialog.getExistingDirectory(self, "Select Root Music Folder")
        if path:
            self.root_path = path
            self.rescan_library()

    def rescan_library(self):
        """Scans the library folder, updates the model, and refreshes the UI."""
        self.library, self.warnings = self.scan_library(self.root_path)
        self.warnings_action.setText(f"Warnings ({len(self.warnings)})")
        folder_structure = {artist.name: [album.name for album in artist.albums] for artist in self.library.values()}
        self.folder_browser.populate_tree(self.root_path, folder_structure)

    def on_folder_selected(self):
        """Handles selection changes in the folder browser to update the file browser."""
        self.is_highlighting_active = False
        selected_items = self.folder_browser.selectedItems()
        if not selected_items:
            self.current_tracks_in_view = []
            self.file_browser.populate_files([])
            self.update_tags_panel_with_selected_tracks() # Add this line
            return

        selected_item = selected_items[0]
        self.current_tracks_in_view = []

        if selected_item.parent() is None: # Artist selected
            artist_name = selected_item.text(0)
            if artist_name in self.library:
                for album in self.library[artist_name].albums:
                    self.current_tracks_in_view.extend(copy.deepcopy(album.tracks))
        else: # Album selected
            album_name = selected_item.text(0)
            artist_name = selected_item.parent().text(0)
            if artist_name in self.library:
                for album in self.library[artist_name].albums:
                    if album.name == album_name:
                        self.current_tracks_in_view.extend(copy.deepcopy(album.tracks))
        # Auto-generate filename preview
        for track in self.current_tracks_in_view:
            generate_filename_from_tags(track, self.settings_manager)
        
        self.refresh_file_browser()
        self.update_tags_panel_with_selected_tracks()
        # Manually trigger the count update after refreshing the view
        self.update_selected_files_count(len(self.file_browser.selectionModel().selectedRows()))

    def update_tools_state(self):
        """Enables or disables tool groups based on current selections."""
        # The tools group and tags group should be enabled if there are any tracks in view
        # as tools will now operate on all tracks if none are explicitly selected.
        has_tracks_in_view = bool(self.current_tracks_in_view)
        self.tools_panel.tools_group.setEnabled(has_tracks_in_view)
        self.tools_panel.tags_group.setEnabled(has_tracks_in_view)
        self.tools_panel.btn_revert.setEnabled(has_tracks_in_view)
        self.set_save_button_enabled(not has_tracks_in_view)

    def set_save_button_enabled(self, has_invalid_rows):
        """Enables or disables the save button based on validation status."""
        self.tools_panel.btn_save_changes.setEnabled(not has_invalid_rows)

    # --- TOOL HANDLERS ---
    def handle_name_to_title(self):
        """Applies the 'name to title' tool to selected tracks."""
        selected_tracks = self.file_browser.get_selected_tracks()
        selected_paths = [track.path for track in selected_tracks]

        # Temporarily disconnect the signal to prevent premature refresh
        self.tools_panel.tag_editor_widget.tags_applied.disconnect(self.refresh_file_browser)

        try:
            # First, apply any pending changes from the tag editor to the data model
            self.tools_panel.tag_editor_widget.apply_tags_to_selected()

            # Then, generate title from the filename
            tracks_to_operate_on = self._get_tracks_for_tool_operation()
            if tracks_to_operate_on:
                for track in tracks_to_operate_on:
                    name_to_title(track, self.settings_manager)

            # Finally, manually refresh the browser to show all changes
            self.refresh_file_browser()
            self.file_browser.select_tracks_by_path(selected_paths)

        finally:
            # Always reconnect the signal
            self.tools_panel.tag_editor_widget.tags_applied.connect(self.refresh_file_browser)

    def handle_generate_filename_from_tags(self):
        """Applies the 'filename from tags' tool to selected tracks."""
        selected_tracks = self.file_browser.get_selected_tracks()
        selected_paths = [track.path for track in selected_tracks]

        # Temporarily disconnect the signal to prevent premature refresh
        self.tools_panel.tag_editor_widget.tags_applied.disconnect(self.refresh_file_browser)

        try:
            # First, apply any pending changes from the tag editor to the data model
            self.tools_panel.tag_editor_widget.apply_tags_to_selected()

            # Then, generate the new filename from the updated tags
            tracks_to_operate_on = self._get_tracks_for_tool_operation()
            if tracks_to_operate_on:
                for track in tracks_to_operate_on:
                    if not track.is_manual_rename:
                        generate_filename_from_tags(track, self.settings_manager)
            
            # Finally, manually refresh the browser to show all changes
            self.refresh_file_browser()
            self.file_browser.select_tracks_by_path(selected_paths)

        finally:
            # Always reconnect the signal
            self.tools_panel.tag_editor_widget.tags_applied.connect(self.refresh_file_browser)

    def handle_clear_preview(self):
        """Clears all proposed changes for selected tracks."""
        selected_tracks = self.file_browser.get_selected_tracks()
        selected_paths = [track.path for track in selected_tracks]

        tracks_to_operate_on = self._get_tracks_for_tool_operation()
        if not tracks_to_operate_on: return
        for track in tracks_to_operate_on: clear_preview(track)
        self.refresh_file_browser()
        self.file_browser.select_tracks_by_path(selected_paths)

    

    def handle_generate_tags_from_folder_name(self):
        """Placeholder for generating tags from folder name."""
        pass

    def handle_generate_filename_from_folder_tags(self):
        """Placeholder for generating filename from folder tags."""
        pass

    def handle_clear_folder_preview(self):
        """Placeholder for clearing folder preview."""
        pass

    def handle_camel_case_title(self):
        """Applies camel case formatting to the Title tag of selected tracks."""
        selected_tracks = self.file_browser.get_selected_tracks()
        selected_paths = [track.path for track in selected_tracks]

        tracks_to_operate_on = self._get_tracks_for_tool_operation()
        if not tracks_to_operate_on:
            return
        
        camel_case(tracks_to_operate_on, self.settings_manager)
        self.refresh_file_browser()
        self.file_browser.select_tracks_by_path(selected_paths)

    def handle_find_replace(self):
        """Opens a dialog for find/replace and applies it to the Title tag."""
        tracks_to_operate_on = self._get_tracks_for_tool_operation()
        if not tracks_to_operate_on:
            return

        dialog = FindReplaceDialog(self)
        if dialog.exec():
            find_text, replace_text = dialog.get_values()
            if find_text:  # Only proceed if there's something to find
                selected_paths = [track.path for track in self.file_browser.get_selected_tracks()]

                find_replace_in_title(tracks_to_operate_on, find_text, replace_text, self.settings_manager)

                self.refresh_file_browser()
                self.file_browser.select_tracks_by_path(selected_paths)

    def handle_clean_special_folder_name(self):
        """Placeholder for cleaning special folder name."""
        pass

    def handle_revert_changes(self):
        """Reloads the current view, discarding all pending changes."""
        self.on_folder_selected()

    def handle_clear_hidden_tags(self):
        """Clears any metadata that is set to hidden in settings for selected or all tracks."""
        tracks_to_operate_on = self._get_tracks_for_tool_operation()
        if not tracks_to_operate_on:
            return

        visible_columns = self.settings_manager.get_visible_columns()

        # This is the correct place for this logic.
        # We create a clean list of tag keys to keep, excluding non-tag columns.
        tags_to_keep = {
            t.lower().replace(' ', '')
            for t in visible_columns
            if t not in ['Original Name', 'New Name', '[Suffixes]', 'Title Raw']
        }
        
        selected_tracks = self.file_browser.get_selected_tracks()
        selected_paths = [track.path for track in selected_tracks]

        cleared_count, errors = clear_hidden_tags(tracks_to_operate_on, tags_to_keep)

        if errors:
            warnings_text = "\n".join(errors)
            dialog = WarningsWindow(self, warnings_text)
            dialog.exec()
            self.tools_panel.save_status_label.setText(f"{len(errors)} errors occurred.")
        else:
            # Update the main library object
            for track in tracks_to_operate_on:
                for artist in self.library.values():
                    for album in artist.albums:
                        for i, t in enumerate(album.tracks):
                            if t.path == track.path:
                                album.tracks[i] = track
                                break

            self.refresh_file_browser()
            self.file_browser.select_tracks_by_path(selected_paths)
            self.tools_panel.save_status_label.setText(f"Cleared {cleared_count} hidden tags.")

    def handle_refresh(self):
        """Refreshes and reloads the current folder and files."""
        if self.root_path:
            self.rescan_library()

    def handle_highlight_special(self):
        pass

    def handle_open_tag_form(self):
        """Opens the batch tag editing dialog."""
        tracks_to_operate_on = self._get_tracks_for_tool_operation()
        if not tracks_to_operate_on: return
        
        initial_data = {}
        tags_to_check = [t for t in self.settings_manager.get_visible_columns() if t not in ['Original Name', 'New Name', '[Suffixes]']] # Exclude [Suffixes]
        for tag in tags_to_check:
            first_val = tracks_to_operate_on[0].tags.get(tag)
            if all(t.tags.get(tag) == first_val for t in tracks_to_operate_on):
                initial_data[tag] = str(first_val or '')
            else:
                initial_data[tag] = '<multiple values>'
        
        dialog = TagForm(self, tags_to_check=tags_to_check, initial_data=initial_data)
        if dialog.exec():
            form_data = dialog.get_form_data()
            for track in tracks_to_operate_on:
                track.proposed_tags.update(form_data)
            self.refresh_file_browser()

    def handle_highlight_special(self):
        """Activates special highlighting mode."""
        self.is_highlighting_active = True
        self.refresh_file_browser()

    def handle_open_settings(self):
        """Opens the settings dialog and applies changes if saved."""
        dialog = SettingsWindow(self, self.settings_manager)
        if dialog.exec():
            # Store current state to restore after refresh
            current_selected_folder_path = None
            selected_items = self.folder_browser.selectedItems()
            if selected_items:
                # Assuming the first selected item is the relevant one
                current_selected_folder_path = self.folder_browser.get_path_from_item(selected_items[0])

            # Store current proposed changes for all tracks
            # This is a simplified approach; a more robust solution might involve
            # deep copying or a dedicated state management system.
            # For now, we'll store proposed changes for tracks that have them.
            proposed_changes_map = {}
            for artist in self.library.values():
                for album in artist.albums:
                    for track in album.tracks:
                        if track.proposed_tags or track.proposed_filename:
                            proposed_changes_map[track.path] = {
                                'proposed_tags': track.proposed_tags.copy(),
                                'proposed_filename': track.proposed_filename,
                                'is_manual_rename': track.is_manual_rename
                            }

            self.settings_manager.load_settings()
            self.update_file_browser_columns()
            
            if self.root_path:
                self.rescan_library() # This will re-populate self.library and clear proposed changes

                # Reapply proposed changes
                for artist in self.library.values():
                    for album in artist.albums:
                        for track in album.tracks:
                            if track.path in proposed_changes_map:
                                changes = proposed_changes_map[track.path]
                                track.proposed_tags = changes['proposed_tags']
                                track.proposed_filename = changes['proposed_filename']
                                track.is_manual_rename = changes['is_manual_rename']
                
                # Re-select the previously selected folder
                if current_selected_folder_path:
                    self.folder_browser.select_path(current_selected_folder_path)
                
                self.refresh_file_browser() # Refresh file browser to show reapplied changes

    def handle_show_warnings(self):
        """Displays the list of structural library warnings."""
        if not self.warnings:
            QMessageBox.information(self, "No Warnings", "No structural warnings found in the library.")
            return
        warnings_text = "\n".join(self.warnings)
        dialog = WarningsWindow(self, warnings_text)
        dialog.exec()

    def handle_debug_load_folder(self):
        """Loads the folder specified in Quick Folder Path setting."""
        quick_path = self.settings_manager.get('general', {}).get('quick_folder_path', '')
        if quick_path and os.path.exists(quick_path) and os.path.isdir(quick_path):
            self.root_path = quick_path
            self.rescan_library()
            
        else:
            QMessageBox.warning(self, "Quick Load Error", f"Quick folder not found or not set: {quick_path}")

    def handle_save_changes(self):
        """Saves all proposed tag and filename changes to disk for the selected artist's folder."""
        selected_items = self.folder_browser.selectedItems()
        if not selected_items:
            self.tools_panel.save_status_label.setText("Select an artist/album to save.")
            return

        selected_item = selected_items[0]
        
        artist_obj = None
        if selected_item.parent() is None:
            artist_name = selected_item.text(0)
            artist_obj = self.library.get(artist_name)
        else:
            artist_name = selected_item.parent().text(0)
            artist_obj = self.library.get(artist_name)

        if not artist_obj:
            self.tools_panel.save_status_label.setText("Could not find artist.")
            return

        # Get the tracks to operate on, respecting the current selection
        tracks_to_operate_on = self._get_tracks_for_tool_operation()

        tracks_with_changes = [
            track for track in tracks_to_operate_on
            if track.proposed_tags or (track.proposed_filename and track.proposed_filename != track.filename)
        ]

        # Store old paths for library update
        for track in tracks_with_changes:
            track.old_path = track.path

        if not tracks_with_changes:
            self.tools_panel.save_status_label.setText("No changes to save.")
            return

        errors = []
        success_count = 0
        for track in tracks_with_changes:
            success, error_message = save_track_changes(track)
            if success:
                success_count += 1
                track.has_error = False
            else:
                errors.append(error_message)
                track.has_error = True

        if errors:
            warnings_text = "\n".join(errors)
            dialog = WarningsWindow(self, warnings_text)
            dialog.exec()
            self.tools_panel.save_status_label.setText(f"{len(errors)} errors occurred.")
        else:
            self.tools_panel.save_status_label.setText(f"Saved {success_count} files successfully.")

        # Update self.library with new filenames and paths to reflect changes when navigating back
        for track in tracks_with_changes:
            old_path = getattr(track, 'old_path', track.path)
            for artist in self.library.values():
                for album in artist.albums:
                    for i, lib_track in enumerate(album.tracks):
                        if lib_track.path == old_path:
                            lib_track.filename = track.filename
                            lib_track.path = track.path
                            break

        # Save selection before refresh
        selected_tracks = self.file_browser.get_selected_tracks()
        selected_paths = [track.path for track in selected_tracks]
        
        self.refresh_file_browser()

        # Restore selection
        self.file_browser.select_tracks_by_path(selected_paths)

    # --- UI REFRESH ---
    def update_file_browser_columns(self):
        """Reloads column configuration from settings and applies it to the file browser."""
        visible_columns = self.settings_manager.get_visible_columns()
        
        # Replace 'Title' with 'Title Raw' and 'Title'
        title_was_present = False
        if 'Title' in visible_columns:
            title_was_present = True
            index = visible_columns.index('Title')
            visible_columns.pop(index)
            visible_columns.insert(index, 'Title')

        if '[Suffixes]' not in visible_columns:
            # try to insert it before 'New Name'
            if 'New Name' in visible_columns:
                index = visible_columns.index('New Name')
                visible_columns.insert(index, '[Suffixes]')
            else:
                visible_columns.append('[Suffixes]')

        # Add Title Raw at the very end if it was originally present
        if title_was_present:
            visible_columns.append('Title Raw')
        
        visible_columns.append('OTHER')

        self.file_browser.set_columns(visible_columns)

    def refresh_file_browser(self):
        """Repopulates the file browser, applying highlights if active."""
        highlight_rules = self.settings_manager.get("ui", {}).get("highlight_colors") if self.is_highlighting_active else None
        self.file_browser.populate_files(self.current_tracks_in_view, highlight_rules)
        self.file_browser.update()
        self.file_browser.viewport().repaint()
        self.file_browser.model().layoutChanged.emit()

    def _refresh_file_browser_display(self):
        """Refreshes the file browser display with the current tracks."""
        highlight_rules = self.settings_manager.get("ui", {}).get("highlight_colors") if self.is_highlighting_active else None
        self.file_browser.populate_files(self.current_tracks_in_view, highlight_rules)

    # --- DATA MODELING ---
    def scan_library(self, root_path):
        """Scans the given root path and builds a library of Artist, Album, and Track objects."""
        library = {}
        warnings = []
        excluded_folders = self.settings_manager.get("general", {}).get("excluded_folders", [])
        
        for artist_name in os.listdir(root_path):
            artist_path = os.path.join(root_path, artist_name)
            if not os.path.isdir(artist_path) or artist_name in excluded_folders:
                continue
            
            artist_obj = Artist(name=artist_name, path=artist_path)
            for item_name in os.listdir(artist_path):
                item_path = os.path.join(artist_path, item_name)
                if os.path.isfile(item_path):
                    warnings.append(f"File in artist folder: {item_path}")
                    continue
                
                album_obj = Album(name=item_name, path=item_path)
                supported_formats = self.settings_manager.get("general", {}).get("supported_audio_formats", [])
                for filename in os.listdir(item_path):
                    file_path = os.path.join(item_path, filename)
                    if os.path.isdir(file_path):
                        warnings.append(f"Folder in album folder: {file_path}")
                        continue
                    
                    # Check if the file extension is in the supported formats list
                    file_extension = os.path.splitext(filename)[1].lower()
                    if file_extension not in supported_formats:
                        warnings.append(f"Unsupported audio format: {file_path}")
                        continue
                    
                    original_tags = self.read_metadata(file_path)

                    # Normalize apostrophes in the loaded metadata
                    if 'title' in original_tags:
                        original_tags['title'] = normalize_apostrophes(original_tags['title'])
                    if 'artist' in original_tags:
                        original_tags['artist'] = normalize_apostrophes(original_tags['artist'])

                    # Check for read-only files and add warning
                    if not os.access(file_path, os.W_OK):
                        warnings.append(f"Read-only file: {file_path}")

                    # The folder structure is the source of truth for artist/album
                    folder_artist = artist_name
                    folder_album = album_obj.name
                    
                    # The raw title is from the original file tags
                    raw_title = original_tags.get('title', '')
                    
                    # Clean the title using folder-derived artist/album for accuracy
                    clean_title, suffixes = extract_suffixes(raw_title, folder_artist)

                    # Create the track object. 'tags' MUST be the original file tags.
                    track_obj = Track(path=file_path, filename=filename, tags=original_tags, suffixes=suffixes, clean_title=clean_title)
                    
                    # --- LOGIC TO PROPOSE CHANGES ---
                    # Always propose artist to be the folder artist
                    track_obj.proposed_tags['artist'] = folder_artist

                    # Propose album change if it differs from the original file tag
                    if original_tags.get('album') != folder_album:
                        track_obj.proposed_tags['album'] = folder_album

                    # Propose title change if cleaning it resulted in a difference
                    reconstructed_title = f"{clean_title}{''.join(suffixes)}"
                    normalized_reconstructed = re.sub(r'[\s\[\]\(\)]', '', reconstructed_title).lower()
                    normalized_raw = re.sub(r'[\s\[\]\(\)]', '', raw_title).lower()
                    if normalized_reconstructed != normalized_raw:
                        track_obj.proposed_tags['title'] = clean_title
                    
                    album_obj.tracks.append(track_obj)
                
                if album_obj.tracks: artist_obj.albums.append(album_obj)
            
            if artist_obj.albums: library[artist_name] = artist_obj
        return library, warnings

    def read_metadata(self, file_path):
        """Reads metadata from a single audio file using mutagen."""
        try:
            audio = mutagen.File(file_path, easy=True)
            if audio is None: return {}
            
            tags = {}
            for key, value in audio.items():
                tags[key] = value[0] if value else ''
            return tags
        except Exception as e:
            error_message = f"Error reading metadata for {file_path}: {e}"
            self.warnings.append(error_message) # Add to warnings list
            return {}

    def _get_tracks_for_tool_operation(self):
        """Returns the list of tracks to operate on for a tool.
        If files are explicitly selected in the file browser, returns those.
        Otherwise, returns all tracks currently in view (from the selected folder).
        """
        selected_tracks = self.file_browser.get_selected_tracks()
        if not selected_tracks and self.current_tracks_in_view:
            return self.current_tracks_in_view
        return selected_tracks

    def keyPressEvent(self, event):
        """Handles key press events for the main window."""
        if event.key() == Qt.Key.Key_F1:
            self.toggle_side_panels()
        elif event.key() == Qt.Key.Key_F5:
            self.handle_save_changes()
        elif event.key() == Qt.Key.Key_F6:
            self.folder_browser.select_next_sibling()
        elif event.key() == Qt.Key.Key_F7:
            self.folder_browser.select_previous_sibling()
        elif event.key() == Qt.Key.Key_F3:
            self.handle_clear_hidden_tags()
        elif event.key() == Qt.Key.Key_F4:
            self.handle_camel_case_title()
        else:
            super().keyPressEvent(event)

    def toggle_side_panels(self):
        """Toggles the visibility of the side panels."""
        if self.side_panels_visible:
            self.last_splitter_sizes = self.main_splitter.sizes()
            self.main_splitter.setSizes([0, self.last_splitter_sizes[1], 0])
            self.side_panels_visible = False
        else:
            self.main_splitter.setSizes(self.last_splitter_sizes)
            self.side_panels_visible = True

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())
