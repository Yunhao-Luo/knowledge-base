# Overview

This wiki is maintained by the terminal assistant using the [[sources/llm-wiki-idea]] approach. Add sources to `knowledge/raw/` or use `ingest` to begin building out the knowledge base.

## Architecture
The wiki follows a three-layer architecture:
- **Raw sources**: Immutable documents such as articles, papers, notes, and media files stored in `knowledge/raw/`
- **The wiki**: LLM-generated markdown pages that summarize, connect, and synthesize the raw sources in `knowledge/wiki/`
- **The schema**: Instruction document (`AGENTS.md` or similar) that teaches the LLM how to maintain the wiki consistently

## Operations
### Ingest
When a new source arrives, the system:
1. Reads the source
2. Extracts key claims, entities, and concepts
3. Creates or updates relevant wiki pages
4. Updates the wiki index (`index.md`)
5. Appends a record to the chronological log (`log.md`)

### Query
Questions should be answered against the wiki rather than the raw corpus whenever possible. The LLM first reads the index, then relevant pages, then synthesizes an answer with citations. Durable answers can be saved back into the wiki as new pages.

### Lint
The assistant periodically checks the wiki for:
- Contradictions across pages
- Stale claims
- Orphan pages
- Missing concept pages
- Weak cross-linking
- Research gaps

## Indexing and Logging
Two special files help navigation:
- `index.md`: A content-oriented catalog of all wiki pages
- `log.md`: An append-only chronological history of ingests, queries, and lint passes

## Why this works
The hard part of maintaining a knowledge base is the bookkeeping: updating links, preserving synthesis, and keeping many pages consistent. LLMs can do this repetitive maintenance cheaply, allowing humans to focus on curation, judgment, and higher-level thinking.

## See Also
- [[sources/llm-wiki-idea]] - Original source document describing the pattern
- [[concepts/artificial-intelligence]] - Core AI concepts being applied
- [[analyses/xr-ai-intersection]] - Example of synthesized analysis from sources
