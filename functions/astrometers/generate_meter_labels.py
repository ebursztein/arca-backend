#!/usr/bin/env python3
"""
Generate individual JSON files for each astrometer with experience labels.

Creates 23 separate JSON files (one per meter) containing:
- Meter metadata
- Experience labels for each intensity/harmony combination
- Super group interpretations

Usage:
    python generate_meter_labels.py

Output:
    functions/astrometers/labels/*.json (23 files)
"""

import json
import os
from typing import Dict, List
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from hierarchy import Meter, MeterGroup, SuperGroup, HIERARCHY, get_group, get_super_group
from constants import (
    INTENSITY_QUIET_THRESHOLD,
    INTENSITY_MILD_THRESHOLD,
    INTENSITY_MODERATE_THRESHOLD,
    INTENSITY_HIGH_THRESHOLD,
    HARMONY_CHALLENGING_THRESHOLD,
    HARMONY_HARMONIOUS_THRESHOLD
)

# Import Gemini
from google import genai
from google.genai import types

# Load environment variables
load_dotenv()


# =============================================================================
# Pydantic Models for Structured Output
# =============================================================================

class IntensityLabels(BaseModel):
    """Labels for intensity-only dimension (5 levels)."""
    quiet: str = Field(description="Max 2 words describing quiet/minimal activity state")
    mild: str = Field(description="Max 2 words describing mild/gentle activity state")
    moderate: str = Field(description="Max 2 words describing moderate/notable activity state")
    high: str = Field(description="Max 2 words describing high/strong activity state")
    extreme: str = Field(description="Max 2 words describing extreme/intense activity state")


class HarmonyLabels(BaseModel):
    """Labels for harmony-only dimension (3 levels)."""
    challenging: str = Field(description="Max 2 words describing difficult/friction state")
    mixed: str = Field(description="Max 2 words describing mixed/neutral state")
    harmonious: str = Field(description="Max 2 words describing supportive/flowing state")


class CombinedLabels(BaseModel):
    """Labels for combined intensity+harmony (5x3 nested)."""
    quiet: HarmonyLabels
    mild: HarmonyLabels
    moderate: HarmonyLabels
    high: HarmonyLabels
    extreme: HarmonyLabels


class ExperienceLabels(BaseModel):
    """All three label structures."""
    intensity_only: IntensityLabels
    harmony_only: HarmonyLabels
    combined: CombinedLabels


class AdviceTemplates(BaseModel):
    """Advice templates for each intensity+harmony combination."""
    quiet: HarmonyLabels
    mild: HarmonyLabels
    moderate: HarmonyLabels
    high: HarmonyLabels
    extreme: HarmonyLabels


class MeterDescription(BaseModel):
    """Meter description fields."""
    overview: str = Field(description="One-sentence summary of what this meter measures")
    detailed: str = Field(description="Detailed explanation of astrological factors")
    keywords: List[str] = Field(description="5 keywords describing this meter")


class MeterLabels(BaseModel):
    """Complete label generation for a single meter."""
    description: MeterDescription
    experience_labels: ExperienceLabels
    advice_templates: AdviceTemplates


# =============================================================================
# Intensity and Harmony Level Definitions (from constants.py)
# =============================================================================

INTENSITY_LEVELS = {
    "quiet": {"range": f"0-{INTENSITY_QUIET_THRESHOLD-1}", "threshold": INTENSITY_QUIET_THRESHOLD},
    "mild": {"range": f"{INTENSITY_QUIET_THRESHOLD}-{INTENSITY_MILD_THRESHOLD-1}", "threshold": INTENSITY_MILD_THRESHOLD},
    "moderate": {"range": f"{INTENSITY_MILD_THRESHOLD}-{INTENSITY_MODERATE_THRESHOLD-1}", "threshold": INTENSITY_MODERATE_THRESHOLD},
    "high": {"range": f"{INTENSITY_MODERATE_THRESHOLD}-{INTENSITY_HIGH_THRESHOLD-1}", "threshold": INTENSITY_HIGH_THRESHOLD},
    "extreme": {"range": f"{INTENSITY_HIGH_THRESHOLD}-100", "threshold": None}
}

HARMONY_LEVELS = {
    "challenging": {"range": f"0-{HARMONY_CHALLENGING_THRESHOLD-1}", "threshold": HARMONY_CHALLENGING_THRESHOLD},
    "mixed": {"range": f"{HARMONY_CHALLENGING_THRESHOLD}-{HARMONY_HARMONIOUS_THRESHOLD-1}", "threshold": HARMONY_HARMONIOUS_THRESHOLD},
    "harmonious": {"range": f"{HARMONY_HARMONIOUS_THRESHOLD}-100", "threshold": None}
}


# =============================================================================
# Meter Type Detection
# =============================================================================

def _determine_meter_type(meter: Meter) -> str:
    """
    All meters measure both intensity and harmony dimensions.

    Returns "both" for all meters since the astrometer system always
    calculates both DTI (intensity) and HQS (harmony) for every meter.
    """
    return "both"


# =============================================================================
# Gemini Label Generation
# =============================================================================

def get_meter_metadata(meter: Meter) -> Dict:
    """Extract metadata for a specific meter."""
    group = get_group(meter)
    super_group = get_super_group(meter)

    # Find description from HIERARCHY
    group_description = ""
    super_group_description = ""
    for super_def in HIERARCHY:
        if super_def["super_group"] == super_group:
            super_group_description = super_def["description"]
            for group_def in super_def["groups"]:
                if group_def["group"] == group:
                    group_description = group_def["description"]
                    break

    # Generate human-readable name
    name = meter.value.replace("_", " ").title()

    return {
        "meter_id": meter.value,
        "display_name": name,
        "group": group.value,
        "super_group": super_group.value,
        "group_description": group_description,
        "super_group_description": super_group_description,
        "measures": _determine_meter_type(meter)
    }


def get_meter_context(meter: Meter) -> str:
    """
    Extract detailed context about what this meter measures.
    """
    meter_contexts = {
        Meter.OVERALL_INTENSITY: "Measures total astrological activity across all transits. Sum of DTI (Daily Transit Intensity). High readings mean major cosmic forces active.",
        Meter.OVERALL_HARMONY: "Measures net supportive vs challenging quality. Sum of HQS (Harmony Quality Score). Shows whether transits are helpful or difficult.",

        Meter.MENTAL_CLARITY: "Mercury transits to natal Mercury. Affects thinking, communication, mental processing. Mercury aspects to Sun/Moon also influence cognition.",
        Meter.DECISION_QUALITY: "Mercury, Sun, and Jupiter aspects. Shows quality of judgment and decision-making capacity. Saturn adds caution, Neptune confusion.",
        Meter.COMMUNICATION_FLOW: "Mercury transits affecting expression and information exchange. Venus adds charm, Mars adds directness, Saturn blocks.",

        Meter.EMOTIONAL_INTENSITY: "Moon transits and aspects to natal Moon. Emotional volume and sensitivity level. Fast-moving, changes daily.",
        Meter.RELATIONSHIP_HARMONY: "Venus transits to natal Venus, Moon, Sun. Quality of relating, harmony in connections. Mars/Saturn create friction.",
        Meter.EMOTIONAL_RESILIENCE: "Moon + Saturn aspects. Ability to handle emotional pressure. Saturn strengthens, Neptune dissolves boundaries.",

        Meter.PHYSICAL_ENERGY: "Mars transits affecting vitality and action capacity. Mars to Sun/Ascendant boosts energy. Saturn depletes.",
        Meter.CONFLICT_RISK: "Mars challenging aspects (square/opposition). Likelihood of arguments, accidents, aggression. Mars/Uranus = explosive.",
        Meter.MOTIVATION_DRIVE: "Mars + Sun aspects. Drive to initiate and achieve. Mars/Jupiter expands ambition, Mars/Saturn restrains.",

        Meter.CAREER_AMBITION: "Saturn transits to natal Sun/Saturn/Midheaven. Professional drive and authority themes. Capricorn/10th house matters.",
        Meter.OPPORTUNITY_WINDOW: "Jupiter transits bringing expansion and luck. Jupiter to Sun/Moon/Ascendant = growth opportunities. Doors opening.",

        Meter.CHALLENGE_INTENSITY: "Square and opposition aspects only. Measures friction and growth pressure. Excludes harmonious aspects.",
        Meter.TRANSFORMATION_PRESSURE: "Pluto transits forcing deep change. Intensity of death/rebirth cycles. Plutonian transformation themes.",
        Meter.INNOVATION_BREAKTHROUGH: "Uranus transits bringing sudden change and awakening. Liberation, revolution, breakthroughs. Aquarian themes.",

        Meter.FIRE_ENERGY: "Transits in Aries/Leo/Sagittarius. Action, passion, inspiration, courage. Yang, active, creative force.",
        Meter.EARTH_ENERGY: "Transits in Taurus/Virgo/Capricorn. Grounding, practicality, manifestation, structure. Material world focus.",
        Meter.AIR_ENERGY: "Transits in Gemini/Libra/Aquarius. Communication, ideas, social connection, mental activity. Intellectual realm.",
        Meter.WATER_ENERGY: "Transits in Cancer/Scorpio/Pisces. Emotion, intuition, depth, psychic sensitivity. Feeling realm.",

        Meter.INTUITION_SPIRITUALITY: "Neptune transits enhancing spiritual sensitivity. Mystical awareness, dreams, psychic openings. Piscean themes.",
        Meter.KARMIC_LESSONS: "North Node transits showing soul growth direction. Destiny points, life lessons, evolutionary themes.",

        Meter.SOCIAL_COLLECTIVE: "Outer planet transits (Jupiter/Saturn/Uranus/Neptune/Pluto) reflecting collective currents and societal themes."
    }

    return meter_contexts.get(meter, "Context not available")


def get_super_group_context() -> str:
    """Provide rich context about what each super group represents."""
    return """
SUPER GROUP MEANINGS:

1. OVERVIEW
   - Dashboard summary of total cosmic activity
   - High-level intensity and quality readings
   - Answers: "How much is happening?" and "Is it helpful or challenging?"

2. INNER WORLD
   - Internal states: thoughts, feelings, psychology
   - MIND group: thinking, decisions, communication
   - EMOTIONS group: feelings, relationships, resilience
   - Personal subjective experience

3. OUTER WORLD
   - External engagement: action, career, physical reality
   - BODY group: physical energy, conflict, motivation
   - CAREER group: professional ambition, opportunities
   - What you DO in the world

4. EVOLUTION
   - Growth through challenge and transformation
   - Pressure that creates diamonds
   - Innovation, breakthrough, forced change
   - The hero's journey difficulties

5. DEEPER DIMENSIONS
   - ELEMENTS: Temperament energies (fire/earth/air/water)
   - SPIRITUAL: Intuition, karmic lessons, mystical awareness
   - COLLECTIVE: Societal currents, outer planet themes
   - Foundational and transpersonal layers
"""


def generate_labels_with_gemini(meter: Meter, client: genai.Client) -> MeterLabels:
    """
    Use Gemini to generate labels for a single meter with structured output.
    """
    metadata = get_meter_metadata(meter)
    meter_context = get_meter_context(meter)
    super_group_context = get_super_group_context()

    prompt = f"""You are an astrologer creating labels for an astrometer system used in daily horoscopes.

**Tone:** Direct, actionable, honest, relatable. Write like a wise friend, not a mystical guru.

{super_group_context}

=== METER DETAILS ===
METER: {metadata['display_name']}
ID: {metadata['meter_id']}
GROUP: {metadata['group']} - {metadata['group_description']}
SUPER GROUP: {metadata['super_group']} - {metadata['super_group_description']}

WHAT THIS METER MEASURES:
{meter_context}

=== SCALES ===
INTENSITY (0-100 scale - "how much is happening"):
- quiet (0-30): Minimal activity
- mild (31-50): Gentle activity
- moderate (51-70): Notable activity
- high (71-85): Strong activity
- extreme (86-100): Intense activity

HARMONY (0-100 scale - "is it flowing or challenging"):
- challenging (0-30): Difficult, friction
- mixed (31-69): Mix of supportive and challenging
- harmonious (70-100): Supportive, flowing

=== YOUR TASK ===

1. EXPERIENCE LABELS (state_label - used directly in horoscopes):
   - Max 2 words each
   - These appear in sentences like: "Your career is at HIGH STAKES today" or "Your emotions are FRAGILE right now"
   - intensity_only: 5 labels for intensity levels
   - harmony_only: 3 labels for harmony qualities
   - combined: 5×3 = 15 labels for each intensity+harmony combo

   GOOD examples: "High Stakes", "Fragile", "Peak Wisdom", "Driven", "Friction", "Favorable", "Strong", "Restful", "Tense", "Flowing"
   BAD examples: "Cosmic Alignment", "Mystical Flow", "Sacred Stillness", "Profound Contemplation", "Celestial Harmony"

2. ADVICE TEMPLATES (advice category/class):
   - These are TYPE/CLASS of advice, NOT the actual advice
   - LLM will generate specific personalized advice using these categories
   - Match 5×3 combined structure

   GOOD examples: "Rest/recovery", "Bold action", "Careful navigation", "Direct confrontation", "Patient endurance", "Strategic planning", "Boundary setting"
   BAD examples: "Take a break at 3pm", "Push forward boldly now", "Be very careful today"

3. DESCRIPTION:
   - overview: 1 sentence, 8th grade reading level, 15-20 words
   - detailed: 2-3 sentences on which planets/aspects/houses drive this meter
   - keywords: 5 understandable terms (avoid "catalyze", "archetypal", "manifestation")

=== STYLE RULES ===

Voice: Warm, direct, conversational - like talking to a friend over coffee

Language Level: 8th grade, short sentences (15-20 words)

BAD: "Your soul undergoes profound alchemical transmutation"
GOOD: "You're going through a deep change in how you see yourself"

BAD: "Celestial configuration catalyzes recalibration"
GOOD: "Today's planets push you to rethink this area"

BAD: "Mystical energies flow through your essence"
GOOD: "You're feeling more intuitive than usual"

Be concrete, stay grounded, don't oversell the mystical angle."""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=MeterLabels
        )
    )

    return MeterLabels.model_validate_json(response.text)


def generate_meter_file(meter: Meter, labels: MeterLabels) -> Dict:
    """Generate complete JSON structure with Gemini-generated labels."""
    return {
        "_schema_version": "1.0",
        "_meter": meter.value,
        "_last_updated": "Generated by Gemini",

        "metadata": get_meter_metadata(meter),

        "description": labels.description.model_dump(),

        "experience_labels": labels.experience_labels.model_dump(),

        "advice_templates": labels.advice_templates.model_dump()
    }


# =============================================================================
# Main Script
# =============================================================================

def main():
    """Generate labeled JSON files for all meters using Gemini."""
    import sys

    # Get API key from environment
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: GEMINI_API_KEY environment variable not set")
        sys.exit(1)

    print("🤖 Initializing Gemini client...")
    client = genai.Client(api_key=api_key)

    print("Generating astrometer label files with Gemini...\n")

    # Create output directory
    output_dir = "labels"
    os.makedirs(output_dir, exist_ok=True)

    # Generate file for each meter
    meters_by_type = {"intensity_only": [], "harmony_only": [], "both": []}
    successful = 0
    failed = []

    for i, meter in enumerate(Meter, 1):
        try:
            print(f"[{i}/23] Generating {meter.value}...", end=" ", flush=True)

            # Call Gemini to generate labels
            labels = generate_labels_with_gemini(meter, client)

            # Build complete file structure
            meter_config = generate_meter_file(meter, labels)
            meter_type = meter_config["metadata"]["measures"]
            meters_by_type[meter_type].append(meter.value)

            # Save to file
            filename = f"{meter.value}.json"
            filepath = os.path.join(output_dir, filename)

            with open(filepath, "w") as f:
                json.dump(meter_config, f, indent=2)

            print(f"✅")
            successful += 1

        except Exception as e:
            print(f"❌ Failed: {e}")
            failed.append((meter.value, str(e)))

    # Print summary
    print(f"\n📊 Summary:")
    print(f"   Successful: {successful}/23")
    print(f"   Failed: {len(failed)}/23")
    print(f"   Location: {output_dir}/")

    if failed:
        print(f"\n❌ Failed meters:")
        for meter_name, error in failed:
            print(f"   • {meter_name}: {error}")

    if successful > 0:
        print(f"\n   Meter types generated:")
        print(f"   - Intensity only: {len(meters_by_type['intensity_only'])}")
        for m in meters_by_type['intensity_only']:
            print(f"     • {m}")
        print(f"   - Harmony only: {len(meters_by_type['harmony_only'])}")
        for m in meters_by_type['harmony_only']:
            print(f"     • {m}")
        print(f"   - Both: {len(meters_by_type['both'])}")
        for m in meters_by_type['both']:
            print(f"     • {m}")

    print(f"\n✨ All files generated with Gemini labels!")
    print(f"📁 Check {output_dir}/ to review the generated content")


if __name__ == "__main__":
    main()
