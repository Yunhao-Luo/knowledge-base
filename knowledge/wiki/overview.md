# Overview

This wiki is a small markdown knowledge base maintained by the terminal assistant. Add source files to `knowledge/raw/` and ingest them to grow the wiki over time.

## Current State

The repository currently has three wiki files:

- `index.md` - navigation entry point
- `overview.md` - project and workflow summary
- `log.md` - append-only activity log

## Structure

The project is organized into three layers:

- Raw sources: immutable documents in `knowledge/raw/`
- Wiki pages: generated markdown summaries in `knowledge/wiki/`
- Schema: maintenance instructions in `knowledge/schema/AGENTS.md`

## Workflow

1. Read or add a source in `knowledge/raw/`
2. Ingest the source into the wiki
3. Update `index.md` so the new page is easy to find
4. Append a concise note to `log.md`

## Maintenance Notes

- Keep wiki pages short, factual, and cross-linked
- Keep source summaries separate from thematic synthesis
- Preserve uncertainty when sources disagree
- Treat `log.md` as append-only

## Related Files

- [index.md](index.md) - current wiki index
- [log.md](log.md) - operation history
