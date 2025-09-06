import re
from typing import List, Tuple

# This list contains words that should be removed from any captured suffix.
# The matching is case-insensitive and looks for whole words.

# Don't forget to add the comma, after each entry, including the final ones.
BANNED_SUFFIX_WORDS = [
    # General
    "Version",
    "Ver.",
    "Bonus Track",
    "Free Download",
    "Remaster",

    # Video Types
    "Music Video",
    "Lyric Video",
    "Lyrics Video",
    "Dynamic Art Video",
    "Visualizer",
    "Art Track",
    "Officiell Video",
    "Official Visual",
    
    # Audio Types
    "Official Audio",
    "Official Music",
    "Radio Edit",

    # Quality
    "HD",
    "HQ",
    "4K",

    # Catch-alls & Typos
    "Official",
    "Offical", # Common typo
    "Audio",
    "Video",
]

# A simple regex to capture any content within parentheses or brackets.
SUFFIX_CONTENT_REGEX = re.compile(r'[\(\[](?P<content>[^)\]]+)[\)\]]')

# Regexes to find specific keywords within the captured content and treat them as suffixes
FT_REGEX = re.compile(r'(feat|ft|featuring)\.?(.*)', re.I)
REMIX_REGEX = re.compile(r'(.*)(remix|r3m1x|rmx)', re.I)
ACOUSTIC_REGEX = re.compile(r'acoustic', re.I)
INSTRUMENTAL_REGEX = re.compile(r'instrumental', re.I)
PIANO_REGEX = re.compile(r'piano', re.I)
LIVE_REGEX = re.compile(r'live', re.I)
VOCAL_COVER_REGEX = re.compile(r'vocal cover', re.I)
DEMO_REGEX = re.compile(r'demo', re.I)
ALTERNATIVE_VERSION_REGEX = re.compile(r'alternative version', re.I)
RADIO_VERSION_REGEX = re.compile(r'radio version', re.I)
RADIO_EDIT_REGEX = re.compile(r'radio edit', re.I)

# Normalize apostrophes to standard format
def normalize_apostrophes(text: str) -> str:
    """
    Replace Unicode apostrophe (\u00B4) with standard apostrophe (')
    before any other processing.
    """
    return text.replace('\u00B4', "'")

def _clean_suffix_content(content: str) -> str:
    """Removes banned words from suffix content."""
    content = content.strip()
    for banned_word in BANNED_SUFFIX_WORDS:
        pattern = re.compile(r'\b' + re.escape(banned_word) + r'\b', re.IGNORECASE)
        content = pattern.sub('', content)
    return re.sub(r'\s+', ' ', content).strip()

def _format_artist_names(artists_str: str) -> str:
    """Formats a string of artist names, handling multiple separators."""
    artists_str = re.sub(r'\s*&\s*|\s+and\s+', ', ', artists_str, flags=re.I)
    artists = [' '.join(word.title() for word in artist.strip().split())
               for artist in artists_str.split(',') if artist.strip()]
    return ', '.join(artists)

def extract_suffixes(title: str, artist: str = "") -> Tuple[str, List[str]]:
    """
    Extracts special suffixes from a title string by first finding any text in brackets
    or parentheses, cleaning it of banned words, and then checking for keywords.
    """
    suffixes = []
    parts_to_remove = []

    for match in SUFFIX_CONTENT_REGEX.finditer(title):
        original_match_text = match.group(0)
        content = match.group('content')

        # First, clean the content of any banned words.
        cleaned_content = _clean_suffix_content(content)

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

        if ACOUSTIC_REGEX.search(cleaned_content):
            found_tags.append("[Acoustic]")

        if INSTRUMENTAL_REGEX.search(cleaned_content):
            found_tags.append("[Instrumental]")

        if PIANO_REGEX.search(cleaned_content):
            found_tags.append("[Piano]")

        if LIVE_REGEX.search(cleaned_content):
            found_tags.append("[Live]")

        if VOCAL_COVER_REGEX.search(cleaned_content):
            found_tags.append("[Vocal Cover]")

        if DEMO_REGEX.search(cleaned_content):
            found_tags.append("[Demo]")

        if ALTERNATIVE_VERSION_REGEX.search(cleaned_content):
            found_tags.append("[Alternative Remix]")

        if RADIO_VERSION_REGEX.search(cleaned_content):
            found_tags.append("[Radio Remix]")

        if RADIO_EDIT_REGEX.search(cleaned_content):
            found_tags.append("[Radio Remix]")

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
    #if artist:
    #    clean_title = re.sub(re.escape(artist), '', clean_title, flags=re.IGNORECASE)

    # Final cleanup of extra whitespace and remove duplicate suffixes.
    clean_title = re.sub(r'\s+', ' ', clean_title).strip()
    clean_title = clean_title.strip(' -')
    unique_suffixes = sorted(list(dict.fromkeys(suffixes)), key=str.lower)

    return clean_title, unique_suffixes