from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem, QTreeWidgetItemIterator

class FolderBrowser(QTreeWidget):
    """
    A widget to display the folder structure of the music library.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabel("Music Library")
        self.setIndentation(15)

    def populate_tree(self, root_path, folder_structure):
        """
        Populates the tree view with the given folder structure.

        Args:
            root_path (str): The root path of the library.
            folder_structure (dict): A nested dictionary representing the folder structure.
        """
        self.root_path = root_path # Set root_path here
        self.clear()
        for artist, albums in folder_structure.items():
            artist_item = QTreeWidgetItem(self, [artist])
            if albums:
                for album in albums:
                    album_item = QTreeWidgetItem(artist_item, [album])
                    # You can store the full path in the item for later use
                    # album_item.setData(0, Qt.ItemDataRole.UserRole, os.path.join(root_path, artist, album))
            artist_item.setExpanded(False) # Collapse artists by default

    def get_path_from_item(self, item):
        """
        Constructs the full path from a QTreeWidgetItem.
        Assumes a structure of Artist -> Album.
        """
        if item.parent() is None: # Artist item
            return self.root_path
        else: # Album item
            artist_name = item.parent().text(0)
            album_name = item.text(0)
            return os.path.join(self.root_path, artist_name, album_name)

    def select_path(self, path):
        """
        Selects the QTreeWidgetItem corresponding to the given path.
        """
        # First, clear any existing selection
        self.clearSelection()

        # Iterate through top-level items (artists)
        iterator = QTreeWidgetItemIterator(self)
        while iterator.value():
            item = iterator.value()
            item_path = self.get_path_from_item(item)
            if item_path == path:
                self.setCurrentItem(item)
                self.scrollToItem(item)
                break
            iterator += 1

    def select_next_sibling(self):
        """
        Selects the next sibling item in the tree.
        For albums, moves to next album under same artist.
        For artists, moves to next artist.
        """
        current = self.currentItem()
        if not current:
            return

        parent = current.parent()
        if parent:  # Album item
            for i in range(parent.childCount()):
                if parent.child(i) == current:
                    next_index = (i + 1) % parent.childCount()
                    next_item = parent.child(next_index)
                    self.setCurrentItem(next_item)
                    self.scrollToItem(next_item)
                    # Trigger selection change if connected
                    break
        else:  # Artist item
            for i in range(self.topLevelItemCount()):
                if self.topLevelItem(i) == current:
                    next_index = (i + 1) % self.topLevelItemCount()
                    next_item = self.topLevelItem(next_index)
                    self.setCurrentItem(next_item)
                    self.scrollToItem(next_item)
                    # Trigger selection change if connected
                    break

    def select_previous_sibling(self):
        """
        Selects the previous sibling item in the tree.
        For albums, moves to previous album under same artist.
        For artists, moves to previous artist.
        """
        current = self.currentItem()
        if not current:
            return

        parent = current.parent()
        if parent:  # Album item
            for i in range(parent.childCount()):
                if parent.child(i) == current:
                    prev_index = (i - 1) % parent.childCount()
                    prev_item = parent.child(prev_index)
                    self.setCurrentItem(prev_item)
                    self.scrollToItem(prev_item)
                    # Trigger selection change if connected
                    break
        else:  # Artist item
            for i in range(self.topLevelItemCount()):
                if self.topLevelItem(i) == current:
                    prev_index = (i - 1) % self.topLevelItemCount()
                    prev_item = self.topLevelItem(prev_index)
                    self.setCurrentItem(prev_item)
                    self.scrollToItem(prev_item)
                    # Trigger selection change if connected
                    break
