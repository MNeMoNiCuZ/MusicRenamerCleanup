from tools.filename_generators import generate_filename_from_tags
from tools.special_cleaner import extract_suffixes, normalize_apostrophes

def find_replace_in_title(tracks, find_text, replace_text, settings_manager):
    """
    Performs a find and replace operation on the displayed title (title + suffixes)
    of the given tracks and regenerates the proposed filename.
    """
    if not tracks or not find_text:
        return

    for track in tracks:
        # 1. Get the full displayed title
        clean_title = track.proposed_tags.get('title', track.tags.get('title', ''))
        # Normalize apostrophes in the title
        clean_title = normalize_apostrophes(clean_title)
        suffixes_str = "".join(track.suffixes)
        displayed_title = f"{clean_title}{suffixes_str}"

        # 2. Perform the replacement
        if find_text in displayed_title:
            new_displayed_title = displayed_title.replace(find_text, replace_text)

            # 3. Re-extract suffixes from the modified string
            artist = track.proposed_tags.get('artist', track.tags.get('artist', ''))
            album = track.proposed_tags.get('album', track.tags.get('album', ''))
            new_clean_title, new_suffixes = extract_suffixes(new_displayed_title, artist)

            # 4. Update the track object
            track.proposed_tags['title'] = new_clean_title
            track.suffixes = new_suffixes
            
            # Regenerate the proposed filename to reflect the changes
            if not track.is_manual_rename:
                generate_filename_from_tags(track, settings_manager)