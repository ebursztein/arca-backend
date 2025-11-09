"""
Enhanced Moon Transit System

Dedicated module for comprehensive lunar analysis including:
- Moon aspects to natal chart
- Void-of-course detection
- Dispositor tracking
- Next lunar events (sign changes, phases, aspects)
- LLM-ready summaries

Separated from astro.py to reduce bloat and improve maintainability.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timedelta
from enum import Enum

# Import minimal dependencies from astro module
from astro import (
    Planet,
    ZodiacSign,
    House,
    AspectType,
    NatalTransitAspect,
    LunarPhase,
    find_natal_transit_aspects,
    calculate_lunar_phase,
    calculate_solar_house,
    compute_birth_chart,
    SIGN_RULERS,
)


# =============================================================================
# Moon-Specific Models
# =============================================================================

class VoidOfCourseStatus(str, Enum):
    """Void-of-course status."""
    ACTIVE = "active"  # Moon is currently void
    NOT_VOID = "not_void"  # Moon will make more aspects before sign change
    UNKNOWN = "unknown"  # Cannot determine (insufficient data)


class NextLunarEvent(BaseModel):
    """Upcoming significant lunar event."""
    event_type: str = Field(description="Type of event: 'sign_change', 'phase_change', 'aspect'")
    event_description: str = Field(description="Human-readable description")
    datetime_utc: str = Field(description="UTC datetime when event occurs (ISO format)")
    hours_away: float = Field(description="Hours until event")
    significance: str = Field(description="Why this matters (brief)")


class MoonDispositor(BaseModel):
    """Dispositor chain for the Moon."""
    ruler: Planet = Field(description="Planet that rules Moon's current sign")
    ruler_sign: ZodiacSign = Field(description="Sign where ruler is located")
    ruler_house: int = Field(ge=1, le=12, description="House where ruler is located")
    interpretation: str = Field(description="What this means for emotional state")


class MoonTransitDetail(BaseModel):
    """
    Comprehensive Moon transit analysis.

    Provides emotional climate context separate from major life transits.
    Moon moves fast (13.2°/day), so aspects last 2-3 hours max.
    """
    # Current Moon position
    moon_sign: ZodiacSign = Field(description="Current Moon sign")
    moon_house: House = Field(description="Moon's solar house position")
    moon_degree: float = Field(ge=0, lt=360, description="Absolute degree of Moon")
    moon_degree_in_sign: float = Field(ge=0, lt=30, description="Degree within sign")

    # Lunar phase
    lunar_phase: LunarPhase = Field(description="Current lunar phase with guidance")

    # Moon aspects to natal chart (filtered from main transit list)
    moon_aspects: list[NatalTransitAspect] = Field(
        default_factory=list,
        description="Moon aspects to natal planets (sorted by tightness)"
    )

    # Void-of-course
    void_of_course: VoidOfCourseStatus = Field(description="Void-of-course status")
    void_start_time: Optional[str] = Field(
        None,
        description="UTC time when void period started (if active)"
    )
    void_end_time: Optional[str] = Field(
        None,
        description="UTC time when Moon enters next sign (if void or calculable)"
    )

    # Dispositor
    dispositor: Optional[MoonDispositor] = Field(
        None,
        description="Planet ruling Moon's sign (emotional energy filter)"
    )

    # Next events
    next_sign_change: NextLunarEvent = Field(
        description="When Moon changes signs (~2.5 days)"
    )
    next_major_aspect: Optional[NextLunarEvent] = Field(
        None,
        description="Next significant Moon aspect to natal chart"
    )
    next_phase_milestone: Optional[NextLunarEvent] = Field(
        None,
        description="Next new/full moon (major phase shift)"
    )

    # Quick reference
    emotional_tone: str = Field(
        description="Brief emotional quality description (from Moon sign)"
    )
    timing_guidance: str = Field(
        description="What to do/avoid based on void-of-course status"
    )

    # LLM-generated interpretation
    interpretation: str = Field(
        default="",
        description="LLM-generated lunar cycle guidance (3-4 sentences)"
    )


# =============================================================================
# Void-of-Course Detection
# =============================================================================

def detect_void_of_course(
    moon_position: dict,
    transit_chart: dict,
    natal_chart: dict,
    current_datetime: str
) -> tuple[VoidOfCourseStatus, Optional[str], Optional[str]]:
    """
    Detect if Moon is void-of-course.

    Moon is void when it makes no more major aspects (conjunction, sextile,
    square, trine, opposition) before changing signs.

    Args:
        moon_position: Moon planet dict from transit_chart
        transit_chart: Current transit chart
        natal_chart: User's natal chart
        current_datetime: Current UTC datetime (ISO format)

    Returns:
        Tuple of (status, void_start_time, void_end_time)
        - status: VoidOfCourseStatus enum
        - void_start_time: UTC ISO string of last aspect (if void)
        - void_end_time: UTC ISO string when Moon enters next sign

    Example:
        >>> status, start, end = detect_void_of_course(moon, transit, natal, "2025-11-03T12:00:00")
        >>> status
        VoidOfCourseStatus.ACTIVE
    """
    # Calculate when Moon changes signs
    moon_sign_degree = moon_position["degree_in_sign"]
    degrees_remaining = 30.0 - moon_sign_degree
    moon_speed = abs(moon_position["speed"])  # Degrees per day

    if moon_speed < 0.1:
        # Moon essentially stationary (rare but possible)
        return VoidOfCourseStatus.UNKNOWN, None, None

    hours_until_sign_change = (degrees_remaining / moon_speed) * 24

    current_dt = datetime.fromisoformat(current_datetime.replace('Z', '+00:00'))
    sign_change_time = current_dt + timedelta(hours=hours_until_sign_change)

    # Check if Moon makes any natal aspects before sign change
    # Use tight orb (1°) since we only care about upcoming aspects
    all_aspects = find_natal_transit_aspects(natal_chart, transit_chart, orb=1.0, sort_by_priority=False)

    # Filter for Moon aspects only
    moon_aspects = [asp for asp in all_aspects if asp.transit_planet == Planet.MOON]

    # Check if any aspects are applying (building to exact)
    applying_moon_aspects = [asp for asp in moon_aspects if asp.applying]

    if not applying_moon_aspects:
        # No more aspects before sign change = VOID
        return (
            VoidOfCourseStatus.ACTIVE,
            current_datetime,  # Approximate (last aspect was before now)
            sign_change_time.isoformat()
        )
    else:
        # Moon will make more aspects = NOT VOID
        return (
            VoidOfCourseStatus.NOT_VOID,
            None,
            sign_change_time.isoformat()  # Still return next sign change time
        )


# =============================================================================
# Dispositor Analysis
# =============================================================================

def calculate_moon_dispositor(
    moon_sign: ZodiacSign,
    natal_chart: dict,
    transit_chart: dict
) -> MoonDispositor:
    """
    Calculate Moon's dispositor (ruler of Moon's sign).

    The dispositor shows what filters/colors the Moon's emotional expression.

    Args:
        moon_sign: Moon's current sign
        natal_chart: User's natal chart
        transit_chart: Current transit chart

    Returns:
        MoonDispositor with ruler position and interpretation

    Example:
        >>> dispositor = calculate_moon_dispositor(ZodiacSign.ARIES, natal, transit)
        >>> dispositor.ruler
        Planet.MARS
    """
    ruler = SIGN_RULERS[moon_sign]

    # Find ruler in transit chart
    transit_planets = {p["name"]: p for p in transit_chart["planets"]}
    ruler_position = transit_planets[ruler.value]

    ruler_sign = ZodiacSign(ruler_position["sign"])
    ruler_house = ruler_position["house"]

    # Generate interpretation
    interpretation = f"Your emotional state is filtered through {ruler.value.title()} in {ruler_sign.value.title()}"

    # Add house context
    house_meanings = {
        1: "affecting your self-image and identity",
        2: "influencing your sense of security and values",
        3: "coloring your communication and thinking",
        4: "rooted in home and family matters",
        5: "expressed through creativity and pleasure",
        6: "tied to daily routines and health",
        7: "shaped by relationships and partnerships",
        8: "deepened by intimacy and transformation",
        9: "expanded by beliefs and meaning-seeking",
        10: "connected to career and public role",
        11: "channeled through community and friendships",
        12: "influenced by subconscious and spirituality"
    }

    interpretation += f", {house_meanings.get(ruler_house, 'in your chart')}"

    return MoonDispositor(
        ruler=ruler,
        ruler_sign=ruler_sign,
        ruler_house=ruler_house,
        interpretation=interpretation
    )


# =============================================================================
# Next Lunar Events
# =============================================================================

def calculate_next_sign_change(
    moon_position: dict,
    current_datetime: str
) -> NextLunarEvent:
    """
    Calculate when Moon changes signs.

    Args:
        moon_position: Moon planet dict from transit chart
        current_datetime: Current UTC datetime (ISO format)

    Returns:
        NextLunarEvent for sign change
    """
    moon_sign_degree = moon_position["degree_in_sign"]
    degrees_remaining = 30.0 - moon_sign_degree
    moon_speed = abs(moon_position["speed"])  # Degrees per day

    hours_until_change = (degrees_remaining / moon_speed) * 24

    current_dt = datetime.fromisoformat(current_datetime.replace('Z', '+00:00'))
    change_time = current_dt + timedelta(hours=hours_until_change)

    current_sign = ZodiacSign(moon_position["sign"])

    # Next sign in zodiac wheel
    signs_list = list(ZodiacSign)
    current_index = signs_list.index(current_sign)
    next_sign = signs_list[(current_index + 1) % 12]

    return NextLunarEvent(
        event_type="sign_change",
        event_description=f"Moon enters {next_sign.value.title()}",
        datetime_utc=change_time.isoformat(),
        hours_away=round(hours_until_change, 1),
        significance=f"Emotional tone shifts to {next_sign.value} qualities"
    )


def find_next_moon_aspect(
    moon_aspects: list[NatalTransitAspect],
    current_datetime: str
) -> Optional[NextLunarEvent]:
    """
    Find next significant Moon aspect to natal chart.

    Args:
        moon_aspects: List of Moon aspects (applying only)
        current_datetime: Current UTC datetime

    Returns:
        NextLunarEvent for next aspect, or None if no applying aspects
    """
    if not moon_aspects:
        return None

    # Find tightest applying aspect (closest to exact)
    applying = [asp for asp in moon_aspects if asp.applying]
    if not applying:
        return None

    next_aspect = applying[0]  # Already sorted by orb

    # Estimate hours until exact
    # Moon moves ~0.55°/hour on average
    hours_until_exact = next_aspect.orb / 0.55

    current_dt = datetime.fromisoformat(current_datetime.replace('Z', '+00:00'))
    aspect_time = current_dt + timedelta(hours=hours_until_exact)

    return NextLunarEvent(
        event_type="aspect",
        event_description=f"Moon {next_aspect.aspect_type.value} natal {next_aspect.natal_planet.value.title()}",
        datetime_utc=aspect_time.isoformat(),
        hours_away=round(hours_until_exact, 1),
        significance=next_aspect.meaning
    )


def estimate_next_lunar_phase(
    current_phase: LunarPhase,
    current_datetime: str
) -> Optional[NextLunarEvent]:
    """
    Estimate next major lunar phase (new or full moon).

    Uses approximate 29.5-day lunar cycle.

    Args:
        current_phase: Current LunarPhase
        current_datetime: Current UTC datetime

    Returns:
        NextLunarEvent for next new/full moon
    """
    angle = current_phase.angle

    # Determine next major phase
    if 0 <= angle < 180:
        # Currently waxing, next is Full Moon at 180°
        degrees_to_full = 180 - angle
        next_phase_name = "Full Moon"
        next_phase_significance = "Peak illumination, culmination, release"
    else:
        # Currently waning, next is New Moon at 360°/0°
        degrees_to_new = 360 - angle
        next_phase_name = "New Moon"
        next_phase_significance = "Fresh start, new intentions, beginnings"

    # Moon orbits ~13.2°/day relative to Sun
    days_until_phase = degrees_to_full / 13.2 if angle < 180 else degrees_to_new / 13.2
    hours_until_phase = days_until_phase * 24

    current_dt = datetime.fromisoformat(current_datetime.replace('Z', '+00:00'))
    phase_time = current_dt + timedelta(hours=hours_until_phase)

    return NextLunarEvent(
        event_type="phase_change",
        event_description=next_phase_name,
        datetime_utc=phase_time.isoformat(),
        hours_away=round(hours_until_phase, 1),
        significance=next_phase_significance
    )


# =============================================================================
# Main Function: Get Complete Moon Transit Detail
# =============================================================================

def get_moon_transit_detail(
    natal_chart: dict,
    transit_chart: dict,
    current_datetime: str
) -> MoonTransitDetail:
    """
    Generate complete Moon transit detail for LLM context.

    This is the main function to call from llm.py or main.py.

    Args:
        natal_chart: User's natal chart from compute_birth_chart()
        transit_chart: Current transit chart from compute_birth_chart()
        current_datetime: Current UTC datetime (ISO format)

    Returns:
        MoonTransitDetail with all lunar analysis

    Example:
        >>> natal, _ = compute_birth_chart("1985-05-15")
        >>> transit, _ = compute_birth_chart("2025-11-03", birth_time="12:00")
        >>> moon_detail = get_moon_transit_detail(natal, transit, "2025-11-03T12:00:00")
        >>> print(moon_detail.emotional_tone)
        'impulsive, direct emotional responses and desire for action'
    """
    # Extract Moon from transit chart
    transit_planets = {p["name"]: p for p in transit_chart["planets"]}
    moon = transit_planets[Planet.MOON.value]
    sun = transit_planets[Planet.SUN.value]

    moon_sign = ZodiacSign(moon["sign"])
    sun_sign = ZodiacSign(natal_chart["planets"][0]["sign"])

    # Calculate Moon's solar house
    moon_house = calculate_solar_house(sun_sign, moon_sign)

    # Calculate lunar phase
    lunar_phase = calculate_lunar_phase(sun["absolute_degree"], moon["absolute_degree"])

    # Get all natal-transit aspects (tight orb for Moon)
    all_aspects = find_natal_transit_aspects(natal_chart, transit_chart, orb=3.0, sort_by_priority=False)

    # Filter for Moon aspects only, sort by orb
    moon_aspects = [asp for asp in all_aspects if asp.transit_planet == Planet.MOON]
    moon_aspects_sorted = sorted(moon_aspects, key=lambda x: x.orb)

    # Detect void-of-course
    void_status, void_start, void_end = detect_void_of_course(
        moon, transit_chart, natal_chart, current_datetime
    )

    # Calculate dispositor
    dispositor = calculate_moon_dispositor(moon_sign, natal_chart, transit_chart)

    # Next sign change
    next_sign = calculate_next_sign_change(moon, current_datetime)

    # Next major aspect
    next_aspect = find_next_moon_aspect(moon_aspects_sorted, current_datetime)

    # Next phase milestone
    next_phase = estimate_next_lunar_phase(lunar_phase, current_datetime)

    # Emotional tone (from sign)
    emotional_qualities = {
        ZodiacSign.ARIES: "impulsive, direct emotional responses and desire for action",
        ZodiacSign.TAURUS: "grounded, sensual feelings and need for comfort",
        ZodiacSign.GEMINI: "mental stimulation, curiosity, and emotional versatility",
        ZodiacSign.CANCER: "heightened sensitivity, nurturing instincts, and emotional depth",
        ZodiacSign.LEO: "warmth, generosity, and desire for recognition",
        ZodiacSign.VIRGO: "analytical feelings, attention to detail, and practical concerns",
        ZodiacSign.LIBRA: "harmony-seeking, relational awareness, and aesthetic sensitivity",
        ZodiacSign.SCORPIO: "emotional intensity, depth, and transformative power",
        ZodiacSign.SAGITTARIUS: "optimism, restlessness, and philosophical perspective",
        ZodiacSign.CAPRICORN: "emotional reserve, ambition, and practical focus",
        ZodiacSign.AQUARIUS: "detached perspective, humanitarian concern, and innovative thinking",
        ZodiacSign.PISCES: "empathy, dreaminess, and spiritual receptivity"
    }
    emotional_tone = emotional_qualities.get(moon_sign, "emotional coloring")

    # Timing guidance based on void-of-course
    if void_status == VoidOfCourseStatus.ACTIVE:
        timing_guidance = "Moon is void-of-course. Avoid starting new projects or making major decisions. Focus on reflection, completion, and rest."
    else:
        timing_guidance = "Moon is active. Good time for emotional processing and taking action on feelings."

    return MoonTransitDetail(
        moon_sign=moon_sign,
        moon_house=moon_house,
        moon_degree=moon["absolute_degree"],
        moon_degree_in_sign=moon["degree_in_sign"],
        lunar_phase=lunar_phase,
        moon_aspects=moon_aspects_sorted[:5],  # Top 5 tightest
        void_of_course=void_status,
        void_start_time=void_start,
        void_end_time=void_end,
        dispositor=dispositor,
        next_sign_change=next_sign,
        next_major_aspect=next_aspect,
        next_phase_milestone=next_phase,
        emotional_tone=emotional_tone,
        timing_guidance=timing_guidance
    )


# =============================================================================
# LLM-Friendly Formatting
# =============================================================================

def format_moon_summary_for_llm(moon_detail: MoonTransitDetail) -> str:
    """
    Format moon transit detail for LLM prompt inclusion.

    Creates a structured, markdown-formatted summary optimized for
    Gemini/Claude to interpret and weave into horoscope.

    Args:
        moon_detail: MoonTransitDetail object

    Returns:
        Formatted string for LLM context

    Example:
        >>> summary = format_moon_summary_for_llm(moon_detail)
        >>> print(summary)
        [LUNAR CLIMATE - Emotional Weather]
        ...
    """
    phase = moon_detail.lunar_phase

    lines = [
        "═══════════════════════════════════════════════════════════════════",
        "LUNAR CLIMATE - Your Emotional Weather Right Now",
        "═══════════════════════════════════════════════════════════════════",
        "",
        "[CURRENT LUNAR POSITION]",
        f"├─ Phase: {phase.phase_name.replace('_', ' ').title()} {phase.phase_emoji} ({phase.illumination_percent}% illuminated)",
        f"├─ Sign: {moon_detail.moon_sign.value.title()} ({moon_detail.moon_degree_in_sign:.1f}°)",
        f"├─ House: {moon_detail.moon_house.ordinal} ({moon_detail.moon_house.meaning})",
        f"└─ Void of Course: {moon_detail.void_of_course.value.replace('_', ' ').title()}",
        "",
        "[PHASE WISDOM]",
        f"├─ Energy: {phase.energy}",
        f"└─ Ritual: {phase.ritual_suggestion}",
        "",
        "[EMOTIONAL TONE]",
        f"└─ {moon_detail.moon_sign.value.title()} Moon brings {moon_detail.emotional_tone}",
        ""
    ]

    # Moon aspects to natal chart
    if moon_detail.moon_aspects:
        lines.append("[ACTIVE MOON ASPECTS - Next 2-3 Hours]")
        for asp in moon_detail.moon_aspects[:3]:  # Top 3
            applying_status = "BUILDING" if asp.applying else "WANING"
            lines.append(
                f"├─ {asp.aspect_type.value.title()} natal {asp.natal_planet.value.title()} "
                f"({asp.orb:.1f}° orb, {applying_status}) - {asp.meaning}"
            )
        lines.append("")

    # Dispositor
    if moon_detail.dispositor:
        lines.append("[MOON'S DISPOSITOR]")
        lines.append(f"└─ {moon_detail.dispositor.interpretation}")
        lines.append("")

    # Timing guidance
    lines.append("[TIMING GUIDANCE]")
    lines.append(f"└─ {moon_detail.timing_guidance}")

    if moon_detail.void_of_course == VoidOfCourseStatus.ACTIVE and moon_detail.void_end_time:
        try:
            end_dt = datetime.fromisoformat(moon_detail.void_end_time.replace('Z', '+00:00'))
            lines.append(f"   Void ends: {end_dt.strftime('%I:%M %p')} UTC when Moon enters next sign")
        except:
            pass
    lines.append("")

    # Next events
    lines.append("[NEXT LUNAR EVENTS]")
    lines.append(
        f"├─ Sign Change: {moon_detail.next_sign_change.event_description} "
        f"in {moon_detail.next_sign_change.hours_away:.1f} hours"
    )

    if moon_detail.next_major_aspect:
        lines.append(
            f"├─ Next Aspect: {moon_detail.next_major_aspect.event_description} "
            f"in {moon_detail.next_major_aspect.hours_away:.1f} hours"
        )

    if moon_detail.next_phase_milestone:
        lines.append(
            f"└─ Next Phase: {moon_detail.next_phase_milestone.event_description} "
            f"in {moon_detail.next_phase_milestone.hours_away / 24:.1f} days"
        )

    return "\n".join(lines)
