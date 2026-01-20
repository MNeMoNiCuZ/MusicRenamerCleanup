import re
from utils.data_models import Track
from .special_cleaner import extract_suffixes, normalize_apostrophes
from utils.settings_manager import SettingsManager

def name_to_title(track: Track, settings_manager):
    """
    Converts the original filename to a title, extracting suffixes.
    Ignores non-letter characters at the start (numbers, periods, etc.).
    Ignores file extension.
    """
    # Remove file extension
    import os
    original_name = os.path.splitext(track.filename)[0]

    # Step 0: Normalize apostrophes to standard format
    original_name = normalize_apostrophes(original_name)

    # Step 1: Ignore leading non-letter characters
    cleaned_name = re.sub(r'^[^a-zA-Z]+', '', original_name)

    # Step 2: Extract suffixes and get clean title
    artist = track.tags.get('artist', track.proposed_tags.get('artist', ''))
    # Normalize apostrophes in artist metadata
    artist = normalize_apostrophes(artist)

    # Also normalize title metadata if it exists
    existing_title = track.tags.get('title', track.proposed_tags.get('title', ''))
    if existing_title:
        normalized_title = normalize_apostrophes(existing_title)
        track.tags['title'] = normalized_title
        track.proposed_tags['title'] = normalized_title

    clean_title, extracted_suffixes = extract_suffixes(cleaned_name, artist, settings_manager)

    # Step 3: Apply title case formatting (simple implementation)
    title_cased = re.sub(r'\b\w', lambda m: m.group(0).upper(), clean_title.lower())

    # Step 4: Update track fields (only title and suffixes)
    track.clean_title = title_cased
    track.proposed_tags['title'] = title_cased
    track.suffixes = extracted_suffixes

    # Step 5: Regenerate the proposed filename to reflect the title change
    from .filename_generators import generate_filename_from_tags
    if not track.is_manual_rename:
        generate_filename_from_tags(track, settings_manager)
