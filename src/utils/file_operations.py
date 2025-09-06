import os
import mutagen
import mutagen.id3

def save_track_changes(track):
    """
    Saves the proposed changes to a track's tags and filename.
    Returns a tuple: (bool: success, str: error_message or None).
    """
    try:
        # Check if file is writable
        if not os.access(track.path, os.W_OK):
            return False, f"File is read-only: {track.path}"

        # --- 1. Save Tags ---
        if track.proposed_tags:
            # If the title was changed, reconstruct it with suffixes before saving.
            if 'title' in track.proposed_tags:
                # The proposed title is the "clean" one, without suffixes.
                clean_title = track.proposed_tags.get('title', track.clean_title)
                full_title = f"{clean_title}{''.join(track.suffixes)}"
                # Update the proposed tags dict so it's saved and merged correctly.
                track.proposed_tags['title'] = full_title

            audio = mutagen.File(track.path, easy=True)
            if audio is None:
                return False, f"Could not load file for tag writing: {track.path}"
            
            tags_to_delete = []
            for tag_name, value in track.proposed_tags.items():
                tag_key = tag_name.lower().replace(' ', '')
                if value:  # If there's a value, set it
                    audio[tag_key] = value
                elif tag_key in audio:  # If the value is empty, delete the tag
                    del audio[tag_key]
                    tags_to_delete.append(tag_key)
            audio.save()

            # For FLAC files, save a fresh non-easy instance to ensure all changes are written
            if track.path.lower().endswith('.flac'):
                fresh_audio = mutagen.File(track.path)
                fresh_audio.save()
            
            # Merge proposed tags into the main tags dictionary
            for tag_key, value in track.proposed_tags.items():
                if value:
                    track.tags[tag_key] = value
                elif tag_key in track.tags:
                    del track.tags[tag_key] # Ensure cleared tags are removed from the main dict

            # Clear proposed tags after they've been merged
            track.proposed_tags.clear()

        # --- 2. Rename File ---
        if track.proposed_filename and track.proposed_filename != track.filename:
            new_path = os.path.join(os.path.dirname(track.path), track.proposed_filename)
            
            # On case-insensitive filesystems (like Windows), os.path.exists can be tricky.
            # If the only difference is case, we should allow the rename.
            if os.path.exists(new_path) and track.path.lower() != new_path.lower():
                return False, f"Cannot rename, file already exists: {new_path}"
            
            os.rename(track.path, new_path)
            track.path = new_path
            track.filename = track.proposed_filename
            # Clear proposed_filename after saving to indicate changes are applied
            track.proposed_filename = ""

        return True, None

    except Exception as e:
        return False, f"Error saving changes for {track.path}: {e}"


