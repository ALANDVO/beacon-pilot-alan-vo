"""Rule-based extraction engine for deterministic fact extraction from conversation text.

This module provides pattern-based entity and relationship extraction without requiring
an LLM. It supports configurable extraction rules, entity type detection, and fact
extraction from natural language conversation logs.

The extraction uses regex patterns and keyword matching to identify:
- Named entities (people, organizations, locations, dates, times, events, concepts)
- Software/products mentioned
- Relationships between entities
- Structured facts with types and metadata
"""

import re
from typing import Any, Dict, List, Optional, Set, Tuple

# Default extraction rules - case-sensitive patterns
# Pattern -> (entity_type, extraction_metadata)
EXTRACTION_RULES: Dict[str, Tuple[str, Dict[str, Any]]] = {
    r"([A-Z][a-z]+(?: [A-Z][a-z]+){0,2})": (
        "ENTITY_PERSON",
        {"confidence": 0.8, "pattern": "capitalized_name"},
    ),
    r"([A-Z][a-zA-Z0-9&.-]*(?: Inc| LLC| Corp| Ltd| University| Institute| Company))[^\w]*":?\s*"?([A-Z][a-zA-Z0-9&.-]*)?":?": (
        "ENTITY_ORGANIZATION",
        {"confidence": 0.7, "pattern": "org_name"},
    ),
    r"(?:in|at|from|to)\s+([A-Z][a-zA-Z]+(?: [A-Z][a-zA-Z]+)*)":?\s*$": (
        "ENTITY_LOCATION",
        {"confidence": 0.75, "pattern": "location_after_preposition"},
    ),
    r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}(?:st|nd|rd|th)?:?": (
        "ENTITY_DATE",
        {"confidence": 0.85, "pattern": "month_day"},
    ),
    r"\d{4}-\d{2}-\d{2}": (
        "ENTITY_DATE",
        {"confidence": 0.95, "pattern": "iso_date"},
    ),
    r"\d{1,2}:\d{2}(?: [AP]M)?:?": (
        "ENTITY_TIME",
        {"confidence": 0.8, "pattern": "clock_time"},
    ),
    r"(?:am|pm|noon|midnight)": (
        "ENTITY_TIME",
        {"confidence": 0.6, "pattern": "time_descriptor"},
    ),
    r"(?:met|discussed|reviewed|created|saw|heard|said)\s+(?:with|by|on)": (
        "ENTITY_EVENT",
        {"confidence": 0.7, "pattern": "verb_phrase"},
    ),
    r"(?:algorithm|framework|model|approach|strategy|method)": (
        "ENTITY_CONCEPT",
        {"confidence": 0.75, "pattern": "technical_concept"},
    ),
    r"(?:Python|JavaScript|TypeScript|React|Node|Docker|Kubernetes|AWS|GCP|Azure)": (
        "ENTITY_SOFTWARE",
        {"confidence": 0.8, "pattern": "known_software"},
    ),
    r"(\w+[ ]?(?:API|SDK|CLI|Framework|Library))": (
        "ENTITY_SOFTWARE",
        {"confidence": 0.65, "pattern": "software_suffix"},
    ),
}

# Keyword sets for heuristic extraction
PERSON_KEYWORDS = {
    "i", "me", "my", "myself", "we", "us", "our", "ourselves",
    "john", "jane", "alice", "bob", "charlie"
}

ORG_KEYWORDS = {
    "company", "corporation", "inc", "llc", "corp", "ltd",
    "organization", "institute", "university", "department",
    "team", "group", "division"
}

LOCATION_KEYWORDS = {
    "here", "there", "where", "location", "site",
    "office", "building", "floor", "room"
}

SOFTWARE_KEYWORDS = {
    "python", "javascript", "typescript", "react", "node",
    "docker", "kubernetes", "aws", "gcp", "azure",
    "sqlite", "postgresql", "mysql", "redis"
}

CONCEPT_KEYWORDS = {
    "algorithm", "framework", "model", "approach", "strategy",
    "method", "technique", "pattern", "architecture"
}


def _extract_span(text: str, start: int, end: int) -> Tuple[int, int]:
    if start < 0: start = 0
    if end > len(text): end = len(text)
    if start >= end: end = start + 1
    return (start, end)


def _apply_patterns(text: str, rules: Dict[str, Tuple[str, Dict[str, Any]]]) -> List[Dict[str, Any]]:
    matches = []
    for pattern, (entity_type, metadata) in rules.items():
        for match in re.finditer(pattern, text):
            extracted = {
                "entity_type": entity_type,
                "value": match.group(0),
                "span": _extract_span(text, match.start(), match.end()),
                "confidence": metadata.get("confidence", 0.5),
                "pattern": metadata.get("pattern", "unknown"),
            }
            if match.groups():
                groups = []
                for i in range(1, len(match.groups()) + 1):
                    g_start = match.start(i) if match.start(i) is not None else match.start()
                    g_end = match.end(i) if match.end(i) is not None else match.end()
                    groups.append({
                        "value": match.group(i),
                        "span": _extract_span(text, g_start, g_end),
                    })
                extracted["groups"] = groups
            matches.append(extracted)
    return matches


def _heuristic_extract(text: str, entity_type: str) -> List[Dict[str, Any]]:
    results = []
    lower_text = text.lower()
    for match in re.finditer(r"[a-zA-Z']+", text):
        word = match.group(0)
        w_start = match.start()
        w_end = match.end()

        if entity_type == "ENTITY_PERSON":
            if word[0].isupper() and word.lower() not in PERSON_KEYWORDS and len(word) > 2:
                results.append({
                    "entity_type": "ENTITY_PERSON",
                    "value": word,
                    "span": _extract_span(text, w_start, w_end),
                    "confidence": 0.4,
                    "pattern": "heuristic_capitalized",
                })

        elif entity_type == "ENTITY_ORGANIZATION":
            for kw in ORG_KEYWORDS:
                if kw in lower_text:
                    kw_match = re.search(re.escape(kw), lower_text)
                    if kw_match:
                        results.append({
                            "entity_type": "ENTITY_ORGANIZATION",
                            "value": kw,
                            "span": _extract_span(text, kw_match.start(), kw_match.end()),
                            "confidence": 0.5,
                            "pattern": "keyword_match",
                        })
                    break

        elif entity_type == "ENTITY_SOFTWARE":
            for kw in SOFTWARE_KEYWORDS:
                if kw in lower_text:
                    kw_match = re.search(re.escape(kw), lower_text)
                    if kw_match:
                        results.append({
                            "entity_type": "ENTITY_SOFTWARE",
                            "value": kw,
                            "span": _extract_span(text, kw_match.start(), kw_match.end()),
                            "confidence": 0.7,
                            "pattern": "keyword_match",
                        })
                    break

        elif entity_type == "ENTITY_CONCEPT":
            for kw in CONCEPT_KEYWORDS:
                if kw in lower_text:
                    kw_match = re.search(re.escape(kw), lower_text)
                    if kw_match:
                        results.append({
                            "entity_type": "ENTITY_CONCEPT",
                            "value": kw,
                            "span": _extract_span(text, kw_match.start(), kw_match.end()),
                            "confidence": 0.6,
                            "pattern": "keyword_match",
                        })
                    break

    return results


def extract_entities(
    text: str,
    patterns: Optional[Dict[str, Tuple[str, Dict[str, Any]]]] = None,
    use_heuristic: bool = True,
) -> List[Dict[str, Any]]:
    if not text or not text.strip():
        return []
    rules = patterns or EXTRACTION_RULES
    results: List[Dict[str, Any]] = []
    pattern_matches = _apply_patterns(text, rules)
    results.extend(pattern_matches)
    if use_heuristic:
        heuristic_persons = _heuristic_extract(text, "ENTITY_PERSON")
        existing_values = {m["value"] for m in results if m["entity_type"] == "ENTITY_PERSON"}
        for h in heuristic_persons:
            if h["value"] not in existing_values:
                results.append(h)
        heuristic_software = _heuristic_extract(text, "ENTITY_SOFTWARE")
        existing_software = {m["value"] for m in results if m["entity_type"] == "ENTITY_SOFTWARE"}
        for h in heuristic_software:
            if h["value"] not in existing_software:
                results.append(h)
        heuristic_concepts = _heuristic_extract(text, "ENTITY_CONCEPT")
        existing_concepts = {m["value"] for m in results if m["entity_type"] == "ENTITY_CONCEPT"}
        for h in heuristic_concepts:
            if h["value"] not in existing_concepts:
                results.append(h)
    seen: Set[str] = set()
    deduplicated = []
    for entity in results:
        key = (entity["entity_type"], entity["value"].lower())
        if key not in seen:
            seen.add(key)
            deduplicated.append(entity)
    deduplicated.sort(key=lambda e: (-e["confidence"], e.get("span", (0, 0))[0]))
    return deduplicated


def extract_relationships(
    text: str,
    entity_types: Optional[List[str]] = None,
    patterns: Optional[Dict[str, Tuple[str, Dict[str, Any]]]] = None,
) -> List[Dict[str, Any]]:
    if not text or not text.strip():
        return []
    rules = patterns or EXTRACTION_RULES
    results: List[Dict[str, Any]] = []
    if entity_types is None:
        entity_types = [
            "ENTITY_PERSON", "ENTITY_ORGANIZATION", "ENTITY_SOFTWARE",
            "ENTITY_CONCEPT", "ENTITY_LOCATION", "ENTITY_DATE", "ENTITY_TIME"
        ]
    entities = extract_entities(text, rules, use_heuristic=True)
    entity_map: Dict[str, Dict[str, Any]] = {}
    for entity in entities:
        val = entity["value"].lower()
        if val not in entity_map or entity["confidence"] > entity_map[val]["confidence"]:
            entity_map[val] = {"type": entity["entity_type"], "value": entity["value"], "confidence": entity["confidence"]}
    relationship_patterns = [
        (r"([A-Z][a-z]+(?: [A-Z][a-z]+){0,2})\s+(?:discussed|mentioned|talked|said|wrote|created)\s+(\w+[a-z]*)", "discussed_with", 0.8),
        (r"([A-Z][a-z]+(?: [A-Z][a-z]+){0,2})\s+(?:used|works|built|developed|implemented)\s+(\w+[a-z]*)", "used", 0.75),
        (r"([A-Z][a-z]+(?: [A-Z][a-z]+){0,2})\s+(?:met|met with)\s+([A-Z][a-z]+(?: [A-Z][a-z]+){0,2})", "met_with", 0.8),
        (r"(?:from|at|in)\s+([A-Z][a-zA-Z]+(?: [A-Z][a-zA-Z]+)*)",?\s*$", "located_at", 0.75),
        (r"([A-Z][a-z]+(?: [A-Z][a-z]+){0,2})\s+(?:said|reported|stated|claimed)\s+that", "said_that", 0.7),
    ]
    for pattern, rel_type, base_confidence in relationship_patterns:
        for match in re.finditer(pattern, text):
            groups = match.groups()
            if len(groups) >= 2:
                source_val = groups[0].strip()
                target_val = groups[1].strip()
                source_entity = next((e for e in entities if e["value"].lower() == source_val.lower()), None)
                target_entity = next((e for e in entities if e["value"].lower() == target_val.lower()), None)
                if source_entity and target_entity:
                    confidence = base_confidence
                    if source_entity["entity_type"] == "ENTITY_PERSON" and target_entity["entity_type"] in ("ENTITY_CONCEPT", "ENTITY_SOFTWARE"):
                        confidence = min(base_confidence + 0.1, 0.9)
                    results.append({
                        "source": source_entity["value"],
                        "target": target_entity["value"],
                        "relationship": rel_type,
                        "confidence": confidence,
                        "pattern": f"rel_{rel_type}",
                        "source_type": source_entity["entity_type"],
                        "target_type": target_entity["entity_type"],
                        "span": (match.start(), match.end()),
                    })
    seen_rels: Set[Tuple[str, str, str]] = set()
    deduplicated = []
    for rel in results:
        key = (rel["source"], rel["target"], rel["relationship"])
        if key not in seen_rels:
            seen_rels.add(key)
            deduplicated.append(rel)
    deduplicated.sort(key=lambda r: -r["confidence"])
    return deduplicated


def extract_facts(
    text: str,
    entity_types: Optional[List[str]] = None,
    relationship_types: Optional[List[str]] = None,
    patterns: Optional[Dict[str, Tuple[str, Dict[str, Any]]]] = None,
) -> List[Dict[str, Any]]:
    if not text or not text.strip():
        return []
    entities = extract_entities(text, patterns, use_heuristic=True)
    relationships = extract_relationships(text, entity_types, patterns)
    if entity_types:
        entities = [e for e in entities if e["entity_type"] in entity_types]
    if relationship_types:
        relationships = [r for r in relationships if r["relationship"] in relationship_types]
    facts: List[Dict[str, Any]] = []
    if entities:
        entity_by_type: Dict[str, List[str]] = {}
        for entity in entities:
            etype = entity["entity_type"]
            if etype not in entity_by_type:
                entity_by_type[etype] = []
            entity_by_type[etype].append(entity["value"])
        for etype, values in entity_by_type.items():
            unique_values = list(dict.fromkeys(values))
            fact = {
                "fact_type": "entity",
                "entities": unique_values,
                "relationships": [],
                "confidence": max((e["confidence"] for e in entities if e["entity_type"] == etype), default=0.5),
                "source_text": text[:60] + "..." if len(text) > 60 else text,
                "pattern": f"entity_extraction_{etype}",
            }
            facts.append(fact)
    if relationships:
        rel_by_type: Dict[str, List[Dict[str, Any]]] = {}
        for rel in relationships:
            rt = rel["relationship"]
            if rt not in rel_by_type:
                rel_by_type[rt] = []
            rel_by_type[rt].append({"source": rel["source"], "target": rel["target"], "confidence": rel["confidence"]})
        for rt, rels in rel_by_type.items():
            all_entities = set()
            for rel in rels:
                all_entities.add(rel["source"])
                all_entities.add(rel["target"])
            fact = {
                "fact_type": "relationship",
                "entities": list(all_entities),
                "relationships": rels,
                "confidence": max((r["confidence"] for r in rels), default=0.5),
                "source_text": text[:60] + "..." if len(text) > 60 else text,
                "pattern": f"relationship_extraction_{rt}",
            }
            facts.append(fact)
    if not entities and not relationships and text.strip():
        simple_entities = extract_entities(text, patterns, use_heuristic=True)
        if simple_entities:
            fact = {
                "fact_type": "conversation_event",
                "entities": [e["value"] for e in simple_entities[:3]],
                "relationships": [],
                "confidence": 0.4,
                "source_text": text[:60] + "..." if len(text) > 60 else text,
                "pattern": "basic_extraction_fallback",
            }
            facts.append(fact)
        else:
            fact = {
                "fact_type": "conversation_event",
                "entities": [],
                "relationships": [],
                "confidence": 0.2,
                "source_text": text[:60] + "..." if len(text) > 60 else text,
                "pattern": "text_only_fallback",
            }
            facts.append(fact)
    facts.sort(key=lambda f: -f["confidence"])
    return facts


def set_rule(key: str, entity_type: str, confidence: float = 0.5) -> None:
    EXTRACTION_RULES[key] = (entity_type, {"confidence": confidence, "pattern": key})


def get_rule(key: str) -> Optional[Tuple[str, Dict[str, Any]]]:
    return EXTRACTION_RULES.get(key)


def add_rule(key: str, entity_type: str, confidence: float = 0.5, pattern_desc: str = "") -> None:
    EXTRACTION_RULES[key] = (entity_type, {"confidence": confidence, "pattern": pattern_desc or key})


def extract_persons(text: str) -> List[Dict[str, Any]]:
    return [e for e in extract_entities(text) if e["entity_type"] == "ENTITY_PERSON"]


def extract_organizations(text: str) -> List[Dict[str, Any]]:
    return [e for e in extract_entities(text) if e["entity_type"] == "ENTITY_ORGANIZATION"]


def extract_software(text: str) -> List[Dict[str, Any]]:
    return [e for e in extract_entities(text) if e["entity_type"] == "ENTITY_SOFTWARE"]


def extract_concepts(text: str) -> List[Dict[str, Any]]:
    return [e for e in extract_entities(text) if e["entity_type"] == "ENTITY_CONCEPT"]


def extract_dates(text: str) -> List[Dict[str, Any]]:
    return [e for e in extract_entities(text) if e["entity_type"] == "ENTITY_DATE"]


def extract_locations(text: str) -> List[Dict[str, Any]]:
    return [e for e in extract_entities(text) if e["entity_type"] == "ENTITY_LOCATION"]


def extract_times(text: str) -> List[Dict[str, Any]]:
    return [e for e in extract_entities(text) if e["entity_type"] == "ENTITY_TIME"]


def extract_events(text: str) -> List[Dict[str, Any]]:
    return [e for e in extract_entities(text) if e["entity_type"] == "ENTITY_EVENT"]


__all__ = [
    "ENTITY_PERSON",
    "ENTITY_ORGANIZATION",
    "ENTITY_LOCATION",
    "ENTITY_DATE",
    "ENTITY_TIME",
    "ENTITY_EVENT",
    "ENTITY_CONCEPT",
    "ENTITY_SOFTWARE",
    "ENTITY_PRODUCT",
    "extract_entities",
    "extract_relationships",
    "extract_facts",
    "set_rule",
    "get_rule",
    "add_rule",
    "EXTRACTION_RULES",
]
