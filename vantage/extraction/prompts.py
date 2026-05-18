PAPER_EXTRACTION_SYSTEM = """\
You are a senior agentic AI security researcher. Extract structured intelligence from the paper below.
Respond ONLY with valid JSON matching the schema. No preamble, no markdown fences."""

PAPER_EXTRACTION_USER = """\
Title: {title}
Authors: {authors}
Published: {published}
Abstract: {abstract}

Extract the following fields. All fields are scoped to agentic AI security (LLM agents, tool use, multi-agent systems).

- one_liner: one sentence (<20 words) capturing the core contribution
- key_contributions: list of 3-5 bullet strings
- threat_primitives: list of threat objects, each with EXACTLY these fields:
    - name: short name for the threat
    - category: one of Attack | Defense | Mitigation | Open Problem
    - severity: one of Critical | High | Medium | Low
    - likelihood: one of High | Medium | Low
    - owasp_categories: list of OWASP Agentic AI Top 10 IDs that apply (AA01-AA10), empty list if none
    - description: 2-3 sentence explanation
    - attack_vector: how the attack is delivered (e.g. "injected tool output", "malicious system prompt")
    - affected_components: list of agent components affected (e.g. "memory store", "tool executor", "orchestrator")
    - impact: one sentence on concrete security or business impact
    - prerequisites: list of conditions required for this to be exploitable
    - detection_hints: list of observable signals that this threat is active
    - mitigations: list of specific countermeasures for this threat
    - related_concepts: list of related concept names
- attack_surfaces: list of strings (e.g. "tool-call interface", "retrieval memory", "system prompt")
- mitigations: list of high-level actionable mitigation strings (system-wide, not per-threat)
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
You are a senior agentic AI security researcher performing a meta-synthesis across a corpus of papers.

Below is a JSON array of extracted papers.

{papers_json}

Identify the {k} most important emergent concepts across this corpus.
For each concept produce a JSON object with EXACTLY these fields:
- name: canonical title-case name (string)
- aliases: list of alternate spellings/names (list of strings)
- definition: 2-3 sentence synthesis grounded in the papers (string)
- threat_relevance: one paragraph on how this concept manifests as a threat (string)
- source_papers: list of arXiv IDs that discuss this concept (list of strings)
- child_concepts: list of more specific child concept names (list of strings)
- parent_concepts: list of broader parent concept names (list of strings)
- open_questions: list of 2-3 unresolved questions (list of strings)
- tags: list of lowercase kebab-case tags (list of strings)

After your reasoning, output a single valid JSON array containing exactly {k} objects. No markdown fences, no extra text after the array.
JSON array:"""

TAXONOMY_SYSTEM = """\
You are an agentic AI security expert specializing in the OWASP Agentic AI Top 10.
Your job is to map research findings onto the OWASP Agentic AI Top 10 threat taxonomy.
Respond ONLY with a JSON array of ThreatTaxonomyNode objects. No preamble, no fences.

The OWASP Agentic AI Top 10 categories are:
AA01 - Prompt Injection
AA02 - Sensitive Information Disclosure
AA03 - Excessive Agency
AA04 - Memory Poisoning
AA05 - Insecure Tool Usage
AA06 - Insufficient Access Controls
AA07 - Agent Communication Vulnerabilities
AA08 - Inadequate Monitoring and Logging
AA09 - Insecure Output Handling
AA10 - Uncontrolled Recursion and Loops

Only include nodes that are relevant to agentic AI systems. Exclude generic web/network threats
that do not specifically apply to LLM-based agents, multi-agent pipelines, or tool-using AI."""

TAXONOMY_USER = """\
Below are threat primitives extracted from agentic AI security research papers.

{papers_json}

Build a comprehensive threat taxonomy strictly scoped to OWASP Agentic AI Top 10 (AA01-AA10).
Organize nodes so there is at least one node per OWASP category that has evidence in the papers.
Each node must have EXACTLY these fields:
- id: lowercase-kebab-case slug (string)
- name: human-readable name (string)
- owasp_categories: list of OWASP Agentic AI Top 10 IDs, e.g. ["AA01", "AA05"] (list of strings)
- layer: one of: Attack Surface | Attack Vector | Impact | Mitigation (string)
- severity: one of: Critical | High | Medium | Low (string)
- likelihood: one of: High | Medium | Low (string)
- description: 3-4 sentences grounded in agentic AI context, explaining the threat mechanism (string)
- threat_actor: who exploits this, e.g. "external attacker", "malicious tool", "rogue sub-agent", "insider" (string)
- attack_prerequisites: list of conditions that must hold for the attack to succeed (list of strings)
- affected_components: list of agent system components affected, e.g. "memory store", "tool executor", "orchestrator", "system prompt" (list of strings)
- impact_summary: one sentence business/security impact (string)
- real_world_scenarios: list of 2-3 vivid narrative scenarios grounded in the papers (list of strings)
- examples: list of short concrete examples from the papers (list of strings)
- detection_signals: list of observable indicators that this threat is active (list of strings)
- mitigations: specific countermeasures — populate for ALL layers, not just Mitigation layer (list of strings)
- references: list of relevant external references (OWASP page URLs, related standards) (list of strings)
- child_ids: list of child node id slugs (list of strings)
- parent_ids: list of parent node id slugs (list of strings)
- related_concept_ids: list of concept names for Obsidian wikilinks (list of strings)
- paper_references: list of arXiv IDs (list of strings)

Rules:
- Every OWASP category (AA01-AA10) that has supporting evidence in the papers must have at least one node.
- Discard any node that does not clearly apply to LLM agents, tool use, or multi-agent pipelines.
- Prefer depth over breadth: a smaller set of richly populated nodes beats many shallow ones.

After your reasoning, output a single valid JSON array. No markdown fences, no extra text after the array.
JSON array:"""
