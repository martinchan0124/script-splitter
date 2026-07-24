# Script Splitter ◬

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Status](https://img.shields.io/badge/status-alpha-yellow)]()

**A layout-aware screenplay parser** that turns PDF, DOCX, or Fountain scripts into structured scene-shot JSON for storyboarding pipelines. Combines coordinate-based text classification with rule-based entity extraction and optional LLM semantic routing.

```
Input:  Screenplay (PDF / DOCX / TXT)
              ↓
Stage 0  Clarify   → Layout-based text classification (pdfplumber x0 / python-docx indent)
Stage 1  Split     → Scene heading detection + shot timeline generation
Stage 1.5 Scan     → spaCy NER pre-scan for character/location candidates
Stage 2  Extract   → Rule-based: characters, locations, visual elements, props
Stage 3  Route     → LLM per-shot semantic routing (spatial_path, entity IDs, attributes)

Output: scenes/ (Markdown), data/ (JSONL), review/ (CSV)
```

---

## Why layout-aware parsing?

Most screenplay parsers use regex or semantic heuristics to distinguish scene headings, character cues, dialogue, and action. This works for clean text but breaks on PDFs — page numbers get confused with scene headings, line-wrapped paragraphs split sentences, and indentation-based cues vanish when text is extracted without layout information.

Script Splitter takes a different approach: it reads the **physical layout** of the page first.

| Parser | PDF | DOCX | TXT |
|--------|-----|------|-----|
| **Regex-only** | ❌ page numbers, broken lines | ❌ indentation lost | ✅ |
| **Script Splitter** | ✅ `x0` coordinates → text classification | ✅ `paragraph.left_indent` → text classification | ✅ regex fallback |

### Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Pipeline Stages                    │
├─────────┬──────────┬──────────┬──────────┬──────────┤
│ Stage 0 │ Stage 1  │Stage 1.5 │ Stage 2  │ Stage 3  │
│ Clarify │ Split    │ Scan     │ Extract  │ Route    │
├─────────┼──────────┼──────────┼──────────┼──────────┤
│ PDF     │ Heading  │ spaCy    │ Location │ LLM per- │
│ x0 coord│ detect   │ NER      │ class.   │ shot     │
│ DOCX    │ → merge  │ char/    │ Char.    │ spatial  │
│ indent  │ → shots  │ loc pre- │ extract  │ path     │
│         │          │ registry │ Visual   │ char IDs │
│         │          │          │ elements │ attribs  │
└─────────┴──────────┴──────────┴──────────┴──────────┘
```

### Data model: 1+n topology

```
Global Registry (1 file per type):
  global_characters.jsonl     [character_id: int, name_raw, type, semantic_attributes]
  global_location_assets.jsonl [location_id: int, class, raw_name, ...]
  global_visual_elements.jsonl [element_id: int, type, ...]

Per-Scene Data (n files):
  scenes/S001.md              Human-readable scene + shot timeline
  scenes.jsonl                Scene records with entity relationships
  shots.jsonl                 Shot-level timeline
  scene_character_instances.jsonl  Character instances per scene → global IDs
  scene_location_instances.jsonl   Location instances per scene → global IDs
  ...
```

Entity IDs are integers when referencing global assets (e.g., `character_id: 1004`), and string IDs for per-scene instances (e.g., `SCI_S003_JACK_001`).

---

## Quick start

### Web GUI (recommended)
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

Then double-click **Script Splitter.app** or run:
```bash
python app/gui.py
```
Opens a browser at `http://127.0.0.1:5001` with drag-and-drop upload, pipeline config, and result viewers.

### CLI
```bash
# Parse a PDF (stage 2, no LLM)
python -m app.main parse script.pdf --stage 2 --no-llm --output ./output

# Parse a DOCX
python -m app.main parse script.docx --stage 2 --no-llm --output ./output

# Full pipeline with LLM (requires DeepSeek API key in .env)
python -m app.main parse script.pdf --stage 3 --output ./output
```

### CLI reference

```text
python -m app.main parse <script_path> [options]

Options:
  --output, -o   Output directory (default: Script_Splitter_Output)
  --stage        1 = scene splitting only
                 2 = + entity extraction (default)
                 3 = + LLM semantic routing
  --no-llm       Skip all LLM calls
  --no-nlp       Skip spaCy NER pre-scan
  --quiet        Suppress progress output
```

### Output structure

```
output/
├── scenes/
│   ├── S001.md       Human-readable scene + shot breakdown
│   ├── S002.md
│   └── ...
├── data/
│   ├── scenes.jsonl                Scene records
│   ├── shots.jsonl                 Shot-level timeline
│   ├── parse_report.json           Pipeline summary
│   ├── global_characters.jsonl     Global character registry
│   ├── global_location_assets.jsonl
│   ├── scene_character_instances.jsonl
│   ├── scene_location_instances.jsonl
│   ├── scene_visual_elements.jsonl
│   ├── character_equipment_instances.jsonl
│   └── scene_prop_interactions.jsonl
├── review/
│   ├── human_review_required.csv   Items needing manual inspection
│   └── extraction_warnings.csv     Low-confidence or failed extractions
└── llm_cache/                      (Stage 3) Per-scene cache for resumption
```

---

## Stage details

### Stage 0: Clarify

The clarifier is the key innovation. Instead of guessing text semantics, it reads document layout:

- **PDF**: Uses `pdfplumber` to extract `x0` coordinates per text line.
  - `x0 > 3.0 in` + `isupper` + short → character cue (`### Name`)
  - `x0 > 2.0 in` → dialogue (`> text`)
  - Scene heading pattern → heading (`# INT. ROOM - DAY`)
  - Otherwise → action text

- **DOCX**: Uses `python-docx` paragraph indentation.
  - `effective_indent > 1.0 in` → dialogue
  - Scene heading pattern → heading
  - Character cue pattern → character

- **TXT / Fountain**: Falls back to regex-based detection.

### Stage 1: Split

- Detects scene headings from clarified Markdown
- Splits each scene into a `ShotRecord` timeline at sentence granularity
- Merges PDF line-wrapped paragraphs broken by page layout

### Stage 2: Extract

Rule-based extraction (no LLM required):

| Entity | Method |
|--------|--------|
| **Characters** | Regex dialogue cue matching (`^[A-Z][A-Z0-9 '\\-.]+`) + spaCy NER |
| **Locations** | Heading classifier → 9 spatial classes (interior_single_room, outdoor_street, vehicle_interior, etc.) |
| **Background population** | Keyword matching (COMMUTERS, CROWD, EXTRAS...) |
| **Visual elements** | Pattern matching for props, weapons, accessories |
| **Prop interactions** | Verb-pattern matching (draws, points, holds) |
| **Equipment** | Carrier-pattern matching (holstered weapons) |

### Stage 3: Route (LLM)

Optional LLM pass via DeepSeek API:

- Per-shot semantic routing: maps shot content to pre-registered global entity IDs
- Sliding window context (4 previous shots) for pronoun resolution
- LLM is constrained to use only existing IDs — cannot invent new entities
- Failures degrade gracefully: empty routing instead of crashing the pipeline

---

## Configuration

### `.env`

```bash
DEEPSEEK_API_KEY=sk-your-key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

### Ruleset

Location classification rules live in `rules/active_ruleset.json`. Add custom location classes or override default confidence thresholds.

---

## Testing

```bash
# Run all tests
python -m pytest

# Run specific test suite
python -m pytest tests/test_stage1_split.py -v
python -m pytest tests/test_scene_heading_parser.py -v
python -m pytest tests/test_schemas.py -v
```

### Tested scripts

| Script | Format | Scenes | Shots | Source |
|--------|--------|--------|-------|--------|
| Carol (1-page excerpt) | PDF | 4 | 57 | `Test File/Carol Test.pdf` |
| Carol (full script) | PDF | 63 | 983 | `Test File/TEST SCRIPT carol-2015.pdf` |
| Breaking Bad (excerpt) | PDF | 12 | — | W4/1 |
| Avatar (excerpt) | PDF | 18 | — | W4/2 |
| Parasite (excerpt) | PDF | — | — | W4/3 |
| La La Land (excerpt) | TXT | — | — | W4/5 |

---

## Comparison: AI3Dstoryboard vs Prism vs Script Splitter

| Capability | AI3Dstoryboard | Prism | Script Splitter |
|---|---|---|---|
| PDF layout parsing | ❌ pypdf text-only | ✅ pdfplumber x0 | ✅ pdfplumber x0 |
| DOCX support | ❌ | ✅ python-docx | ✅ python-docx |
| Entity extraction | ✅ rule-based (dialogue cues) | ✅ spaCy NER + cues | ✅ spaCy NER + cues |
| Location classification | ✅ 9 classes | ❌ | ✅ 9 classes |
| Visual element detection | ✅ weapons, accessories | ❌ | ✅ weapons, accessories |
| Shot timeline | ❌ scene-level | ✅ shot-level | ✅ shot-level |
| Integer ID registry | ❌ string IDs | ✅ 1+n topology | ✅ 1+n topology |
| LLM cache + resumption | ✅ | ❌ | ✅ |
| Pydantic validation | ✅ | ❌ | ✅ |
| Review output (CSV) | ✅ | ❌ | ✅ |
| Unit tests | ✅ | ❌ | ✅ |
| Graceful LLM fallback | ✅ | ❌ | ✅ |

---

## Roadmap

- [ ] **Improved character extraction**: NER-based entity linking across scenes, alias resolution
- [ ] **Deeper location intelligence**: Environment-aware lighting/weather inference from context
- [ ] **Shot merging**: ML-based shot boundary detection beyond sentence splitting
- [ ] **Batch LLM routing**: Reduce API calls by batching shots per scene
- [ ] **CI pipeline**: Automated cross-script regression testing

## License

MIT
