# LLM Wiki

LLM Wiki is a terminal-first knowledge base assistant for turning raw source documents into a persistent markdown wiki. It keeps the workflow intentionally simple: raw material stays immutable, wiki pages are generated and maintained separately, and the index and log preserve navigation and history.

## How It Works

1. Put source material in `knowledge/raw/`.
2. Ingest sources into `knowledge/wiki/`.
3. Use the wiki pages for synthesis, queries, and follow-up editing.
4. Keep `knowledge/wiki/index.md` and `knowledge/wiki/log.md` up to date.

The wiki is designed around three layers:

- `knowledge/raw/` for immutable source documents
- `knowledge/wiki/` for generated summaries, concepts, and analyses
- `knowledge/schema/AGENTS.md` for the maintenance rules used by the assistant

## Quick Start

1. Copy the example config:

```bash
cp config/llm_wiki.example.toml config/llm_wiki.toml
```

2. Set provider credentials for your configured backend. For OpenAI-style providers, that is usually:

```bash
export OPENAI_API_KEY=...
```

3. Start the assistant:

```bash
./wiki
```

If you prefer a single command instead of the REPL, use one of the subcommands below.

## Commands

```bash
./wiki ingest path/to/source.md
./wiki ingest --all
./wiki query "What changed across the latest sources?"
./wiki lint
./wiki lint --apply
./wiki links check
./wiki links fix
./wiki status
./wiki gui
```

## GUI

`./wiki gui` starts a lightweight local web app on `http://127.0.0.1:8765` by default. The interface lets you:

- browse raw sources and wiki pages
- render markdown for reading
- run ingest, query, lint, and link checks
- inspect the current knowledge-base status

## Configuration

The CLI reads `config/llm_wiki.toml` by default. Copy the example file and configure one of the supported providers:

- `openai_compatible`: OpenAI-style chat completions APIs, including many hosted and local servers
- `lm_studio`: LM Studio's local OpenAI-style server
- `anthropic`: Anthropic Messages API
- `command`: a custom adapter command that reads JSON from stdin and writes JSON from stdout

Example LM Studio configuration:

```toml
[provider]
kind = "lm_studio"
model = "replace-with-your-loaded-lm-studio-model"
base_url = "http://127.0.0.1:1234/v1"
```

Use the exact model identifier shown by LM Studio for the loaded model. The CLI surfaces provider errors directly so configuration problems are easier to diagnose.

## Repository Layout

- `src/llm_wiki/` contains the assistant, CLI, GUI, providers, and helpers
- `knowledge/raw/` stores source files that should not be edited in place
- `knowledge/wiki/` stores generated wiki pages, indexes, and logs
- `knowledge/schema/AGENTS.md` defines the wiki maintenance rules
- `tests/` contains the automated test suite

## Documentation Notes

The wiki should stay concise, factual, and cross-linked. Source summaries belong under `knowledge/wiki/sources/`, thematic synthesis belongs under folders such as `concepts/` or `analyses/`, and `knowledge/wiki/log.md` should remain append-only.

## Workflow Notes

- `./wiki ingest --all` processes pending raw markdown or text files that do not already have matching source summaries.
- `./wiki lint --apply` asks the model to repair the wiki, writes any returned page updates, rebuilds the index, and logs the lint pass.
- `./wiki links check` scans wiki markdown for missing or ambiguous internal links.
- `./wiki links fix` rewrites resolvable internal links to canonical targets and then re-checks the wiki.
