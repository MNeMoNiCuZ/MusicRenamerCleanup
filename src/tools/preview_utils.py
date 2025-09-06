def clear_preview(track):
    """
    Clears all proposed changes for a track.
    """
    track.proposed_tags.clear()
    track.proposed_filename = ""
    track.is_manual_rename = False
    return track
