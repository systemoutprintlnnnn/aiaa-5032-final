"""Precursor name normalizer"""
import re
from typing import Dict, Set


class PrecursorNormalizer:
    """Normalize precursor names to enable entity matching

    Example:
        "H2O" → "water"
        "Cu(NO₃)₂" → "copper nitrate"
    """

    # Solvent synonyms mapping
    SOLVENT_SYNONYMS: Dict[str, str] = {
        # Water variants
        "h2o": "water",
        "h2 o": "water",
        "aqueous solution": "water",
        "distilled water": "water",
        "deionized water": "water",
        "demineralized water": "water",
        # Methanol variants
        "methanol solution": "methanol",
        "methanol (meoh)": "methanol",
        "meoh": "methanol",
        "ch3oh": "methanol",
        # Ethanol variants
        "ethanol solution": "ethanol",
        "ethanol (etoh)": "ethanol",
        "etoh": "ethanol",
        # DMF variants
        "n,n-dimethylformamide": "dmf",
        "dimethylformamide": "dmf",
        "dmf solution": "dmf",
        # Other solvents
        "thf": "tetrahydrofuran",
        "tetrahydrofuran (thf)": "tetrahydrofuran",
        "acetonitrile solution": "acetonitrile",
        "ch3cn": "acetonitrile",
    }

    # Metal precursor normalization patterns
    METAL_NORMALIZERS: Dict[str, str] = {
        # Standardize hydrate notation
        # "Zn(NO3)2·6H2O" → "zinc nitrate hexahydrate"
    }

    def __init__(self):
        self._custom_mappings: Dict[str, str] = {}

    def add_custom_mapping(self, original: str, normalized: str) -> None:
        """Add custom mapping for precursor normalization"""
        self._custom_mappings[original.lower().strip()] = normalized.lower().strip()

    def normalize_solvent(self, name: str) -> str:
        """Normalize solvent name"""
        normalized = name.lower().strip()

        # Check custom mappings first
        if normalized in self._custom_mappings:
            return self._custom_mappings[normalized]

        # Check synonyms
        if normalized in self.SOLVENT_SYNONYMS:
            return self.SOLVENT_SYNONYMS[normalized]

        return normalized

    def normalize_metal_precursor(self, name: str) -> str:
        """Normalize metal precursor name

        Strategy:
        1. Lowercase
        2. Remove hydrate info for matching (keep as attribute)
        3. Standardize chemical notation
        """
        normalized = name.lower().strip()

        # Remove common hydrate patterns for matching
        # Keep original name as attribute
        hydrate_patterns = [
            r"\s*·\s*\d*h2o",  # ·6H2O
            r"\s*\.\s*\d*h2o",  # .6H2O
            r"\s*\d*h2o",  # 6H2O
            r"\s*hexahydrate",
            r"\s*tetrahydrate",
            r"\s*trihydrate",
            r"\s*dihydrate",
            r"\s*monohydrate",
            r"\s*hydrate",
        ]

        for pattern in hydrate_patterns:
            normalized = re.sub(pattern, "", normalized)

        normalized = normalized.strip()

        # Check custom mappings
        if normalized in self._custom_mappings:
            return self._custom_mappings[normalized]

        return normalized

    def normalize_organic_precursor(self, name: str) -> str:
        """Normalize organic precursor (linker) name"""
        normalized = name.lower().strip()

        # Remove common variations
        normalized = re.sub(r"\s*acid$", "", normalized)  # "terephthalic acid" → "terephthalic"
        normalized = normalized.strip()

        if normalized in self._custom_mappings:
            return self._custom_mappings[normalized]

        return normalized

    def get_normalized_key(self, name: str, precursor_type: str) -> str:
        """Get normalized key for precursor matching

        Args:
            name: Original precursor name
            precursor_type: "metal", "organic", or "solvent"

        Returns:
            Normalized key for matching
        """
        if precursor_type == "solvent":
            return self.normalize_solvent(name)
        elif precursor_type == "metal":
            return self.normalize_metal_precursor(name)
        elif precursor_type == "organic":
            return self.normalize_organic_precursor(name)
        else:
            return name.lower().strip()

    def find_duplicates(self, precursors: list[tuple[str, str]]) -> Dict[str, Set[str]]:
        """Find precursor names that should be merged

        Args:
            precursors: List of (precursor_type, name) tuples

        Returns:
            Dict mapping normalized_key → set of original names that map to it
        """
        duplicates: Dict[str, Set[str]] = {}

        for precursor_type, name in precursors:
            normalized_key = self.get_normalized_key(name, precursor_type)
            if normalized_key not in duplicates:
                duplicates[normalized_key] = set()
            duplicates[normalized_key].add(name)

        # Filter to only return keys with multiple names
        return {k: v for k, v in duplicates.items() if len(v) > 1}