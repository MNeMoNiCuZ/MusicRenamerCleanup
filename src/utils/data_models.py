from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class Track:
    """Data class representing a single audio track."""
    path: str
    filename: str
    clean_title: str
    tags: Dict[str, Any] = field(default_factory=dict)
    proposed_tags: Dict[str, Any] = field(default_factory=dict)
    proposed_filename: str = ""
    is_manual_rename: bool = False
    suffixes: List[str] = field(default_factory=list)
    has_error: bool = False
    has_duplicate: bool = False

@dataclass
class Album:
    """Data class representing an album, containing tracks."""
    name: str
    path: str
    tracks: List[Track] = field(default_factory=list)

@dataclass
class Artist:
    """Data class representing an artist, containing albums."""
    name: str
    path: str
    albums: List[Album] = field(default_factory=list)
