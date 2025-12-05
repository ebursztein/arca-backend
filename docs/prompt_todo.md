# Plan: Clean Up Daily Horoscope Prompt

## Deep Section-by-Section Analysis

---

### SECTION 1: Persona (voice.md lines 7-12)
**Purpose:** Establish the LLM's identity
**Current state:** 3 bullets defining who/what/not
**Relationship:** Sets up identity referenced by Core Philosophy
**Issues:** "What you're NOT" is defensive framing - could be tighter
**Verdict:** KEEP, minor tightening

---

### SECTION 2: Core Philosophy (voice.md lines 15-27)
**Purpose:** The emotional formula - honest + empowering + actionable
**Current state:** 3 bullets + formula + example + 2 prohibitions + heavy transit note
**Relationship:** This IS the brand. Everything else supports it.
**Issues:**
- The example (line 23) is good
- "Heavy transits" note (line 27) is important edge case
**Verdict:** KEEP as-is - this is the heart

---

### SECTION 3: Target Audience (voice.md lines 31-36)
**Purpose:** Define who we're writing for
**Current state:** Primary audience + generations + reading level + sentence length
**Issues:**
- "Generations" line references Gen Z/Millennials - but we're removing generational adaptability
- Reading level + sentence length could be in Language Rules
**Verdict:** REMOVE generation reference, keep primary audience, move language mechanics to Language Rules

---

### SECTION 4: Generational Adaptability (voice.md lines 40-57)
**Purpose:** Adapt voice by age group
**Current state:** Gen Z vs Millennial distinctions with 2 full examples
**Relationship:** CONFLICTS with uniform voice goal
**Issues:**
- You explicitly want to remove this
- The examples are good quality but shouldn't vary by generation
**Verdict:** DELETE ENTIRELY

---

### SECTION 5: Language Rules (voice.md lines 61-97)
**Purpose:** Specific language do's and don'ts
**Current state:** 6 sub-rules, each with examples

| Sub-rule | Purpose | Issues |
|----------|---------|--------|
| Prohibited Phrases | Blacklist | Good, keep |
| Active Voice | Experience-first framing | Good single example |
| Don't Echo Labels | Rephrase input | Example format weird (arrow notation) |
| Natural Language | How to use "energy/vibe/flow" | 3 examples, not bad/good format |
| No Math Language | Hide calculations | No example |
| No Jargon Without Translation | Translate astro mumbo jumbo | Good, reduce to 1 example |
| Show Don't Tell | Use data to explain WHY | 4 examples - reduce to 1 |

**Issues:**
- "Natural Language" has 3 bullets but no bad/good - inconsistent format
- Multiple examples where one would do
**Clarification on No Jargon vs Show Don't Tell:**
- **No Jargon** = Translate astro mumbo jumbo into plain language ("Saturn square Mars" -> "you're hitting a wall")
- **Show Don't Tell** = Use data to explain reasoning - leverage transits to explain WHY they feel something
- These are DIFFERENT. Keep both as separate rules.
**Verdict:** Keep No Jargon + Show Don't Tell separate. STANDARDIZE examples to 1 bad/good per rule.

---

### SECTION 6: Critical Prohibitions (voice.md lines 100-104)
**Purpose:** Hard rules - medical, AI mention, preachy
**Current state:** 3 NEVER bullets
**Issues:** None - clean and clear
**Verdict:** KEEP as-is

---

### SECTION 7: Style Rules (voice.md lines 108-112)
**Purpose:** General writing style
**Current state:** 3 numbered rules
**Relationship:** DUPLICATES with "Horoscope Style Rules" in daily_static.j2
**Issues:**
- "Lead with direct answer" = good
- "Frame challenges constructively" = REPEATS Core Philosophy
- "Keep it conversational" = vague
**Verdict:** MERGE with Horoscope Style Rules, remove redundancy with Core Philosophy

---

### SECTION 8: Understanding the Data (daily_static.j2 lines 10-19)
**Purpose:** Explain what the input data means
**Current state:** Score/State/Guidance explanation + OVERALL sets tone
**Issues:**
- Good - tells LLM to trust the State labels over raw numbers
- "Guidance" field tells you how to write about each state - follow it
**Verdict:** KEEP as-is - essential context for the reading

---

### SECTION 9: Horoscope Style Rules (daily_static.j2 lines 21-26)
**Purpose:** Horoscope-specific formatting
**Current state:** No emoji, use name once, sun sign specific, one concrete action
**Relationship:** Should merge with Style Rules from voice.md
**Issues:** Good rules, just in wrong place
**Verdict:** MERGE with voice.md Style Rules into single section

---

### SECTION 10: Logic & Prioritization (daily_static.j2 lines 30-68)
**Purpose:** 4 rules for how to process input data
**Current state:**
1. SUN SIGN FILTER - 3 sign examples
2. VOID OVERRIDE - moon offline handling
3. SPOTLIGHT RULE - featured connection
4. SYNTHESIS RULE - cross-reference meters

**Issues:**
- SUN SIGN FILTER has 3 inline examples (Gemini, Aries, Cancer) - should be 1
- SYNTHESIS RULE (lines 54-68) is redundant - the input data already tells you what to lead with and what to acknowledge
**Verdict:**
- SUN SIGN FILTER: reduce to 1 example
- VOID OVERRIDE: MAKE PROGRAMMATIC - move to Python code, remove from LLM prompt
- SPOTLIGHT: keep (tells you who to focus on)
- SYNTHESIS: DELETE ENTIRELY - input data already provides this guidance directly

---

### SECTION 11: LANGUAGE: BAD vs GOOD (daily_static.j2 lines 72-83)
**Purpose:** More bad/good examples
**Current state:** TABLE with 6 rows
**Relationship:** DUPLICATES Language Rules in voice.md
**Issues:**
- Why is this a separate section? Should be in Language Rules
- Table format is inconsistent with other examples
- 6 examples is overkill
**Verdict:** DELETE section. Move 2-3 best examples into Language Rules with standardized format.

---

### SECTION 12: SYNTHESIS EXAMPLES (daily_static.j2 lines 87-99)
**Purpose:** Show full output examples
**Current state:** 3 scenarios with mock outputs
**Issues:**
- These generic examples conflict with the specific guidance provided in each reading's input
- The input data tells you exactly what to lead with and acknowledge - no need for generic synthesis examples
**Verdict:** DELETE ENTIRELY - trust the guidance in each reading's input data

---

### SECTION 13: JSON FIELD SPECIFICATIONS (daily_static.j2 lines 103-181)
**Purpose:** Define each output field
**Current state:** 10 fields, each with constraints + examples

**PROBLEM: This is a mess.**

You're passing structured JSON input to the LLM and expecting JSON output. But the field specs are written like documentation with markdown formatting, JSON code blocks embedded in the prompt, etc. This is confusing because:
1. The LLM sees ```json code blocks IN the prompt - might think it's showing output format
2. Multiple examples per field
3. Duplicate rules (active voice)
4. No clear relationship between fields

**FIX: Replace with a clean relationship table (LLM perspective - no implementation details)**

| Field | What It Is (UX Context) | Relationship | Personalization | What Makes It Unique |
|-------|-------------------------|--------------|-----------------|---------------------|
| `daily_theme_headline` | NOTIFICATION - what pulls them in | SETS the day's tone | Use name + main transit | Max 12 words |
| `daily_overview` | MAIN HOROSCOPE when they open app | EXPANDS on headline | Name once, cite main transit | 60-80 words, the core reading |
| `technical_analysis` | Astro explanation | BACKS UP overview | Transit-focused | Names planet aspects directly |
| `actionable_advice.do` | One micro-action | LEVERAGES strongest meter | Speak to their sun sign | Aligned with day's strength |
| `actionable_advice.dont` | One boundary | PROTECTS weakest meter | Speak to their sun sign | Aligned with day's challenge |
| `actionable_advice.reflect_on` | One question | OPENS possibility | Personal to their situation | Forward-looking |
| `mind_interpretation` | Mental state | Expands on MIND meter | Cite the Why transit | Weave into personal narrative |
| `heart_interpretation` | Emotional state | Expands on HEART meter | Cite the Why transit | Weave into personal narrative |
| `body_interpretation` | Physical state | Expands on BODY meter | Cite the Why transit | Weave into personal narrative |
| `instincts_interpretation` | Intuition state | Expands on INSTINCTS meter | Cite the Why transit | Weave into personal narrative |
| `growth_interpretation` | Momentum state | Expands on GROWTH meter | Cite the Why transit | Weave into personal narrative |
| `energy_rhythm` | Day timing guidance | Based on Moon position | Practical for their day | Helps plan WHEN to act |
| `relationship_weather` | Connection guidance | Based on SPOTLIGHT person + HEART state | Reference connection by name | Only field about other people |
| `collective_energy` | Shared experience | Based on outer planets | Validates they're not alone | Everyone feeling this |
| `look_ahead_preview` | Week preview | Based on upcoming transits | Give them hope | Something to look forward to |
| `follow_up_questions` | 5 simple questions | Prompts reflection | Personal, direct | No astro jargon |

**Current Issues:**
- JSON code blocks in examples (actionable_advice, follow_up_questions) - REMOVE
- Multiple examples per field - REDUCE to 1 each
- "Use active voice" repeated - REMOVE (already global rule)
- Headline conjunction logic duplicated - REMOVE (input data already specifies this)

**Verdict:**
- Replace current field specs with relationship table above
- Each field gets ONE example (as a string value, not JSON block)
- Remove all duplicate instructions

---

## Summary of Problems

1. **Duplication:** Active voice said 3 times. Style rules in 2 places. Bad/good examples in 2 places.
2. **Conflict:** Synthesis Rule + Synthesis Examples redundant with input data guidance - DELETE both
3. **Format inconsistency:** Some examples are tables, some are bullets, some are JSON blocks
4. **Generational section:** To be removed (uniform voice)
5. **JSON blocks in prompt:** Confusing - looks like output format but it's examples - REMOVE all
6. **Too many examples:** Multiple examples per point when 1 would do
7. **Field specs lack context:** No clear relationship between fields - FIX with relationship table
8. **Missing "Be Actionable" rule:** Core to the voice but not explicitly stated

---

## Proposed New Structure

```
# ARCA VOICE
├── Persona (who you are as the reader)
├── Core Philosophy (honest + empowering + actionable formula)
├── Target Audience (who you're reading for)
├── Language Rules
│   ├── Active Voice - lead with their experience
│   ├── No Mystical Filler - be direct
│   ├── No Jargon - translate astro mumbo jumbo
│   ├── Show Don't Tell - explain WHY using the transits
│   ├── Don't Echo Labels - rephrase, don't copy
│   ├── No Math Language - hide the calculations
│   ├── Natural Language - how to use energy/vibe/flow
│   └── Be Actionable - concrete moves, not vague guidance
├── Style
│   ├── Lead with direct answer
│   ├── Use name once
│   ├── Be sun-sign specific
│   ├── One concrete action
│   └── No emojis
└── Critical Prohibitions

# DAILY HOROSCOPE READING
├── Understanding the Input (how to read the data you're given)
├── Logic Rules (only 2 - VOID is now programmatic)
│   ├── SUN SIGN FILTER - acknowledge their sign
│   └── SPOTLIGHT - who to focus on
├── Field Specifications (what goes where)
│   - Relationship table showing how fields connect
│   - ONE example per field
└── Output Format
```

---

## Files to Modify

1. **`functions/templates/voice.md`** - Voice and language rules
2. **`functions/templates/horoscope/daily_static.j2`** - Horoscope-specific rules and field specs
3. **`functions/templates/horoscope/daily_dynamic.j2`** - Clean up output format to be tidier
4. **`functions/llm.py`** - Add void-of-course programmatic handling (modify actionable_advice guidance when moon is VoC)

---

## Additional Changes

### Clean up daily_dynamic.j2 output
Current output is messy. Make it cleaner and more scannable for the LLM:
- Group related data together
- Use consistent formatting
- Remove redundant labels

### Make VOID OVERRIDE programmatic
The "Void of Course" moon rule should NOT be an LLM instruction. Instead:
- Detect void-of-course in Python code
- When active, programmatically modify the actionable_advice guidance in the input data
- Remove VOID OVERRIDE from the LLM prompt entirely
- This reduces LLM cognitive load and ensures consistent behavior

**Implementation:**
- In the code that builds the prompt input, check if moon is void-of-course
- If yes, inject specific guidance into the actionable_advice section of the input:
  - `do` guidance: focus on rest, reflection, editing, completing
  - `dont` guidance: avoid starting new things, launching initiatives
- The LLM just follows the guidance it receives - no special rule needed

---

## Verification

```bash
DEBUG_PROMPT=1 uv run pytest functions/tests/e2e/test_03_daily_horoscope.py -v -s
```
Review `functions/debug_prompt.txt` for:
- No generational references
- No duplicate rules
- No JSON code blocks in examples
- Single example per rule
- Synthesis examples removed
- Check void of the course is handled programmatically
- the section are properly formatted and numbered
