# Sprint: Implement Meter Taxonomy & Specifications

**Sprint Goal**: Implement Section 5 of the Astrometers V2.0 specification - the 23-meter taxonomy system that translates raw DTI/HQS scores into domain-specific insights with full explainability.

**Spec Reference**: `arca-backend/functions/astrometers/astrometers.md` Section 5 (lines 763-2500+)

---

## Current Implementation Status

### ✅ Completed (Sprint 1-4)
All foundational algorithms are implemented and tested:

**Core Algorithm** (`arca-backend/functions/astrometers/core.py`)
- `calculate_aspect_contribution()` - Calculate W_i × P_i × Q_i for single aspect
- `calculate_astrometers()` - Sum all aspects to get total DTI/HQS
- `get_score_breakdown_text()` - Debug output
- Data classes: `TransitAspect`, `AspectContribution`, `AstrometerScore`
- **Spec Reference**: Section 2 (Core Algorithm)

**Weightage Factor W_i** (`arca-backend/functions/astrometers/weightage.py`)
- `calculate_weightage()` - Planet base + dignity + house multiplier + ruler bonus + sensitivity
- `calculate_chart_ruler()` - Determine ascendant ruler
- `get_weightage_breakdown()` - Explainability
- **Spec Reference**: Section 2.3.A

**Transit Power P_i** (`arca-backend/functions/astrometers/transit_power.py`)
- `calculate_transit_power_complete()` - Aspect base × orb factor × direction mod × station mod × transit weight
- `detect_aspect()` - Find aspects within orb
- `calculate_orb_factor()` - Linear decay from exact
- `get_direction_modifier()` - Applying/exact/separating
- `calculate_station_modifier()` - Retrograde station boost
- **Spec Reference**: Section 2.3.B

**Quality Factor Q_i** (`arca-backend/functions/astrometers/quality.py`)
- `calculate_quality_factor()` - Aspect harmonic nature (-1.0 to +1.0)
- Dynamic conjunction quality based on planet combinations
- **Spec Reference**: Section 2.3.C

**Dignity System** (`arca-backend/functions/astrometers/dignity.py`)
- `calculate_dignity_score()` - Domicile/exaltation/detriment/fall
- **Spec Reference**: Section 3.2

**Normalization** (`arca-backend/functions/astrometers/normalization.py`)
- `normalize_intensity()` - DTI to 0-100 scale
- `normalize_harmony()` - HQS to 0-100 scale (50 = neutral)
- `normalize_with_soft_ceiling()` - Logarithmic compression for outliers
- `get_intensity_label()` - "Quiet", "Moderate", "High", "Very High", "Extreme"
- `get_harmony_label()` - "Very Challenging", "Challenging", "Mixed", "Supportive", "Very Supportive"
- **Spec Reference**: Section 2.4-2.5

**Constants** (`arca-backend/functions/astrometers/constants.py`)
- All planet base scores, house multipliers, aspect intensities
- Essential dignities table
- Orb definitions by aspect and planet type
- Direction and station modifiers
- Quality factors
- **Spec Reference**: Sections 2.3, 3.2, 4.1

**Test Coverage** (`arca-backend/functions/astrometers/tests/`)
- `test_core.py` - 60+ tests for DTI/HQS calculations
- `test_weightage.py` - 40+ tests for W_i
- `test_transit_power.py` - 50+ tests for P_i
- `test_quality.py` - 30+ tests for Q_i
- `test_dignity.py` - 35+ tests for dignity system
- `test_normalization.py` - 30+ tests for scaling

---

## What We're Building: The 23-Meter System

### Overview
The meter system transforms raw DTI/HQS scores into actionable insights by:
1. **Filtering aspects** - Each meter focuses on specific planets/houses
2. **Calculating scores** - Using existing DTI/HQS algorithms on filtered aspects
3. **Normalizing** - Converting to 0-100 scales
4. **Interpreting** - Generating natural language explanations
5. **Advising** - Providing actionable guidance
6. **Explaining** - Showing which aspects contribute and why

### The 23 Meters (Spec Section 5.1)

**🌍 Global Meters (2)**
- Overall Intensity Gauge - Total DTI across all aspects
- Overall Harmony Meter - Total HQS with supportive/challenging breakdown

**🔥 Element Meters (4)**
- Fire Energy - Initiative, enthusiasm, action
- Earth Energy - Stability, practicality, grounding
- Air Energy - Communication, ideas, logic
- Water Energy - Emotion, intuition, empathy

**🧠 Cognitive Meters (3)**
- Mental Clarity - Mercury aspects, 3rd house
- Decision Quality - Mercury + Jupiter + Saturn + Neptune
- Communication Flow - Mercury + Venus + Mars

**❤️ Emotional Meters (3)**
- Emotional Intensity - Moon + Venus + Pluto + Neptune
- Relationship Harmony - Venus + 7th house
- Emotional Resilience - Sun + Saturn-Moon + Mars + Jupiter

**⚡ Physical/Action Meters (3)**
- Physical Energy - Sun + Mars
- Conflict Risk - Mars hard aspects
- Motivation Drive - Mars + Jupiter + Saturn

**🎯 Life Domain Meters (4)**
- Career Ambition - Saturn + 10th house + Capricorn
- Opportunity Window - Jupiter aspects
- Challenge Intensity - Saturn + outer planets
- Transformation Pressure - Pluto + Uranus + Neptune

**🔮 Specialized Meters (4)**
- Intuition/Spirituality - Neptune + Moon + 12th house
- Innovation/Breakthroughs - Uranus aspects
- Karmic Lessons - Saturn + North Node
- Social/Collective Energy - Outer planets + 11th house

---

## Architecture: MeterReading Model

Based on Spec Section 7.4.2-7.4.3, each meter returns a `MeterReading` object:

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Dict

class MeterReading(BaseModel):
    """Complete meter reading with explainability."""

    # Core values
    meter_name: str = Field(description="Meter identifier (e.g., 'mental_clarity')")
    date: datetime = Field(description="Date of calculation")
    intensity: float = Field(ge=0, le=100, description="Intensity meter (0-100)")
    harmony: float = Field(ge=0, le=100, description="Harmony meter (0-100, 50=neutral)")

    # Interpretation
    state_label: str = Field(description="Current state (e.g., 'Sharp Focus', 'Scattered')")
    interpretation: str = Field(description="Natural language interpretation")
    advice: List[str] = Field(description="Actionable guidance items")

    # Explainability
    top_aspects: List[AspectContribution] = Field(
        description="Top 5 contributing aspects with W_i, P_i, Q_i breakdown"
    )
    raw_scores: Dict[str, float] = Field(
        description="Raw DTI and HQS before normalization"
    )

    # Optional metadata
    additional_context: Dict[str, any] = Field(
        default_factory=dict,
        description="Meter-specific context (e.g., Mercury retrograde, element deviations)"
    )
```

### AspectContribution Structure (for explainability)

Already defined in `core.py`:

```python
@dataclass
class AspectContribution:
    """Breakdown of a single aspect's contribution."""
    label: str                    # "Transit Saturn square Natal Sun"
    natal_planet: Planet
    transit_planet: Planet
    aspect_type: AspectType
    weightage: float             # W_i value
    transit_power: float         # P_i value
    quality_factor: float        # Q_i value
    dti_contribution: float      # W_i × P_i
    hqs_contribution: float      # W_i × P_i × Q_i
```

---

## Implementation Plan

### File 1: `arca-backend/functions/astrometers/meters.py`

**Purpose**: Implement all 23 meters with filtering, calculation, interpretation, and advice generation.

**Structure**:

```python
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

from typing import List, Dict, Optional
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
    additional_context: Dict[str, any] = Field(default_factory=dict)


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
        contrib_text = "\\n\\nTop contributing aspects:\\n"
        for aspect in top_3:
            contrib_text += f"• {aspect.label} (DTI: {aspect.dti_contribution:.1f})\\n"
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
    breakdown = f"\\n\\nAspect breakdown: {supportive} supportive, {challenging} challenging, {neutral} neutral"
    reading.interpretation += breakdown

    reading.state_label = get_harmony_label(reading.harmony)
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
    # This requires accessing planet elements from charts
    # Implementation depends on chart structure from astro.py
    # Placeholder for now - would use chart["distributions"]["elements"]
    return {
        "fire": 25.0,
        "earth": 25.0,
        "air": 25.0,
        "water": 25.0
    }


# [Continue with remaining 18 meters...]
# Mental Clarity, Decision Quality, Communication Flow (Cognitive)
# Emotional Intensity, Relationship Harmony, Emotional Resilience (Emotional)
# Physical Energy, Conflict Risk, Motivation Drive (Physical/Action)
# Career Ambition, Opportunity Window, Challenge Intensity, Transformation Pressure (Life Domain)
# Intuition/Spirituality, Innovation/Breakthroughs, Karmic Lessons, Social/Collective (Specialized)


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
    mercury_rx = transit_chart["planets"][2].get("retrograde", False)  # Mercury index
    if mercury_rx:
        reading.harmony *= 0.6  # Reduce clarity during Rx
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
        reading.interpretation += "\\n\\nNote: Mercury is retrograde, adding review, revision, and reconsideration themes."

    return reading


# Continue implementing remaining 20 meters...
# Each follows same pattern:
# 1. Filter aspects to relevant planets/houses
# 2. Calculate using calculate_meter_score()
# 3. Add meter-specific interpretation logic
# 4. Generate tailored advice
# 5. Return MeterReading with full explainability
```

**Key Implementation Notes**:
- Use existing functions from `core.py`, `normalization.py`
- Each meter function returns `MeterReading` Pydantic model
- Filter aspects first, then calculate (modular and testable)
- Interpretation logic based on intensity/harmony matrix (Spec Section 5)
- Top 5 aspects provide explainability
- Additional context field for meter-specific data (Rx status, element deviations, etc.)

---

### File 2: `arca-backend/functions/astrometers/show_meters.py`

**Purpose**: Demo script showing all meters for today with a fixed test user.

```python
"""
Demo script to display all 23 meters for today.

Usage:
  cd /Users/elie/git/arca/arca-backend
  uv run python -m functions.astrometers.show_meters

Fixed test user: Born 1990-06-15 (Gemini Sun)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Import astro functions
from astro import compute_birth_chart, find_natal_transit_aspects, Planet

# Import astrometer functions
from astrometers.core import TransitAspect
from astrometers.meters import (
    calculate_overall_intensity_meter,
    calculate_overall_harmony_meter,
    calculate_mental_clarity_meter,
    # ... import all 23 meter functions
)

console = Console()


def convert_to_transit_aspects(
    natal_chart: dict,
    transit_chart: dict,
    natal_transit_aspects: list
) -> list[TransitAspect]:
    """
    Convert NatalTransitAspect objects to TransitAspect format.

    Maps data from astro.find_natal_transit_aspects() to format
    expected by astrometers.core algorithms.
    """
    transit_aspects = []

    for aspect in natal_transit_aspects:
        # Get natal planet data
        natal_planet_data = next(
            p for p in natal_chart["planets"]
            if p["name"] == aspect.natal_planet
        )

        # Get transit planet data
        transit_planet_data = next(
            p for p in transit_chart["planets"]
            if p["name"] == aspect.transit_planet
        )

        # Create TransitAspect
        ta = TransitAspect(
            natal_planet=Planet(aspect.natal_planet),
            natal_sign=aspect.natal_sign,
            natal_house=aspect.natal_house,
            transit_planet=Planet(aspect.transit_planet),
            aspect_type=aspect.aspect_type,
            orb_deviation=aspect.orb,
            max_orb=8.0,  # Default, refine based on aspect type
            natal_degree_in_sign=natal_planet_data.get("signed_degree", 0),
            ascendant_sign=natal_chart.get("ascendant_sign"),
            sensitivity=1.0,
            today_deviation=aspect.orb,
            tomorrow_deviation=aspect.orb - 0.1 if aspect.applying else aspect.orb + 0.1,
            label=f"Transit {aspect.transit_planet} {aspect.aspect_type.value} Natal {aspect.natal_planet}"
        )
        transit_aspects.append(ta)

    return transit_aspects


def display_meter_reading(reading, console):
    """Display a single meter reading with rich formatting."""

    # Create header
    header = f"[bold]{reading.meter_name.replace('_', ' ').title()}[/bold]"

    # Create table for scores
    table = Table(show_header=False, box=None)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="yellow")

    table.add_row("Intensity", f"{reading.intensity:.1f}/100")
    table.add_row("Harmony", f"{reading.harmony:.1f}/100")
    table.add_row("State", reading.state_label)
    table.add_row("Raw DTI", f"{reading.raw_scores['dti']:.2f}")
    table.add_row("Raw HQS", f"{reading.raw_scores['hqs']:.2f}")

    # Create content
    content = f"""
{table}

[bold]Interpretation:[/bold]
{reading.interpretation}

[bold]Advice:[/bold]
"""
    for advice_item in reading.advice:
        content += f"• {advice_item}\\n"

    # Top aspects
    if reading.top_aspects:
        content += "\\n[bold]Top Contributing Aspects:[/bold]\\n"
        for i, aspect in enumerate(reading.top_aspects[:3], 1):
            content += f"{i}. {aspect.label}\\n"
            content += f"   W_i={aspect.weightage:.1f}, P_i={aspect.transit_power:.1f}, Q_i={aspect.quality_factor:.1f}\\n"
            content += f"   DTI={aspect.dti_contribution:.1f}, HQS={aspect.hqs_contribution:.1f}\\n"

    # Display panel
    panel = Panel(content, title=header, border_style="blue")
    console.print(panel)
    console.print()


def main():
    """Run meter demo for fixed test user."""

    console.print("[bold blue]Astro Meters Demo - All 23 Meters[/bold blue]\\n")

    # Fixed test user
    birth_date = "1990-06-15"  # Gemini Sun
    today = datetime.now().strftime("%Y-%m-%d")

    console.print(f"Test User: Born {birth_date}")
    console.print(f"Analysis Date: {today}\\n")

    # Get charts
    console.print("[yellow]Calculating natal chart...[/yellow]")
    natal_chart, is_exact = compute_birth_chart(birth_date)

    console.print("[yellow]Calculating transit chart...[/yellow]")
    transit_chart, _ = compute_birth_chart(today, birth_time="12:00")

    # Find aspects
    console.print("[yellow]Finding natal-transit aspects...[/yellow]")
    nt_aspects = find_natal_transit_aspects(natal_chart, transit_chart, orb=8.0)
    console.print(f"Found {len(nt_aspects)} aspects\\n")

    # Convert to TransitAspect format
    all_aspects = convert_to_transit_aspects(natal_chart, transit_chart, nt_aspects)

    # Calculate all meters
    date_obj = datetime.now()

    console.print("[bold green]═══════════════════════════════════════════[/bold green]")
    console.print("[bold green]GLOBAL METERS[/bold green]")
    console.print("[bold green]═══════════════════════════════════════════[/bold green]\\n")

    intensity = calculate_overall_intensity_meter(all_aspects, date_obj)
    display_meter_reading(intensity, console)

    harmony = calculate_overall_harmony_meter(all_aspects, date_obj)
    display_meter_reading(harmony, console)

    console.print("[bold green]═══════════════════════════════════════════[/bold green]")
    console.print("[bold green]COGNITIVE METERS[/bold green]")
    console.print("[bold green]═══════════════════════════════════════════[/bold green]\\n")

    clarity = calculate_mental_clarity_meter(all_aspects, date_obj, transit_chart)
    display_meter_reading(clarity, console)

    # ... continue for all 23 meters

    console.print("[bold blue]Demo complete![/bold blue]")


if __name__ == "__main__":
    main()
```

---

### File 3: Update `arca-backend/functions/astrometers/__init__.py`

Add meter exports:

```python
from .meters import (
    MeterReading,
    calculate_overall_intensity_meter,
    calculate_overall_harmony_meter,
    calculate_mental_clarity_meter,
    # ... all 23 meter functions
)

__all__ = [
    # ... existing exports
    "MeterReading",
    "calculate_overall_intensity_meter",
    "calculate_overall_harmony_meter",
    "calculate_mental_clarity_meter",
    # ... all 23 meter functions
]
```

---

### File 4: `arca-backend/functions/astrometers/tests/test_meters.py` (Optional)

Basic smoke tests:

```python
"""
Tests for meter calculation functions.

Ensures all meters calculate without errors and return valid MeterReading objects.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from datetime import datetime
from astro import Planet, AspectType, ZodiacSign
from astrometers.core import TransitAspect
from astrometers.meters import (
    calculate_overall_intensity_meter,
    calculate_overall_harmony_meter,
    calculate_mental_clarity_meter,
    MeterReading
)


@pytest.fixture
def sample_aspects():
    """Create sample transit aspects for testing."""
    return [
        TransitAspect(
            natal_planet=Planet.SUN,
            natal_sign=ZodiacSign.LEO,
            natal_house=10,
            transit_planet=Planet.SATURN,
            aspect_type=AspectType.SQUARE,
            orb_deviation=2.0,
            max_orb=8.0,
            today_deviation=2.0,
            tomorrow_deviation=1.8
        ),
        TransitAspect(
            natal_planet=Planet.MERCURY,
            natal_sign=ZodiacSign.GEMINI,
            natal_house=3,
            transit_planet=Planet.JUPITER,
            aspect_type=AspectType.TRINE,
            orb_deviation=1.5,
            max_orb=7.0,
            today_deviation=1.5,
            tomorrow_deviation=1.3
        )
    ]


def test_overall_intensity_meter_returns_valid_reading(sample_aspects):
    """Test that overall intensity meter returns valid MeterReading."""
    date = datetime.now()
    reading = calculate_overall_intensity_meter(sample_aspects, date)

    assert isinstance(reading, MeterReading)
    assert reading.meter_name == "overall_intensity"
    assert 0 <= reading.intensity <= 100
    assert 0 <= reading.harmony <= 100
    assert len(reading.advice) > 0
    assert reading.interpretation != ""


def test_overall_harmony_meter_returns_valid_reading(sample_aspects):
    """Test that overall harmony meter returns valid MeterReading."""
    date = datetime.now()
    reading = calculate_overall_harmony_meter(sample_aspects, date)

    assert isinstance(reading, MeterReading)
    assert reading.meter_name == "overall_harmony"
    assert 0 <= reading.intensity <= 100
    assert 0 <= reading.harmony <= 100


def test_mental_clarity_meter_with_mercury_aspects(sample_aspects):
    """Test mental clarity meter calculation."""
    date = datetime.now()
    transit_chart = {"planets": [{"retrograde": False}] * 11}  # Mock chart

    reading = calculate_mental_clarity_meter(sample_aspects, date, transit_chart)

    assert isinstance(reading, MeterReading)
    assert reading.meter_name == "mental_clarity"
    assert reading.state_label in ["Mental Quiet", "Sharp Focus", "Scattered", "Genius Mode", "Mental Overload", "Mixed Mental Energy", "Intense Mixed"]


def test_meter_with_no_aspects_returns_quiet_state():
    """Test that meters handle empty aspect list gracefully."""
    date = datetime.now()
    reading = calculate_overall_intensity_meter([], date)

    assert reading.intensity == 0.0
    assert reading.harmony == 50.0
    assert reading.state_label == "Quiet"
    assert len(reading.top_aspects) == 0


# Add tests for remaining 20 meters...
```

---

## Testing & Validation

### Commands (run from `/Users/elie/git/arca/arca-backend`)

```bash
# Run all tests including new meter tests
uv run pytest functions/astrometers/tests/

# Run only meter tests
uv run pytest functions/astrometers/tests/test_meters.py -v

# Run demo script
uv run python -m functions.astrometers.show_meters
```

### Expected Output from Demo Script

```
Astro Meters Demo - All 23 Meters

Test User: Born 1990-06-15
Analysis Date: 2025-10-26

Calculating natal chart...
Calculating transit chart...
Finding natal-transit aspects...
Found 12 aspects

═══════════════════════════════════════════
GLOBAL METERS
═══════════════════════════════════════════

╭─ Overall Intensity ──────────────────────╮
│ Intensity: 68.5/100                      │
│ Harmony: 42.3/100                        │
│ State: High + Mixed                      │
│ Raw DTI: 137.2                           │
│ Raw HQS: -15.4                           │
│                                          │
│ Interpretation:                          │
│ Significant astrological activity...     │
│                                          │
│ Advice:                                  │
│ • Pay attention to emerging themes       │
│ • This is not a time to coast           │
│ ...                                      │
│                                          │
│ Top Contributing Aspects:                │
│ 1. Transit Saturn square Natal Sun       │
│    W_i=45.0, P_i=9.2, Q_i=-1.0          │
│    DTI=414.0, HQS=-414.0                │
│ ...                                      │
╰──────────────────────────────────────────╯
```

---

## Function Reference Map

### From `astro.py`
**Path**: `/Users/elie/git/arca/arca-backend/functions/astro.py`

- `compute_birth_chart(birth_date, birth_time, birth_timezone, birth_lat, birth_lon)` (line 812)
  - Returns: `(chart_dict, is_exact)`
  - Used for: Getting natal and transit charts

- `find_natal_transit_aspects(natal_chart, transit_chart, orb)` (line 1160)
  - Returns: `list[NatalTransitAspect]`
  - Used for: Finding aspects between natal and transit planets

### From `astrometers/core.py`
**Path**: `/Users/elie/git/arca/arca-backend/functions/astrometers/core.py`

- `TransitAspect` (line 26)
  - Dataclass with all aspect data needed for W_i, P_i, Q_i

- `AspectContribution` (line 59)
  - Dataclass with W_i, P_i, Q_i breakdown for explainability

- `AstrometerScore` (line 73)
  - Dataclass with total DTI, HQS, contributions list

- `calculate_aspect_contribution(aspect: TransitAspect)` (line 81)
  - Returns: `AspectContribution`
  - Used for: Single aspect calculation

- `calculate_astrometers(aspects: List[TransitAspect])` (line 167)
  - Returns: `AstrometerScore`
  - Used for: Main calculation engine for filtered aspects

### From `astrometers/normalization.py`
**Path**: `/Users/elie/git/arca/arca-backend/functions/astrometers/normalization.py`

- `normalize_intensity(dti: float)` (line 97)
  - Returns: `float` (0-100)
  - Used for: Converting raw DTI to intensity meter

- `normalize_harmony(hqs: float)` (line 112)
  - Returns: `float` (0-100, 50=neutral)
  - Used for: Converting raw HQS to harmony meter

- `get_intensity_label(intensity: float)` (line 144)
  - Returns: `str` ("Quiet", "Mild", "Moderate", "High", "Very High", "Extreme")

- `get_harmony_label(harmony: float)` (line 159)
  - Returns: `str` ("Very Challenging", "Challenging", "Mixed", "Supportive", "Very Supportive")

### From `astrometers/weightage.py`
**Path**: `/Users/elie/git/arca/arca-backend/functions/astrometers/weightage.py`

- Used internally by `calculate_aspect_contribution()` - no direct calls needed

### From `astrometers/transit_power.py`
**Path**: `/Users/elie/git/arca/arca-backend/functions/astrometers/transit_power.py`

- Used internally by `calculate_aspect_contribution()` - no direct calls needed

### From `astrometers/quality.py`
**Path**: `/Users/elie/git/arca/arca-backend/functions/astrometers/quality.py`

- Used internally by `calculate_aspect_contribution()` - no direct calls needed

---

## Implementation Checklist

### Phase 1: Core Infrastructure
- [ ] Create `meters.py` with `MeterReading` model
- [ ] Implement helper filter functions
- [ ] Implement generic `calculate_meter_score()` function
- [ ] Test with 2 global meters (intensity + harmony)

### Phase 2: Meter Categories (implement in order)
- [ ] Global Meters (2): Overall Intensity, Overall Harmony
- [ ] Cognitive Meters (3): Mental Clarity, Decision Quality, Communication Flow
- [ ] Emotional Meters (3): Emotional Intensity, Relationship Harmony, Emotional Resilience
- [ ] Physical/Action Meters (3): Physical Energy, Conflict Risk, Motivation Drive
- [ ] Life Domain Meters (4): Career Ambition, Opportunity Window, Challenge Intensity, Transformation Pressure
- [ ] Element Meters (4): Fire, Earth, Air, Water Energy
- [ ] Specialized Meters (4): Intuition/Spirituality, Innovation, Karmic Lessons, Social Energy

### Phase 3: Demo & Testing
- [ ] Create `show_meters.py` demo script
- [ ] Test with fixed user (1990-06-15)
- [ ] Create `test_meters.py` with smoke tests
- [ ] Update `__init__.py` exports
- [ ] Run full test suite

### Phase 4: Documentation & Polish
- [ ] Add docstrings to all meter functions
- [ ] Document interpretation logic
- [ ] Add inline spec references
- [ ] Create usage examples

---

## Success Criteria

1. All 23 meters calculate successfully
2. Each returns valid `MeterReading` with all fields populated
3. Demo script runs without errors and displays formatted output
4. Test suite passes with 100% success rate
5. Explainability via `top_aspects` provides W_i, P_i, Q_i breakdown
6. Interpretations are contextual and actionable
7. Code is well-documented with spec references

---

## Spec References

**Primary Spec**: `/Users/elie/git/arca/arca-backend/functions/astrometers/astrometers.md`

- **Section 2**: Core Algorithm (DTI, HQS, W_i, P_i, Q_i) - Lines 26-250
- **Section 2.4**: Normalization to 0-100 scales - Lines 180-200
- **Section 2.5**: Interpretation matrices - Lines 201-250
- **Section 5**: Meter Taxonomy & Specifications - Lines 763-2500
  - 5.1: Overview of 23 meters - Lines 765-809
  - 5.2: Global Meters - Lines 812-965
  - 5.3: Element Meters - Lines 967-1057
  - 5.4: Cognitive Meters - Lines 1060-1278
  - 5.5: Emotional Meters - Lines 1281-1459
  - 5.6: Physical/Action Meters - Lines 1474-1696
  - 5.7: Life Domain Meters - Lines 1698-1997
  - 5.8: Specialized Meters - Lines 1999-2268
- **Section 7.4**: Meter Base Class & Architecture - Lines 2932-3329

---

## Notes

- Use `uv` for all Python operations (NOT pip)
- Virtual environment at: `/Users/elie/git/arca/arca-backend/.venv`
- All imports should use: `sys.path.insert(0, ...)` pattern for module resolution
- Pydantic models ensure type safety and API-readiness
- Each meter is independently testable due to filtering architecture
- Explainability is built-in via `AspectContribution` breakdown
- Demo script uses `rich` library for beautiful terminal output
