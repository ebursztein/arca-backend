# Headline Generation System

This document explains how Arca generates daily notification headlines - the first touchpoint that pulls users into the app.

## Psychological Foundations

### The Digital Barnum Effect

Traditional astrology apps rely on the Forer/Barnum Effect - vague statements that feel personally meaningful. Arca evolves this into the **Digital Barnum Effect**: users input precise birth data (date, time, location) creating a psychological contract. They expect hyper-personalized insight in exchange for intimate data.

Headlines must signal they're derived from **specific planetary transits relative to the user's unique chart**, not generic horoscopes.

### Variable Ratio Reinforcement

Like slot machines, unpredictable feedback maintains engagement better than consistent praise. Arca uses a **contrastive formula** - acknowledging both strengths and challenges - to create tension without toxicity.

This avoids:
- **Toxic positivity** (constant praise = habituation = disengagement)
- **Rage baiting** (constant criticism = user feels attacked)

Instead: honest acknowledgment + path through = engagement + trust.

### Temporal Markers

The "eerie" quality of notifications - feeling like the app knows what you're experiencing right now - drives retention. Every headline includes **"today"** to simulate real-time awareness.

### Standalone Value

Headlines are not teasers ("Your horoscope is ready"). They deliver **complete, actionable thoughts** that resolve a micro-tension for the user.

---

## Three Voice Modes

Headlines rotate through three modes for variety. Mode selection is **deterministic** based on `hash(user_id + date)` - same user on same day always gets same mode.

### 1. Provocative

**Style:** Direct, honest snapshot with a way through. Uses their name.

**Formula:** `[Name], [honest state] today - [how to handle it].`

**Rules:**
- Start with their name
- State the honest situation (realistic, not harsh)
- Include "today" for temporality
- End with how to handle it (path through)
- No emoji
- Speak to the day's energy, not the user's worth

**Examples:**
- Positive: "Maya, your head's sharp today - don't waste it."
- Negative: "Maya, your gut feels off today - double-check before you act."
- Contrast: "Maya, your head's clear but your body's not today - think, don't push."

### 2. Personalized

**Style:** Names the transit behind the vibe. Uses "you/your".

**Formula:** `[Planet] is [doing X] today. [How you handle it].`

**Rules:**
- MUST name at least one planet (Mercury, Venus, Mars, Saturn, Neptune, etc.)
- For contrast patterns: use "but" to connect Planet 1's effect with Planet 2's
- Use "you" or "your" at least once
- Include "today" for temporality
- End with supportive guidance (path through)
- Do NOT use their name (that's provocative mode)
- No emoji
- Avoid astro jargon (no houses/aspects)

**Examples:**
- Positive: "Mercury's on your side today. Trust your thinking."
- Negative: "Neptune's blurring your instincts today. Take your time deciding."
- Contrast: "Saturn's pressing on your heart today, but Neptune keeps your instincts clear. Trust your gut."

### 3. Imperative

**Style:** Direct command with a soft landing. Starts with emoji.

**Formula:** `[emoji] [Action] today. [Supportive reason using you/your].`

**Rules:**
- Start with one emoji to soften the command
- Give a clear, simple action directive
- Include "today" for temporality
- Use "you" or "your" in the supportive reason
- Keep it punchy - max 10 words (excluding emoji)
- Do not mention specific planets (behavior-focused)

**Examples:**
- Positive: "✨ Decide today. Your clarity's here."
- Negative: "🛑 Slow down today. Your gut needs a beat."
- Contrast: "📝 Plan today. Save your energy to act later."

---

## Five Patterns

Headlines are classified into five patterns based on meter scores:

| Pattern | Condition | Conjunction |
|---------|-----------|-------------|
| `one_positive` | 1 meter, score >= 50 | n/a |
| `one_negative` | 1 meter, score < 50 | n/a |
| `two_positive` | 2 meters, both >= 50 | "and" |
| `two_negative` | 2 meters, both < 50 | "and" |
| `contrast` | 1 positive + 1 negative | "but" |

### Score Bands

Scores map to four bands using natural quartiles:

| Band | Score Range | Meaning |
|------|-------------|---------|
| `high` | 75-100 | Thriving |
| `mid_high` | 50-74 | Solid/positive |
| `mid_low` | 25-49 | Struggling/challenged |
| `low` | 0-24 | Depleted |

---

## Data Flow

### Input to LLM

The `HEADLINE GUIDANCE` section provides:

```
HEART: 43/100 (Tender)
  Driver: resilience
  Why: Saturn square natal Uranus

INSTINCTS: 57/100 (Tuned In)
  Driver: flow
  Why: Neptune square natal Neptune

Use "but" to connect both areas.

VOICE MODE: personalized
Style: Names the transit behind the vibe...
Formula: [Planet] is [doing X] today. [How you handle it].
Rules:
- MUST name at least one planet...
- For contrast patterns: use 'but'...
Example: Saturn's pressing on your heart today, but Neptune keeps your instincts clear. Trust your gut.
```

### Key Fields

- **Group** (HEART, INSTINCTS, etc.) - what area of life
- **Score** - 0-100, how that area is doing
- **Group label** (Tender, Tuned In) - human-readable state
- **Driver** - the specific meter causing this
- **Why** - the transit (planet + aspect) causing it
- **Conjunction** - "and" or "but" for two-meter headlines
- **Voice mode** - which style to use
- **Mode rules** - specific requirements for that mode
- **Example** - pattern-specific example to follow

---

## Implementation Files

| File | Purpose |
|------|---------|
| `functions/astrometers/labels/headline_examples.json` | Mode definitions, rules, and examples |
| `functions/astrometers/meters.py` | `generate_headline_guidance()`, `_get_headline_mode()`, `HEADLINE_MATRIX` |
| `functions/templates/horoscope/daily_dynamic.j2` | Passes headline guidance to LLM |
| `functions/templates/horoscope/daily_static.j2` | Field spec for `daily_theme_headline` |

---

## Testing

Run headline-specific tests:
```bash
uv run pytest functions/astrometers/tests/test_headline_generation.py -v
```

Tests cover:
- JSON structure validation
- Mode characteristic enforcement (name usage, planet references, emoji placement)
- Temporality ("today" in every example)
- Path through in negative examples
- Deterministic mode selection
- Pattern classification from scores

---

## Brand Voice Alignment

Headlines follow Arca's core voice principles from `templates/voice.md`:

1. **Genuine optimism** - acknowledge obstacles honestly, then show the path through
2. **No toxic positivity** - don't dismiss struggles
3. **No doom-and-gloom** - don't make things feel hopeless
4. **Actionable** - every headline implies or states what to do
5. **Conversational** - like texting a smart friend
6. **No mystical filler** - concrete, not flowery
7. **8th grade reading level** - clear and direct

The formula: **"The stars show this challenge" + "Here's the move"**
