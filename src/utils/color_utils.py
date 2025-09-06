from PyQt6.QtGui import QColor

def get_contrasting_text_color(background_color):
    """
    Determines if black or white text should be used based on the background color's luminance.
    Args:
        background_color (QColor): The background color.
    Returns:
        QColor: A contrasting color (black or white) for the text.
    """
    # Using the luminance formula (Y = 0.299*R + 0.587*G + 0.114*B)
    # A threshold of 128 is common.
    luminance = (0.299 * background_color.red() + 0.587 * background_color.green() + 0.114 * background_color.blue())
    return QColor('#000000') if luminance > 128 else QColor('#FFFFFF')
