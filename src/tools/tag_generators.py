import os

def generate_tags_from_filename(track):
    """
    Generates proposed tags for a track based on its filename.
    Prioritizes proposed_filename if it exists, otherwise uses the original filename.
    Simple implementation assuming 'Artist - Title' format.
    """
    # Use the proposed filename if it exists and is different, otherwise use the original
    source_filename = track.proposed_filename if track.proposed_filename and track.proposed_filename != track.filename else track.filename
    #print(f"[DEBUG] generate_tags_from_filename called for track: {track.filename}, using source: {source_filename}")

    filename_no_ext, _ = os.path.splitext(source_filename)
    parts = filename_no_ext.split(' - ', 1)
    
    proposed_tags = {}
    if len(parts) == 2:
        proposed_tags['artist'] = parts[0].strip()
        proposed_tags['title'] = parts[1].strip()
    else:
        # If pattern doesn't match, propose the filename as the title
        proposed_tags['title'] = filename_no_ext.strip()

    track.proposed_tags.update(proposed_tags)
    # Since we've successfully generated tags from the name, it's no longer a "manual" override
    track.is_manual_rename = False
    #print(f"[DEBUG] Proposed tags for {track.filename}: {track.proposed_tags}")
    return track
