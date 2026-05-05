# LLM Wiki

A pattern for building personal knowledge bases using LLMs.

## The core idea

Instead of relying on retrieval alone, an LLM incrementally builds and maintains a persistent markdown wiki that sits between raw sources and the user. New sources are not merely indexed for later search; they are read, summarized, cross-referenced, and integrated into the evolving knowledge base.

The wiki becomes a compounding artifact. Cross-links, contradictions, summaries, and synthesis are preserved and updated over time rather than rediscovered from scratch on each query.

## Architecture

There are three layers:

- Raw sources: immutable documents such as articles, papers, notes, and media files.
- The wiki: LLM-generated markdown pages that summarize, connect, and synthesize the raw sources.
- The schema: an instruction document such as `AGENTS.md` that teaches the LLM how to maintain the wiki consistently.

## Operations

### Ingest

When a new source arrives, the LLM should:

1. Read the source.
2. Extract the key claims, entities, and concepts.
3. Create or update relevant wiki pages.
4. Update the wiki index.
5. Append a record to the chronological log.

### Query

Questions should be answered against the wiki rather than the raw corpus whenever possible. The LLM first reads the index, then relevant pages, then synthesizes an answer with citations. Durable answers can be saved back into the wiki as new pages.

### Lint

The assistant should periodically check the wiki for contradictions, stale claims, orphan pages, missing concept pages, weak cross-linking, and research gaps.

## Indexing and logging

Two special files help navigation:

- `index.md`: a content-oriented catalog of pages.
- `log.md`: an append-only chronological history of ingests, queries, and lint passes.

## Why this works

The hard part of maintaining a knowledge base is the bookkeeping: updating links, preserving synthesis, and keeping many pages consistent. LLMs can do this repetitive maintenance cheaply, allowing humans to focus on curation, judgment, and higher-level thinking.
