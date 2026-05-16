from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class ThreatPrimitive(BaseModel):
    name: str
    category: str  # Attack | Defense | Mitigation | Open Problem
    severity: str  # Critical | High | Medium | Low
    description: str
    related_concepts: list[str] = []


class Paper(BaseModel):
    arxiv_id: str
    title: str
    authors: list[str]
    published: date
    abstract: str
    url: str
    citation_count: int = 0
    # LLM-extracted fields
    one_liner: str = ""
    key_contributions: list[str] = []
    threat_primitives: list[ThreatPrimitive] = []
    attack_surfaces: list[str] = []
    mitigations: list[str] = []
    open_problems: list[str] = []
    related_papers: list[str] = []
    concepts: list[str] = []
    tags: list[str] = []


class ConceptNode(BaseModel):
    name: str
    aliases: list[str] = []
    definition: str
    threat_relevance: str
    source_papers: list[str] = []
    child_concepts: list[str] = []
    parent_concepts: list[str] = []
    open_questions: list[str] = []
    tags: list[str] = []


class ThreatTaxonomyNode(BaseModel):
    id: str
    name: str
    layer: str  # Attack Surface | Attack Vector | Impact | Mitigation
    description: str
    examples: list[str] = []
    mitigations: list[str] = []
    child_ids: list[str] = []
    paper_references: list[str] = []
