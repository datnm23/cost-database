"""
Vietnamese text normalization for pattern matching.

Strips Vietnamese diacritics for matching purposes while preserving
original text for output. This allows matching patterns like
"ván khuôn" and "van khuon" with a single pattern entry.
"""
import re
import unicodedata


# Vietnamese diacritics to ASCII mapping
_VIET_MAP = str.maketrans({
    'à': 'a', 'á': 'a', 'ả': 'a', 'ã': 'a', 'ạ': 'a',
    'ă': 'a', 'ằ': 'a', 'ắ': 'a', 'ẳ': 'a', 'ẵ': 'a', 'ặ': 'a',
    'â': 'a', 'ầ': 'a', 'ấ': 'a', 'ẩ': 'a', 'ẫ': 'a', 'ậ': 'a',
    'è': 'e', 'é': 'e', 'ẻ': 'e', 'ẽ': 'e', 'ẹ': 'e',
    'ê': 'e', 'ề': 'e', 'ế': 'e', 'ể': 'e', 'ễ': 'e', 'ệ': 'e',
    'ì': 'i', 'í': 'i', 'ỉ': 'i', 'ĩ': 'i', 'ị': 'i',
    'ò': 'o', 'ó': 'o', 'ỏ': 'o', 'õ': 'o', 'ọ': 'o',
    'ô': 'o', 'ồ': 'o', 'ố': 'o', 'ổ': 'o', 'ỗ': 'o', 'ộ': 'o',
    'ơ': 'o', 'ờ': 'o', 'ớ': 'o', 'ở': 'o', 'ỡ': 'o', 'ợ': 'o',
    'ù': 'u', 'ú': 'u', 'ủ': 'u', 'ũ': 'u', 'ụ': 'u',
    'ư': 'u', 'ừ': 'u', 'ứ': 'u', 'ử': 'u', 'ữ': 'u', 'ự': 'u',
    'ỳ': 'y', 'ý': 'y', 'ỷ': 'y', 'ỹ': 'y', 'ỵ': 'y',
    'đ': 'd',
    # Uppercase
    'À': 'A', 'Á': 'A', 'Ả': 'A', 'Ã': 'A', 'Ạ': 'A',
    'Ă': 'A', 'Ằ': 'A', 'Ắ': 'A', 'Ẳ': 'A', 'Ẵ': 'A', 'Ặ': 'A',
    'Â': 'A', 'Ầ': 'A', 'Ấ': 'A', 'Ẩ': 'A', 'Ẫ': 'A', 'Ậ': 'A',
    'È': 'E', 'É': 'E', 'Ẻ': 'E', 'Ẽ': 'E', 'Ẹ': 'E',
    'Ê': 'E', 'Ề': 'E', 'Ế': 'E', 'Ể': 'E', 'Ễ': 'E', 'Ệ': 'E',
    'Ì': 'I', 'Í': 'I', 'Ỉ': 'I', 'Ĩ': 'I', 'Ị': 'I',
    'Ò': 'O', 'Ó': 'O', 'Ỏ': 'O', 'Õ': 'O', 'Ọ': 'O',
    'Ô': 'O', 'Ồ': 'O', 'Ố': 'O', 'Ổ': 'O', 'Ỗ': 'O', 'Ộ': 'O',
    'Ơ': 'O', 'Ờ': 'O', 'Ớ': 'O', 'Ở': 'O', 'Ỡ': 'O', 'Ợ': 'O',
    'Ù': 'U', 'Ú': 'U', 'Ủ': 'U', 'Ũ': 'U', 'Ụ': 'U',
    'Ư': 'U', 'Ừ': 'U', 'Ứ': 'U', 'Ử': 'U', 'Ữ': 'U', 'Ự': 'U',
    'Ỳ': 'Y', 'Ý': 'Y', 'Ỷ': 'Y', 'Ỹ': 'Y', 'Ỵ': 'Y',
    'Đ': 'D',
})

# Threshold for short patterns that need word-boundary matching
# Patterns <= this length will use word boundary matching to avoid
# false positives like "op" matching inside "lop"
_SHORT_PATTERN_THRESHOLD = 4

# Pre-compiled word boundary regex cache
_WORD_BOUNDARY_CACHE = {}


def normalize_vietnamese(text: str) -> str:
    """
    Strip Vietnamese diacritics for matching purposes.

    Converts Vietnamese characters to their ASCII equivalents:
    - ắ, ằ, ẳ, ẵ, ặ, ă → a
    - đ → d
    - etc.

    Args:
        text: Vietnamese text

    Returns:
        ASCII-normalized text (lowercase)
    """
    return text.lower().translate(_VIET_MAP)


def _is_word_boundary_match(text: str, keyword: str) -> bool:
    """
    Check if keyword appears in text at word boundaries.

    Uses word-boundary regex matching to prevent false positives like:
    - "op" matching inside "lop" (ốp vs lớp)
    - "cong tron" matching inside "cong trong" (cống tròn vs công trồng)

    Args:
        text: Normalized text to search in
        keyword: Normalized keyword to find

    Returns:
        True if keyword found with word boundary matching
    """
    if keyword not in _WORD_BOUNDARY_CACHE:
        # Use word boundary regex: (?<![a-z0-9]) pattern (?![a-z0-9])
        # Include digits to prevent "cat" matching inside "cat6"
        #
        # Special case: if keyword ends with "space + single letter" (e.g., "dam chat k"),
        # the trailing boundary allows digits, because such patterns are prefix-markers
        # in Vietnamese BOQ (e.g., "đầm chặt K95", "bê tông M200")
        if re.match(r'.+ [a-z]$', keyword):
            trailing = r'(?![a-z])'
        else:
            trailing = r'(?![a-z0-9])'
        _WORD_BOUNDARY_CACHE[keyword] = re.compile(
            r'(?<![a-z0-9])' + re.escape(keyword) + trailing
        )

    return bool(_WORD_BOUNDARY_CACHE[keyword].search(text))


def build_normalized_dict(pattern_dict: dict) -> dict:
    """
    Build a lookup from a pattern dictionary where keys are
    already in normalized (ASCII) form.

    Deduplicates entries where both Vietnamese and non-Vietnamese
    forms map to the same object name.

    Args:
        pattern_dict: Original pattern dict with Vietnamese keys

    Returns:
        New dict with only normalized (ASCII) keys, preserving
        longest-match-first ordering
    """
    normalized = {}
    for keyword, obj_name in pattern_dict.items():
        norm_key = normalize_vietnamese(keyword)
        # Keep the first (longest) entry for each normalized key
        if norm_key not in normalized:
            normalized[norm_key] = obj_name
    return normalized
