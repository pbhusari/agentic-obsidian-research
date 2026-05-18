from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class ThreatPrimitive(BaseModel):
    name: str
    category: str                           # Attack | Defense | Mitigation | Open Problem
    severity: str                           # Critical | High | Medium | Low
    likelihood: str = ""                    # High | Medium | Low
    owasp_categories: list[str] = []        # AA01-AA10 mappings
    description: str
    attack_vector: str = ""                 # how the attack is delivered
    affected_components: list[str] = []     # what parts of the agent system are affected
    impact: str = ""                        # concrete security/business impact
    prerequisites: list[str] = []          # conditions required for this to be exploitable
    detection_hints: list[str] = []        # signals that this is occurring
    mitigations: list[str] = []            # specific countermeasures for this primitive
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
    owasp_categories: list[str] = []        # e.g. ["AA01", "AA05"]
    layer: str                               # Attack Surface | Attack Vector | Impact | Mitigation
    severity: str = ""                       # Critical | High | Medium | Low
    likelihood: str = ""                     # High | Medium | Low
    description: str
    threat_actor: str = ""                   # who exploits this: external attacker | malicious tool | rogue agent | insider
    attack_prerequisites: list[str] = []    # conditions that must hold for the attack to succeed
    affected_components: list[str] = []     # e.g. memory store, tool executor, orchestrator, system prompt
    impact_summary: str = ""                # one sentence business/security impact
    real_world_scenarios: list[str] = []    # concrete narrative scenarios (more vivid than examples)
    examples: list[str] = []               # short concrete examples from papers
    detection_signals: list[str] = []      # observable indicators that this is happening
    mitigations: list[str] = []
    references: list[str] = []             # external links, OWASP pages, CVEs
    child_ids: list[str] = []
    parent_ids: list[str] = []
    related_concept_ids: list[str] = []    # wikilinks to concept nodes
    paper_references: list[str] = []
