import re
from tools.filename_generators import generate_filename_from_tags
from .special_cleaner import normalize_apostrophes

def camel_case(tracks, settings_manager):
    """
    Applies camel case formatting to the 'Title' tag of the given tracks
    and regenerates the proposed filename.
    Spaces are preserved.
    """
    roman_pattern = re.compile(r'\b(II|III|IV|VII|VIII|IX|XI|XII|XIII|XIV|XVI|XVII|XVIII)\b', re.I)

    def roman_replacer(m):
        roman_matches.append(m.group(0))
        return f"roman{len(roman_matches)-1}"

    if not tracks:
        return

    for track in tracks:
        roman_matches = []  # Reset for each track
        title = getattr(track, 'clean_title', '') or track.proposed_tags.get('title', track.tags.get('title', ''))
        # Normalize apostrophes in the title
        title = normalize_apostrophes(title)
        if title:
            # Preserve Roman numerals by replacing with lowercase placeholders
            title_with_placeholders = roman_pattern.sub(roman_replacer, title)

            # Capitalize the first letter of each word, including inside parentheses
            # Include both straight and smart quotes in the regex to handle Unicode apostrophes
            camel_cased_title = re.sub(r"\b[\w''\u2019]+", lambda m: m.group(0) if m.group(0).startswith("roman") else m.group(0).capitalize(), title_with_placeholders.lower())

            # Restore Roman numerals in uppercase
            for i, roman in enumerate(roman_matches):
                camel_cased_title = camel_cased_title.replace(f"roman{i}", roman.upper())

            track.proposed_tags['title'] = camel_cased_title
            # Also update clean_title to refresh the new name
            track.clean_title = camel_cased_title

            # Regenerate the proposed filename to reflect the title change
            if not track.is_manual_rename:
                generate_filename_from_tags(track, settings_manager)