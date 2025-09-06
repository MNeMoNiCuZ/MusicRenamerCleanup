# This script updates the metadata of music files in the same directory.
# It extracts the Artist and Title from the filename, assuming the format "Artist - Title".
# It preserves the existing Album tag and any album art.
# All other metadata tags are removed.

import os
import mutagen
from mutagen.id3 import ID3, TIT2, TPE1, TALB, APIC
from mutagen.flac import Picture

# Supported file extensions
SUPPORTED_EXTENSIONS = ['.mp3', '.flac', '.m4a', '.ogg', '.opus']

def update_metadata(file_path):
    """
    Updates the metadata of a music file based on its filename,
    preserving the album tag and album art.
    """
    try:
        audio = mutagen.File(file_path)
        if audio is None:
            print(f"Could not load file: {file_path}")
            return

        filename = os.path.splitext(os.path.basename(file_path))[0]

        if " - " in filename:
            artist, title = filename.split(" - ", 1)
        else:
            print(f"Could not parse artist and title from filename: {filename}")
            return

        # Store album, artwork and lyrics based on file type
        album = None
        artwork = None
        lyrics = None
        if isinstance(audio.tags, ID3): # MP3
            if 'TALB' in audio.tags:
                album = audio.tags['TALB'].text[0]
            if 'APIC:' in audio.tags:
                artwork = audio.tags['APIC:']
            if 'USLT::XXX' in audio.tags:
                lyrics = audio.tags['USLT::XXX']
        else: # FLAC, M4A, etc.
            if 'album' in audio.tags:
                album = audio.tags['album'][0]
            if 'metadata_block_picture' in audio.tags:
                 artwork = audio.tags['metadata_block_picture']
            if 'lyrics' in audio.tags:
                lyrics = audio.tags['lyrics'][0]


        # Clear all tags
        audio.delete()
        audio.save() # For some formats, tags need to be saved before adding new ones

        # Re-load the file to add new tags
        audio = mutagen.File(file_path)

        # Restore essential tags
        if isinstance(audio.tags, ID3): # MP3
            audio.tags.add(TPE1(encoding=3, text=artist))
            audio.tags.add(TIT2(encoding=3, text=title))
            if album:
                audio.tags.add(TALB(encoding=3, text=album))
            if artwork:
                audio.tags.add(artwork)
            if lyrics:
                audio.tags.add(lyrics)
        else: # FLAC, M4A, etc.
            audio.tags['artist'] = artist
            audio.tags['title'] = title
            if album:
                audio.tags['album'] = album
            if artwork:
                 # For FLAC, artwork is a list of Picture objects
                if isinstance(artwork, list):
                    for art in artwork:
                        audio.add_picture(art)
                else: # For other vorbis comments
                    audio['metadata_block_picture'] = artwork
            if lyrics:
                audio.tags['lyrics'] = lyrics


        audio.save()
        print(f"Updated metadata for: {filename}")

    except Exception as e:
        print(f"Error processing file {file_path}: {e}")

def main():
    """
    Processes all music files in the current directory.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    for filename in os.listdir(script_dir):
        if any(filename.lower().endswith(ext) for ext in SUPPORTED_EXTENSIONS):
            file_path = os.path.join(script_dir, filename)
            update_metadata(file_path)

if __name__ == "__main__":
    main()