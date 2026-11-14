"""Deterministic memory extraction engine service.

Provides rule-based, LLM-free extraction of structured facts from conversation text.
This is the core offline engine for the memory extraction feature.

The service uses:
- Regex pattern matching against configured extraction rules
- Heuristic keyword-based fallback extraction
- Relationship detection between entities
- Configurable rule sets for different domains

All extraction is deterministic and does not require an LLM inference call.
"""

from typing import Any, Dict, List, Optional, Set, Tuple

from app.services.rules import (
    EXTRACTION_RULES,
    extract_entities,
    extract_relationships,
    extract_facts,
    set_rule,
    get_rule,
    add_rule,
    extract_persons,
    extract_organizations,
    extract_software,
    extract_concepts,
    extract_dates,
    extract_locations,
    extract_times,
    extract_events,
)


# ── Service class ────────────────────────────────────────────────────────────
class ExtractionService:
    """Service for deterministic extraction of entities and facts from text."""

    def __init__(
        self,
        custom_rules: Optional[Dict[str, Tuple[str, Dict[str, Any]]]] = None,
        enable_heuristic: bool = True,
    ):
        """Initialize the extraction service.

        Args:
            custom_rules: Optional override for the default extraction rules dict.
                        If provided, merges with EXTRACTION_RULES (custom takes precedence).
            enable_heuristic: Whether to use heuristic keyword-based extraction alongside
                              regex patterns. Default True for maximum coverage.
        """
        self.enable_heuristic = enable_heuristic

        if custom_rules:
            # Merge: custom rules override defaults, but keep defaults for missing keys
            merged = dict(EXTRACTION_RULES)
            merged.update(custom_rules)
            self.rules = merged
        else:
            self.rules = EXTRACTION_RULES

    def extract_entities(
        self,
        text: str,
        patterns: Optional[Dict[str, Tuple[str, Dict[str, Any]]]] = None,
        use_heuristic: Optional[bool] = None,
    ) -> List[Dict[str, Any]]:
        """Extract named entities from conversation text.

        Uses the service's configured rules and heuristic setting.
        Deterministic, LLM-free extraction.

        Args:
            text: The conversation text to extract from.
            patterns: Optional custom rules override for this call.
            use_heuristic: Override the service-level heuristic setting for this call.

        Returns:
            List of extracted entities sorted by confidence then position.
        """
        effective_heuristic = use_heuristic if use_heuristic is not None else self.enable_heuristic
        return extract_entities(text, patterns, use_heuristic=effective_heuristic)

    def extract_relationships(
        self,
        text: str,
        entity_types: Optional[List[str]] = None,
        patterns: Optional[Dict[str, Tuple[str, Dict[str, Any]]]] = None,
    ) -> List[Dict[str, Any]]:
        """Extract relationships between entities from text.

        Args:
            text: The conversation text to extract from.
            entity_types: Optional filter for entity types to consider.
            patterns: Optional custom rules override.

        Returns:
            List of extracted relationships sorted by confidence.
        """
        return extract_relationships(text, entity_types, patterns)

    def extract_facts(
        self,
        text: str,
        entity_types: Optional[List[str]] = None,
        relationship_types: Optional[List[str]] = None,
        patterns: Optional[Dict[str, Tuple[str, Dict[str, Any]]]] = None,
    ) -> List[Dict[str, Any]]:
        """Extract structured facts from conversation text.

        Combines entity and relationship extraction into unified fact representations.

        Args:
            text: The conversation text to extract from.
            entity_types: Optional filter for entity types.
            relationship_types: Optional filter for relationship types.
            patterns: Optional custom rules override.

        Returns:
            List of structured facts sorted by confidence.
        """
        return extract_facts(text, entity_types, relationship_types, patterns)

    def set_rule(self, key: str, entity_type: str, confidence: float = 0.5) -> None:
        """Set a custom extraction rule at the service level.

        Args:
            key: The regex pattern string.
            entity_type: The entity type this pattern extracts.
            confidence: Default confidence for matches (0.0-1.0).
        """
        add_rule(key, entity_type, confidence)

    def get_rule(self, key: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        """Get a custom extraction rule.

        Args:
            key: The regex pattern to look up.

        Returns:
            Tuple of (entity_type, metadata) or None.
        """
        return get_rule(key)

    def configure(
        self,
        custom_rules: Optional[Dict[str, Tuple[str, Dict[str, Any]]]] = None,
        enable_heuristic: Optional[bool] = None,
    ) -> None:
        """Reconfigure the service rules and settings.

        Args:
            custom_rules: New rules to merge with defaults.
            enable_heuristic: Override heuristic extraction enablement.
        """
        if custom_rules:
            merged = dict(EXTRACTION_RULES)
            merged.update(custom_rules)
            self.rules = merged
        if enable_heuristic is not None:
            self.enable_heuristic = enable_heuristic

    def extract_persons(self, text: str) -> List[Dict[str, Any]]:
        """Convenience: extract person entities from text."""
        return extract_persons(text)

    def extract_organizations(self, text: str) -> List[Dict[str, Any]]:
        """Convenience: extract organization entities from text."""
        return extract_organizations(text)

    def extract_software(self, text: str) -> List[Dict[str, Any]]:
        """Convenience: extract software/product entities from text."""
        return extract_software(text)

    def extract_concepts(self, text: str) -> List[Dict[str, Any]]:
        """Convenience: extract concept entities from text."""
        return extract_concepts(text)

    def extract_dates(self, text: str) -> List[Dict[str, Any]]:
        """Convenience: extract date entities from text."""
        return extract_dates(text)

    def extract_locations(self, text: str) -> List[Dict[str, Any]]:
        """Convenience: extract location entities from text."""
        return extract_locations(text)

    def extract_times(self, text: str) -> List[Dict[str, Any]]:
        """Convenience: extract time entities from text."""
        return extract_times(text)

    def extract_events(self, text: str) -> List[Dict[str, Any]]:
        """Convenience: extract event entities from text."""
        return extract_events(text)


# ── Module-level convenience functions ──────────────────────────────────────
def create_service(
    custom_rules: Optional[Dict[str, Tuple[str, Dict[str, Any]]]] = None,
    enable_heuristic: bool = True,
) -> ExtractionService:
    """Factory function to create an ExtractionService instance.

    Args:
        custom_rules: Optional custom extraction rules.
        enable_heuristic: Whether to enable heuristic keyword extraction.

    Returns:
        A new ExtractionService instance.
    """
    return ExtractionService(custom_rules=custom_rules, enable_heuristic=enable_heuristic)


# ── Pre-configured services for common domains ───────────────────────────────
# Default service with full rule set and heuristic extraction
default_service = ExtractionService(enable_heuristic=True)

# Domain-specific service for technical/software conversations
technical_service = ExtractionService(
    custom_rules={
        # Emphasize software/product extraction in technical contexts
        r"\b(?:Python|JavaScript|TypeScript|React|Node|Docker|Kubernetes|AWS|GCP|Azure)\b": (
            "ENTITY_SOFTWARE",
            {"confidence": 0.9, "pattern": "known_software"},
        ),
        r"\b(?:algorithm|framework|model|approach|strategy|method|pattern)\b": (
            "ENTITY_CONCEPT",
            {"confidence": 0.85, "pattern": "technical_concept"},
        ),
        r"\b(?:API|SDK|CLI|Framework|Library)\b": (
            "ENTITY_SOFTWARE",
            {"confidence": 0.8, "pattern": "software_suffix"},
        ),
    },
    enable_heuristic=True,
)

# Domain-specific service for conversational/chat logs
conversational_service = ExtractionService(
    custom_rules={
        # Person name patterns for chat logs
        r"\b([A-Z][a-z]+(?: [A-Z][a-z]+){1,2})\b\s*[:\-]?\s*\":?\":?\":?\"?": (
            "ENTITY_PERSON",
            {"confidence": 0.85, "pattern": "chat_person"},
        ),
        # Message-style patterns
        r"\b(?:i|we|they|he|she)\s+(?:discussed|talked|said|mentioned)\b": (
            "ENTITY_EVENT",
            {"confidence": 0.7, "pattern": "chat_verb"},
        ),
    },
    enable_heuristic=True,
)


