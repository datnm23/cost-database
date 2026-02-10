"""
Base extractor class for context-aware extraction.
"""
import re
from abc import ABC, abstractmethod
from typing import Dict, Optional, List


class BaseExtractor(ABC):
    """Base class for context-aware extractors."""

    @abstractmethod
    def extract(self, text: str) -> Dict:
        """
        Extract specs from text.

        Args:
            text: Input description text

        Returns:
            Dict with extracted specifications
        """
        pass

    def _extract_dimensions(self, text: str) -> Optional[str]:
        """
        Extract dimensions in WxH or WxHxL format.

        Args:
            text: Input text

        Returns:
            Dimension string or None
        """
        # Pattern for 3D dimensions (e.g., 1000x500x300)
        match_3d = re.search(
            r'(\d+)\s*[xX×]\s*(\d+)\s*[xX×]\s*(\d+)',
            text
        )
        if match_3d:
            return f"{match_3d.group(1)}x{match_3d.group(2)}x{match_3d.group(3)}"

        # Pattern for 2D dimensions (e.g., 600x600)
        match_2d = re.search(
            r'(\d+)\s*[xX×]\s*(\d+)',
            text
        )
        if match_2d:
            return f"{match_2d.group(1)}x{match_2d.group(2)}"

        return None

    def _extract_thickness(self, text: str) -> Optional[str]:
        """
        Extract thickness specification.

        Args:
            text: Input text

        Returns:
            Thickness string or None
        """
        text_lower = text.lower()

        # Pattern: dày Xcm or dày Xmm
        match = re.search(r'dày\s*(\d+(?:\.\d+)?)\s*(cm|mm)?', text_lower)
        if match:
            value = match.group(1)
            unit = match.group(2) or 'mm'
            return f"dày {value}{unit}"

        return None

    def _extract_height(self, text: str) -> Optional[str]:
        """
        Extract height specification.

        Args:
            text: Input text

        Returns:
            Height string or None
        """
        text_lower = text.lower()

        # Pattern: H=Xm or H Xm or cao Xm
        patterns = [
            r'[Hh]\s*[=:]?\s*(\d+(?:\.\d+)?)\s*m',
            r'cao\s+(\d+(?:\.\d+)?)\s*m',
            r'chiều\s+cao\s+(\d+(?:\.\d+)?)\s*m',
        ]

        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                return f"H={match.group(1)}m"

        return None

    def _extract_grade(self, text: str) -> Optional[str]:
        """
        Extract material grade (M200, CB300, etc.).

        Args:
            text: Input text

        Returns:
            Grade string or None
        """
        text_lower = text.lower()

        # Concrete grade (M100, M200, M350, etc.)
        match = re.search(r'\b[Mm](\d{2,3})\b', text)
        if match:
            return f"M{match.group(1)}"

        # Rebar grade (CB300, CB400V, etc.)
        match = re.search(r'\bCB(\d{3})([VvWwTt])?\b', text, re.IGNORECASE)
        if match:
            suffix = match.group(2).upper() if match.group(2) else ''
            return f"CB{match.group(1)}{suffix}"

        return None

    def _normalize_unit(self, value: str, from_unit: str, to_unit: str = 'mm') -> str:
        """
        Convert unit to standard unit.

        Args:
            value: Numeric value as string
            from_unit: Source unit (cm, m, mm)
            to_unit: Target unit (default: mm)

        Returns:
            Converted value with unit
        """
        try:
            num = float(value.replace(',', '.'))
            from_unit_lower = from_unit.lower()

            if to_unit == 'mm':
                if from_unit_lower == 'cm':
                    return f"{int(num * 10)}mm"
                elif from_unit_lower == 'm':
                    return f"{int(num * 1000)}mm"
                else:
                    return f"{int(num)}mm"
            return f"{value}{from_unit}"
        except ValueError:
            return f"{value}{from_unit}"
