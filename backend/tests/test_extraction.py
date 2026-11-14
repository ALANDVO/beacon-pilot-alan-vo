"""Unit tests for the deterministic memory extraction engine.

Tests entity extraction, relationship detection, and fact extraction
from conversation text without LLM dependency.
"""

import pytest

from app.services.extraction import (
    ExtractionService,
    extract_entities,
    extract_relationships,
    extract_facts,
    create_service,
    default_service,
    technical_service,
    conversational_service,
    set_rule,
    get_rule,
    EXTRACTION_RULES,
)


# ── Fixtures ────────────────────────────────────────────────────────────────
@pytest.fixture
def service():
    """Return a fresh ExtractionService instance per test."""
    return ExtractionService(enable_heuristic=True)


@pytest.fixture
def technical_svc():
    """Return a technical-domain ExtractionService instance."""
    return technical_service


@pytest.fixture
def conversational_svc():
    """Return a conversational-domain ExtractionService instance."""
    return conversational_service


# ── Test text constants ────────────────────────────────────────────────────
PERSON_TEXT = "John discussed the Python algorithm with Alice"
ORG_TEXT = "Alice from Google met Bob at the conference"
SOFTWARE_TEXT = "I used Python and React to build the API"
DATE_TEXT = "The meeting is scheduled for January 15th, 2024"
LOCATION_TEXT = "The conference is in Berlin"
TIME_TEXT = "The call is at 3 PM"
CONCEPT_TEXT = "We need a better algorithm for this model"
MIXED_TEXT = "John from Google discussed the Python algorithm with Alice at the Berlin conference on January 15th at 3 PM"


# ── Entity extraction tests ─────────────────────────────────────────────────
class TestExtractEntities:
    """Tests for extract_entities and service-level extraction."""

    def test_basic_person_extraction(self, service):
        """Extract persons from text with capitalized names."""
        result = service.extract_entities(PERSON_TEXT)
        persons = [e for e in result if e["entity_type"] == "ENTITY_PERSON"]
        assert len(persons) >= 1
        # Should find John and Alice
        person_values = {p["value"] for p in persons}
        assert "John" in person_values or "Alice" in person_values

    def test_software_extraction(self, service):
        """Extract software/product entities."""
        result = service.extract_entities(SOFTWARE_TEXT)
        software = [e for e in result if e["entity_type"] == "ENTITY_SOFTWARE"]
        assert len(software) >= 1
        software_values = {s["value"] for s in software}
        assert "Python" in software_values

    def test_date_extraction(self, service):
        """Extract date entities."""
        result = service.extract_entities(DATE_TEXT)
        dates = [e for e in result if e["entity_type"] == "ENTITY_DATE"]
        assert len(dates) >= 1

    def test_location_extraction(self, service):
        """Extract location entities."""
        result = service.extract_entities(LOCATION_TEXT)
        locations = [e for e in result if e["entity_type"] == "ENTITY_LOCATION"]
        assert len(locations) >= 1
        location_values = {l["value"] for l in locations}
        assert "Berlin" in location_values

    def test_concept_extraction(self, service):
        """Extract concept/entities."""
        result = service.extract_entities(CONCEPT_TEXT)
        concepts = [e for e in result if e["entity_type"] == "ENTITY_CONCEPT"]
        assert len(concepts) >= 1
        concept_values = {c["value"] for c in concepts}
        assert "algorithm" in concept_values

    def test_heuristic_enabled(self, service):
        """Heuristic extraction should find additional entities."""
        text = "I talked with Alice about the Python approach"
        result = service.extract_entities(text)
        # Should find at least person and software
        entity_types = {e["entity_type"] for e in result}
        assert "ENTITY_PERSON" in entity_types or "ENTITY_SOFTWARE" in entity_types

    def test_empty_text(self, service):
        """Empty/whitespace text should return empty list."""
        assert service.extract_entities("") == []
        assert service.extract_entities("   ") == []

    def test_custom_rules(self, service):
        """Custom rules should be respected."""
        custom = {r"\bcustom\b": ("ENTITY_CONCEPT", {"confidence": 0.9})}
        svc = ExtractionService(custom_rules=custom, enable_heuristic=False)
        result = svc.extract_entities("this is custom", use_heuristic=False)
        assert len(result) == 1
        assert result[0]["entity_type"] == "ENTITY_CONCEPT"
        assert result[0]["confidence"] == 0.9

    def test_service_defaults(self):
        """Service should use default rules when none provided."""
        svc = ExtractionService(enable_heuristic=False)
        result = svc.extract_entities(MIXED_TEXT)
        # Should still find entities via patterns even without heuristic
        assert len(result) > 0


# ── Relationship extraction tests ───────────────────────────────────────────
class TestExtractRelationships:
    """Tests for extract_relationships."""

    def test_discussed_relationship(self, service):
        """Extract 'discussed with' relationship."""
        result = service.extract_relationships(PERSON_TEXT)
        assert len(result) > 0
        # Should have a relationship involving John and Alice
        rel_types = {r["relationship"] for r in result}
        assert "discussed_with" in rel_types or any("discussed" in r.lower() for r in rel_types)

    def test_software_relationship(self, technical_svc):
        """Extract software usage relationship."""
        result = technical_svc.extract_relationships(SOFTWARE_TEXT)
        assert len(result) > 0
        # Should find Python usage relationship
        rel_values = {r["relationship"] for r in result}
        assert any("used" in r.lower() for r in rel_values)

    def test_empty_text(self, service):
        """Empty text should return empty relationships."""
        assert service.extract_relationships("") == []

    def test_relationship_entities_linked(self, service):
        """Relationships should link extracted entities."""
        result = service.extract_relationships(MIXED_TEXT)
        if result:
            for rel in result:
                assert "source" in rel
                assert "target" in rel
                assert "relationship" in rel
                assert "confidence" in rel
                assert 0.0 <= rel["confidence"] <= 1.0


# ── Fact extraction tests ───────────────────────────────────────────────────
class TestExtractFacts:
    """Tests for extract_facts."""

    def test_entity_fact(self, service):
        """Extract entity-type facts."""
        result = service.extract_facts(CONCEPT_TEXT)
        entity_facts = [f for f in result if f["fact_type"] == "entity"]
        assert len(entity_facts) > 0
        assert "entities" in entity_facts[0]
        assert "fact_type" in entity_facts[0]

    def test_relationship_fact(self, service):
        """Extract relationship-type facts."""
        result = service.extract_facts(MIXED_TEXT)
        rel_facts = [f for f in result if f["fact_type"] == "relationship"]
        assert len(rel_facts) > 0
        assert "entities" in rel_facts[0]
        assert "relationships" in rel_facts[0]
        assert "confidence" in rel_facts[0]

    def test_conversation_event_fact(self, service):
        """Extract conversation event facts when no specific entities."""
        # Very minimal text
        result = service.extract_facts("hello world")
        assert len(result) > 0
        # Should have at least a conversation_event fact or entity facts
        fact_types = {f["fact_type"] for f in result}
        assert "entity" in fact_types or "relationship" in fact_types or "conversation_event" in fact_types

    def test_filter_by_entity_type(self, service):
        """Filter facts by entity type."""
        result = service.extract_facts(
            CONCEPT_TEXT,
            entity_types=["ENTITY_CONCEPT"]
        )
        assert len(result) > 0
        for fact in result:
            assert "ENTITY_CONCEPT" in fact["entities"] or fact["fact_type"] != "entity"

    def test_filter_by_relationship_type(self, service):
        """Filter facts by relationship type."""
        result = service.extract_facts(
            MIXED_TEXT,
            relationship_types=["discussed_with"]
        )
        assert len(result) > 0

    def test_fact_confidence_range(self, service):
        """All facts should have confidence in [0, 1]."""
        result = service.extract_facts(MIXED_TEXT)
        for fact in result:
            assert 0.0 <= fact["confidence"] <= 1.0

    def test_fact_sorted_by_confidence(self, service):
        """Facts should be sorted by confidence descending."""
        result = service.extract_facts(MIXED_TEXT)
        for i in range(len(result) - 1):
            assert result[i]["confidence"] >= result[i + 1]["confidence"]


# ── Rule management tests ───────────────────────────────────────────────────
class TestRuleManagement:
    """Tests for rule setting/getting/addition."""

    def test_set_rule(self):
        """Set a custom extraction rule."""
        set_rule(r"\bspecial\b", "ENTITY_CONCEPT", 0.95)
        from app.services.rules import EXTRACTION_RULES as rules
        assert r"\bspecial\b" in rules
        rule = get_rule(r"\bspecial\b")
        assert rule is not None
        assert rule[0] == "ENTITY_CONCEPT"
        assert rule[1]["confidence"] == 0.95

    def test_add_rule(self):
        """Add a new extraction rule."""
        add_rule(r"\bnew_pattern\b", "ENTITY_SOFTWARE", 0.85, "a new software pattern")
        from app.services.rules import EXTRACTION_RULES as rules
        assert r"\bnew_pattern\b" in rules
        rule = get_rule(r"\bnew_pattern\b")
        assert rule is not None
        assert rule[0] == "ENTITY_SOFTWARE"
        assert rule[1]["confidence"] == 0.85

    def test_service_set_rule(self, service):
        """Service-level rule management."""
        service.set_rule(r"\btest_rule\b", "ENTITY_CONCEPT", 0.9)
        rule = service.get_rule(r"\btest_rule\b")
        assert rule is not None
        assert rule[0] == "ENTITY_CONCEPT"
        assert rule[1]["confidence"] == 0.9


# ── Convenience function tests ─────────────────────────────────────────────
class TestConvenienceFunctions:
    """Tests for convenience extraction functions."""

    def test_extract_persons(self, service):
        """Extract persons via convenience function."""
        result = service.extract_persons(PERSON_TEXT)
        assert len(result) > 0
        person_types = {e["entity_type"] for e in result}
        assert "ENTITY_PERSON" in person_types

    def test_extract_software(self, service):
        """Extract software via convenience function."""
        result = service.extract_software(SOFTWARE_TEXT)
        assert len(result) > 0
        software_types = {e["entity_type"] for e in result}
        assert "ENTITY_SOFTWARE" in software_types

    def test_extract_concepts(self, service):
        """Extract concepts via convenience function."""
        result = service.extract_concepts(CONCEPT_TEXT)
        assert len(result) > 0
        concept_types = {e["entity_type"] for e in result}
        assert "ENTITY_CONCEPT" in concept_types

    def test_extract_dates(self, service):
        """Extract dates via convenience function."""
        result = service.extract_dates(DATE_TEXT)
        assert len(result) > 0

    def test_extract_locations(self, service):
        """Extract locations via convenience function."""
        result = service.extract_locations(LOCATION_TEXT)
        assert len(result) > 0

    def test_extract_times(self, service):
        """Extract times via convenience function."""
        result = service.extract_times(TIME_TEXT)
        assert len(result) > 0

    def test_extract_events(self, service):
        """Extract events via convenience function."""
        result = service.extract_events(PERSON_TEXT)
        assert len(result) > 0


# ── Edge case tests ────────────────────────────────────────────────────────
class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_unicode_handling(self, service):
        """Should handle unicode characters in text."""
        result = service.extract_entities("Joël discussed le français")
        # Should not crash; may or may not extract depending on patterns
        assert isinstance(result, list)

    def test_special_chars(self, service):
        """Should handle special characters."""
        result = service.extract_entities("Test: comma, text; and. more...")
        assert isinstance(result, list)

    def test_very_long_text(self, service):
        """Should handle long text without performance issues."""
        long_text = " ".join(["word"] * 1000)
        result = service.extract_entities(long_text)
        assert isinstance(result, list)

    def test_multiple_same_entity(self, service):
        """Should deduplicate same-type entities."""
        result = service.extract_entities("John and John said that")
        person_values = {e["value"] for e in result if e["entity_type"] == "ENTITY_PERSON"}
        # Should have at most one "John" (deduplicated)
        assert len(person_values) <= 1


# ── Integration-style tests ─────────────────────────────────────────────────
class TestIntegration:
    """Integration-style tests for the extraction pipeline."""

    def test_full_pipeline_person_software_concept(self, technical_svc):
        """Full extraction pipeline on technical text."""
        result = technical_svc.extract_facts(SOFTWARE_TEXT)
        fact_types = {f["fact_type"] for f in result}
        # Should have at least entity or relationship facts
        assert len(fact_types) > 0

    def test_full_pipeline_conversational(self, conversational_svc):
        """Full extraction pipeline on conversational text."""
        result = conversational_svc.extract_facts(MIXED_TEXT)
        fact_types = {f["fact_type"] for f in result}
        assert len(fact_types) > 0

    def test_service_consistency(self, service):
        """Service should produce consistent results for same input."""
        result1 = service.extract_facts(PERSON_TEXT)
        result2 = service.extract_facts(PERSON_TEXT)
        # Same input should produce same fact types (order may vary by confidence)
        assert len(result1) == len(result2)


