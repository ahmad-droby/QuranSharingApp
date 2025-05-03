# text_utils.py
# (No changes needed from the previous version)
import arabic_reshaper
from bidi.algorithm import get_display

def prepare_arabic_text(text: str) -> str:
    """Reshapes and applies bidi algorithm for correct Arabic display."""
    if not text:
        return ""
    reshaped_text = arabic_reshaper.reshape(text)
    bidi_text = get_display(reshaped_text)
    return bidi_text