# Future Work: Horoscope Prompt Enhancements

---

## 1. Dynamic Examples Based on User Context

### Overview
Generate prompt examples dynamically based on the user's actual sun sign and current meter values. This gives the LLM tighter guidance since the examples match their situation.

### Implementation Ideas
- In `llm.py`, before rendering template, generate 1-2 examples that match:
  - User's sun sign (e.g., if Gemini, example shows Gemini-specific framing)
  - Current meter pattern (e.g., if MIND is Flowing and BODY is Challenging, example shows that combo)
- Inject these into template context as `dynamic_examples`
- Template uses them in the SYNTHESIS EXAMPLES section

### Example Logic
```python
def generate_dynamic_example(sun_sign: str, meters: dict) -> str:
    strongest = max(meters, key=lambda k: meters[k].unified_score)
    weakest = min(meters, key=lambda k: meters[k].unified_score)

    # Generate example text matching their pattern
    return f"Your {strongest.lower()} is strong today - lean into it. Your {weakest.lower()} needs rest."
```

### Benefits
- LLM sees examples that match the exact scenario it's generating for
- Reduces hallucination / generic output
- Makes synthesis rule concrete, not abstract

---

## 2. Energy Mix Chart

### Overview
Visual chart showing how the user's energy is distributed across the 4 planet buckets. Users see at a glance where their energy is concentrated and how it's shifting over time.

### The 4 Buckets
1. **Personal** (Sun, Moon, Mercury, Venus, Mars) - Day-to-day vibe
2. **Social** (Jupiter, Saturn) - Growth & structure
3. **Transpersonal** (Uranus, Neptune, Pluto) - Deep transformation
4. **Points** (Nodes, Angles) - Life direction

### Chart Concepts
- **Radar/Spider chart** - 4 axes, shows shape of energy distribution
- **Stacked bar** - Today vs yesterday vs week ago, shows movement
- **Animated flow** - Energy "flowing" between buckets over time

### Backend Returns
```python
class EnergyMixChart(BaseModel):
    personal: float      # 0-100 intensity
    social: float
    transpersonal: float
    points: float
    dominant: str        # "personal", "social", etc.
    trend_direction: str # "inward", "outward", "stable"

# Example response
{
    "personal": 72,
    "social": 45,
    "transpersonal": 28,
    "points": 15,
    "dominant": "personal",
    "trend_direction": "inward"
}
```

### iOS renders the chart
- Backend sends the 4 values + metadata
- iOS draws radar chart or custom visualization
- Caption below: "Energy concentrated inward today"

### Benefits
- Visual > text for this kind of data
- Users instantly see their "shape" for the day
- Comparing shapes day-over-day shows movement

---

## 3. Generational Voice Variations

### Overview
Different generational voices for horoscope output. Currently shelved - using single direct voice.

## Gen Z Voice (1997-2012)
- Directness, cutting through BS, shorter, more casual
- Example for Flowing Mind + Challenging Body:
> "Your brain's on fire today - use it. Ideas are clicking, decisions feel obvious. Your body though? Running on empty. Think, plan, strategize - but skip anything physical. Let your mind carry the day."

- Example for All Turbulent:
> "Everything's in motion - nothing's broken, nothing's clicking. Hold steady day. Don't force decisions, don't expect breakthroughs. Stay flexible."

- Example for All Challenging:
> "Today is heavy. Your mind, heart, and body all want the same thing: rest. Don't push through. Cancel what you can. Recovery is the goal."

## Millennial Voice (1981-1996)
- More emotional processing, vulnerability, "we're in this together"
- Example for Flowing Mind + Challenging Body:
> "There's a clarity in your thinking today that feels rare. Your mind is cutting through noise that usually trips you up. But your body is telling a different story - it's tired, maybe more than you want to admit. Honor both: let your mind lead, give your body grace."

- Example for All Turbulent:
> "Things feel unsettled today, and that's okay. Nothing is falling apart, but nothing is quite landing either. This is a day to hold steady and trust that the pieces are rearranging themselves."

- Example for All Challenging:
> "Today is asking a lot of you, and honestly? You don't have a lot to give right now. That's not failure - that's information. The win today is taking care of yourself. Lower the bar and let that be enough."

## Implementation Notes
- Would need to pass `user_age_group` or `generation` to template context
- Could add conditional sections in prompt based on generation
- Consider A/B testing to see if generational voice improves engagement
