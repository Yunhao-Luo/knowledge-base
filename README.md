# LLM Wiki

Terminal-first knowledge base assistant for maintaining a persistent markdown wiki from raw source material.

## Quick start

1. Copy the example config:

```bash
cp config/llm_wiki.example.toml config/llm_wiki.toml
```

2. Set your provider credentials:

```bash
export OPENAI_API_KEY=...
```

3. Launch the assistant:

```bash
./wiki
```

You can also run a single command:

```bash
./wiki ingest path/to/source.md
./wiki ingest --all
./wiki query "What changed across the latest sources?"
./wiki lint
./wiki lint --apply
./wiki links check
./wiki links fix
./wiki gui
```

## Structure

- `src/` contains the assistant code.
- `knowledge/raw/` stores immutable source files.
- `knowledge/wiki/` stores generated markdown pages.
- `knowledge/schema/AGENTS.md` defines the wiki maintenance rules for the assistant.

## Graphical interface

Launch the local GUI with:

```bash
./wiki gui
```

It serves a lightweight web app on `http://127.0.0.1:8765` by default. The interface can:

- browse raw sources and wiki pages
- render markdown for reading
- run query, ingest, ingest-all, lint, and lint-apply actions
- show pending raw sources and current knowledge-base status

## Supported providers

- `openai_compatible`: OpenAI-style chat completions APIs, including many hosted and local servers.
- `lm_studio`: LM Studio's local OpenAI-style server. No API key is required by default.
- `anthropic`: Anthropic Messages API.
- `command`: run any custom adapter command that accepts JSON on stdin and returns JSON on stdout.

## LM Studio

Use this config if you're pointing at LM Studio's local server:

```toml
[provider]
kind = "lm_studio"
model = "replace-with-your-loaded-lm-studio-model"
base_url = "http://127.0.0.1:1234/v1"
```

Use the exact model identifier shown by LM Studio for the currently loaded model. If LM Studio returns an error payload, the CLI now surfaces that message directly instead of failing with a raw `'choices'` exception.

The app is text-first out of the box. Non-text raw sources are preserved in `knowledge/raw/`, but only plain-text-readable files are ingested into prompts in this first version.

## Workflow additions

- `./wiki ingest --all` ingests every pending raw markdown or text file under `knowledge/raw/` that does not already have a matching source summary under `knowledge/wiki/sources/`.
- `./wiki lint --apply` asks the model to repair the wiki directly, writes any returned page updates, rebuilds the index, and logs the applied lint pass.
- `./wiki links check` scans wiki markdown for missing or ambiguous internal links.
- `./wiki links fix` rewrites resolvable internal links to canonical targets, then re-checks the wiki.
