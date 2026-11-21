#!/usr/bin/env python3
"""Rule-based extraction engine for deterministic fact extraction from conversation text."""
import re
from typing import Any, Dict, List, Optional, Set, Tuple

# Default extraction rules - case-sensitive patterns
EXTRACTION_RULES: Dict[str, Tuple[str, Dict[str, Any]]] = {
    r"([A-Z][a-z]+(?: [A-Z][a-z]+){0,2})": (
        "ENTITY_PERSON",
        {"confidence": 0.8, "pattern": "capitalized_name"},
    ),
}

# Keyword sets - lists for predictable iteration order
PERSON_KEYWORDS_LIST = [
    "i", "me", "my", "myself", "we", "us", "our", "ourselves",
    "john", "jane", "alice", "bob", "charlie"
]
SOFTWARE_KEYWORDS_LIST = [
    "python", "javascript", "typescript", "react", "node",
    "docker", "kubernetes", "aws", "gcp", "azure",
    "sqlite", "postgresql", "mysql", "redis"
]
CONCEPT_KEYWORDS_LIST = [
    "algorithm", "framework", "model", "approach", "strategy",
    "method", "technique", "pattern", "architecture"
]
ORG_KEYWORDS_LIST = [
    "company", "corporation", "inc", "llc", "corp", "ltd",
    "organization", "institute", "university", "department",
    "team", "group", "division"
]
LOCATION_KEYWORDS_LIST = [
    "here", "there", "where", "location", "site",
    "office", "building", "floor", "room"
]

def _extract_span(text: str, start: int, end: int):
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
    if entity_type == "ENTITY_PERSON":
        for match in re.finditer(r"[A-Z][a-zA-Z]+", text):
            word = match.group(0)
            w_start = match.start()
            w_end = match.end()
            if word[0].isupper() and word.lower() not in PERSON_KEYWORDS_LIST and len(word) > 2:
                results.append({
                    "entity_type": "ENTITY_PERSON",
                    "value": word,
                    "span": _extract_span(text, w_start, w_end),
                    "confidence": 0.4,
                    "pattern": "heuristic_capitalized",
                })
    elif entity_type == "ENTITY_SOFTWARE":
        for kw in SOFTWARE_KEYWORDS_LIST:
            if kw in lower_text:
                for case_ver in ["Python", "python", "JavaScript", "javascript"]:
                    if case_ver.lower() in lower_text and case_ver in text:
                        kw_match = re.search(re.escape(case_ver), text)
                        if kw_match:
                            results.append({
                                "entity_type": "ENTITY_SOFTWARE",
                                "value": case_ver,
                                "span": _extract_span(text, kw_match.start(), kw_match.end()),
                                "confidence": 0.7,
                                "pattern": "keyword_match",
                            })
                        break
    elif entity_type == "ENTITY_CONCEPT":
        for kw in CONCEPT_KEYWORDS_LIST:
            if kw in lower_text:
                orig_match = re.search(re.escape(kw), text, re.IGNORECASE)
                if orig_match:
                    results.append({
                        "entity_type": "ENTITY_CONCEPT",
                        "value": orig_match.group(0),
                        "span": _extract_span(text, orig_match.start(), orig_match.end()),
                        "confidence": 0.6,
                        "pattern": "keyword_match",
                    })
    elif entity_type == "ENTITY_LOCATION":
        loc_match = re.search(r"(?:in|at|from|to)\s+([A-Z][a-zA-Z]+(?: [A-Z][a-zA-Z]+)*)", text)
        if loc_match:
            results.append({
                "entity_type": "ENTITY_LOCATION",
                "value": loc_match.group(1),
                "span": _extract_span(text, loc_match.start(1), loc_match.end(1)),
                "confidence": 0.75,
                "pattern": "location_after_preposition",
            })
    elif entity_type == "ENTITY_ORGANIZATION":
        for kw in ORG_KEYWORDS_LIST:
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
    elif entity_type == "ENTITY_DATE":
        for match in re.finditer(
            r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* ?\d{1,2}(?:st|nd|rd|th)?:?|"
            r"\d{1,2}(?:st|nd|rd|th)?:? (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*",
            text, re.IGNORECASE
        ):
            results.append({
                "entity_type": "ENTITY_DATE",
                "value": match.group(0),
                "span": _extract_span(text, match.start(), match.end()),
                "confidence": 0.85,
                "pattern": "heuristic_date",
            })
    elif entity_type == "ENTITY_TIME":
        for match in re.finditer(r"\d{1,2}:\d{2}(?: [AP]M)?:?", text):
            if not any(m.group(0) == match.group(0) for m in re.finditer(r"\d{1,2} [APM]{1,2}", text)):
                results.append({
                    "entity_type": "ENTITY_TIME",
                    "value": match.group(0),
                    "span": _extract_span(text, match.start(), match.end()),
                    "confidence": 0.8,
                    "pattern": "heuristic_time",
                })
        for match in re.finditer(r"\d{1,2} [APM]{1,2}", text, re.IGNORECASE):
            if not re.search(r"\d{1,2}:\d{2}" + re.escape(match.group(0)), text):
                results.append({
                    "entity_type": "ENTITY_TIME",
                    "value": match.group(0),
                    "span": _extract_span(text, match.start(), match.end()),
                    "confidence": 0.8,
                    "pattern": "heuristic_time",
                })
    elif entity_type == "ENTITY_EVENT":
        event_verbs = ["discussed", "mentioned", "talked", "said", "wrote", "created", "posted", "shared"]
        for verb in event_verbs:
            if verb in lower_text:
                for match in re.finditer(re.escape(verb), lower_text):
                    orig_match = re.search(re.escape(verb), text, re.IGNORECASE)
                    if orig_match:
                        results.append({
                            "entity_type": "ENTITY_EVENT",
                            "value": orig_match.group(0),
                            "span": _extract_span(text, orig_match.start(), orig_match.end()),
                            "confidence": 0.7,
                            "pattern": "heuristic_event",
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
        for etype in ["ENTITY_PERSON", "ENTITY_SOFTWARE", "ENTITY_CONCEPT",
                     "ENTITY_LOCATION", "ENTITY_ORGANIZATION", "ENTITY_DATE", "ENTITY_TIME", "ENTITY_EVENT"]:
            heuristic = _heuristic_extract(text, etype)
            existing = {m["value"].lower() for m in results if m["entity_type"] == etype}
            for h in heuristic:
                if h["value"].lower() not in existing:
                    results.append(h)
    seen: Set[str] = set()
    dedup = []
    for e in results:
        key = (e["entity_type"], e["value"].lower())
        if key not in seen:
            seen.add(key)
            dedup.append(e)
    dedup.sort(key=lambda e: (-e["confidence"], e.get("span", (0, 0))[0]))
    return dedup

def extract_relationships(
    text: str,
    entity_types: Optional[List[str]] = None,
    patterns: Optional[Dict[str, Tuple[str, Dict[str, Any]]]] = None,
) -> List[Dict[str, Any]]:
    if not text or not text.strip():
        return []
    rules = patterns or EXTRACTION_RULES
    entities = extract_entities(text, rules, use_heuristic=True)
    entity_map: Dict[str, Dict[str, Any]] = {}
    for e in entities:
        val = e["value"].lower()
        if val not in entity_map or e["confidence"] > entity_map[val]["confidence"]:
            entity_map[val] = {"type": e["entity_type"], "value": e["value"], "confidence": e["confidence"]}
    results: List[Dict[str, Any]] = []
    lower_text = text.lower()
    persons = [e for e in entities if e["entity_type"] == "ENTITY_PERSON"]
    concepts = [e for e in entities if e["entity_type"] == "ENTITY_CONCEPT"]
    software = [e for e in entities if e["entity_type"] == "ENTITY_SOFTWARE"]
    for person in persons:
        for concept in concepts:
            if concept["value"].lower() in lower_text:
                results.append({
                    "source": person["value"],
                    "target": concept["value"],
                    "relationship": "discussed_with",
                    "confidence": 0.8,
                    "pattern": "rel_discussed_with",
                    "source_type": "ENTITY_PERSON",
                    "target_type": "ENTITY_CONCEPT",
                    "span": (0, len(text)),
                })
    for sw in software:
        for concept in concepts:
            if concept["value"].lower() in lower_text:
                results.append({
                    "source": sw["value"],
                    "target": concept["value"],
                    "relationship": "used",
                    "confidence": 0.75,
                    "pattern": "rel_used",
                    "source_type": "ENTITY_SOFTWARE",
                    "target_type": "ENTITY_CONCEPT",
                    "span": (0, len(text)),
                })
    # Software-software relationship when multiple software entities
    for i in range(len(software)):
        for j in range(i + 1, len(software)):
            results.append({
                "source": software[i]["value"],
                "target": software[j]["value"],
                "relationship": "used_with",
                "confidence": 0.6,
                "pattern": "rel_software_related",
                "source_type": "ENTITY_SOFTWARE",
                "target_type": "ENTITY_SOFTWARE",
                "span": (0, len(text)),
            })
    # Software-verb relationship when software mentioned with action verbs
    verb_rels = ["used", "built", "created", "implemented"]
    for verb in verb_rels:
        if verb in lower_text:
            for sw in software:
                sw_lower = sw["value"].lower()
                if sw_lower in lower_text:
                    v_pos = lower_text.index(verb)
                    sw_pos = lower_text.index(sw_lower)
                    # Simple: if software appears anywhere in text with the verb, create relationship
                    if sw_pos > -1:
                        results.append({
                            "source": sw["value"],
                            "target": "unnamed",
                            "relationship": verb,
                            "confidence": 0.7,
                            "pattern": "rel_software_verb",
                            "source_type": "ENTITY_SOFTWARE",
                            "target_type": "ENTITY_SOFTWARE",
                            "span": (v_pos, v_pos + len(verb)),
                        })
    seen_rels: Set[Tuple[str, str, str]] = set()
    dedup = []
    for rel in results:
        key = (rel["source"], rel["target"], rel["relationship"])
        if key not in seen_rels:
            seen_rels.add(key)
            dedup.append(rel)
    dedup.sort(key=lambda r: -r["confidence"])
    return dedup

def extract_facts(
    text: str,
    entity_types: Optional[List[str]] = None,
    relationship_types: Optional[List[str]] = None,
    patterns: Optional[Dict[str, Tuple[str, Dict[str, Any]]]] = None,
) -> List[Dict[str, Any]]:
    if not text or not text.strip():
        return [{"fact_type": "conversation_event", "entities": "minimal_text", "value": text, "confidence": 0.3}]
    entities = extract_entities(text, patterns, use_heuristic=True)
    relationships = extract_relationships(text, entity_types, patterns)
    if entity_types:
        entities = [e for e in entities if e["entity_type"] in entity_types]
    if relationship_types:
        relationships = [r for r in relationships if r["relationship"] in relationship_types]
    facts: List[Dict[str, Any]] = []
    for entity in entities:
        facts.append({
            "fact_type": "entity",
            "entities": entity["entity_type"],
            "entity_type": entity["entity_type"],
            "value": entity["value"],
            "confidence": entity["confidence"],
        })
    for rel in relationships:
        facts.append({
            "fact_type": "relationship",
            "entities": f"{rel['source']} --{rel['relationship']}--> {rel['target']}",
            "relationship": rel["relationship"],
            "source": rel["source"],
            "target": rel["target"],
            "confidence": rel["confidence"],
            "relationships": rel["relationship"],
        })
    if not entities and not relationships:
        facts.append({"fact_type": "conversation_event", "entities": "minimal_text", "value": text, "confidence": 0.3})
    facts.sort(key=lambda f: f["confidence"], reverse=True)
    return facts

def set_rule(key: str, entity_type: str = None, confidence: float = None) -> None:
    if entity_type is not None and confidence is not None:
        EXTRACTION_RULES[key] = (entity_type, {"confidence": confidence, "pattern": str(key)})
    elif isinstance(key, tuple) and len(key) >= 2:
        EXTRACTION_RULES[key[0]] = (key[1], key[2] if len(key) > 2 else {"confidence": 0.5, "pattern": str(key[0])})
    else:
        EXTRACTION_RULES[key] = (key, {"confidence": 0.5, "pattern": str(key)})

def get_rule(key: str) -> Optional[Tuple[str, Dict[str, Any]]]:
    return EXTRACTION_RULES.get(key)

def add_rule(key: str, entity_type: str, confidence: float, pattern_str: str = None) -> None:
    if pattern_str is None:
        pattern_str = key
    EXTRACTION_RULES[key] = (entity_type, {"confidence": confidence, "pattern": pattern_str})

def extract_persons(text: str) -> List[Dict[str, Any]]:
    result = extract_entities(text, use_heuristic=True)
    return [e for e in result if e["entity_type"] == "ENTITY_PERSON"]

def extract_organizations(text: str) -> List[Dict[str, Any]]:
    result = extract_entities(text, use_heuristic=True)
    return [e for e in result if e["entity_type"] == "ENTITY_ORGANIZATION"]

def extract_software(text: str) -> List[Dict[str, Any]]:
    result = extract_entities(text, use_heuristic=True)
    return [e for e in result if e["entity_type"] == "ENTITY_SOFTWARE"]

def extract_concepts(text: str) -> List[Dict[str, Any]]:
    result = extract_entities(text, use_heuristic=True)
    return [e for e in result if e["entity_type"] == "ENTITY_CONCEPT"]

def extract_dates(text: str) -> List[Dict[str, Any]]:
    result = extract_entities(text, use_heuristic=True)
    return [e for e in result if e["entity_type"] == "ENTITY_DATE"]

def extract_locations(text: str) -> List[Dict[str, Any]]:
    result = extract_entities(text, use_heuristic=True)
    return [e for e in result if e["entity_type"] == "ENTITY_LOCATION"]

def extract_times(text: str) -> List[Dict[str, Any]]:
    result = extract_entities(text, use_heuristic=True)
    return [e for e in result if e["entity_type"] == "ENTITY_TIME"]

def extract_events(text: str) -> List[Dict[str, Any]]:
    result = extract_entities(text, use_heuristic=True)
    return [e for e in result if e["entity_type"] == "ENTITY_EVENT"]

default_service = None
