# Astrometer State Labels Guide

Complete documentation for the astrometer state label system, including design principles, implementation, and maintenance workflows.

## Overview

The astrometer system uses **345 state labels** across 23 meters (17 individual + 6 groups) to describe cosmic energy states. Each meter has 15 labels arranged in a 5×3 grid:

- **5 intensity levels**: quiet, mild, moderate, high, extreme
- **3 quality types**: challenging, mixed, harmonious

**Critical Constraint**: All labels must be **2 words maximum** due to iOS UI space limitations.

## Brand Voice Principles

### Core Guidelines

Labels must convey **cosmic energy available** (not emotional states) following these principles:

1. **Energy-Focused**: Describe what energy is present, not how the user feels
2. **Empowering**: Frame challenges as growth opportunities, never victim language
3. **Direct & Relatable**: Talk like texting a friend (8th grade reading level)
4. **No Clinical Terms**: Avoid "crisis," "chaos," "burnout," "trauma"
5. **No Mystical Jargon**: Avoid "psychic," "soul," "ego death," "quantum"
6. **No Drama**: Avoid "profound," "brilliant," "total," "absolute"
7. **Actionable**: Imply movement, agency, and possibility

### Label Type Requirements

#### Challenging Labels (Growth Edge)
**Purpose**: Frame difficulties as development opportunities

✅ **Do**:
- Imply movement/progress ("Building discipline," "Finding ground")
- Show intentional choice ("Protecting heart," "Setting boundaries")
- Frame as skill-building ("Gathering strength," "Learning trust")

❌ **Don't**:
- Use victim language ("Stuck," "Lost," "Broken")
- Sound helpless ("Can't focus," "No motivation")
- Clinical terms ("Crisis," "Burnout," "Chaos")

**Examples**:
- ❌ "Foggy thinking" → ✅ "Clearing fog"
- ❌ "Running low" → ✅ "Building reserves"
- ❌ "Words stuck" → ✅ "Finding voice"

#### Mixed Labels (Integration)
**Purpose**: Show both sides working together

✅ **Do**:
- Normalize complexity ("Complex feelings," "Mixed signals")
- Show active process ("Active processing," "Working through")
- Imply growth ("Soft shifts," "Gentle exploration")

❌ **Don't**:
- Sound confused ("All over the place")
- Oversell positives ("Quantum leap")
- Ignore challenges ("Everything's fine")

**Examples**:
- ✅ "Busy thoughts" (not scattered - active)
- ✅ "Scattered brilliance" (creative chaos reframed)
- ✅ "Active evolution" (process happening)

#### Harmonious Labels (Flow State)
**Purpose**: Celebrate ease and natural alignment

✅ **Do**:
- Use strong positive words ("Crystal clear," "Pure flow")
- Make it aspirational ("Peak energy," "Deep harmony")
- Celebrate the ease ("Easy warmth," "Gentle focus")

❌ **Don't**:
- Oversell with drama ("Profound," "Blissful," "Total")
- Use mystical terms ("Cosmic union," "Divine flow")
- Sound fake-positive ("Perfect everything")

**Examples**:
- ✅ "Crystal clear" (specific + positive)
- ✅ "Pure flow" (natural + effortless)
- ✅ "Deep harmony" (substantial + real)

## Empowering Vocabulary Bank

### Growth/Learning Patterns

**Building [X]**: Capacity-building, skill development
- Building foundation, Building momentum, Building discipline
- Building reserves, Building strength, Building focus

**Gathering [X]**: Accumulating resources, preparing
- Gathering strength, Gathering focus, Gathering force

**Finding [X]**: Discovery, search with direction
- Finding ground, Finding voice, Finding rhythm
- Finding clarity, Finding direction

**Creating [X]**: Active agency, making opportunities
- Creating space, Creating timing, Creating paths

**Working [X]**: Active integration, effort with purpose
- Working through, Working edges, Working deeply

**Learning [X]**: Skill acquisition, growth edge
- Learning trust, Learning boundaries

### Flow/Harmony Patterns

**Pure [X]**: Natural, effortless, authentic
- Pure flow, Pure connection

**Deep [X]**: Substantial, meaningful, profound without drama
- Deep focus, Deep unity, Deep harmony, Deep connection
- Deep empathy, Deep love, Deep processing

**Peak [X]**: Optimal, maximum positive
- Peak energy, Peak performance, Peak clarity, Peak action

**Crystal/Laser [X]**: Sharp, precise, excellent
- Crystal clear, Laser focus

**Flowing [X]**: Natural movement, ease
- Flowing exchange, Flowing love

### Intentional Rest Patterns

**Quiet [X]**: Restful, not empty
- Quiet building, Quiet integration, Quiet exploration

**Solo [X]**: Intentional solitude, strength
- Solo strength, Solo recharge, Solo path

**Peaceful [X]**: Calm with purpose
- Peaceful pause, Peaceful rest, Peaceful calm, Peaceful silence

**Conserving [X]**: Strategic rest
- Conserving energy

**Inner [X]**: Internal work, not external action
- Inner searching, Inner exploration

## 2-Word Conversion Patterns

When converting 3+ word labels to 2 empowering words:

### Pattern 1: [Action Verb] + [Noun]
- "Processing hard stuff" → "Deep processing"
- "Building patience" → "Patient building"
- "Need deep rest" → "Deep restoration"
- "Finding the way" → "Gathering force"

### Pattern 2: [Adjective] + [Noun]
- "Mind needs rest" → "Mental restoration"
- "Heart's quiet" → "Peaceful heart"
- "Wild thoughts" → "Racing creativity"
- "All the feels" → "Emotional overflow"

### Pattern 3: [Gerund] + [Adverb/Adjective]
- "All over" → "Scattered brilliance"
- "Slow progress" → "Steady building"
- "Working through it" → "Active processing"

### Pattern 4: Reframe Negative → Empowering
- "Low and heavy" → "Deep restoration" (necessary rest)
- "Off timing" → "Creating timing" (agency)
- "Stuck" → "Breaking through" (movement)
- "Can't focus" → "Building discipline" (skill development)
- "Running low" → "Building reserves" (capacity-building)

## Label Rotation Strategy (Future Enhancement)

### Why Rotation Matters

Users see the same intensity/quality combinations repeatedly. Rotation prevents:
1. **Linguistic fatigue**: Seeing "Working through" 50 times
2. **Predictability**: Labels lose impact when expected
3. **Oversimplification**: Energy states are nuanced, not fixed

### Implementation Approach

**File Structure**:
```json
"experience_labels": {
  "combined": {
    "moderate": {
      "challenging": [
        "Deep processing",      // Primary (60%)
        "Working through",      // Alternate 1 (25%)
        "Active integration"    // Alternate 2 (15%)
      ]
    }
  }
}
```

**Selection Logic**:
```python
def select_label(labels: list[str], user_id: str, date: str) -> str:
    """Deterministic rotation based on user_id + date hash."""
    seed = hash(f"{user_id}:{date}") % len(labels)
    return labels[seed]
```

**Rotation Guidelines**:
- **Keep 1-3 variations** per label (not more)
- **Variations must be semantically equivalent** (same core meaning)
- **Prioritize primary label** (show it most often via weighting)
- **Test combinations** to avoid awkward patterns

**Examples**:
```
Moderate/Challenging Rotations:
- "Deep processing" (primary - shows 60% of time)
- "Working through" (alternate - shows 25% of time)
- "Active integration" (alternate - shows 15% of time)

High/Harmonious Rotations:
- "Peak energy" (primary)
- "Strong drive" (alternate)
- "Maximum force" (alternate)
```

**Next Steps**:
1. Identify 10-15 high-frequency labels for rotation
2. Create 2-3 semantic variations per label
3. Update JSON schema to support arrays
4. Implement deterministic selection algorithm
5. A/B test rotation vs fixed labels for engagement

## Tools & Scripts

### Label Management Scripts

All scripts located in `functions/astrometers/`:

#### `show_group_labels.py`
**Purpose**: Display all group state labels in formatted tables and check for quality issues

```bash
uv run python functions/astrometers/show_group_labels.py
```

**Output**:
- Tables showing all 6 group labels (mind, emotions, body, spirit, growth, overall)
- Tables showing overall_intensity and overall_harmony labels
- Quality check showing:
  - Most common words across labels (identifies overuse)
  - Duplicate labels across groups (identifies redundancy)

**When to run**:
- After editing group labels
- When reviewing label distinctiveness
- Before finalizing label changes

**What to look for**:
- Words appearing >4 times may indicate overuse
- Same word starting multiple labels in same intensity/quality row (e.g., "Quiet processing", "Quiet seeking")
- Generic patterns repeated across groups without domain-specific context

#### `test_label_word_counts.py`
**Purpose**: Validate all labels are 2 words or less (UI constraint)

```bash
uv run python functions/astrometers/test_label_word_counts.py
```

**Output**:
- ✅ Success: "All 25 files passed! All labels are 2 words or less."
- ❌ Failure: Lists all labels exceeding 2 words with file locations

**When to run**:
- After any label edits
- Before committing label changes
- As part of CI/CD validation

#### `show_all_labels.py`
**Purpose**: Display all 345 labels in formatted tables for review

```bash
uv run python functions/astrometers/show_all_labels.py
```

**Output**: Rich-formatted tables showing:
- All 17 individual meters (color-coded by quality)
- All 6 group meters
- 15 labels per meter (5 intensities × 3 qualities)

**When to run**:
- Reviewing label changes
- QA before release
- Sharing with design/product teams
- Creating documentation

#### `show_meters.py`
**Purpose**: Display all meter configurations for astrological review

```bash
uv run python functions/astrometers/show_meters.py
```

**Output**: Shows for each meter:
- Natal planets tracked
- Transit planets tracked
- Key houses
- Aspect weights
- Planetary dignities

**When to run**:
- Reviewing astrological logic
- Before changing meter filters
- Validating meter configurations

### Calibration Scripts

Located in `functions/astrometers/calibration/`:

#### `calculate_historical_v2.py`
**Purpose**: Recalibrate normalization using empirical data

```bash
uv run python functions/astrometers/calibration/calculate_historical_v2.py
```

**What it does**:
- Calculates DTI/HQS scores across 1,000 diverse charts
- Analyzes 1,827 days (2020-01-01 to 2024-12-31)
- Generates ~31M calculations (1,000 charts × 1,827 days × 17 meters)
- Updates `calibration_constants.json` with empirical percentiles
- Outputs `historical_scores_v2.csv` (raw scores for analysis)
- Takes ~5-10 minutes

**CRITICAL**: Run this whenever you change meter configurations or filter logic.

#### `verify_percentile.py`
**Purpose**: Validate score distribution quality

```bash
uv run python functions/astrometers/calibration/verify_percentile.py
```

**What it does**:
- Verifies normalized scores follow proper statistical distribution
- Checks score 99 happens 1% of time (P99)
- Checks score >90 happens 10% of time (P90)
- Validates score 50 is median (P50)
- Takes ~30 seconds

**When to run**: After calibration to ensure normalization works correctly

#### `test_charts_stats_v2.py`
**Purpose**: Detect meter overlap/collision

```bash
uv run python functions/astrometers/test_charts_stats_v2.py
```

**What it does**:
- Tests 1,000 random charts
- Validates meters are distinct (measuring different things)
- Checks for unexpected correlations
- Takes ~2-3 minutes
- **Target**: All overlaps <6%

**When to run**: After calibration to ensure meters aren't too correlated

## File Structure

### Label Files

```
functions/astrometers/labels/
├── career.json                 # Individual meter labels
├── communication.json
├── connection.json
├── creativity.json
├── drive.json
├── focus.json
├── growth.json
├── inner_stability.json
├── intuition.json
├── love.json
├── mental_clarity.json
├── opportunities.json
├── purpose.json
├── sensitivity.json
├── social_life.json
├── vitality.json
├── wellness.json
└── groups/                     # Group meter labels (aggregates)
    ├── body.json               # Vitality + Drive + Wellness
    ├── emotions.json           # Love + Inner Stability + Sensitivity
    ├── growth.json             # Opportunities + Career + Growth + Social Life
    ├── mind.json               # Mental Clarity + Focus + Communication
    ├── spirit.json             # Purpose + Connection + Intuition + Creativity
    └── overall.json            # All meters combined
```

### Label JSON Schema

```json
{
  "_schema_version": "2.0",
  "_meter": "vitality",
  "_last_updated": "2025-01-06",
  "metadata": {
    "meter_id": "vitality",
    "display_name": "Vitality",
    "group": "body",
    "measures": "both"
  },
  "description": {
    "overview": "Brief description",
    "detailed": "Complete explanation",
    "keywords": ["energy", "stamina", "physical"]
  },
  "experience_labels": {
    "combined": {
      "quiet": {
        "challenging": "Building reserves",
        "mixed": "Soft stirrings",
        "harmonious": "Peaceful rest"
      },
      "mild": {
        "challenging": "Warming up",
        "mixed": "Gentle rise",
        "harmonious": "Gentle energy"
      },
      "moderate": {
        "challenging": "Building energy",
        "mixed": "Steady effort",
        "harmonious": "Strong stable"
      },
      "high": {
        "challenging": "Pushing hard",
        "mixed": "Powerful drive",
        "harmonious": "Peak performance"
      },
      "extreme": {
        "challenging": "Restoring vitality",
        "mixed": "Raw power",
        "harmonious": "Maximum energy"
      }
    }
  },
  "interpretation_guidelines": {
    "tone": "Direct and physical",
    "focus_when_high": "Emphasize action windows",
    "focus_when_low": "Emphasize rest and conservation",
    "focus_when_challenging": "Offer strategies",
    "avoid": ["Shaming low energy", "Toxic positivity"],
    "phrasing_examples": {
      "high_harmonious": "Your energy is peak today...",
      "moderate_mixed": "Energy requires effort today...",
      "low_challenging": "Energy is low - honor rest needs..."
    }
  }
}
```

## Maintenance Workflows

### Updating Individual Labels

1. **Edit JSON file** (`functions/astrometers/labels/[meter].json`)
2. **Run validation**: `uv run python functions/astrometers/test_label_word_counts.py`
3. **Review visually**: `uv run python functions/astrometers/show_all_labels.py`
4. **Test in context**: Generate sample horoscopes with new labels
5. **Commit changes**: Document reasoning in commit message

### Changing Meter Configurations

**CRITICAL**: Meter configuration changes require recalibration!

1. **Edit meter config** in `functions/astrometers/meters.py`
2. **Review astrological logic**: `uv run python functions/astrometers/show_meters.py`
3. **Recalibrate normalization**: `uv run python functions/astrometers/calibration/calculate_historical_v2.py` (~5-10 min)
4. **Verify distribution**: `uv run python functions/astrometers/calibration/verify_percentile.py` (~30 sec)
5. **Check meter overlap**: `uv run python functions/astrometers/calibration/test_charts_stats_v2.py` (~2-3 min)
6. **Update labels if needed**: Ensure labels match new energy signatures
7. **Commit all changes**: Include updated `calibration_constants.json`

### Quality Assurance Checklist

Before deploying label changes:

- [ ] All labels pass 2-word validation
- [ ] Labels follow empowering voice guidelines
- [ ] No clinical/mystical/dramatic terms
- [ ] Labels tested in live horoscope generation
- [ ] Visual review completed (show_all_labels.py)
- [ ] Changes documented in commit message
- [ ] Calibration constants up to date (if meters changed)

## Common Label Issues & Fixes

### Issue: Passive/Victim Language
**Problem**: "Stuck," "Lost," "Can't focus"
**Fix**: Reframe as active growth
- "Stuck" → "Breaking through"
- "Lost" → "Finding direction"
- "Can't focus" → "Building discipline"

### Issue: Clinical/Dramatic Terms
**Problem**: "Crisis," "Chaos," "Burnout," "Profound"
**Fix**: Use direct, relatable language
- "Emotional crisis" → "Breaking point"
- "Mental chaos" → "Can't think"
- "Burned out" → "Building reserves"
- "Profound unity" → "Deep unity"

### Issue: Mystical Jargon
**Problem**: "Psychic," "Soul," "Ego death," "Quantum"
**Fix**: Describe experience directly
- "Psychic connection" → "Deeply connected"
- "Ego death crisis" → "Really lost"
- "Quantum leap" → "Big shift"

### Issue: 3+ Word Labels
**Problem**: UI constraint violation
**Fix**: Apply conversion patterns
- "Need deep rest" → "Deep restoration"
- "Working through it" → "Active processing"
- "All the feels" → "Emotional overflow"

## Related Documentation

- **Astrometers Overview**: `docs/astrometers.md` - Complete system documentation
- **Brand Voice**: `functions/templates/horoscope/daily_static.j2` - Tone guidelines
- **Astrology Module**: `docs/ASTROLOGY_MODULE.md` - Chart calculation reference
- **Implementation Plan**: `docs/IMPLEMENTATION_PLAN.md` - Development roadmap

## Version History

- **v2.0** (2025-01-06): Complete empowering label revision
  - All 345 labels updated to 2 words max
  - Removed clinical/mystical/dramatic terms
  - Applied energy-focused empowering patterns
  - Added comprehensive documentation

- **v1.0** (2025-01-04): Initial label system
  - 23 meters with 15 labels each
  - Basic label structure established
  - Calibration system implemented
