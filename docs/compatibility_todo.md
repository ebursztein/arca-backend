# Compatibility Labels & LLM Guidance Revamp

**Status:** TODO
**Date:** December 2025

---

## Refinements from Review

1. **Band IDs instead of string ranges** - Use `"very_low"`, `"low"`, etc. with numeric ranges in metadata so cutoffs can be tweaked without changing keys
2. **Top 2 categories for matrix** - Pass top and bottom (or top 2 by score) with full context to LLM
3. **Optional weight on DrivingAspect** - For future sorting/contribution strength
4. **generate_driving_aspect_summary uses planet_meanings** - Pull from `astrological_basis.planet_meanings` for consistent voice

---

## Problem Summary

1. **Meters lack defined labels and tone** - Unlike astrometers, compatibility categories just pass raw scores with generic labels
2. **LLM prompt doesn't guide interpretation** - No per-band guidance telling the LLM *how* to write about a 25 vs a 75
3. **No programmatic overall guidance** - Unlike astrometers' `generate_headline_guidance()` which uses a matrix-based approach
4. **iOS doesn't receive rich category metadata** - No label, description, or "what this measures" for display
5. **LLM doesn't know WHY a score is what it is** - Aspect info exists but isn't contextualized per category

---

## Solution Overview

### Part 1: JSON Label System
Per-category JSON files with:
- `label` per band (e.g., "Shut Off", "Warm", "Soul-Level")
- `guidance` per band (LLM instruction)
- `description` (what this meter represents)
- `measures` (what astrological factors drive it)

### Part 2: Overall Guidance Matrix (25-case)
Like astrometers' `HEADLINE_MATRIX`:
- Identify top 2 categories (highest/lowest)
- Map band combination to conjunction ("and"/"but") and tone
- Generate instruction text for LLM

### Part 3: Enhanced API Response
Add new fields to `CompatibilityCategory`:
- `label`: The band label (e.g., "Warm")
- `description`: What this category measures (for iOS display)
- `driving_aspects`: Top aspects with planet meanings (for iOS to show WHY)

### Part 4: Update API Docs
Run `generate_api_docs.py` after model changes.

---

## Current API Response (CompatibilityCategory)

```python
class CompatibilityCategory(BaseModel):
    id: str                        # "emotional"
    name: str                      # "Emotional Connection"
    score: int                     # 0-100
    insight: Optional[str]         # LLM-generated text
    aspect_ids: list[str]          # ["asp_001", "asp_002"]
```

## New API Response (CompatibilityCategory)

```python
class CompatibilityCategory(BaseModel):
    # Existing fields (keep all)
    id: str                        # "emotional"
    name: str                      # "Emotional Connection"
    score: int                     # 0-100
    insight: Optional[str]         # LLM-generated text
    aspect_ids: list[str]          # ["asp_001", "asp_002"]

    # NEW fields
    label: str                     # "Warm" (band label)
    description: str               # "How deeply you connect emotionally"
    driving_aspects: list[DrivingAspect]  # Top aspects with meanings
```

## New Model: DrivingAspect

```python
class DrivingAspect(BaseModel):
    """A simplified aspect for iOS display with human-readable meanings."""
    aspect_id: str                 # Reference to full aspect
    user_planet: str               # "Moon"
    their_planet: str              # "Venus"
    aspect_type: str               # "trine"
    is_harmonious: bool            # True
    summary: str                   # "Your emotional needs (Moon) flow easily with their love style (Venus)"
    weight: Optional[float] = None # Optional, for future sorting/contribution strength
```

---

## Files to Create

### Directory Structure
```
functions/compatibility/
├── __init__.py
├── labels.py                  # Label loading + lookup + headline matrix
└── labels/
    ├── overall.json           # Overall compatibility (5 bands)
    ├── romantic/
    │   ├── emotional.json
    │   ├── communication.json
    │   ├── attraction.json
    │   ├── values.json
    │   ├── long_term.json
    │   └── growth.json
    ├── friendship/
    │   ├── emotional.json     # Distinct from romantic
    │   ├── communication.json # Distinct from romantic
    │   ├── fun.json
    │   ├── loyalty.json
    │   └── shared_interests.json
    └── coworker/
        ├── communication.json # Distinct from romantic/friendship
        ├── collaboration.json
        ├── reliability.json
        ├── ambition.json
        └── power_dynamics.json
```

---

## JSON Schema (Enhanced)

### Per-Category Label File (Updated Schema)
```json
{
  "_schema_version": "1.0",
  "_category": "emotional",
  "_mode": "romantic",
  "metadata": {
    "category_id": "emotional",
    "display_name": "Emotional Connection",
    "description": "How deeply you connect emotionally - whether you truly 'get' each other's feelings",
    "sentence_template": "Emotionally, this bond feels ___."
  },
  "bands": [
    { "id": "very_low",  "min": 0,  "max": 20 },
    { "id": "low",       "min": 20, "max": 40 },
    { "id": "mid",       "min": 40, "max": 60 },
    { "id": "high",      "min": 60, "max": 80 },
    { "id": "very_high", "min": 80, "max": 100 }
  ],
  "astrological_basis": {
    "primary_planets": ["Moon", "Venus", "Neptune"],
    "what_it_measures": "Moon-Moon aspects show emotional rhythm. Moon-Venus shows care style alignment. Neptune adds depth or illusion.",
    "planet_meanings": {
      "Moon": "emotional needs and instincts",
      "Venus": "love style and what you value",
      "Neptune": "dreams, idealization, and intuition"
    }
  },
  "bucket_labels": {
    "very_low": {
      "label": "Shut Off",
      "guidance": "They struggle to reach each other emotionally; validate the loneliness and warn against expecting deep support here."
    },
    "low": {
      "label": "Mismatched",
      "guidance": "Feel things on different wavelengths; talk about understanding each other's style, may stay uneven."
    },
    "mid": {
      "label": "Surface-Deep",
      "guidance": "Some depth but not automatic; emotional closeness grows if both make effort."
    },
    "high": {
      "label": "Warm",
      "guidance": "Generally 'get' each other's feelings; encourage honest sharing."
    },
    "very_high": {
      "label": "Soul-Level",
      "guidance": "Strong emotional resonance; describe feeling deeply seen, handle intensity with care."
    }
  }
}
```

---

## Overall Guidance Matrix (25-case)

Using 5 bands to match the label system: 0-20, 20-40, 40-60, 60-80, 80-100 = 5x5 = 25 cases.

Band IDs match JSON: `very_low`, `low`, `mid`, `high`, `very_high`

```python
def get_compat_band(score: float) -> str:
    """Map score to band ID for matrix lookup."""
    if score >= 80: return "very_high"  # 80-100
    if score >= 60: return "high"       # 60-80
    if score >= 40: return "mid"        # 40-60
    if score >= 20: return "low"        # 20-40
    return "very_low"                   # 0-20

# Matrix: (top_category_band, bottom_category_band) -> (pattern, conjunction, tone)
COMPAT_HEADLINE_MATRIX = {
    # very_high (80-100) + X
    ("very_high", "very_high"): ("stellar_match", "and", "celebrate exceptional alignment"),
    ("very_high", "high"): ("strong_foundation", "and", "lead with strength, note solid support"),
    ("very_high", "mid"): ("bright_with_work", "but", "highlight the strength, acknowledge room to grow"),
    ("very_high", "low"): ("strong_contrast", "but", "celebrate the win, honestly name the gap"),
    ("very_high", "very_low"): ("stark_divide", "but", "anchor to the strength, be direct about the struggle"),

    # high (60-80) + X
    ("high", "very_high"): ("solid_with_spark", "and", "both positive, let the stronger shine"),
    ("high", "high"): ("reliable_bond", "and", "steady, dependable connection"),
    ("high", "mid"): ("mostly_positive", "but", "good foundation, one area needs attention"),
    ("high", "low"): ("partial_fit", "but", "acknowledge what works, name the weak spot"),
    ("high", "very_low"): ("uneven_match", "but", "hold onto the good, be real about the hard"),

    # mid (40-60) + X
    ("mid", "very_high"): ("hidden_gem", "but", "name the average, pivot to the bright spot"),
    ("mid", "high"): ("potential_exists", "but", "challenges present, foundation exists"),
    ("mid", "mid"): ("neutral_ground", "and", "neither great nor terrible, effort-dependent"),
    ("mid", "low"): ("uphill_road", "and", "honest about challenges, suggest patience"),
    ("mid", "very_low"): ("heavy_lift", "and", "validate the strain, focus on boundaries"),

    # low (20-40) + X
    ("low", "very_high"): ("lifeline_present", "but", "acknowledge the difficulty, find the lifeline"),
    ("low", "high"): ("some_hope", "but", "name the friction, point to what works"),
    ("low", "mid"): ("mostly_struggling", "and", "validate the effort, suggest realistic expectations"),
    ("low", "low"): ("rough_terrain", "and", "honest about friction, both need work"),
    ("low", "very_low"): ("very_hard", "and", "be direct about difficulty, focus on self-care"),

    # very_low (0-20) + X
    ("very_low", "very_high"): ("extreme_contrast", "but", "one bright light in the dark, name both"),
    ("very_low", "high"): ("glimmer_exists", "but", "mostly struggling, but something works"),
    ("very_low", "mid"): ("largely_draining", "and", "honest about the toll, suggest boundaries"),
    ("very_low", "low"): ("very_rough", "and", "validate how hard this is, protect yourself"),
    ("very_low", "very_low"): ("fundamental_mismatch", "and", "be honest about friction, prioritize self-protection"),
}
```

---

## Label Content (Expert Proposal)

### Overall Compatibility
| Range | Label | Guidance |
|-------|-------|----------|
| 0-20 | Volatile | Treat as intense and draining; name volatility, focus on boundaries and self-protection. |
| 20-40 | Rocky | Acknowledge real connection mixed with frequent bumps; talk about patience. |
| 40-60 | Mixed | Could tilt closer or looser depending on how they both show up. |
| 60-80 | Solid | Generally healthy, dependable bond; encourage investing time while naming weak spots. |
| 80-100 | Seamless | Natural fit where things click; invite them to enjoy it with healthy boundaries. |

### Romantic Categories

**Emotional Connection**
| Range | Label | Guidance |
|-------|-------|----------|
| 0-20 | Shut Off | Struggle to reach each other; validate loneliness, warn against expecting deep support. |
| 20-40 | Mismatched | Feel things on different wavelengths; may stay uneven. |
| 40-60 | Surface-Deep | Some depth but not automatic; grows if both make effort. |
| 60-80 | Warm | Generally "get" each other; encourage honest sharing. |
| 80-100 | Soul-Level | Strong resonance; describe feeling deeply seen. |

**Communication**
| Range | Label | Guidance |
|-------|-------|----------|
| 0-20 | Combustible | Words easily explode; stress slowing down, not texting in anger. |
| 20-40 | Crooked | Messages bend; suggest asking more questions and repeating back. |
| 40-60 | Hit-or-Miss | Sometimes sync, sometimes don't; effort matters more than fate. |
| 60-80 | Clear | Usually get each other; encourage honest talks. |
| 80-100 | Telepathic | Almost mind-reading; highlight deep talks and shared humor. |

**Attraction**
| Range | Label | Guidance |
|-------|-------|----------|
| 0-20 | Flat | Chemistry weak or one-sided; may feel more like friendship. |
| 20-40 | Faint | Light pull but not intense; talk about slow burn or values over heat. |
| 40-60 | Warm | Attraction there but not all-consuming; can grow with trust. |
| 60-80 | Magnetic | Clear mutual pull; encourage owning it while staying grounded. |
| 80-100 | Blazing | Very strong spark; balance passion with emotional safety. |

**Shared Values**
| Range | Label | Guidance |
|-------|-------|----------|
| 0-20 | Cross-Wired | Core beliefs collide; serious long-term risk. |
| 20-40 | Split | Match on some things, clash on others; talk about non-negotiables. |
| 40-60 | Side-by-Side | Not identical but not opposites; how you live it out matters. |
| 60-80 | Aligned | Want similar things; emphasize stability this brings. |
| 80-100 | Same Page | Strong value sync; "building the same kind of life." |

**Long-Term Potential**
| Range | Label | Guidance |
|-------|-------|----------|
| 0-20 | Short-Chapter | Likely meaningful phase, not forever; can still matter without lasting. |
| 20-40 | Fragile | Could last but only with major work; name risk clearly. |
| 40-60 | Unwritten | Future very open; depends on choices both make. |
| 60-80 | Steady Path | Good foundations for going the distance if nurtured. |
| 80-100 | Endgame | Strong long-term signature; genuine lasting potential. |

**Growth Together**
| Range | Label | Guidance |
|-------|-------|----------|
| 0-20 | Draining | May learn but at high emotional cost; ask if price feels worth it. |
| 20-40 | Rough Mirror | Teach through friction; talk about patterns reflected back. |
| 40-60 | Neutral | Doesn't block or supercharge growth; more about comfort. |
| 60-80 | Expanding | Help each other stretch gently out of comfort zones. |
| 80-100 | Transforming | Deep catalyst; can change who you are, for real. |

### Friendship Categories

**Emotional (distinct from romantic)**
| Range | Label | Guidance |
|-------|-------|----------|
| 0-20 | Surface Only | Hard to go deep; may stay casual. |
| 20-40 | Arms Length | Some emotional distance; may not be your "vent friend." |
| 40-60 | Growing | Getting closer over time; trust builds with consistency. |
| 60-80 | Open | Can share real feelings; safe to be vulnerable. |
| 80-100 | Soul Friends | Deep emotional understanding; they truly get you. |

**Communication (distinct from romantic)**
| Range | Label | Guidance |
|-------|-------|----------|
| 0-20 | Static | Messages often get lost; keep conversations simple. |
| 20-40 | Choppy | Takes effort; check in to make sure you're on same page. |
| 40-60 | Workable | Can communicate fine with some patience. |
| 60-80 | Easy | Conversations flow naturally; you understand each other's style. |
| 80-100 | Effortless | Talk for hours without trying; great banter and real talk. |

**Fun & Adventure**
| Range | Label | Guidance |
|-------|-------|----------|
| 0-20 | Dry | Hanging out may feel flat; might not be your "fun friend." |
| 20-40 | Sporadic | Fun happens but not reliably; low-pressure plans. |
| 40-60 | Chill | Can have good time in the right mood. |
| 60-80 | Lively | Bring out each other's playfulness; good for regular hangouts. |
| 80-100 | Wild Card | Big adventure energy; shared stories, spontaneous plans. |

**Loyalty & Support**
| Range | Label | Guidance |
|-------|-------|----------|
| 0-20 | Flimsy | May disappear when things get real; warn about leaning too hard. |
| 20-40 | Patchy | Support comes in waves; watch actions, not just words. |
| 40-60 | Decent | Can show up, but not as primary lifeline. |
| 60-80 | Steady | Usually there when it matters; invite mutual showing up. |
| 80-100 | Ride-or-Die | Very strong loyalty; core person in their corner. |

**Shared Interests**
| Range | Label | Guidance |
|-------|-------|----------|
| 0-20 | Separate Worlds | Live in different universes; more occasional than daily. |
| 20-40 | Parallel | Some overlap, mostly different lanes; curiosity about hobbies. |
| 40-60 | Crossroads | Enough shared ground to build on. |
| 60-80 | In Sync | Plenty in common; good for frequent plans. |
| 80-100 | Same Obsession | Deep overlap; great for geeking out together. |

### Coworker Categories

**Communication (distinct from romantic/friendship)**
| Range | Label | Guidance |
|-------|-------|----------|
| 0-20 | Blocked | Professional communication strained; use email and documentation. |
| 20-40 | Formal | Keep it professional and structured; small talk may fall flat. |
| 40-60 | Professional | Standard work communication; neither great nor problematic. |
| 60-80 | Productive | Ideas flow well in meetings; good brainstorming partner. |
| 80-100 | In Sync | Excellent professional rapport; anticipate each other's thinking. |

**Collaboration**
| Range | Label | Guidance |
|-------|-------|----------|
| 0-20 | Clash | Teamwork very hard; clear roles and minimal shared projects. |
| 20-40 | Clunky | Can collaborate but feels awkward; extra structure needed. |
| 40-60 | Functional | Collaboration fine with some planning. |
| 60-80 | Smooth | Team up well; good for shared tasks. |
| 80-100 | Dream Team | Very strong synergy; big project potential. |

**Reliability**
| Range | Label | Guidance |
|-------|-------|----------|
| 0-20 | Unsteady | Likely can't rely on them; suggest backups. |
| 20-40 | Spotty | Sometimes solid, sometimes not; clear deadlines help. |
| 40-60 | Adequate | Usually fine for normal work. |
| 60-80 | Trustworthy | Can mostly count on them; good for important tasks. |
| 80-100 | Rock-Solid | Very dependable; safe for critical pieces. |

**Ambition Alignment**
| Range | Label | Guidance |
|-------|-------|----------|
| 0-20 | Misaligned | Want very different things; priorities may clash. |
| 20-40 | Uneven | One pushes harder; calibrate expectations. |
| 40-60 | Parallel | Not identical but not in conflict; can coexist. |
| 60-80 | Driven Together | Motivate each other; good for shared goals. |
| 80-100 | Power Pair | Big shared drive; potential for major moves. |

**Power Dynamics**
| Range | Label | Guidance |
|-------|-------|----------|
| 0-20 | Lopsided | One tends to dominate; stress boundaries and clarity. |
| 20-40 | Tilted | Power leans one way; notice when shrinking or over-functioning. |
| 40-60 | Shifting | Balance changes by context; invite awareness. |
| 60-80 | Balanced | Power generally mutual; good for collaboration. |
| 80-100 | Empowering | Uplift each other's authority; great for co-leading. |

---

## Files to Modify

### 1. `functions/compatibility.py` (models)

**Add new model:**
```python
class DrivingAspect(BaseModel):
    """Simplified aspect for iOS display with human-readable meanings."""
    aspect_id: str = Field(description="Reference to full aspect in aspects list")
    user_planet: str = Field(description="Your planet (e.g., 'Moon')")
    their_planet: str = Field(description="Their planet (e.g., 'Venus')")
    aspect_type: str = Field(description="trine, square, etc.")
    is_harmonious: bool
    summary: str = Field(description="Human-readable: 'Your emotional needs flow with their love style'")
```

**Extend CompatibilityCategory:**
```python
class CompatibilityCategory(BaseModel):
    # EXISTING (keep all)
    id: str
    name: str
    score: int
    insight: Optional[str]
    aspect_ids: list[str]

    # NEW
    label: str = Field(description="Band label (e.g., 'Warm', 'Combustible')")
    description: str = Field(description="What this category measures (for iOS display)")
    driving_aspects: list[DrivingAspect] = Field(default_factory=list, description="Top aspects with meanings")
```

### 2. `functions/compatibility/labels.py` (new)

```python
from typing import TypedDict

class BandDef(TypedDict):
    id: str
    min: int
    max: int

class HeadlineGuidance(TypedDict):
    pattern: str
    conjunction: str
    tone: str
    top_category: dict
    bottom_category: dict
    instruction: str

def get_band_for_score(score: float, bands: list[BandDef]) -> str:
    """Given score and band definitions, return band ID."""
    ...

def load_category_labels(mode: str, category_id: str) -> dict:
    """Load JSON config for a category."""
    ...

def get_category_label(mode: str, category_id: str, score: float) -> str:
    """Get the label (e.g., 'Warm') for a score."""
    ...

def get_category_guidance(mode: str, category_id: str, score: float) -> str:
    """Get the LLM guidance string for a score band."""
    ...

def get_category_description(mode: str, category_id: str) -> str:
    """Get the category description from metadata."""
    ...

def get_planet_meaning(mode: str, category_id: str, planet: str) -> str:
    """Get planet meaning from astrological_basis.planet_meanings."""
    ...

def generate_driving_aspect_summary(
    user_planet: str,
    their_planet: str,
    aspect_type: str,
    is_harmonious: bool,
    mode: str,
    category_id: str,
) -> str:
    """Generate human-readable summary using planet_meanings from JSON."""
    ...

def get_compat_band(score: float) -> str:
    """Map score to band ID for matrix lookup (very_low/low/mid/high/very_high)."""
    ...

def generate_compat_headline_guidance(categories: list) -> HeadlineGuidance:
    """Generate headline guidance based on top and bottom categories."""
    ...
```

### 3. `functions/llm.py` (~lines 1362-1508)

**Update prompt to include:**
1. Overall guidance matrix result
2. Per-category labels and guidance
3. Driving aspect summaries for each category

**New prompt structure:**
```
[COMPATIBILITY SNAPSHOT]

Overall: 62 (Solid)
- Use tone: "generally healthy, dependable bond with some weak spots."

TOP FOCUS AREAS:
1) Emotional Connection - score 81, band "very_high", label "Soul-Level"
   - Guidance: Strong emotional resonance; describe feeling deeply seen, but remind them to handle intensity with care.
   - Why:
     - Your Moon trine their Venus - Your emotional needs flow easily with their way of loving.
     - Your Neptune conjunct their Moon - You tap into each other's dreams and vulnerabilities.

2) Communication - score 34, band "low", label "Crooked"
   - Guidance: Messages bend on the way through; suggest asking more questions and not assuming tone.
   - Why:
     - Your Mercury square their Mars - Words can hit like a spark and start fights.

[HEADLINE PATTERN]
- Band combo: ("very_high", "low") -> "strong_contrast"
- Conjunction: "but"
- Tone: "celebrate the win, honestly name the gap"

[INSTRUCTION]
When you write about this connection, combine Emotional Connection and Communication in one main paragraph. Use "but" to pivot from Soul-Level emotion to Crooked communication. Name the strength first, then the challenge, then a practical path through.

CATEGORY SCORES (all categories):
- emotional (Emotional Connection): 81
  Label: Soul-Level
  Description: How deeply you connect emotionally
  Guidance: Strong emotional resonance; describe feeling deeply seen, handle intensity with care.

- communication (Communication): 34
  Label: Crooked
  Description: How well you understand each other's words and meaning
  Guidance: Messages bend on the way through; suggest asking more questions and repeating back.

... (remaining categories)
```

### 4. `functions/generate_api_docs.py`

Run after model changes to update `docs/PUBLIC_API_GENERATED.md`.

---

## Implementation Steps (Minimal Thrash Order)

### Phase 1: Labels JSON + Loader
1. Create directory structure: `functions/compatibility/labels/{romantic,friendship,coworker}/`
2. Create `functions/compatibility/__init__.py`
3. Create `overall.json` + a few romantic category files (emotional, communication, attraction)
4. Create `functions/compatibility/labels.py` with core functions:
   - `get_band_for_score()`, `load_category_labels()`, `get_category_label()`, `get_category_guidance()`
5. Add unit tests: given score -> band -> label/guidance

### Phase 2: Extend Models
6. Add `DrivingAspect` model to `functions/compatibility.py`
7. Add new fields to `CompatibilityCategory`: `label`, `description`, `driving_aspects`
8. Populate these in existing compatibility calculator (no LLM changes yet)

### Phase 3: Headline Guidance
9. Add `generate_compat_headline_guidance()` to `labels.py`
10. Implement `COMPAT_HEADLINE_MATRIX` (25-case)
11. Unit tests for top/bottom category combinations

### Phase 4: Wire into LLM
12. Import from `compatibility.labels` in `llm.py`
13. Add new fields to prompt (no behavior change at first)
14. Add explicit instructions (use pattern.conjunction/tone)
15. Update `generate_driving_aspect_summary()` to use `planet_meanings` from JSON

### Phase 5: Finalize
16. Complete remaining JSON files (friendship, coworker categories)
17. Run `uv run python functions/generate_api_docs.py`
18. Run full test suite + type check
19. Manual test with `DEBUG_LLM=1` to inspect prompts

---

## Testing

```bash
uv run pytest functions/tests/unit/ -v
uv run pytest functions/tests/integration/ -v
uv run mypy functions/ --ignore-missing-imports --exclude venv
DEBUG_LLM=1 uv run python -c "..." # Inspect prompts
```
