"""
Meter taxonomy implementation - 23 specialized meters.

Each meter:
1. Filters aspects to relevant planets/houses
2. Calculates DTI/HQS using core algorithms
3. Normalizes to 0-100 scales
4. Generates interpretations and advice
5. Provides explainability via AspectContribution breakdown

Spec Reference: astrometers.md Section 5
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field

# Import from existing modules
from astro import Planet, AspectType, ZodiacSign, House
from .core import (
    TransitAspect,
    AspectContribution,
    calculate_astrometers,
    AstrometerScore
)
from .normalization import (
    normalize_intensity,
    normalize_harmony,
    get_intensity_label,
    get_harmony_label
)


# ============================================================================
# MeterReading Model (Spec Section 7.4.2)
# ============================================================================

class MeterReading(BaseModel):
    """Complete meter reading with explainability."""
    meter_name: str
    date: datetime
    intensity: float = Field(ge=0, le=100)
    harmony: float = Field(ge=0, le=100)
    state_label: str
    interpretation: str
    advice: List[str]
    top_aspects: List[AspectContribution]
    raw_scores: Dict[str, float]
    additional_context: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Helper Functions
# ============================================================================

def filter_aspects_by_natal_planet(
    aspects: List[TransitAspect],
    planets: List[Planet]
) -> List[TransitAspect]:
    """Filter aspects to specific natal planets."""
    return [a for a in aspects if a.natal_planet in planets]


def filter_aspects_by_transit_planet(
    aspects: List[TransitAspect],
    planets: List[Planet]
) -> List[TransitAspect]:
    """Filter aspects to specific transit planets."""
    return [a for a in aspects if a.transit_planet in planets]


def filter_aspects_by_natal_house(
    aspects: List[TransitAspect],
    houses: List[int]
) -> List[TransitAspect]:
    """Filter aspects to planets in specific natal houses."""
    return [a for a in aspects if a.natal_house in houses]


def filter_hard_aspects(aspects: List[TransitAspect]) -> List[TransitAspect]:
    """Filter to hard aspects only (square, opposition)."""
    hard = [AspectType.SQUARE, AspectType.OPPOSITION]
    return [a for a in aspects if a.aspect_type in hard]


def filter_soft_aspects(aspects: List[TransitAspect]) -> List[TransitAspect]:
    """Filter to soft aspects only (trine, sextile)."""
    soft = [AspectType.TRINE, AspectType.SEXTILE]
    return [a for a in aspects if a.aspect_type in soft]


def calculate_meter_score(
    aspects: List[TransitAspect],
    meter_name: str,
    date: datetime
) -> MeterReading:
    """
    Generic meter calculation function.

    Uses existing calculate_astrometers() from core.py
    Returns MeterReading with all fields populated
    """
    if not aspects:
        return MeterReading(
            meter_name=meter_name,
            date=date,
            intensity=0.0,
            harmony=50.0,
            state_label="Quiet",
            interpretation=f"No significant astrological activity for {meter_name}.",
            advice=["Normal baseline period - routine operations"],
            top_aspects=[],
            raw_scores={"dti": 0.0, "hqs": 0.0}
        )

    # Calculate using core algorithm
    score = calculate_astrometers(aspects)

    # Normalize
    intensity = normalize_intensity(score.dti)
    harmony = normalize_harmony(score.hqs)

    # Get labels
    intensity_label = get_intensity_label(intensity)
    harmony_label = get_harmony_label(harmony)
    state_label = f"{intensity_label} + {harmony_label}"

    # Sort by contribution
    top_aspects = sorted(
        score.contributions,
        key=lambda a: abs(a.dti_contribution),
        reverse=True
    )[:5]

    return MeterReading(
        meter_name=meter_name,
        date=date,
        intensity=intensity,
        harmony=harmony,
        state_label=state_label,
        interpretation="",  # Filled by specific meter function
        advice=[],  # Filled by specific meter function
        top_aspects=top_aspects,
        raw_scores={"dti": score.dti, "hqs": score.hqs}
    )


# ============================================================================
# GLOBAL METERS (Spec Section 5.2)
# ============================================================================

def calculate_overall_intensity_meter(
    all_aspects: List[TransitAspect],
    date: datetime
) -> MeterReading:
    """
    Overall Intensity Gauge - measures total astrological activity.

    Spec: Section 5.2.1
    Formula: Total DTI across all transits
    Interpretation:
    - 0-25: Quiet (rest, integrate)
    - 26-50: Moderate (normal operations)
    - 51-75: High (pay attention)
    - 76-90: Very High (major themes active)
    - 91-100: Extreme (life-defining period)
    """
    reading = calculate_meter_score(all_aspects, "overall_intensity", date)

    # Generate interpretation
    if reading.intensity < 26:
        reading.interpretation = (
            "Your astrological activity is minimal right now. This is a quiet "
            "period with low cosmic demands. Energy is subtle and internal."
        )
        reading.advice = [
            "Rest and integrate recent experiences",
            "Good time for routine maintenance and reflection",
            "No major external pushes - go with your own flow"
        ]
    elif reading.intensity < 51:
        reading.interpretation = (
            "Normal level of astrological activity. Background cosmic currents "
            "are present but not overwhelming. Standard life operations."
        )
        reading.advice = [
            "Proceed with normal activities and plans",
            "Incremental progress is favored",
            "Balance activity with adequate rest"
        ]
    elif reading.intensity < 76:
        reading.interpretation = (
            "Significant astrological activity is present. The cosmos is clearly "
            "sending signals and activating themes. Things are moving."
        )
        reading.advice = [
            "Pay attention to emerging themes and synchronicities",
            "This is not a time to coast - engage actively",
            "Multiple life areas may be activated simultaneously"
        ]
    elif reading.intensity < 91:
        reading.interpretation = (
            "Very high intensity period - you're in the top 5% of cosmic activity. "
            "Major themes are active and demanding attention. Life is happening."
        )
        reading.advice = [
            "Major life themes are in focus - strategic engagement required",
            "High-stakes period - your choices matter significantly",
            "Ensure adequate support systems and self-care",
            "This intensity won't last forever - ride the wave"
        ]
    else:
        reading.interpretation = (
            "EXTREME intensity period - top 1% of cosmic activity. This is a "
            "life-defining window. Multiple powerful transits converge. All hands on deck."
        )
        reading.advice = [
            "Life-defining period - stay grounded and centered",
            "Seek support from trusted advisors and friends",
            "Major transformations are underway - embrace the process",
            "Document this period - future you will want to remember",
            "Prioritize ruthlessly - you can't do everything at once"
        ]

    # Add top contributors
    if reading.top_aspects:
        top_3 = reading.top_aspects[:3]
        contrib_text = "\n\nTop contributing aspects:\n"
        for aspect in top_3:
            contrib_text += f"• {aspect.label} (DTI: {aspect.dti_contribution:.1f})\n"
        reading.interpretation += contrib_text

    reading.state_label = get_intensity_label(reading.intensity)
    return reading


def calculate_overall_harmony_meter(
    all_aspects: List[TransitAspect],
    date: datetime
) -> MeterReading:
    """
    Overall Harmony Meter - measures net supportive vs challenging quality.

    Spec: Section 5.2.2
    Formula: Total HQS across all transits
    Scale: 0-100 where 50 is neutral
    Interpretation:
    - 0-20: Very Challenging (heavy difficult aspects)
    - 21-40: Challenging (net difficult influence)
    - 41-60: Mixed/Neutral (balance of both)
    - 61-80: Supportive (net harmonious influence)
    - 81-100: Very Supportive (predominantly harmonious)
    """
    reading = calculate_meter_score(all_aspects, "overall_harmony", date)

    # Count supportive vs challenging aspects
    supportive = sum(1 for a in reading.top_aspects if a.quality_factor > 0)
    challenging = sum(1 for a in reading.top_aspects if a.quality_factor < 0)
    neutral = sum(1 for a in reading.top_aspects if a.quality_factor == 0)

    reading.additional_context = {
        "supportive_count": supportive,
        "challenging_count": challenging,
        "neutral_count": neutral
    }

    # Generate interpretation
    if reading.harmony < 21:
        reading.interpretation = (
            "Very challenging astrological climate. Heavy difficult aspects dominate. "
            "Growth through friction, obstacles, and tests. High resistance period."
        )
        reading.advice = [
            "Expect obstacles and friction - this is temporary",
            "Focus on building resilience and character",
            "Avoid major risks or aggressive moves",
            "Seek support and maintain perspective",
            "Lessons are being forged - lean into the growth"
        ]
    elif reading.harmony < 41:
        reading.interpretation = (
            "Challenging astrological climate. Net difficult influence present. "
            "Effort and conscious navigation required. Growth through challenge."
        )
        reading.advice = [
            "Proceed with patience and persistence",
            "Double-check plans and communications",
            "Challenges are teaching valuable lessons",
            "Maintain self-care and boundaries"
        ]
    elif reading.harmony < 61:
        reading.interpretation = (
            "Mixed astrological climate. Opportunities and challenges coexist. "
            "Neither fully easy nor fully difficult. Balanced navigation required."
        )
        reading.advice = [
            "Be discerning - some areas flow, others require effort",
            "Leverage opportunities while managing challenges",
            "Stay flexible and adaptive",
            "Mixed periods often bring important growth"
        ]
    elif reading.harmony < 81:
        reading.interpretation = (
            "Supportive astrological climate. Net harmonious influence present. "
            "Flow, ease, and natural unfolding. Favorable conditions for progress."
        )
        reading.advice = [
            "Take advantage of favorable conditions",
            "Good time for initiatives and forward movement",
            "Things fall into place more easily than usual",
            "Express gratitude for the grace period"
        ]
    else:
        reading.interpretation = (
            "Very supportive astrological climate. Predominantly harmonious aspects. "
            "Grace, luck, and things falling into place. Peak favorable conditions."
        )
        reading.advice = [
            "Rare window of exceptional cosmic support",
            "Launch important initiatives and projects",
            "Serendipity and synchronicity are heightened",
            "Make meaningful progress while conditions favor you",
            "Celebrate and appreciate this blessed period"
        ]

    # Add breakdown
    breakdown = f"\n\nAspect breakdown: {supportive} supportive, {challenging} challenging, {neutral} neutral"
    reading.interpretation += breakdown

    reading.state_label = get_harmony_label(reading.harmony)
    return reading


# ============================================================================
# COGNITIVE METERS (Spec Section 5.4)
# ============================================================================

def calculate_mental_clarity_meter(
    all_aspects: List[TransitAspect],
    date: datetime,
    transit_chart: dict
) -> MeterReading:
    """
    Mental Clarity Meter - ease of thinking, concentration, mental processing.

    Spec: Section 5.4.1
    Primary: All aspects to natal Mercury
    Secondary: 3rd house transits
    Modifier: Mercury retrograde (×0.6 to clarity)

    Interpretation Matrix:
    - Low Intensity: Mental Quiet
    - Moderate/High Harmony: Sharp Focus / Genius Mode
    - Moderate/Low Harmony: Scattered / Overload
    """
    # Filter to Mercury aspects
    mercury_aspects = filter_aspects_by_natal_planet(all_aspects, [Planet.MERCURY])

    reading = calculate_meter_score(mercury_aspects, "mental_clarity", date)

    # Check Mercury retrograde
    mercury_data = next(
        (p for p in transit_chart["planets"] if p["name"] == Planet.MERCURY),
        None
    )
    mercury_rx = mercury_data.get("retrograde", False) if mercury_data else False

    if mercury_rx:
        reading.harmony *= 0.6
        reading.additional_context["mercury_retrograde"] = True

    # Generate interpretation based on matrix
    intensity = reading.intensity
    harmony = reading.harmony

    if intensity < 40:
        reading.interpretation = "Your mind is quiet with low mental demand. Rest and integration period."
        reading.advice = ["Low cognitive demands - good for mental rest", "Integration and reflection favored"]
        reading.state_label = "Mental Quiet"
    elif intensity < 70:
        if harmony > 70:
            reading.interpretation = "Excellent mental clarity. Thinking is sharp and communication flows easily."
            reading.advice = [
                "Excellent time for learning, writing, decisions",
                "Complex problem-solving favored",
                "Important conversations go well"
            ]
            reading.state_label = "Sharp Focus"
        elif harmony < 30:
            reading.interpretation = "Significantly reduced mental clarity. Brain fog, confusion, communication difficulties."
            reading.advice = [
                "Avoid important decisions if possible",
                "Double-check details and communications",
                "Give extra time for mental tasks",
                "Rest your mind - reduce information overload"
            ]
            reading.state_label = "Scattered"
        else:
            reading.interpretation = "Mixed mental state with both clear moments and foggy periods."
            reading.advice = [
                "Mixed mental energy - proceed thoughtfully",
                "Give extra time for important decisions",
                "Be especially clear in communications"
            ]
            reading.state_label = "Mixed Mental Energy"
    else:  # High intensity
        if harmony > 70:
            reading.interpretation = "Peak mental performance. Exceptional clarity, insight, and communication."
            reading.advice = [
                "Genius mode activated - tackle complex problems",
                "Ideal for presentations, negotiations, creative work",
                "Major mental breakthroughs possible",
                "Document your insights - they're valuable"
            ]
            reading.state_label = "Genius Mode"
        elif harmony < 30:
            reading.interpretation = "Mind under significant stress. Mental overload, scattered thinking, or major miscommunications likely."
            reading.advice = [
                "Mental overload risk - prioritize and simplify",
                "NOT the time for major decisions",
                "High misunderstanding/argument risk - be careful",
                "Consider postponing difficult conversations",
                "Rest and recovery crucial"
            ]
            reading.state_label = "Mental Overload"
        else:
            reading.interpretation = "Intense mental activity with both breakthroughs and challenges."
            reading.advice = [
                "High mental activity - manage your energy",
                "Both insights and confusion possible",
                "Give yourself extra processing time"
            ]
            reading.state_label = "Intense Mixed"

    if mercury_rx:
        reading.interpretation += "\n\nNote: Mercury is retrograde, adding review, revision, and reconsideration themes."

    return reading


def calculate_decision_quality_meter(
    all_aspects: List[TransitAspect],
    date: datetime
) -> MeterReading:
    """
    Decision Quality Meter - wisdom, judgment, strategic thinking.

    Spec: Section 5.4.2
    Planets: Mercury (analysis), Jupiter (wisdom), Saturn (discernment), Neptune (intuition vs confusion)
    """
    decision_planets = [Planet.MERCURY, Planet.JUPITER, Planet.SATURN, Planet.NEPTUNE]
    filtered_aspects = filter_aspects_by_natal_planet(all_aspects, decision_planets)

    reading = calculate_meter_score(filtered_aspects, "decision_quality", date)

    if reading.intensity < 40:
        reading.interpretation = "Decision-making is relatively quiet. No major pushes or pressures."
        reading.advice = ["Standard decision-making applies", "No urgent choices required"]
        reading.state_label = "Baseline"
    elif reading.intensity < 70:
        if reading.harmony > 70:
            reading.interpretation = "Excellent judgment and strategic thinking. Clarity and wisdom combine."
            reading.advice = [
                "Great time for important decisions",
                "Trust your analysis and intuition",
                "Long-term planning favored"
            ]
            reading.state_label = "Clear Judgment"
        elif reading.harmony < 30:
            reading.interpretation = "Clouded judgment or conflicting inputs. Decision-making is compromised."
            reading.advice = [
                "Postpone major decisions if possible",
                "Seek outside counsel and perspective",
                "Watch for self-deception or wishful thinking"
            ]
            reading.state_label = "Clouded"
        else:
            reading.interpretation = "Mixed signals for decision-making. Some clarity, some confusion."
            reading.advice = [
                "Take your time with important choices",
                "Gather multiple perspectives",
                "Trust logic over emotion"
            ]
            reading.state_label = "Mixed Signals"
    else:  # High intensity
        if reading.harmony > 70:
            reading.interpretation = "Peak wisdom and strategic clarity. Major decisions favor you."
            reading.advice = [
                "Excellent window for life-changing decisions",
                "Your judgment is exceptionally sound",
                "Trust yourself - act decisively"
            ]
            reading.state_label = "Peak Wisdom"
        elif reading.harmony < 30:
            reading.interpretation = "High-stakes period with compromised judgment. Major confusion or delusion risk."
            reading.advice = [
                "AVOID major decisions if at all possible",
                "High risk of costly mistakes",
                "Seek professional advice for important matters",
                "Wait for clarity"
            ]
            reading.state_label = "High Risk"
        else:
            reading.interpretation = "Important decision pressure with mixed clarity."
            reading.advice = [
                "Major choices are pressing but proceed carefully",
                "Gather all available information",
                "Sleep on big decisions"
            ]
            reading.state_label = "Pressure Mixed"

    return reading


def calculate_communication_flow_meter(
    all_aspects: List[TransitAspect],
    date: datetime
) -> MeterReading:
    """
    Communication Flow Meter - expression, connection, being heard.

    Spec: Section 5.4.3
    Planets: Mercury (words), Venus (diplomacy), Mars (directness)
    """
    comm_planets = [Planet.MERCURY, Planet.VENUS, Planet.MARS]
    filtered_aspects = filter_aspects_by_natal_planet(all_aspects, comm_planets)

    reading = calculate_meter_score(filtered_aspects, "communication_flow", date)

    if reading.intensity < 40:
        reading.interpretation = "Communication is quiet and routine. No special dynamics."
        reading.advice = ["Normal communication patterns apply"]
        reading.state_label = "Routine"
    elif reading.intensity < 70:
        if reading.harmony > 70:
            reading.interpretation = "Communication flows beautifully. You're articulate, heard, and persuasive."
            reading.advice = [
                "Excellent time for important conversations",
                "Negotiations go well",
                "Express yourself freely"
            ]
            reading.state_label = "Flowing"
        elif reading.harmony < 30:
            reading.interpretation = "Communication is strained. Misunderstandings, conflicts, or being misheard."
            reading.advice = [
                "Be extra clear and patient",
                "Avoid heated arguments",
                "Written communication may be safer than verbal",
                "Clarify assumptions"
            ]
            reading.state_label = "Strained"
        else:
            reading.interpretation = "Mixed communication energy. Some clarity, some friction."
            reading.advice = [
                "Be mindful of tone and timing",
                "Confirm understanding in conversations",
                "Stay flexible"
            ]
            reading.state_label = "Mixed"
    else:  # High intensity
        if reading.harmony > 70:
            reading.interpretation = "Peak communication power. Your words have exceptional impact and resonance."
            reading.advice = [
                "Ideal for presentations, pitches, or difficult talks",
                "Your message lands powerfully",
                "Speak your truth - people will listen"
            ]
            reading.state_label = "Powerful Voice"
        elif reading.harmony < 30:
            reading.interpretation = "High communication stress. Major conflicts, explosive arguments, or severe blocks."
            reading.advice = [
                "High argument/conflict risk - tread carefully",
                "Postpone sensitive conversations if possible",
                "Count to ten before responding",
                "Seek mediation for disputes"
            ]
            reading.state_label = "Volatile"
        else:
            reading.interpretation = "Intense communication activity with mixed results."
            reading.advice = [
                "Important talks are happening but proceed thoughtfully",
                "Balance assertiveness with diplomacy",
                "Choose words carefully"
            ]
            reading.state_label = "Intense"

    return reading


# ============================================================================
# EMOTIONAL METERS (Spec Section 5.5)
# ============================================================================

def calculate_emotional_intensity_meter(
    all_aspects: List[TransitAspect],
    date: datetime
) -> MeterReading:
    """
    Emotional Intensity Meter - depth of feeling, emotional activation.

    Spec: Section 5.5.1
    Planets: Moon (emotions), Venus (affection), Pluto (depth), Neptune (sensitivity)
    """
    emotion_planets = [Planet.MOON, Planet.VENUS, Planet.PLUTO, Planet.NEPTUNE]
    filtered_aspects = filter_aspects_by_natal_planet(all_aspects, emotion_planets)

    reading = calculate_meter_score(filtered_aspects, "emotional_intensity", date)

    if reading.intensity < 40:
        reading.interpretation = "Emotional life is calm and balanced. Feelings are stable."
        reading.advice = ["Normal emotional baseline", "Good time for emotional rest"]
        reading.state_label = "Calm"
    elif reading.intensity < 70:
        if reading.harmony > 60:
            reading.interpretation = "Heightened positive emotions. Joy, love, connection, or creative inspiration."
            reading.advice = [
                "Savor the good feelings",
                "Share emotions with loved ones",
                "Channel into creative expression"
            ]
            reading.state_label = "Uplifted"
        elif reading.harmony < 40:
            reading.interpretation = "Emotional challenges present. Difficult feelings, old wounds, or relationship stress."
            reading.advice = [
                "Honor your feelings without being overwhelmed",
                "Seek support if needed",
                "This too shall pass",
                "Process emotions healthily"
            ]
            reading.state_label = "Challenged"
        else:
            reading.interpretation = "Mixed emotional currents. Highs and lows, complexity."
            reading.advice = [
                "Ride the emotional waves mindfully",
                "Allow space for all feelings",
                "Stay grounded"
            ]
            reading.state_label = "Mixed Feelings"
    else:  # High intensity
        if reading.harmony > 60:
            reading.interpretation = "Peak emotional experiences. Profound joy, love, or spiritual connection."
            reading.advice = [
                "Treasure this emotionally rich period",
                "Peak experiences are unfolding",
                "Open your heart fully",
                "Document meaningful moments"
            ]
            reading.state_label = "Peak Emotion"
        elif reading.harmony < 40:
            reading.interpretation = "Extreme emotional intensity. Crisis, catharsis, or deep transformation underway."
            reading.advice = [
                "Seek support - don't go through this alone",
                "Professional help may be appropriate",
                "Intense emotions are valid and important",
                "This is a transformational passage",
                "Be gentle with yourself"
            ]
            reading.state_label = "Emotional Storm"
        else:
            reading.interpretation = "Powerful emotional activation with complex layers."
            reading.advice = [
                "Major emotional themes are active",
                "Give yourself space to feel",
                "Stay connected to support systems"
            ]
            reading.state_label = "Intense Complex"

    return reading


def calculate_relationship_harmony_meter(
    all_aspects: List[TransitAspect],
    date: datetime
) -> MeterReading:
    """
    Relationship Harmony Meter - connection quality, partnership dynamics.

    Spec: Section 5.5.2
    Primary: Venus aspects + 7th house transits
    """
    # Venus aspects
    venus_aspects = filter_aspects_by_natal_planet(all_aspects, [Planet.VENUS])
    # 7th house planets
    seventh_house = filter_aspects_by_natal_house(all_aspects, [7])
    # Combine (simple concatenation - duplicates don't matter for scoring)
    combined = venus_aspects + seventh_house

    reading = calculate_meter_score(combined, "relationship_harmony", date)

    if reading.intensity < 40:
        reading.interpretation = "Relationship dynamics are stable and routine. No major themes."
        reading.advice = ["Normal relationship baseline", "Maintain routines"]
        reading.state_label = "Stable"
    elif reading.intensity < 70:
        if reading.harmony > 70:
            reading.interpretation = "Excellent relationship energy. Connection, harmony, and mutual understanding flow."
            reading.advice = [
                "Wonderful time for quality time together",
                "Deepen bonds and intimacy",
                "Resolve conflicts easily"
            ]
            reading.state_label = "Harmonious"
        elif reading.harmony < 30:
            reading.interpretation = "Relationship friction or disconnection. Conflicts, misunderstandings, or distance."
            reading.advice = [
                "Practice patience and compassion",
                "Address issues constructively",
                "Avoid blame or criticism",
                "Seek understanding first"
            ]
            reading.state_label = "Friction"
        else:
            reading.interpretation = "Mixed relationship dynamics. Some connection, some challenges."
            reading.advice = [
                "Navigate with awareness",
                "Communicate openly",
                "Balance needs"
            ]
            reading.state_label = "Mixed"
    else:  # High intensity
        if reading.harmony > 70:
            reading.interpretation = "Peak relationship magic. Deep connection, breakthroughs, or falling in love."
            reading.advice = [
                "Savor this exceptional connection",
                "Major relationship milestones possible",
                "Open your heart to love"
            ]
            reading.state_label = "Magic"
        elif reading.harmony < 30:
            reading.interpretation = "Major relationship crisis or transformation. Breakups, betrayals, or profound tests."
            reading.advice = [
                "Relationships are under extreme pressure",
                "Seek counseling or mediation if needed",
                "Major decisions may be necessary",
                "Honor your truth and boundaries"
            ]
            reading.state_label = "Crisis"
        else:
            reading.interpretation = "Intense relationship activity with complexity."
            reading.advice = [
                "Major relationship themes demand attention",
                "Stay present and authentic",
                "Transformations are underway"
            ]
            reading.state_label = "Intense"

    return reading


def calculate_emotional_resilience_meter(
    all_aspects: List[TransitAspect],
    date: datetime
) -> MeterReading:
    """
    Emotional Resilience Meter - capacity to handle stress, bounce back.

    Spec: Section 5.5.3
    Planets: Sun (vitality), Saturn-Moon (emotional structure), Mars (courage), Jupiter (optimism)
    """
    resilience_planets = [Planet.SUN, Planet.MOON, Planet.SATURN, Planet.MARS, Planet.JUPITER]
    filtered_aspects = filter_aspects_by_natal_planet(all_aspects, resilience_planets)

    reading = calculate_meter_score(filtered_aspects, "emotional_resilience", date)

    if reading.intensity < 40:
        reading.interpretation = "Normal emotional resilience. No special pressures or support."
        reading.advice = ["Maintain healthy practices"]
        reading.state_label = "Baseline"
    elif reading.intensity < 70:
        if reading.harmony > 70:
            reading.interpretation = "Strong emotional resilience. You feel capable, optimistic, and supported."
            reading.advice = [
                "Tackle challenges confidently",
                "Your emotional foundation is solid",
                "Take on stretches"
            ]
            reading.state_label = "Strong"
        elif reading.harmony < 30:
            reading.interpretation = "Compromised resilience. Feeling fragile, depleted, or overwhelmed."
            reading.advice = [
                "Prioritize self-care and rest",
                "Reduce stressors where possible",
                "Lean on support systems",
                "Be gentle with yourself"
            ]
            reading.state_label = "Fragile"
        else:
            reading.interpretation = "Variable resilience. Some days stronger than others."
            reading.advice = [
                "Monitor your capacity",
                "Adjust expectations as needed",
                "Ask for help when needed"
            ]
            reading.state_label = "Variable"
    else:  # High intensity
        if reading.harmony > 70:
            reading.interpretation = "Exceptional resilience and inner strength. You're remarkably capable."
            reading.advice = [
                "Your strength is extraordinary right now",
                "Lead and support others",
                "Major challenges are manageable"
            ]
            reading.state_label = "Unshakeable"
        elif reading.harmony < 30:
            reading.interpretation = "Severe resilience depletion. Burnout, breakdown, or exhaustion risk."
            reading.advice = [
                "Emergency self-care required",
                "Reduce all non-essential demands",
                "Professional support strongly recommended",
                "This is not weakness - this is being human"
            ]
            reading.state_label = "Depleted"
        else:
            reading.interpretation = "Major stress with mixed capacity to handle it."
            reading.advice = [
                "Significant pressure is present",
                "Carefully manage your resources",
                "Prioritize ruthlessly"
            ]
            reading.state_label = "Under Pressure"

    return reading


# ============================================================================
# PHYSICAL/ACTION METERS (Spec Section 5.6)
# ============================================================================

def calculate_physical_energy_meter(
    all_aspects: List[TransitAspect],
    date: datetime
) -> MeterReading:
    """
    Physical Energy Meter - vitality, stamina, body energy.

    Spec: Section 5.6.1
    Planets: Sun (vitality) + Mars (action)
    """
    energy_planets = [Planet.SUN, Planet.MARS]
    filtered_aspects = filter_aspects_by_natal_planet(all_aspects, energy_planets)

    reading = calculate_meter_score(filtered_aspects, "physical_energy", date)

    if reading.intensity < 40:
        reading.interpretation = "Normal physical energy levels. No special activation."
        reading.advice = ["Standard energy baseline", "Regular routines"]
        reading.state_label = "Normal"
    elif reading.intensity < 70:
        if reading.harmony > 70:
            reading.interpretation = "Great physical energy. You feel strong, vital, and energized."
            reading.advice = [
                "Excellent time for physical activity",
                "Take on active projects",
                "Channel energy productively"
            ]
            reading.state_label = "Energized"
        elif reading.harmony < 30:
            reading.interpretation = "Low or blocked energy. Fatigue, depletion, or frustration."
            reading.advice = [
                "Rest and restore",
                "Avoid overexertion",
                "Gentle activity only",
                "Check health if persistent"
            ]
            reading.state_label = "Low Energy"
        else:
            reading.interpretation = "Variable energy. Some vitality, some depletion."
            reading.advice = [
                "Listen to your body",
                "Pace yourself",
                "Balance activity and rest"
            ]
            reading.state_label = "Variable"
    else:  # High intensity
        if reading.harmony > 70:
            reading.interpretation = "Peak physical vitality. Exceptional energy, strength, and drive."
            reading.advice = [
                "Harness this exceptional energy",
                "Major physical accomplishments possible",
                "Athletic peak",
                "Channel productively"
            ]
            reading.state_label = "Peak Vitality"
        elif reading.harmony < 30:
            reading.interpretation = "Extreme energy depletion or burnout. Health concerns possible."
            reading.advice = [
                "Immediate rest required",
                "Medical attention if symptoms persist",
                "Cancel non-essential activities",
                "This is your body demanding care"
            ]
            reading.state_label = "Burnout Risk"
        else:
            reading.interpretation = "Intense physical activation with mixed quality."
            reading.advice = [
                "High energy but use it wisely",
                "Avoid overexertion",
                "Monitor your body"
            ]
            reading.state_label = "Intense"

    return reading


def calculate_conflict_risk_meter(
    all_aspects: List[TransitAspect],
    date: datetime
) -> MeterReading:
    """
    Conflict Risk Meter - likelihood of arguments, confrontations, aggression.

    Spec: Section 5.6.2
    Focus: Mars hard aspects (square, opposition)
    """
    mars_aspects = filter_aspects_by_natal_planet(all_aspects, [Planet.MARS])
    hard_aspects = filter_hard_aspects(mars_aspects)

    reading = calculate_meter_score(hard_aspects, "conflict_risk", date)

    if reading.intensity < 30:
        reading.interpretation = "Low conflict risk. Tensions are minimal."
        reading.advice = ["Normal peaceful baseline"]
        reading.state_label = "Low Risk"
    elif reading.intensity < 60:
        reading.interpretation = "Moderate conflict risk. Some irritation or friction possible."
        reading.advice = [
            "Be mindful of tone",
            "Avoid unnecessary provocation",
            "Choose battles wisely"
        ]
        reading.state_label = "Moderate Risk"
    else:  # High intensity
        reading.interpretation = "High conflict risk. Arguments, confrontations, or aggression likely."
        reading.advice = [
            "Conflict potential is elevated",
            "Practice patience and restraint",
            "Count to ten before reacting",
            "Avoid volatile people or situations",
            "Channel anger into exercise or productive action"
        ]
        reading.state_label = "High Risk"

    return reading


def calculate_motivation_drive_meter(
    all_aspects: List[TransitAspect],
    date: datetime
) -> MeterReading:
    """
    Motivation Drive Meter - ambition, initiative, pushing forward.

    Spec: Section 5.6.3
    Planets: Mars (drive), Jupiter (expansion), Saturn (discipline)
    """
    motivation_planets = [Planet.MARS, Planet.JUPITER, Planet.SATURN]
    filtered_aspects = filter_aspects_by_natal_planet(all_aspects, motivation_planets)

    reading = calculate_meter_score(filtered_aspects, "motivation_drive", date)

    if reading.intensity < 40:
        reading.interpretation = "Normal motivation levels. No special push or drag."
        reading.advice = ["Standard productivity applies"]
        reading.state_label = "Normal"
    elif reading.intensity < 70:
        if reading.harmony > 70:
            reading.interpretation = "Strong motivation and focus. You feel driven and capable."
            reading.advice = [
                "Great time to advance goals",
                "Productivity is high",
                "Tackle important projects"
            ]
            reading.state_label = "Driven"
        elif reading.harmony < 30:
            reading.interpretation = "Low motivation or blocked drive. Procrastination, frustration, or obstacles."
            reading.advice = [
                "Lower your expectations temporarily",
                "Focus on small wins",
                "Address what's blocking you",
                "Be patient with yourself"
            ]
            reading.state_label = "Blocked"
        else:
            reading.interpretation = "Mixed motivation. Some drive, some resistance."
            reading.advice = [
                "Work with your natural rhythms",
                "Progress is possible but requires effort",
                "Stay consistent"
            ]
            reading.state_label = "Mixed"
    else:  # High intensity
        if reading.harmony > 70:
            reading.interpretation = "Exceptional drive and ambition. Major goal achievement window."
            reading.advice = [
                "Peak productivity period",
                "Major goals are achievable",
                "Capitalize on this exceptional drive",
                "Set ambitious targets"
            ]
            reading.state_label = "Peak Drive"
        elif reading.harmony < 30:
            reading.interpretation = "Severe motivational crisis. Burnout, depression, or major blocks."
            reading.advice = [
                "Something fundamental needs addressing",
                "Don't force yourself",
                "Seek help if this persists",
                "Reevaluate goals and direction"
            ]
            reading.state_label = "Crisis"
        else:
            reading.interpretation = "Intense push with mixed effectiveness."
            reading.advice = [
                "High drive but manage it wisely",
                "Avoid burnout",
                "Balance effort with rest"
            ]
            reading.state_label = "Intense Push"

    return reading


# ============================================================================
# LIFE DOMAIN METERS (Spec Section 5.7)
# ============================================================================

def calculate_career_ambition_meter(
    all_aspects: List[TransitAspect],
    date: datetime
) -> MeterReading:
    """
    Career Ambition Meter - professional drive, status, achievement.

    Spec: Section 5.7.1
    Focus: Saturn aspects + 10th house + Capricorn placements
    """
    # Saturn aspects
    saturn_aspects = filter_aspects_by_natal_planet(all_aspects, [Planet.SATURN])
    # 10th house
    tenth_house = filter_aspects_by_natal_house(all_aspects, [10])
    # Combine (simple concatenation - duplicates don't matter for scoring)
    combined = saturn_aspects + tenth_house

    reading = calculate_meter_score(combined, "career_ambition", date)

    if reading.intensity < 40:
        reading.interpretation = "Normal career activity. No special pressure or opportunity."
        reading.advice = ["Maintain steady progress"]
        reading.state_label = "Steady"
    elif reading.intensity < 70:
        if reading.harmony > 70:
            reading.interpretation = "Strong career momentum. Recognition, advancement, or achievement."
            reading.advice = [
                "Excellent time for career moves",
                "Your efforts are recognized",
                "Push for what you want"
            ]
            reading.state_label = "Advancing"
        elif reading.harmony < 30:
            reading.interpretation = "Career challenges or setbacks. Obstacles, criticism, or delays."
            reading.advice = [
                "Patience and persistence required",
                "Learn from setbacks",
                "Reevaluate strategy if needed",
                "Long-term thinking"
            ]
            reading.state_label = "Challenged"
        else:
            reading.interpretation = "Mixed career dynamics. Progress and obstacles coexist."
            reading.advice = [
                "Navigate carefully",
                "Celebrate small wins",
                "Stay professional"
            ]
            reading.state_label = "Mixed"
    else:  # High intensity
        if reading.harmony > 70:
            reading.interpretation = "Major career breakthrough window. Peak achievement and recognition."
            reading.advice = [
                "Career-defining opportunities present",
                "Go for major goals",
                "Your reputation shines",
                "Leadership opportunities"
            ]
            reading.state_label = "Breakthrough"
        elif reading.harmony < 30:
            reading.interpretation = "Major career crisis. Job loss, failure, or profound tests."
            reading.advice = [
                "Career is under major pressure",
                "Seek guidance and support",
                "This may be a necessary transformation",
                "Consider all options carefully"
            ]
            reading.state_label = "Crisis"
        else:
            reading.interpretation = "Intense career pressure with mixed outcomes."
            reading.advice = [
                "High-stakes career period",
                "Stay strategic and professional",
                "Major changes underway"
            ]
            reading.state_label = "High Stakes"

    return reading


def calculate_opportunity_window_meter(
    all_aspects: List[TransitAspect],
    date: datetime
) -> MeterReading:
    """
    Opportunity Window Meter - luck, expansion, doors opening.

    Spec: Section 5.7.2
    Focus: Jupiter aspects (the Great Benefic)
    """
    jupiter_aspects = filter_aspects_by_natal_planet(all_aspects, [Planet.JUPITER])

    reading = calculate_meter_score(jupiter_aspects, "opportunity_window", date)

    if reading.intensity < 40:
        reading.interpretation = "Normal opportunity baseline. No special luck or expansion."
        reading.advice = ["Create your own opportunities"]
        reading.state_label = "Normal"
    elif reading.intensity < 70:
        if reading.harmony > 70:
            reading.interpretation = "Good opportunities present. Things fall into place more easily."
            reading.advice = [
                "Be open to opportunities",
                "Say yes to invitations",
                "Network and connect",
                "Optimism is justified"
            ]
            reading.state_label = "Favorable"
        elif reading.harmony < 30:
            reading.interpretation = "False opportunities or overextension risk. Beware excess."
            reading.advice = [
                "Scrutinize opportunities carefully",
                "Avoid overcommitment",
                "Check the fine print",
                "Realistic expectations"
            ]
            reading.state_label = "Caution"
        else:
            reading.interpretation = "Mixed opportunities. Some are real, some may disappoint."
            reading.advice = [
                "Evaluate opportunities on merit",
                "Don't rush into commitments",
                "Trust your discernment"
            ]
            reading.state_label = "Mixed"
    else:  # High intensity
        if reading.harmony > 70:
            reading.interpretation = "Major opportunity window. Rare doors are opening. Peak luck."
            reading.advice = [
                "Exceptional opportunity period",
                "Be bold and say yes",
                "Expansion is favored",
                "This is your time - seize it"
            ]
            reading.state_label = "Peak Opportunity"
        elif reading.harmony < 30:
            reading.interpretation = "Major overextension or false promise risk. Beware excess."
            reading.advice = [
                "Too much too fast - slow down",
                "Major reality check needed",
                "Avoid grandiose schemes",
                "Get grounded"
            ]
            reading.state_label = "Excess Risk"
        else:
            reading.interpretation = "Major opportunities with complexity. Discernment required."
            reading.advice = [
                "Big possibilities are present",
                "Evaluate carefully",
                "Balance optimism with realism"
            ]
            reading.state_label = "Big Complex"

    return reading


def calculate_challenge_intensity_meter(
    all_aspects: List[TransitAspect],
    date: datetime
) -> MeterReading:
    """
    Challenge Intensity Meter - tests, lessons, hard work required.

    Spec: Section 5.7.3
    Focus: Saturn + outer planets (Uranus, Neptune, Pluto)
    """
    challenge_planets = [Planet.SATURN, Planet.URANUS, Planet.NEPTUNE, Planet.PLUTO]
    filtered_aspects = filter_aspects_by_natal_planet(all_aspects, challenge_planets)

    reading = calculate_meter_score(filtered_aspects, "challenge_intensity", date)

    if reading.intensity < 40:
        reading.interpretation = "Low challenge level. Life flows relatively easily."
        reading.advice = ["Appreciate the ease", "Build reserves for future challenges"]
        reading.state_label = "Easy"
    elif reading.intensity < 70:
        reading.interpretation = "Moderate challenges present. Growth through effort."
        reading.advice = [
            "Embrace the lessons",
            "Persistence pays off",
            "You're building character and skill",
            "Ask for help when needed"
        ]
        reading.state_label = "Moderate"
    else:  # High intensity
        reading.interpretation = "Major challenges active. Life is testing you significantly."
        reading.advice = [
            "You're in the crucible",
            "These tests are shaping who you're becoming",
            "Seek support and guidance",
            "One day at a time",
            "This difficulty serves your growth"
        ]
        reading.state_label = "Intense"

    return reading


def calculate_transformation_pressure_meter(
    all_aspects: List[TransitAspect],
    date: datetime
) -> MeterReading:
    """
    Transformation Pressure Meter - evolutionary push, metamorphosis.

    Spec: Section 5.7.4
    Focus: Pluto, Uranus, Neptune (agents of transformation)
    """
    transform_planets = [Planet.PLUTO, Planet.URANUS, Planet.NEPTUNE]
    filtered_aspects = filter_aspects_by_natal_planet(all_aspects, transform_planets)

    reading = calculate_meter_score(filtered_aspects, "transformation_pressure", date)

    if reading.intensity < 40:
        reading.interpretation = "Low transformation pressure. Relative stability."
        reading.advice = ["Integrate recent changes", "Stability is okay"]
        reading.state_label = "Stable"
    elif reading.intensity < 70:
        reading.interpretation = "Moderate transformation underway. Evolution is present."
        reading.advice = [
            "You're changing and that's good",
            "Release what no longer serves",
            "Embrace becoming",
            "Trust the process"
        ]
        reading.state_label = "Evolving"
    else:  # High intensity
        reading.interpretation = "Major transformation underway. Your life is fundamentally changing."
        reading.advice = [
            "Profound metamorphosis is happening",
            "Death and rebirth themes active",
            "You won't be the same person after this",
            "Surrender to the transformation",
            "Support is crucial - don't isolate"
        ]
        reading.state_label = "Metamorphosis"

    return reading


# ============================================================================
# ELEMENT METERS (Spec Section 5.3)
# ============================================================================

def calculate_element_distribution(
    natal_chart: dict,
    transit_chart: dict
) -> Dict[str, float]:
    """
    Calculate element distribution (blend of natal + transit).

    Spec: Section 5.3
    Formula: 70% natal baseline + 30% current transits

    Returns: {fire: %, earth: %, air: %, water: %}
    """
    # Count planets by element in natal chart
    natal_elements = {"fire": 0, "earth": 0, "air": 0, "water": 0}
    for planet in natal_chart.get("planets", []):
        sign = planet.get("sign")
        if sign:
            element = sign.element if hasattr(sign, "element") else None
            if element and element in natal_elements:
                natal_elements[element] += 1

    # Count planets by element in transit chart
    transit_elements = {"fire": 0, "earth": 0, "air": 0, "water": 0}
    for planet in transit_chart.get("planets", []):
        sign = planet.get("sign")
        if sign:
            element = sign.element if hasattr(sign, "element") else None
            if element and element in transit_elements:
                transit_elements[element] += 1

    # Calculate percentages (70% natal, 30% transit)
    total_planets = sum(natal_elements.values())
    blended = {}
    for elem in ["fire", "earth", "air", "water"]:
        natal_pct = (natal_elements[elem] / total_planets * 100) if total_planets > 0 else 25.0
        transit_pct = (transit_elements[elem] / total_planets * 100) if total_planets > 0 else 25.0
        blended[elem] = (0.7 * natal_pct) + (0.3 * transit_pct)

    return blended


def calculate_fire_energy_meter(
    all_aspects: List[TransitAspect],
    date: datetime,
    element_dist: Dict[str, float]
) -> MeterReading:
    """
    Fire Energy Meter - initiative, enthusiasm, action, passion.

    Spec: Section 5.3.1
    Fire signs: Aries, Leo, Sagittarius
    Fire planets: Sun, Mars, Jupiter
    """
    fire_planets = [Planet.SUN, Planet.MARS, Planet.JUPITER]
    filtered_aspects = filter_aspects_by_transit_planet(all_aspects, fire_planets)

    reading = calculate_meter_score(filtered_aspects, "fire_energy", date)

    fire_pct = element_dist.get("fire", 25.0)
    reading.additional_context["fire_percentage"] = fire_pct

    # Adjust interpretation based on element balance
    if fire_pct > 35:
        emphasis = "Fire is naturally strong in your chart."
    elif fire_pct < 15:
        emphasis = "Fire is naturally weak in your chart - transits may feel more impactful."
    else:
        emphasis = "Fire is balanced in your chart."

    if reading.intensity < 40:
        reading.interpretation = f"Low fire activation. Initiative and enthusiasm are quiet. {emphasis}"
        reading.advice = ["Rest from action", "Inner reflection time"]
        reading.state_label = "Low Fire"
    elif reading.intensity < 70:
        if reading.harmony > 60:
            reading.interpretation = f"Good fire energy. Enthusiasm, confidence, and initiative flow. {emphasis}"
            reading.advice = [
                "Take initiative",
                "Start new projects",
                "Express passion"
            ]
            reading.state_label = "Good Fire"
        else:
            reading.interpretation = f"Challenging fire energy. Anger, impatience, or recklessness risk. {emphasis}"
            reading.advice = [
                "Channel fire constructively",
                "Avoid impulsive actions",
                "Patience required"
            ]
            reading.state_label = "Difficult Fire"
    else:  # High intensity
        if reading.harmony > 60:
            reading.interpretation = f"Peak fire energy. Exceptional drive, passion, and courage. {emphasis}"
            reading.advice = [
                "Harness this powerful fire",
                "Be bold and take action",
                "Leadership opportunities"
            ]
            reading.state_label = "Peak Fire"
        else:
            reading.interpretation = f"Explosive fire energy. Anger, conflict, or burnout risk. {emphasis}"
            reading.advice = [
                "Manage fire carefully",
                "Avoid confrontations",
                "Channel into exercise"
            ]
            reading.state_label = "Explosive"

    return reading


def calculate_earth_energy_meter(
    all_aspects: List[TransitAspect],
    date: datetime,
    element_dist: Dict[str, float]
) -> MeterReading:
    """
    Earth Energy Meter - stability, practicality, grounding, material world.

    Spec: Section 5.3.2
    Earth signs: Taurus, Virgo, Capricorn
    Earth planets: Venus, Mercury (Virgo), Saturn
    """
    earth_planets = [Planet.VENUS, Planet.SATURN]
    filtered_aspects = filter_aspects_by_transit_planet(all_aspects, earth_planets)

    reading = calculate_meter_score(filtered_aspects, "earth_energy", date)

    earth_pct = element_dist.get("earth", 25.0)
    reading.additional_context["earth_percentage"] = earth_pct

    if earth_pct > 35:
        emphasis = "Earth is naturally strong in your chart."
    elif earth_pct < 15:
        emphasis = "Earth is naturally weak in your chart - grounding may require extra attention."
    else:
        emphasis = "Earth is balanced in your chart."

    if reading.intensity < 40:
        reading.interpretation = f"Low earth activation. Grounding and practical matters are quiet. {emphasis}"
        reading.advice = ["Routine maintenance", "Basic stability"]
        reading.state_label = "Low Earth"
    elif reading.intensity < 70:
        if reading.harmony > 60:
            reading.interpretation = f"Good earth energy. Practicality, stability, and productivity flow. {emphasis}"
            reading.advice = [
                "Build and stabilize",
                "Financial planning favored",
                "Create tangible results"
            ]
            reading.state_label = "Grounded"
        else:
            reading.interpretation = f"Challenging earth energy. Rigidity, limitation, or material stress. {emphasis}"
            reading.advice = [
                "Don't cling to false security",
                "Flexibility needed",
                "Address practical concerns"
            ]
            reading.state_label = "Stuck"
    else:  # High intensity
        if reading.harmony > 60:
            reading.interpretation = f"Peak earth energy. Exceptional productivity and manifestation power. {emphasis}"
            reading.advice = [
                "Build something lasting",
                "Major material gains possible",
                "Create solid foundations"
            ]
            reading.state_label = "Peak Manifestation"
        else:
            reading.interpretation = f"Heavy earth pressure. Severe limitations or material crisis. {emphasis}"
            reading.advice = [
                "Major practical challenges",
                "Address material reality",
                "Seek concrete solutions"
            ]
            reading.state_label = "Heavy"

    return reading


def calculate_air_energy_meter(
    all_aspects: List[TransitAspect],
    date: datetime,
    element_dist: Dict[str, float]
) -> MeterReading:
    """
    Air Energy Meter - communication, ideas, logic, connection.

    Spec: Section 5.3.3
    Air signs: Gemini, Libra, Aquarius
    Air planets: Mercury, Venus (Libra), Uranus
    """
    air_planets = [Planet.MERCURY, Planet.URANUS]
    filtered_aspects = filter_aspects_by_transit_planet(all_aspects, air_planets)

    reading = calculate_meter_score(filtered_aspects, "air_energy", date)

    air_pct = element_dist.get("air", 25.0)
    reading.additional_context["air_percentage"] = air_pct

    if air_pct > 35:
        emphasis = "Air is naturally strong in your chart."
    elif air_pct < 15:
        emphasis = "Air is naturally weak in your chart - mental activity may feel amplified."
    else:
        emphasis = "Air is balanced in your chart."

    if reading.intensity < 40:
        reading.interpretation = f"Low air activation. Mental activity and communication are quiet. {emphasis}"
        reading.advice = ["Mental rest", "Intuition over logic"]
        reading.state_label = "Mental Quiet"
    elif reading.intensity < 70:
        if reading.harmony > 60:
            reading.interpretation = f"Good air energy. Ideas flow, communication is clear, connections form. {emphasis}"
            reading.advice = [
                "Intellectual pursuits favored",
                "Network and communicate",
                "Learn and teach"
            ]
            reading.state_label = "Clear Thinking"
        else:
            reading.interpretation = f"Challenging air energy. Anxiety, overthinking, or disconnection. {emphasis}"
            reading.advice = [
                "Get out of your head",
                "Ground in body and feelings",
                "Limit information overload"
            ]
            reading.state_label = "Scattered Mind"
    else:  # High intensity
        if reading.harmony > 60:
            reading.interpretation = f"Peak air energy. Brilliant ideas, exceptional communication, breakthroughs. {emphasis}"
            reading.advice = [
                "Genius-level thinking",
                "Share your ideas widely",
                "Intellectual breakthroughs"
            ]
            reading.state_label = "Genius Air"
        else:
            reading.interpretation = f"Extreme mental pressure. Severe anxiety, confusion, or information overload. {emphasis}"
            reading.advice = [
                "Serious mental overwhelm",
                "Unplug and rest your mind",
                "Seek support if spiraling"
            ]
            reading.state_label = "Mental Overload"

    return reading


def calculate_water_energy_meter(
    all_aspects: List[TransitAspect],
    date: datetime,
    element_dist: Dict[str, float]
) -> MeterReading:
    """
    Water Energy Meter - emotion, intuition, empathy, spirituality.

    Spec: Section 5.3.4
    Water signs: Cancer, Scorpio, Pisces
    Water planets: Moon, Pluto, Neptune
    """
    water_planets = [Planet.MOON, Planet.PLUTO, Planet.NEPTUNE]
    filtered_aspects = filter_aspects_by_transit_planet(all_aspects, water_planets)

    reading = calculate_meter_score(filtered_aspects, "water_energy", date)

    water_pct = element_dist.get("water", 25.0)
    reading.additional_context["water_percentage"] = water_pct

    if water_pct > 35:
        emphasis = "Water is naturally strong in your chart."
    elif water_pct < 15:
        emphasis = "Water is naturally weak in your chart - emotional themes may feel more intense."
    else:
        emphasis = "Water is balanced in your chart."

    if reading.intensity < 40:
        reading.interpretation = f"Low water activation. Emotions and intuition are calm. {emphasis}"
        reading.advice = ["Emotional stability", "Logic and structure emphasized"]
        reading.state_label = "Calm Waters"
    elif reading.intensity < 70:
        if reading.harmony > 60:
            reading.interpretation = f"Good water energy. Emotions flow, intuition is clear, empathy is high. {emphasis}"
            reading.advice = [
                "Trust your intuition",
                "Connect emotionally",
                "Creative and spiritual pursuits"
            ]
            reading.state_label = "Flowing Water"
        else:
            reading.interpretation = f"Challenging water energy. Emotional overwhelm, confusion, or boundary issues. {emphasis}"
            reading.advice = [
                "Protect your emotional space",
                "Set boundaries",
                "Ground and center",
                "Avoid escapism"
            ]
            reading.state_label = "Turbulent"
    else:  # High intensity
        if reading.harmony > 60:
            reading.interpretation = f"Peak water energy. Profound emotional depth, spiritual connection, empathic gifts. {emphasis}"
            reading.advice = [
                "Deep healing available",
                "Spiritual breakthroughs",
                "Profound compassion",
                "Trust the mystery"
            ]
            reading.state_label = "Deep Water Magic"
        else:
            reading.interpretation = f"Extreme emotional intensity. Potential overwhelm, crisis, or dissolution. {emphasis}"
            reading.advice = [
                "Emotional emergency - seek support",
                "Don't go through this alone",
                "Professional help may be needed",
                "You will surface again"
            ]
            reading.state_label = "Drowning Risk"

    return reading


# ============================================================================
# SPECIALIZED METERS (Spec Section 5.8)
# ============================================================================

def calculate_intuition_spirituality_meter(
    all_aspects: List[TransitAspect],
    date: datetime
) -> MeterReading:
    """
    Intuition/Spirituality Meter - psychic sensitivity, spiritual connection.

    Spec: Section 5.8.1
    Focus: Neptune + Moon + 12th house
    """
    spirit_planets = [Planet.NEPTUNE, Planet.MOON]
    filtered_aspects = filter_aspects_by_natal_planet(all_aspects, spirit_planets)
    twelfth_house = filter_aspects_by_natal_house(all_aspects, [12])
    combined = filtered_aspects + twelfth_house

    reading = calculate_meter_score(combined, "intuition_spirituality", date)

    if reading.intensity < 40:
        reading.interpretation = "Normal spiritual baseline. Intuition is quiet."
        reading.advice = ["Routine spiritual practices"]
        reading.state_label = "Baseline"
    elif reading.intensity < 70:
        if reading.harmony > 60:
            reading.interpretation = "Heightened intuition and spiritual connection. The veil is thin."
            reading.advice = [
                "Trust your intuition",
                "Meditation and prayer favored",
                "Pay attention to dreams",
                "Spiritual guidance is available"
            ]
            reading.state_label = "Connected"
        else:
            reading.interpretation = "Spiritual confusion or false guidance. Discernment compromised."
            reading.advice = [
                "Be wary of delusion",
                "Ground your spiritual practice",
                "Avoid gurus or cults",
                "Trust your common sense"
            ]
            reading.state_label = "Confused"
    else:  # High intensity
        if reading.harmony > 60:
            reading.interpretation = "Peak spiritual opening. Mystical experiences, profound insights, divine connection."
            reading.advice = [
                "Rare spiritual opportunity",
                "The cosmos speaks directly",
                "Document your revelations",
                "Sacred experiences are unfolding"
            ]
            reading.state_label = "Mystical"
        else:
            reading.interpretation = "Spiritual crisis or psychic overwhelm. Ego dissolution or dark night themes."
            reading.advice = [
                "Spiritual emergency",
                "Seek grounded guidance",
                "This is part of the path but get support",
                "The dark night leads to dawn"
            ]
            reading.state_label = "Dark Night"

    return reading


def calculate_innovation_breakthrough_meter(
    all_aspects: List[TransitAspect],
    date: datetime
) -> MeterReading:
    """
    Innovation/Breakthrough Meter - eureka moments, revolutionary thinking.

    Spec: Section 5.8.2
    Focus: Uranus aspects (the Awakener)
    """
    uranus_aspects = filter_aspects_by_natal_planet(all_aspects, [Planet.URANUS])

    reading = calculate_meter_score(uranus_aspects, "innovation_breakthrough", date)

    if reading.intensity < 40:
        reading.interpretation = "Low innovation activation. Status quo prevails."
        reading.advice = ["Routine thinking", "Incremental change"]
        reading.state_label = "Status Quo"
    elif reading.intensity < 70:
        if reading.harmony > 60:
            reading.interpretation = "Good innovation energy. Fresh perspectives, creative solutions, breakthroughs."
            reading.advice = [
                "Think outside the box",
                "Try new approaches",
                "Innovation is favored",
                "Embrace the unconventional"
            ]
            reading.state_label = "Innovative"
        else:
            reading.interpretation = "Disruptive change or rebellion. Chaos, instability, or forced change."
            reading.advice = [
                "Change is happening whether you like it or not",
                "Stay flexible",
                "Don't resist necessary evolution",
                "Chaos precedes new order"
            ]
            reading.state_label = "Disruptive"
    else:  # High intensity
        if reading.harmony > 60:
            reading.interpretation = "Major breakthrough window. Revolutionary insights, paradigm shifts, liberation."
            reading.advice = [
                "Breakthrough potential is massive",
                "Break free from limitations",
                "Revolutionary changes possible",
                "Authentic self emerges"
            ]
            reading.state_label = "Revolutionary"
        else:
            reading.interpretation = "Extreme disruption or upheaval. Life is being radically restructured."
            reading.advice = [
                "Major upheaval underway",
                "Old structures are collapsing",
                "This breakdown enables breakthrough",
                "Stay grounded through chaos"
            ]
            reading.state_label = "Upheaval"

    return reading


def calculate_karmic_lessons_meter(
    all_aspects: List[TransitAspect],
    date: datetime
) -> MeterReading:
    """
    Karmic Lessons Meter - soul growth, destiny themes, life lessons.

    Spec: Section 5.8.3
    Focus: Saturn (the Teacher) + North Node
    """
    karmic_planets = [Planet.SATURN, Planet.NORTH_NODE]
    filtered_aspects = filter_aspects_by_natal_planet(all_aspects, karmic_planets)

    reading = calculate_meter_score(filtered_aspects, "karmic_lessons", date)

    if reading.intensity < 40:
        reading.interpretation = "Low karmic pressure. No major life lessons active."
        reading.advice = ["Integration period", "Apply past lessons"]
        reading.state_label = "Integration"
    elif reading.intensity < 70:
        reading.interpretation = "Active life lessons. The universe is teaching important themes."
        reading.advice = [
            "Pay attention to recurring patterns",
            "These lessons are gifts",
            "Growth through experience",
            "Wisdom is being forged"
        ]
        reading.state_label = "Learning"
    else:  # High intensity
        reading.interpretation = "Major karmic themes active. Soul-level lessons and destiny work."
        reading.advice = [
            "You're in soul school right now",
            "These lessons are profound and necessary",
            "Your evolution is accelerating",
            "Embrace the growth even when it's hard",
            "This is what you came here to learn"
        ]
        reading.state_label = "Soul Lessons"

    return reading


def calculate_social_collective_meter(
    all_aspects: List[TransitAspect],
    date: datetime
) -> MeterReading:
    """
    Social/Collective Energy Meter - community, society, collective themes.

    Spec: Section 5.8.4
    Focus: Outer planets (Uranus, Neptune, Pluto) + 11th house
    """
    collective_planets = [Planet.URANUS, Planet.NEPTUNE, Planet.PLUTO]
    filtered_aspects = filter_aspects_by_transit_planet(all_aspects, collective_planets)
    eleventh_house = filter_aspects_by_natal_house(all_aspects, [11])
    combined = filtered_aspects + eleventh_house

    reading = calculate_meter_score(combined, "social_collective", date)

    if reading.intensity < 40:
        reading.interpretation = "Low collective activation. Personal themes dominate."
        reading.advice = ["Focus on personal life", "Individual concerns"]
        reading.state_label = "Personal Focus"
    elif reading.intensity < 70:
        reading.interpretation = "Moderate collective themes. Community, society, or group dynamics are active."
        reading.advice = [
            "Engage with community",
            "Group activities favored",
            "Your role in the collective",
            "Social consciousness"
        ]
        reading.state_label = "Social"
    else:  # High intensity
        reading.interpretation = "Major collective themes. You're connected to larger social/cultural movements."
        reading.advice = [
            "Your life is connected to bigger forces",
            "Collective themes are personal for you now",
            "You may have a role in social change",
            "Individual and collective intertwine"
        ]
        reading.state_label = "Collective Actor"

    return reading


# ============================================================================
# Master Function: Get All Meters
# ============================================================================

def convert_to_transit_aspects(
    natal_chart: dict,
    transit_chart: dict,
    natal_transit_aspects: list
) -> List[TransitAspect]:
    """
    Convert NatalTransitAspect objects to TransitAspect format.

    Maps data from astro.find_natal_transit_aspects() to format
    expected by astrometers.core algorithms.
    """
    transit_aspects = []

    for aspect in natal_transit_aspects:
        # Get natal planet data
        natal_planet_data = next(
            (p for p in natal_chart["planets"] if p["name"] == aspect.natal_planet),
            None
        )
        if not natal_planet_data:
            continue

        # Get transit planet data
        transit_planet_data = next(
            (p for p in transit_chart["planets"] if p["name"] == aspect.transit_planet),
            None
        )
        if not transit_planet_data:
            continue

        # Determine max orb based on aspect type (from constants)
        max_orb_map = {
            AspectType.CONJUNCTION: 8.0,
            AspectType.OPPOSITION: 8.0,
            AspectType.TRINE: 8.0,
            AspectType.SQUARE: 7.0,
            AspectType.SEXTILE: 6.0,
        }
        max_orb = max_orb_map.get(aspect.aspect_type, 8.0)

        # Calculate tomorrow's orb (simple approximation)
        if aspect.applying:
            tomorrow_deviation = aspect.orb - 0.2  # Moving closer
        else:
            tomorrow_deviation = aspect.orb + 0.2  # Moving apart

        # Create TransitAspect
        ta = TransitAspect(
            natal_planet=aspect.natal_planet,
            natal_sign=aspect.natal_sign,
            natal_house=aspect.natal_house,
            transit_planet=aspect.transit_planet,
            aspect_type=aspect.aspect_type,
            orb_deviation=aspect.orb,
            max_orb=max_orb,
            natal_degree_in_sign=natal_planet_data.get("signed_degree", 0.0),
            ascendant_sign=natal_chart.get("ascendant_sign"),
            sensitivity=1.0,
            today_deviation=aspect.orb,
            tomorrow_deviation=tomorrow_deviation,
            label=f"Transit {aspect.transit_planet.value.title()} {aspect.aspect_type.value.title()} Natal {aspect.natal_planet.value.title()}"
        )
        transit_aspects.append(ta)

    return transit_aspects


class AllMetersReading(BaseModel):
    """Complete reading of all 23 meters with metadata."""
    date: datetime
    natal_chart_summary: Dict[str, Any]
    transit_summary: Dict[str, Any]
    aspect_count: int

    # Global Meters (2)
    overall_intensity: MeterReading
    overall_harmony: MeterReading

    # Element Meters (4)
    fire_energy: MeterReading
    earth_energy: MeterReading
    air_energy: MeterReading
    water_energy: MeterReading

    # Cognitive Meters (3)
    mental_clarity: MeterReading
    decision_quality: MeterReading
    communication_flow: MeterReading

    # Emotional Meters (3)
    emotional_intensity: MeterReading
    relationship_harmony: MeterReading
    emotional_resilience: MeterReading

    # Physical/Action Meters (3)
    physical_energy: MeterReading
    conflict_risk: MeterReading
    motivation_drive: MeterReading

    # Life Domain Meters (4)
    career_ambition: MeterReading
    opportunity_window: MeterReading
    challenge_intensity: MeterReading
    transformation_pressure: MeterReading

    # Specialized Meters (4)
    intuition_spirituality: MeterReading
    innovation_breakthrough: MeterReading
    karmic_lessons: MeterReading
    social_collective: MeterReading


def get_meters(
    natal_chart: dict,
    transit_chart: dict,
    date: Optional[datetime] = None
) -> AllMetersReading:
    """
    Calculate all 23 astrological meters for a given date.

    Args:
        natal_chart: User's natal chart from compute_birth_chart()
        transit_chart: Transit chart for target date from compute_birth_chart()
        date: Date for calculation (defaults to today)

    Returns:
        AllMetersReading with all 23 meters calculated

    Example:
        >>> from astro import compute_birth_chart
        >>> from datetime import datetime
        >>> natal_chart, _ = compute_birth_chart("1990-06-15")
        >>> transit_chart, _ = compute_birth_chart("2025-10-26", birth_time="12:00")
        >>> meters = get_meters(natal_chart, transit_chart)
        >>> print(f"Overall Intensity: {meters.overall_intensity.intensity:.1f}/100")
    """
    # Import find_natal_transit_aspects here to avoid circular import
    from astro import find_natal_transit_aspects

    if date is None:
        date = datetime.now()

    # Find all natal-transit aspects
    natal_transit_aspects = find_natal_transit_aspects(
        natal_chart,
        transit_chart,
        orb=8.0
    )

    # Convert to TransitAspect format
    all_aspects = convert_to_transit_aspects(
        natal_chart,
        transit_chart,
        natal_transit_aspects
    )

    # Calculate element distribution
    element_dist = calculate_element_distribution(natal_chart, transit_chart)

    # Calculate all meters
    return AllMetersReading(
        date=date,
        natal_chart_summary={
            "sun_sign": natal_chart.get("sun_sign"),
            "ascendant_sign": natal_chart.get("ascendant_sign"),
            "moon_sign": next((p["sign"] for p in natal_chart["planets"] if p["name"] == "moon"), None)
        },
        transit_summary={
            "sun_sign": transit_chart.get("sun_sign"),
            "aspect_count": len(natal_transit_aspects)
        },
        aspect_count=len(all_aspects),

        # Global Meters
        overall_intensity=calculate_overall_intensity_meter(all_aspects, date),
        overall_harmony=calculate_overall_harmony_meter(all_aspects, date),

        # Element Meters
        fire_energy=calculate_fire_energy_meter(all_aspects, date, element_dist),
        earth_energy=calculate_earth_energy_meter(all_aspects, date, element_dist),
        air_energy=calculate_air_energy_meter(all_aspects, date, element_dist),
        water_energy=calculate_water_energy_meter(all_aspects, date, element_dist),

        # Cognitive Meters
        mental_clarity=calculate_mental_clarity_meter(all_aspects, date, transit_chart),
        decision_quality=calculate_decision_quality_meter(all_aspects, date),
        communication_flow=calculate_communication_flow_meter(all_aspects, date),

        # Emotional Meters
        emotional_intensity=calculate_emotional_intensity_meter(all_aspects, date),
        relationship_harmony=calculate_relationship_harmony_meter(all_aspects, date),
        emotional_resilience=calculate_emotional_resilience_meter(all_aspects, date),

        # Physical/Action Meters
        physical_energy=calculate_physical_energy_meter(all_aspects, date),
        conflict_risk=calculate_conflict_risk_meter(all_aspects, date),
        motivation_drive=calculate_motivation_drive_meter(all_aspects, date),

        # Life Domain Meters
        career_ambition=calculate_career_ambition_meter(all_aspects, date),
        opportunity_window=calculate_opportunity_window_meter(all_aspects, date),
        challenge_intensity=calculate_challenge_intensity_meter(all_aspects, date),
        transformation_pressure=calculate_transformation_pressure_meter(all_aspects, date),

        # Specialized Meters
        intuition_spirituality=calculate_intuition_spirituality_meter(all_aspects, date),
        innovation_breakthrough=calculate_innovation_breakthrough_meter(all_aspects, date),
        karmic_lessons=calculate_karmic_lessons_meter(all_aspects, date),
        social_collective=calculate_social_collective_meter(all_aspects, date),
    )
