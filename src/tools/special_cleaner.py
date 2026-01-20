import re
from typing import List, Tuple

# This list contains words that should be removed from any captured suffix.
# The matching is case-insensitive and looks for whole words.

# Don't forget to add the comma, after each entry, including the final ones.
# Defaults are now in settings / user_defaults.py

# A simple regex to capture any content within parentheses or brackets.
SUFFIX_CONTENT_REGEX = re.compile(r'[\(\[](?P<content>[^)\]]+)[\)\]]')

# Regexes to find specific keywords within the captured content and treat them as suffixes
FT_REGEX = re.compile(r'(feat|ft|featuring)\.?(.*)', re.I)
REMIX_REGEX = re.compile(r'(.*)(remix|r3m1x|rmx)', re.I)

# Normalize apostrophes to standard format
def normalize_apostrophes(text: str) -> str:
    """
    Replace Unicode apostrophe (\u00B4) with standard apostrophe (')
    before any other processing.
    """
    return text.replace('\u00B4', "'")

def _clean_suffix_content(content: str, settings_manager=None) -> str:
    """Removes banned words from suffix content."""
    content = content.strip()
    
    words_to_remove = []
    if settings_manager:
        words_to_remove = settings_manager.get('general', {}).get('words_to_remove', [])
    
    # Fallback/Safety if settings failing or empty, though ideally shouldn't happen if initialized correctly
    if not words_to_remove:
        # Minimal fallback could go here, or just do nothing
        pass

    for banned_word in words_to_remove:
        pattern = re.compile(r'\b' + re.escape(banned_word) + r'\b', re.IGNORECASE)
        content = pattern.sub('', content)
    return re.sub(r'\s+', ' ', content).strip()

def _format_artist_names(artists_str: str) -> str:
    """Formats a string of artist names, handling multiple separators."""
    artists_str = re.sub(r'\s*&\s*|\s+and\s+', ', ', artists_str, flags=re.I)
    artists = [' '.join(word.title() for word in artist.strip().split())
               for artist in artists_str.split(',') if artist.strip()]
    return ', '.join(artists)

def extract_suffixes(title: str, artist: str = "", settings_manager=None) -> Tuple[str, List[str]]:
    """
    Extracts special suffixes from a title string by first finding any text in brackets
    or parentheses, cleaning it of banned words, and then checking for keywords.
    """
    suffixes = []
    parts_to_remove = []
    
    tag_mappings = {}
    if settings_manager:
        tag_mappings = settings_manager.get('general', {}).get('tag_mappings', {})

    for match in SUFFIX_CONTENT_REGEX.finditer(title):
        original_match_text = match.group(0)
        content = match.group('content')

        # First, clean the content of any banned words.
        cleaned_content = _clean_suffix_content(content, settings_manager)

        # Store found tags to avoid creating a generic one if a specific one is found.
        found_tags = []

        # Check for specific keywords in the cleaned content.
        ft_match = FT_REGEX.search(cleaned_content)
        if ft_match:
            artists = _format_artist_names(ft_match.group(2).strip())
            if artists:
                found_tags.append(f"[Ft. {artists}]")

        remix_match = REMIX_REGEX.search(cleaned_content)
        if remix_match:
            remixer = re.sub(r'\b\w', lambda m: m.group(0).upper(), remix_match.group(1).strip())
            if remixer:
                found_tags.append(f"[{remixer} Remix]")
            else:
                found_tags.append("[Remix]")

        # Dynamic Tag Mappings using Settings
        for pattern_str, result_tag in tag_mappings.items():
            # Create regex from the pattern string user provided
            # We assume user provides regex-ready string but we should probably compile gracefully
            try:
                # Assuming case-insensitive matching for user convenience
                custom_regex = re.compile(pattern_str, re.IGNORECASE)
                if custom_regex.search(cleaned_content):
                    found_tags.append(result_tag)
            except re.error:
                # Should log this or handle it, for now just skip invalid regexes
                pass

        # If specific tags were found, add them and mark the part for full removal.
        if found_tags:
            suffixes.extend(found_tags)
            parts_to_remove.append(original_match_text)
        # Otherwise, check cleaned content
        else:
            if cleaned_content.strip():
                # Keep the part (don't remove if it has content after banning)
                pass
            else:
                # It's all banned words, so remove the whole part
                parts_to_remove.append(original_match_text)

    # Remove the original suffix parts from the title.
    clean_title = title
    for part in parts_to_remove:
        clean_title = clean_title.replace(part, '')

    # Remove artist and album from the title
    if artist:
        # Create a regex to replace the artist name (case-insensitive)
        # We use re.escape to handle any special characters in the artist name
        clean_title = re.sub(re.escape(artist), '', clean_title, flags=re.IGNORECASE)

    # Clean up empty brackets/parentheses that might remain
    clean_title = re.sub(r'\(\s*\)|\[\s*\]', '', clean_title)

    # Final cleanup of extra whitespace and remove duplicate suffixes.
    clean_title = re.sub(r'\s+', ' ', clean_title).strip()
    clean_title = clean_title.strip(' -')
    unique_suffixes = sorted(list(dict.fromkeys(suffixes)), key=str.lower)

    return clean_title, unique_suffixes