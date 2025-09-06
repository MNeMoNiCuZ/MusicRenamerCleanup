# MusicRenamerCleanup

MusicRenamerCleanup is a niche utility for cleaning and renaming music files based on a specific folder structure. It's designed to streamline the process of organizing a music library by enforcing a consistent naming and tagging convention.

**Disclaimer:** This tool is currently under construction and is tailored to a very specific workflow. Some features may not work perfectly, and it may not be useful unless you follow the same organizational structure.

## Features

*   **Folder-Based Organization**: Strictly enforces an `Artist/Album/Track.mp3` structure.
*   **Automated Tag Correction**: Proposes tag changes (Artist, Album, Title) based on the folder structure.
*   **Advanced Title Cleaning**: Automatically extracts suffixes like `(feat. Artist)`, `(Remix)`, etc., into a standardized format (e.g., `[Ft. Artist]`, `[Artist Remix]`).
*   **Batch Tag Editing**: Edit tags for multiple files at once.
*   **Customizable Naming**: Generate new filenames from tags using a configurable format.
*   **Metadata Support**: Reads and writes metadata using `mutagen`.
*   **Dark-Themed UI**: A clean, dark interface for comfortable use.

## The Cleanup Structure

The primary purpose of this tool is to enforce a clean and consistent library structure. It assumes your music is organized as follows:

```
/MusicRoot/
├───Artist Name/
│   ├───Album Name 1/
│   │   ├───01. Track Title.mp3
│   │   └───02. Another Track [Ft. Guest].mp3
│   └───Album Name 2/
│       └───01. Some Song (Official Video).mp3
```

The tool will then:
1.  Assume the folder names for **Artist** and **Album** are the source of truth.
2.  Propose to update the `Artist` and `Album` tags in the files to match the folder names.
3.  Clean the `Title` tag by removing the artist name and extracting common suffixes. For example, a file named `Artist - Title (feat. Other Artist) (Remix)` will have its title cleaned to `Title` and the suffixes `[Ft. Other Artist]` and `[Remix]` will be generated.

The final generated filename will look like this: `Artist - Title [Ft. Other Artist] [Remix].mp3`.

## Requirements

*   Python 3.12
*   PyQt6
*   mutagen

## Setup

1.  **Create Virtual Environment**: Run the `venv_create.bat` script to automatically create a Python virtual environment. It will also offer to install the required packages.
2.  **Install Dependencies**: If you didn't install the packages in the previous step, activate the environment (`venv\Scripts\activate.bat`) and run:
    ```
    pip install -r requirements.txt
    ```

## How to Use

1.  **Run Application**: Execute `launch_app_venv.bat` to start the application within its virtual environment.
2.  **Load Folder**: Use the "Load Folder" button to select the root directory of your music library.
3.  **Select and Clean**: Navigate to an Artist or Album in the left panel. The files will appear in the center panel with proposed changes.
4.  **Use Tools**: Use the tools on the right panel to apply changes like "Name to Title" or "Camel Case".
5.  **Save**: Click the "Save" button to write the new tags and rename the files on disk.
