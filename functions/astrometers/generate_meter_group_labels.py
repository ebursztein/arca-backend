#!/usr/bin/env python3
"""
Generate JSON label files for the 5 MeterGroupV2 groups.

Usage:
    python generate_meter_group_labels.py
"""

import os
from hierarchy import MeterGroupV2, GROUP_V2_METERS, GROUP_V2_DISPLAY_NAMES
from generate_meter_labels import (
    IntensityLabels,
    HarmonyLabels,
    CombinedLabels,
    ExperienceLabels,
    AdviceTemplates,
    MeterDescription,
)
from google import genai
from google.genai import types
from dotenv import load_dotenv
import json
from pydantic import BaseModel, Field

load_dotenv()


# =============================================================================
# Pydantic Models for Group Labels
# =============================================================================

class GroupLabels(BaseModel):
    """Complete label generation for a single meter group."""
    description: MeterDescription
    experience_labels: ExperienceLabels
    advice_templates: AdviceTemplates


# =============================================================================
# Group Context
# =============================================================================

def get_group_context(group: MeterGroupV2) -> str:
    """Get detailed context about what this meter group represents."""
    group_contexts = {
        MeterGroupV2.MIND: """
MIND GROUP (3 meters): Cognitive functions, thinking, communication

Meters included:
- mental_clarity: Mercury transits affecting thinking, mental processing
- decision_quality: Mercury/Jupiter/Saturn aspects showing judgment capacity
- communication_flow: Mercury transits affecting expression and information exchange

This group measures your intellectual capacity and communication effectiveness today.
It shows how clear your thinking is, how well you can make decisions, and how easily
you can communicate with others. When this group is high, it's a great day for
important conversations, strategic planning, and mental work. When low, give yourself
grace and avoid major decisions if possible.
""",
        MeterGroupV2.EMOTIONS: """
EMOTIONS GROUP (3 meters): Feelings, relationships, emotional well-being

Meters included:
- emotional_intensity: Moon transits showing emotional volume and sensitivity
- relationship_harmony: Venus aspects to natal points showing quality of connections
- emotional_resilience: Moon + Saturn aspects showing ability to handle emotional pressure

This group measures your emotional state and relationship dynamics today. It shows
how intensely you're feeling things, how harmonious your connections are, and how
well you can handle emotional challenges. High scores mean you're emotionally
balanced and relationships flow well. Low scores suggest extra self-care is needed
and it may not be the best day for difficult conversations.
""",
        MeterGroupV2.BODY: """
BODY GROUP (3 meters): Physical energy, action, vitality

Meters included:
- physical_energy: Mars transits affecting vitality and action capacity
- conflict_risk: Mars challenging aspects showing likelihood of arguments/accidents
- motivation_drive: Mars + Sun aspects showing drive to initiate and achieve

This group measures your physical energy and capacity for action today. It shows
how much vitality you have, whether you're likely to encounter conflicts, and
how motivated you feel to pursue your goals. High scores mean you can accomplish
a lot physically and have strong drive. Watch for conflict risk if intensity is
high. Low scores suggest rest and gentler activities.
""",
        MeterGroupV2.SPIRIT: """
SPIRIT GROUP (6 meters): Inner wisdom, soul path, elemental balance

Meters included:
- intuition_spirituality: Neptune transits enhancing spiritual sensitivity
- karmic_lessons: North Node transits showing soul growth direction
- fire_energy: Transits in Aries/Leo/Sagittarius (action, passion, inspiration)
- earth_energy: Transits in Taurus/Virgo/Capricorn (grounding, practicality)
- air_energy: Transits in Gemini/Libra/Aquarius (communication, ideas, mental)
- water_energy: Transits in Cancer/Scorpio/Pisces (emotion, intuition, depth)

This group measures your spiritual awareness and elemental temperament today.
It shows how connected you are to your intuition, what karmic themes are active,
and which elemental energies are most present. This helps you understand your
inner landscape beyond just thoughts and feelings. High scores mean strong
spiritual connection and balanced elements. This group guides your inner work
and meditation practice.
""",
        MeterGroupV2.GROWTH: """
GROWTH GROUP (6 meters): Career, expansion, transformation, breakthroughs

Meters included:
- career_ambition: Saturn transits to Sun/Saturn/Midheaven affecting professional drive
- opportunity_window: Jupiter transits bringing expansion and luck
- challenge_intensity: Square/opposition aspects measuring friction and growth pressure
- transformation_pressure: Pluto transits forcing deep change and death/rebirth cycles
- innovation_breakthrough: Uranus transits bringing sudden change and awakening
- social_collective: Outer planet transits reflecting collective currents

This group measures your capacity for growth, evolution, and achievement today.
It shows how your career is progressing, what opportunities are available, what
challenges you're facing, and where breakthrough or transformation is happening.
This is the hero's journey group - where pressure creates diamonds. High scores
mean powerful growth is occurring (though challenges may be present). Low scores
suggest a quieter period for integration rather than pushing forward.
"""
    }
    return group_contexts.get(group, "Context not available")


def generate_group_labels_with_gemini(group: MeterGroupV2, client: genai.Client) -> GroupLabels:
    """
    Use Gemini to generate labels for a single meter group with structured output.
    """
    display_name = GROUP_V2_DISPLAY_NAMES[group]
    meters = GROUP_V2_METERS[group]
    meter_names = [m.value for m in meters]
    group_context = get_group_context(group)

    prompt = f"""You are an astrologer creating labels for a METER GROUP in a daily horoscope system.

This is different from individual meters - you're creating labels for an AGGREGATED GROUP
that combines multiple meters into a single life-area summary.

**Tone:** Direct, actionable, honest, relatable. Write like a wise friend, not a mystical guru.

=== METER GROUP DETAILS ===
GROUP: {display_name}
ID: {group.value}
AGGREGATES: {len(meters)} individual meters
MEMBER METERS: {', '.join(meter_names)}

WHAT THIS GROUP MEASURES:
{group_context}

=== SCALES ===
The group gets aggregated scores from its member meters:

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
   - These describe the OVERALL STATE of this life area
   - Think holistically about the group as a whole, not individual meters

   Examples for MIND group:
   - quiet/harmonious: "Clear thinking", "Mental ease"
   - high/harmonious: "Sharp focus", "Peak clarity"
   - high/challenging: "Mental strain", "Overthinking"
   - extreme/challenging: "Mind racing", "Scattered thoughts"

   Examples for EMOTIONS group:
   - quiet/harmonious: "Calm waters", "Peaceful heart"
   - high/harmonious: "Heart full", "Deep connection"
   - high/challenging: "Intense feelings", "Heart heavy"
   - extreme/challenging: "Emotional storm", "Raw nerves"

   Examples for BODY group:
   - quiet/harmonious: "Restful ease", "Gentle energy"
   - high/harmonious: "Peak vitality", "Strong drive"
   - high/challenging: "Restless energy", "Friction risk"
   - extreme/challenging: "High tension", "Explosive"

   Examples for SPIRIT group:
   - quiet/harmonious: "Quiet wisdom", "Subtle knowing"
   - high/harmonious: "Deep connection", "Soul clarity"
   - high/challenging: "Spiritual seeking", "Inner tension"
   - extreme/challenging: "Intense visions", "Overwhelmed"

   Examples for GROWTH group:
   - quiet/harmonious: "Steady progress", "Patient growth"
   - high/harmonious: "Major momentum", "Breakthrough time"
   - high/challenging: "Growth pains", "Hard lessons"
   - extreme/challenging: "Pressure cooker", "Crisis point"

   GOOD: "Sharp focus", "Heart heavy", "Peak vitality", "Growth pains", "Deep connection"
   BAD: "Cosmic Alignment", "Mystical Flow", "Sacred Stillness", "Profound Contemplation"

2. ADVICE TEMPLATES (advice category/class):
   - Type of advice, NOT the actual advice
   - Match 5×3 combined structure

   GOOD examples:
   - MIND: "Focus work", "Mental rest", "Important conversations", "Strategic planning"
   - EMOTIONS: "Self-care", "Boundary setting", "Deep connection", "Process feelings"
   - BODY: "Physical activity", "Rest/recovery", "Conflict avoidance", "Channel energy"
   - SPIRIT: "Meditation", "Creative expression", "Elemental balancing", "Inner reflection"
   - GROWTH: "Seize opportunities", "Patient endurance", "Navigate challenges", "Breakthrough action"

3. DESCRIPTION:
   - overview: 1 sentence, what this group measures overall (15-20 words, 8th grade level)
   - detailed: 2-3 sentences on what life areas are covered
   - keywords: 5 understandable terms

=== STYLE RULES ===

Voice: Warm, direct, conversational - like talking to a friend over coffee

Language Level: 8th grade, short sentences (15-20 words)

BAD: "Your soul undergoes profound alchemical transmutation"
GOOD: "You're going through a deep change in how you see yourself"

BAD: "Celestial configuration catalyzes recalibration"
GOOD: "Today's planets push you to rethink this area"

Be concrete, stay grounded, don't oversell the mystical angle."""

    response = client.models.generate_content(
        model="gemini-2.0-flash-exp",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=GroupLabels
        )
    )

    return GroupLabels.model_validate_json(response.text)


def generate_group_file(group: MeterGroupV2, labels: GroupLabels) -> dict:
    """Generate complete JSON structure for a meter group."""
    return {
        "_schema_version": "1.0",
        "_group": group.value,
        "_last_updated": "Generated by Gemini",

        "metadata": {
            "group_id": group.value,
            "display_name": GROUP_V2_DISPLAY_NAMES[group],
            "meter_count": len(GROUP_V2_METERS[group]),
            "member_meters": [m.value for m in GROUP_V2_METERS[group]],
            "measures": "both"
        },

        "description": labels.description.model_dump(),

        "experience_labels": labels.experience_labels.model_dump(),

        "advice_templates": labels.advice_templates.model_dump()
    }


def main():
    # Get API key
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: GEMINI_API_KEY environment variable not set")
        return

    print("🤖 Initializing Gemini client...")
    client = genai.Client(api_key=api_key)

    print(f"Generating 5 meter group labels...\n")

    output_dir = "labels/groups"
    os.makedirs(output_dir, exist_ok=True)

    successful = 0
    failed = []

    # Generate for each MeterGroupV2
    for i, group in enumerate(MeterGroupV2, 1):
        try:
            print(f"[{i}/5] Generating {group.value}...", end=" ", flush=True)

            # Call Gemini
            labels = generate_group_labels_with_gemini(group, client)

            # Build file structure
            group_config = generate_group_file(group, labels)

            # Save to file
            filename = f"{group.value}.json"
            filepath = os.path.join(output_dir, filename)

            with open(filepath, "w") as f:
                json.dump(group_config, f, indent=2)

            print(f"✅")
            successful += 1

        except Exception as e:
            print(f"❌ Failed: {e}")
            failed.append((group.value, str(e)))

    # Summary
    print(f"\n📊 Summary:")
    print(f"   Successful: {successful}/5")
    print(f"   Failed: {len(failed)}/5")

    if failed:
        print(f"\n❌ Failed groups:")
        for group_name, error in failed:
            print(f"   • {group_name}: {error}")

    if successful > 0:
        print(f"\n✨ Group label files generated!")
        print(f"📁 Check {output_dir}/ to review")


if __name__ == "__main__":
    main()
