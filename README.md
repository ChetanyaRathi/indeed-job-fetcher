# JobFit

Local, private job-matching that runs entirely on your own machine — no API keys, no subscription, no data leaving your laptop. Built for people who can't afford paid AI job tools.

Point it at your resume and a set of job descriptions; it ranks them by how well they fit **you**, using a local LLM (Qwen 3.5 9B) for the reasoning and a small embedding model for fast retrieval.

---

## Why

Paid job-matching and "auto-apply" services cost money most job seekers don't have. JobFit does the genuinely useful part — surfacing the roles actually worth your time and telling you *why* they fit — for free, on hardware you already own (a 16GB Mac is enough).

**Nothing is auto-submitted.** JobFit finds and ranks; you apply. It does not fill or submit application forms.

---

## How it works

Two-stage matching. This is the whole trick, and it's why the tool is both accurate and fast on a laptop:

1. **Embed + rank (cheap).** A small embedding model scores your resume against *every* job and keeps only the top ~10–15.
2. **Judge (expensive).** Qwen 3.5 9B reads only those top matches in `/think` mode and produces a fit score, matched/missing skills, and a plain-English reason.

Running the 9B model over the entire job list would be slow; running it over only the pre-filtered top matches keeps it responsive.

```
resume + jobs ──► embed & rank ALL ──► LLM judges TOP-K ──► filter ──► ranked JSON ──► CLI table
                  (embedding model)     (Qwen 9B /think)   (easy-apply,
                                                            min fit %)
```

The core is **headless**: everything from parsing to the ranked JSON is one reusable engine. The CLI is a thin wrapper that prints that JSON. The web frontend (later) renders the *exact same* JSON — so switching interfaces requires zero changes to the engine. That's why CLI-first is safe: nothing built now gets thrown away.

---

## Requirements

- Apple Silicon Mac with 16GB unified memory (or any machine that can run a ~7–9B model)
- Python 3.11+
- A local model server: **LM Studio** (GUI, easiest) or **Ollama** (CLI)
- ~8GB free disk for the two models

---

## Setup

**1. Install a model server and pull the models.**

Using Ollama:

```
ollama pull qwen3.5:9b        # reasoning model — use the MLX build on Apple Silicon
ollama pull nomic-embed-text  # embedding model (alternative: bge-m3)
```

Or use LM Studio and download the MLX 4-bit builds of the same two models from the `mlx-community` org.

**2. Install the project.**

```
git clone <your-repo> jobfit
cd jobfit
pip install -e .
cp .env.example .env
```

**3. Add your inputs.**

- Put your resume at `data/resume/resume.pdf`
- Put job descriptions (one `.txt` file per job) in `data/jobs/`

---

## Usage (CLI)

```
python -m cli.main --resume data/resume/resume.pdf --jobs data/jobs/
```

**Output:** a ranked table in the terminal, plus full results saved to `data/output/results.json`.

Common flags:

```
--top-k 10          # how many jobs the LLM judges          (default 10)
--min-fit 75        # only show matches at/above this fit %  (default 75)
--easy-apply-only   # drop jobs that redirect to external ATS forms
```

---

## Configuration

Edit `.env`:

```
LLM_ENDPOINT=http://localhost:11434   # Ollama. LM Studio uses http://localhost:1234/v1
LLM_MODEL=qwen3.5:9b
EMBED_MODEL=nomic-embed-text
TOP_K=10
MIN_FIT=75
EASY_APPLY_ONLY=true
```

---

## Project structure

```
jobfit/
├── README.md
├── pyproject.toml               # dependencies + package config
├── .env.example                 # config template: model names, endpoints, thresholds
├── .gitignore
│
├── jobfit/                      # ── HEADLESS CORE ENGINE (reusable) ──
│   ├── __init__.py
│   ├── config.py                # loads .env → model names, top_k, thresholds
│   ├── models.py                # dataclasses: Profile, Job, MatchResult
│   │
│   ├── parse/                   # [1] PARSE — resume → structured profile
│   │   ├── __init__.py
│   │   └── resume.py            # pdf/txt → Profile
│   │
│   ├── ingest/                  # [2] INGEST — jobs → normalized JDs
│   │   ├── __init__.py
│   │   ├── base.py              # Job schema + easy-apply flag
│   │   ├── folder.py            # read JD .txt files from a folder  (Phase 1)
│   │   └── scraper.py           # ATS / Indeed source               (Phase 2 — stub)
│   │
│   ├── engine/                  # [3][4][5] the matching core
│   │   ├── __init__.py
│   │   ├── embed.py             # embedding client + resume/JD vectors
│   │   ├── rank.py              # stage 1: cosine similarity → top-K
│   │   ├── judge.py             # stage 2: Qwen /think scores top-K → fit %
│   │   └── pipeline.py          # orchestrates 1→5, returns ranked JSON
│   │
│   ├── llm/                     # model-server clients (localhost)
│   │   ├── __init__.py
│   │   └── client.py            # calls Qwen + embeddings (LM Studio / Ollama)
│   │
│   ├── cache/                   # caching layer
│   │   ├── __init__.py
│   │   └── store.py             # cache parsed profile + embeddings (json/sqlite)
│   │
│   └── prompts/                 # prompt templates (kept out of code)
│       └── judge.txt            # the fit-scoring prompt
│
├── cli/                         # ── CLI WRAPPER (Phase 1) — thin ──
│   ├── __init__.py
│   └── main.py                  # args → pipeline → print table + save JSON
│
├── frontend/                    # ── FRONTEND (Phase 3) — thin, same JSON ──
│   └── .gitkeep                 # empty until Phase 2 is done
│
├── data/                        # local inputs/outputs (gitignored)
│   ├── resume/                  # put resume.pdf here
│   ├── jobs/                    # put JD .txt files here (Phase 1)
│   ├── cache/                   # auto: embeddings + parsed profile
│   └── output/                  # ranked results.json
│
└── tests/
    ├── __init__.py
    ├── test_rank.py             # embedding-rank sanity check
    ├── test_judge.py            # LLM scoring output shape
    └── fixtures/
        ├── sample_resume.txt
        └── jobs/                # a few sample JDs
```

The dividing line: `jobfit/` is the engine, `cli/` and `frontend/` are interchangeable wrappers around it. The stable contract between them is the ranked JSON that `pipeline.py` returns.

---

## Roadmap

**Phase 1 — CLI (now).** Resume + a folder of JD text files → ranked results in the terminal. In-memory, no database, no scraper. Goal: prove match quality is good before adding anything else.

**Phase 2 — Job source.** Pull jobs automatically from ATS feeds (Greenhouse, Lever, Ashby) and optionally Indeed, tagging each with an easy-apply flag at ingest. Persist to SQLite so re-runs are incremental.

**Phase 3 — Frontend.** A thin web UI (FastAPI + React) that renders the same ranked JSON the CLI already produces. No engine changes required.

---

## Notes

- **Everything runs locally.** Your resume and the job data never leave your machine.
- **Easy-apply is carried, not invented.** It's a flag set at ingest (Indeed's Easily-Apply badge when scraping; always true for direct ATS feeds). The LLM never guesses it — the filter step just reads the flag.
- **Caching.** Your parsed resume and its embedding are computed once; job embeddings are cached — repeat runs are near-instant.
- **Start with the thinnest slice.** One resume + a folder of JD `.txt` files → embed → rank → Qwen scores the top 10 → print. No scraper, no vector DB (in-memory is fine at this scale). Get the match quality right first.

---

## License

MIT
