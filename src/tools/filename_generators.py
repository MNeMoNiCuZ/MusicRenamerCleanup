import os
import re
from .special_cleaner import normalize_apostrophes

ILLEGAL_FILENAME_CHARS = r'[\\/:*?"<>|]'

def _sanitize_filename(filename: str) -> str:
    """Removes illegal filename characters."""
    return re.sub(ILLEGAL_FILENAME_CHARS, '', filename)

def generate_filename_from_tags(track, settings_manager):
    """
    Generates a proposed filename for a track based on its tags.
    Format: 'Artist - Title[Suffix1][Suffix2].ext'
    """
    artist = track.proposed_tags.get('artist', track.tags.get('artist', 'Unknown Artist'))
    # Normalize apostrophes to standard format
    artist = normalize_apostrophes(artist)

    # Use the clean_title which has suffixes pre-stripped
    title = track.proposed_tags.get('title', track.clean_title)
    # Normalize apostrophes to standard format
    title = normalize_apostrophes(title)

    # Replace certain separators with hyphens for better filename compatibility
    title = title.replace(' / ', '-').replace(' \\ ', '-').replace('/', '-').replace('\\', '-')

    # Get words to remove from settings
    words_to_remove = settings_manager.get('general', {}).get('words_to_remove', [])

    # Apply words to remove to artist and title
    for word in words_to_remove:
        artist = re.sub(r'\b' + re.escape(word) + r'\b', '', artist, flags=re.IGNORECASE).strip()
        title = re.sub(r'\b' + re.escape(word) + r'\b', '', title, flags=re.IGNORECASE).strip()

    _, ext = os.path.splitext(track.filename)

    # Basic sanitization
    # Apostrophes have been normalized to standard format above
    safe_artist = "".join(c for c in artist if c.isalnum() or c in " _-()!'&.+@#$%^=;").rstrip()
    safe_title = "".join(c for c in title if c.isalnum() or c in " _-()!'&.+@#$%^=;").rstrip()

    # Format suffixes and append to filename
    suffixes_formatted = ''
    if track.suffixes:
        # Create a set of existing suffix contents for efficient lookup
        existing_suffix_contents = {s.strip('[]').lower() for s in track.suffixes}

        # Suffixes are already de-duplicated during the initial parsing.
        # We just need to format them correctly.
        suffixes_formatted = ''.join(track.suffixes).replace('/', '-').replace('\\', '-')

    track.proposed_filename = _sanitize_filename(f"{safe_artist} - {safe_title}{suffixes_formatted}{ext}")
    return track




