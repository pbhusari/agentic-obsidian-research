PAPER_EXTRACTION_SYSTEM = """\
You are a senior agentic AI security researcher. Extract structured intelligence from the paper below.
Respond ONLY with valid JSON matching the schema. No preamble, no markdown fences."""

PAPER_EXTRACTION_USER = """\
Title: {title}
Authors: {authors}
Published: {published}
Abstract: {abstract}

Extract:
- one_liner: one sentence (<20 words) capturing the core contribution
- key_contributions: list of 3-5 bullet strings
- threat_primitives: list of objects with fields (name, category, severity, description, related_concepts)
  category must be one of: Attack | Defense | Mitigation | Open Problem
  severity must be one of: Critical | High | Medium | Low
- attack_surfaces: list of strings (e.g. "tool-call interface", "retrieval memory", "system prompt")
- mitigations: list of actionable mitigation strings
- open_problems: list of unsolved problems the paper surfaces
- concepts: list of canonical concept names this paper touches (for wikilinks)
- tags: list of lowercase kebab-case tags

JSON ONLY:"""

PAPER_CORRECTION_USER = """\
Your previous response was not valid JSON or did not match the schema. Error: {error}

Original paper:
Title: {title}
Abstract: {abstract}

Try again. JSON ONLY:"""

CONCEPT_SYNTHESIS_SYSTEM = """\
You are a senior agentic AI security researcher performing a meta-synthesis across a corpus of papers.
Respond ONLY with a JSON array of ConceptNode objects. No preamble, no fences."""

CONCEPT_SYNTHESIS_USER = """\
Below is a JSON array of extracted papers.

{papers_json}

Identify the {k} most important emergent concepts across this corpus.
For each concept produce a JSON object with fields:
- name: canonical title-case name
- aliases: list of alternate spellings/names
- definition: 2-3 sentence synthesis grounded in the papers
- threat_relevance: one paragraph on how this concept manifests as a threat
- source_papers: list of arXiv IDs that discuss this concept
- child_concepts: list of more specific child concept names
- parent_concepts: list of broader parent concept names
- open_questions: list of 2-3 unresolved questions
- tags: list of lowercase kebab-case tags

JSON array ONLY:"""

TAXONOMY_SYSTEM = """\
You are a security taxonomy expert. Build a threat taxonomy from the extracted paper data.
Respond ONLY with a JSON array of ThreatTaxonomyNode objects. No preamble, no fences."""

TAXONOMY_USER = """\
Below are extracted papers with threat primitives.

{papers_json}

Build a threat taxonomy. Each node must have:
- id: lowercase-kebab-case slug
- name: human-readable name
- layer: one of Attack Surface | Attack Vector | Impact | Mitigation
- description: 2-3 sentences
- examples: list of concrete examples grounded in the papers
- mitigations: list of mitigations (empty for non-Mitigation layers)
- child_ids: list of child node id slugs
- paper_references: list of arXiv IDs

JSON array ONLY:"""
