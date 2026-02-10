"""
Technical specification patterns for BOQ description extraction.
Uses regex patterns with formatters for standardized output.
"""

import re
from typing import List, Tuple, Callable

# Spec patterns: (regex_pattern, formatter_function)
# Ordered by specificity - most specific patterns first
SPEC_PATTERNS: List[Tuple[str, Callable]] = [
    # ==========================================================================
    # ELECTRICAL SPECS - Dash-separated format (MCCB-3P-400A-36kA)
    # Must be first to match before generic patterns
    # ==========================================================================
    # Full MCCB/MCB/RCCB/ACB pattern with all specs
    (r'(?:MCCB|MCB|RCCB|ACB)[\-\s]*(\d+)\s*[Pp][\-\s]*(\d+)\s*[Aa][\-\s]*(\d+)\s*[Kk][Aa]',
     lambda m: f"{m.group(1)}P {m.group(2)}A {m.group(3)}kA"),

    # Poles with dash: 3P- or -3P
    (r'[\-](\d+)\s*[Pp](?:[\-\s]|$)', lambda m: f"{m.group(1)}P"),
    (r'(\d+)\s*[Pp][\-]', lambda m: f"{m.group(1)}P"),

    # Current with dash: -400A- or -400A (end)
    (r'[\-](\d+)\s*[Aa][\-]', lambda m: f"{m.group(1)}A"),
    (r'[\-](\d+)\s*[Aa](?:\s|$)', lambda m: f"{m.group(1)}A"),

    # Breaking capacity with dash: -36kA or -50kA
    (r'[\-](\d+)\s*[Kk][Aa]', lambda m: f"{m.group(1)}kA"),

    # ==========================================================================
    # CABLE SPECS - Cross-section with neutral conductor
    # Must be before simple cable patterns
    # ==========================================================================
    # Cable cross-section with neutral: 3x95+1x50mm2, 4x300+1x150mm2
    (r'(\d+)\s*[xX×]\s*(\d+(?:\.\d+)?)\s*\+\s*(\d+)\s*[xX×]\s*(\d+(?:\.\d+)?)\s*mm2?',
     lambda m: f"{m.group(1)}x{m.group(2)}+{m.group(3)}x{m.group(4)}mm2"),

    # ==========================================================================
    # DIMENSIONS - Diameter, Height, Length
    # ==========================================================================
    # Dimensions with prefix - DN, D, Φ
    (r'[Dd][Nn]\s*(\d+(?:\.\d+)?)', lambda m: f"DN{m.group(1)}"),  # DN100, DN 110
    (r'[Dd](\d+(?:\.\d+)?)\s*(?:mm)?(?!\d)', lambda m: f"D{m.group(1)}"),  # D110, D90mm
    (r'[Φφ∅Ø](\d+(?:\.\d+)?)', lambda m: f"D{m.group(1)}"),  # Φ110, φ90

    # Height/Length with units
    (r'[Hh]\s*[=:]\s*(\d+(?:\.\d+)?)\s*m(?:et|ét)?(?:er)?', lambda m: f"H={m.group(1)}m"),  # H=8m, H:8met
    (r'[Ll]\s*[=:]\s*(\d+(?:\.\d+)?)\s*m(?:et|ét)?(?:er)?', lambda m: f"L={m.group(1)}m"),  # L=6m
    (r'[Hh](\d+(?:\.\d+)?)\s*m(?:et|ét)?(?:er)?(?!\w)', lambda m: f"H={m.group(1)}m"),  # H8m
    (r'cao\s*(\d+(?:\.\d+)?)\s*m(?:et|ét)?(?:er)?', lambda m: f"H={m.group(1)}m"),  # cao 8m
    (r'dài\s*(\d+(?:\.\d+)?)\s*m(?:et|ét)?(?:er)?', lambda m: f"L={m.group(1)}m"),  # dài 6m

    # Electrical specs - Poles
    (r'(\d+)\s*[Pp](?:ole|ha|has)?(?:\s|$)', lambda m: f"{m.group(1)}P"),  # 3P, 3 poles, 3 pha

    # Electrical specs - Current (Ampere)
    (r'(\d+)\s*[Aa](?:mp|mpe|mps)?(?:\s|$|[,\-])', lambda m: f"{m.group(1)}A"),  # 400A, 400 Amp

    # Electrical specs - Breaking capacity (kA)
    (r'(\d+)\s*[Kk][Aa]', lambda m: f"{m.group(1)}kA"),  # 50kA, 50 kA

    # Electrical specs - Voltage (kV, V)
    (r'(\d+(?:\.\d+)?)\s*[Kk][Vv]', lambda m: f"{m.group(1)}kV"),  # 22kV, 0.4kV
    (r'(\d+)\s*[Vv](?:olt)?(?:\s|$|[,\-])', lambda m: f"{m.group(1)}V"),  # 500V, 220V

    # Dimensions - WxHxD format
    (r'(\d+)\s*[xX×]\s*(\d+)\s*[xX×]\s*(\d+)\s*(?:mm)?',
     lambda m: f"{m.group(1)}x{m.group(2)}x{m.group(3)}"),  # 600x400x200

    # Dimensions - WxH format
    (r'(\d+)\s*[xX×]\s*(\d+)\s*(?:mm)?(?!\d)',
     lambda m: f"{m.group(1)}x{m.group(2)}"),  # 600x600, 900x2200

    # Concrete grades
    (r'[Mm]\s*(\d{2,3})(?:\s|$|[,\-])', lambda m: f"M{m.group(1)}"),  # M200, M350
    (r'[Bb]\s*(\d{2})(?:\s|$|[,\-])', lambda m: f"B{m.group(1)}"),  # B25, B30

    # Rebar grades
    (r'CB\s*(\d{3})\s*[Vv]?', lambda m: f"CB{m.group(1)}"),  # CB300, CB400V

    # Pressure ratings
    (r'[Pp][Nn]\s*(\d+(?:\.\d+)?)', lambda m: f"PN{m.group(1)}"),  # PN10, PN16

    # SDR ratings (for HDPE pipes)
    (r'[Ss][Dd][Rr]\s*(\d+(?:\.\d+)?)', lambda m: f"SDR{m.group(1)}"),  # SDR11, SDR17

    # Cable cross-section - multi-core
    (r'(\d+)\s*[xX×]\s*(\d+(?:\.\d+)?)\s*mm2?',
     lambda m: f"{m.group(1)}x{m.group(2)}mm2"),  # 4x50mm2, 3x25mm2

    # Cable cross-section - single
    (r'(\d+(?:\.\d+)?)\s*mm2?(?:\s|$)',
     lambda m: f"{m.group(1)}mm2"),  # 50mm2, 25mm2

    # Thickness
    (r'dày\s*(\d+(?:\.\d+)?)\s*(?:mm)?', lambda m: f"Dày {m.group(1)}mm"),  # dày 18mm
    (r'd\s*[=:]\s*(\d+(?:\.\d+)?)\s*(?:mm)?', lambda m: f"d={m.group(1)}mm"),  # d=18mm

    # Form designation (for electrical panels)
    (r'[Ff]orm\s*(\d+[ABab]?)', lambda m: f"Form {m.group(1)}"),  # Form 3B, Form 4

    # IP rating
    (r'IP\s*(\d{2})', lambda m: f"IP{m.group(1)}"),  # IP65, IP54

    # R rating (for concrete - slump retention)
    (r'R\s*(\d+)', lambda m: f"R{m.group(1)}"),  # R7, R8

    # Stone size for concrete
    (r'đá\s*(\d+)\s*[xX×]\s*(\d+)', lambda m: f"Đá {m.group(1)}x{m.group(2)}"),  # đá 1x2, đá 2x4

    # Compaction ratio
    (r'[Kk]\s*(\d{2,3})(?:%)?', lambda m: f"K{m.group(1)}"),  # K95, K98

    # Road layer thickness
    (r'[Cc]\s*(\d{1,2})(?:\s|$)', lambda m: f"C{m.group(1)}"),  # C12, C19

    # Traffic sign codes
    (r'[Aa]\s*(\d{2,3})(?:\s|$)', lambda m: f"A{m.group(1)}"),  # A70 (triangle sign)
    (r'[Pp]\s*(\d{2,3})(?:\s|$)', lambda m: f"P{m.group(1)}"),  # P102 (prohibition sign)
    (r'[Rr]\s*(\d{2,3})(?:\s|$)', lambda m: f"R{m.group(1)}"),  # R301 (mandatory sign)
    (r'[Ww]\s*(\d{2,3})(?:\s|$)', lambda m: f"W{m.group(1)}"),  # W201 (warning sign)

    # Paint coats
    (r'(\d+)\s*[Ll]\s*[+\+]\s*(\d+)\s*[Pp]', lambda m: f"{m.group(1)}L+{m.group(2)}P"),  # 1L+2P

    # Line width (for road markings)
    (r'rộng\s*(\d+)\s*(?:mm|cm)?', lambda m: f"W={m.group(1)}mm"),  # rộng 150mm
]


def extract_specs(text: str) -> Tuple[List[str], str]:
    """
    Extract all technical specifications from text.
    Uses subtract-back algorithm: extracts specs and returns remaining text.

    Args:
        text: Input description text

    Returns:
        Tuple of (list of extracted specs, remaining text after extraction)
    """
    specs = []
    remaining = text
    extracted_positions = []

    for pattern, formatter in SPEC_PATTERNS:
        for match in re.finditer(pattern, remaining, re.IGNORECASE):
            # Check if this position overlaps with already extracted
            start, end = match.start(), match.end()
            overlaps = False
            for ext_start, ext_end in extracted_positions:
                if not (end <= ext_start or start >= ext_end):
                    overlaps = True
                    break

            if not overlaps:
                try:
                    formatted_spec = formatter(match)
                    if formatted_spec and formatted_spec not in specs:
                        specs.append(formatted_spec)
                        extracted_positions.append((start, end))
                except Exception:
                    pass

    # Remove extracted specs from remaining text
    # Sort positions in reverse order to preserve indices
    extracted_positions.sort(key=lambda x: x[0], reverse=True)
    for start, end in extracted_positions:
        remaining = remaining[:start] + ' ' + remaining[end:]

    # Clean up remaining text
    remaining = re.sub(r'\s+', ' ', remaining).strip()
    remaining = re.sub(r'^[\s,\-\.]+|[\s,\-\.]+$', '', remaining)

    return specs, remaining


def normalize_dimension(value: str, unit: str) -> str:
    """
    Convert dimension to standard mm format.

    Args:
        value: Numeric value as string
        unit: Unit of measurement (mm, cm, m)

    Returns:
        Standardized dimension string in mm
    """
    try:
        num = float(value)
        unit_lower = unit.lower().strip()

        if unit_lower in ['cm', 'centimeter', 'centimét']:
            return f"{int(num * 10)}mm"
        elif unit_lower in ['m', 'meter', 'mét', 'met']:
            return f"{int(num * 1000)}mm"
        elif unit_lower in ['mm', 'millimeter', 'milimét']:
            return f"{int(num)}mm"
        else:
            return f"{value}{unit}"
    except ValueError:
        return f"{value}{unit}"
