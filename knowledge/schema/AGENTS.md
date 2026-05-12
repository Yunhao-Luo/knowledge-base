# LLM Wiki Schema

You are the maintainer of a persistent markdown knowledge base.

## Layers

- `knowledge/raw/` contains immutable source documents.
- `knowledge/wiki/` contains generated markdown pages that you may create or update.
- `knowledge/wiki/index.md` is the content index.
- `knowledge/wiki/log.md` is an append-only operation log.

## Conventions

- Prefer short, factual markdown pages with explicit links to related pages.
- Preserve uncertainty. If sources disagree, note the contradiction instead of flattening it.
- Treat the wiki as cumulative. New sources should update existing synthesis when appropriate.
- Use wiki links like `[[concepts/example]]` for internal references.
- Add a `## Sources` section on pages that synthesize external evidence.
- Keep source summaries under `sources/`.
- Keep thematic pages under folders such as `concepts/`, `entities/`, `projects/`, or `analyses/`.
- Keep `knowledge/wiki/log.md` append-only.
- Prefer canonical wiki links instead of mixing wiki links with title-style references.

## Ingest workflow

1. Read the source and identify its main claims, entities, concepts, and contradictions.
2. Create or update the relevant wiki pages.
3. Update `index.md` so a future session can discover the affected pages.
4. Append a concise entry to `log.md`.

## Query workflow

1. Read `index.md` first.
2. Read the most relevant wiki pages.
3. Answer with citations to wiki pages and, when useful, source summaries.
4. If the answer is materially valuable, suggest saving it back into the wiki.

## Lint workflow

Look for:

- orphan pages
- stale claims
- contradictions across pages
- missing concept pages
- missing cross-links
- gaps worth researching next

## Maintenance tools

- Use `./wiki links check` when navigation seems broken or you suspect ambiguous internal links.
- Use `./wiki links fix` to normalize resolvable internal links before doing a heavier lint pass.
