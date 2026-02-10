"""
Context-aware extractor for electrical devices (MCCB, MCB, RCCB, ACB).

Extracts specs specific to electrical circuit breakers including:
- Poles (3P, 4P)
- Current rating (amps - 400A, 100A)
- Breaking capacity (kA - 36kA, 50kA)
"""
import re
from typing import Dict
from .base_extractor import BaseExtractor


class ElectricalExtractor(BaseExtractor):
    """Extract specs specific to electrical circuit breakers."""

    def extract(self, text: str) -> Dict:
        """
        Extract electrical device specs.

        Args:
            text: Input description (e.g., "MCCB-3P-400A-36kA")

        Returns:
            Dict with keys: poles, amps, breaking_capacity
        """
        specs = {}

        # Preprocess: replace dashes with spaces for easier extraction
        # but preserve the original for backup matching
        text_normalized = re.sub(r'[-]', ' ', text)

        # Extract poles (3P, 4P, 2P, 1P)
        poles_match = re.search(r'(\d+)\s*[Pp](?:ole|oles|ha|has)?(?:\s|$|[,-])', text_normalized)
        if poles_match:
            specs['poles'] = f"{poles_match.group(1)}P"

        # Extract current rating (amperage)
        # First try with A suffix: 400A, 160A
        amps_match = re.search(r'(\d+)\s*[Aa](?:mp|mps)?(?:\s|$|[,-])', text_normalized)
        if amps_match:
            specs['amps'] = f"{amps_match.group(1)}A"
        else:
            # Try without A suffix: pattern like "3P 160 36kA" (number between poles and kA)
            # Look for a number that's not poles and not kA
            no_a_match = re.search(r'(\d+)\s*[Pp]\s+(\d{2,4})(?:\s|$)', text_normalized)
            if no_a_match:
                amps_val = no_a_match.group(2)
                # Make sure it's not a kA value (usually small numbers like 6, 10, 36, 50)
                if int(amps_val) >= 10:  # Typical amp values are 16, 25, 32, 40, 63, 100, 160, 250, 400, etc.
                    specs['amps'] = f"{amps_val}A"

        # Extract breaking capacity (kA)
        ka_match = re.search(r'(\d+)\s*[Kk][Aa](?:\s|$|[,-])', text_normalized)
        if ka_match:
            specs['breaking_capacity'] = f"{ka_match.group(1)}kA"

        return specs
