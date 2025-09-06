import os
import mutagen
from mutagen.id3 import ID3

def clear_hidden_tags(tracks, tags_to_keep):
    """
    Clears any metadata from the files that is not in the tags_to_keep set.
    Preserves album art and lyrics.
    Returns (total number of tags cleared, list of error messages)
    """
    cleared_tags_count = 0
    errors = []
    if not tracks:
        return 0, []

    tags_to_keep_set = set(tags_to_keep)
    # Add keys for lyrics and album art to the keep set
    tags_to_keep_set.update(['lyrics', 'unsynced lyrics', 'USLT', 'APIC:', 'covr'])

    for track in tracks:
        try:
            # Check if file is writable
            if not os.access(track.path, os.W_OK):
                error_msg = f"File is read-only: {track.path}"
                errors.append(error_msg)
                continue

            # Use non-easy mode to access all tags including artwork
            audio = mutagen.File(track.path)
            if audio is None:
                print(f"Error: Could not load file for tag clearing: {track.path}")
                continue

            # Determine which tags to clear
            tags_to_clear = []
            if isinstance(audio.tags, ID3): # For MP3 files
                # Need to handle ID3 frames which are not simple key-value pairs
                current_tags = {frame.FrameID for frame in audio.tags.values()}
                # This is a simplification; mapping FrameIDs to easy keys is complex.
                # We will clear based on what we can easily identify.
                # A more robust solution would map all relevant FrameIDs to easy keys.
                pass # For now, we will rely on the easy interface for simplicity
            
            audio_easy = mutagen.File(track.path, easy=True)
            if audio_easy:
                      tags_to_clear = [tag for tag in audio_easy.keys() if tag not in tags_to_keep_set]
    
            if not tags_to_clear:
                continue

            for tag_key in tags_to_clear:
                del audio_easy[tag_key]
                cleared_tags_count += 1

            audio_easy.save()

            # Also update the in-memory track object to reflect the change
            for tag_key in tags_to_clear:
                if tag_key in track.tags:
                    del track.tags[tag_key]
                if tag_key in track.proposed_tags:
                    del track.proposed_tags[tag_key]

        except Exception as e:
            error_msg = f"Error clearing hidden tags for {track.path}: {e}"
            errors.append(error_msg)

    return cleared_tags_count, errors