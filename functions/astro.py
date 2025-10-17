from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional, Tuple
from natal import Data
from datetime import datetime
from enum import Enum
import re
import json
from pathlib import Path


class ZodiacSign(str, Enum):
    """Zodiac sign enumeration."""
    ARIES = "aries"
    TAURUS = "taurus"
    GEMINI = "gemini"
    CANCER = "cancer"
    LEO = "leo"
    VIRGO = "virgo"
    LIBRA = "libra"
    SCORPIO = "scorpio"
    SAGITTARIUS = "sagittarius"
    CAPRICORN = "capricorn"
    AQUARIUS = "aquarius"
    PISCES = "pisces"


class Planet(str, Enum):
    """Planet enumeration."""
    SUN = "sun"
    MOON = "moon"
    MERCURY = "mercury"
    VENUS = "venus"
    MARS = "mars"
    JUPITER = "jupiter"
    SATURN = "saturn"
    URANUS = "uranus"
    NEPTUNE = "neptune"
    PLUTO = "pluto"
    NORTH_NODE = "north node"


class Element(str, Enum):
    """Element enumeration."""
    FIRE = "fire"
    EARTH = "earth"
    AIR = "air"
    WATER = "water"


class Modality(str, Enum):
    """Modality enumeration."""
    CARDINAL = "cardinal"
    FIXED = "fixed"
    MUTABLE = "mutable"


class AspectType(str, Enum):
    """Aspect type enumeration."""
    CONJUNCTION = "conjunction"
    OPPOSITION = "opposition"
    TRINE = "trine"
    SQUARE = "square"
    SEXTILE = "sextile"
    QUINCUNX = "quincunx"


class ChartType(str, Enum):
    """Chart type enumeration."""
    NATAL = "natal"
    TRANSIT = "transit"

# Pydantic Models for Chart Data
class PlanetPosition(BaseModel):
    """A planet's position and metadata."""
    name: str
    symbol: str
    position_dms: str = Field(description="Formatted position like '15° ♈ 23'")
    sign: str
    degree_in_sign: float = Field(ge=0, lt=30)
    absolute_degree: float = Field(ge=0, lt=360)
    house: int = Field(ge=1, le=12)
    speed: float
    retrograde: bool
    element: Element
    modality: Modality


class HouseCusp(BaseModel):
    """A house cusp with ruler information."""
    number: int = Field(ge=1, le=12)
    sign: str
    degree_in_sign: float = Field(ge=0, lt=30)
    absolute_degree: float = Field(ge=0, lt=360)
    ruler: str
    ruler_sign: str
    ruler_house: int = Field(ge=1, le=12)
    classic_ruler: str
    classic_ruler_sign: str
    classic_ruler_house: int = Field(ge=1, le=12)


class AspectData(BaseModel):
    """An aspect between two celestial bodies."""
    body1: str
    body2: str
    aspect_type: AspectType
    aspect_symbol: str
    exact_degree: int = Field(description="Exact degree of aspect (0, 60, 90, 120, 180)")
    orb: float = Field(ge=0, description="Orb in degrees from exact")
    applying: bool = Field(description="True if applying, False if separating")


class AnglePosition(BaseModel):
    """Position of one of the four angles (Asc, IC, Dsc, MC)."""
    sign: str
    degree_in_sign: float = Field(ge=0, lt=30)
    absolute_degree: float = Field(ge=0, lt=360)
    position_dms: str = Field(description="Formatted position like '15° ♈ 23'")


class ChartAngles(BaseModel):
    """The four angles of the chart."""
    ascendant: AnglePosition
    imum_coeli: AnglePosition
    descendant: AnglePosition
    midheaven: AnglePosition


class ElementDistribution(BaseModel):
    """Distribution of planets across elements."""
    fire: int = Field(ge=0, le=11)
    earth: int = Field(ge=0, le=11)
    air: int = Field(ge=0, le=11)
    water: int = Field(ge=0, le=11)


class ModalityDistribution(BaseModel):
    """Distribution of planets across modalities."""
    cardinal: int = Field(ge=0, le=11)
    fixed: int = Field(ge=0, le=11)
    mutable: int = Field(ge=0, le=11)


class QuadrantDistribution(BaseModel):
    """Distribution of planets across quadrants."""
    first: int = Field(ge=0, le=11, description="Houses 1-3 (Self)")
    second: int = Field(ge=0, le=11, description="Houses 4-6 (Foundation)")
    third: int = Field(ge=0, le=11, description="Houses 7-9 (Relationships)")
    fourth: int = Field(ge=0, le=11, description="Houses 10-12 (Social/Career)")


class HemisphereDistribution(BaseModel):
    """Distribution of planets across hemispheres."""
    northern: int = Field(ge=0, le=11, description="Houses 1-6")
    southern: int = Field(ge=0, le=11, description="Houses 7-12")
    eastern: int = Field(ge=0, le=11, description="Houses 10-3")
    western: int = Field(ge=0, le=11, description="Houses 4-9")


class ChartDistributions(BaseModel):
    """All distribution metrics for the chart."""
    elements: ElementDistribution
    modalities: ModalityDistribution
    quadrants: QuadrantDistribution
    hemispheres: HemisphereDistribution


class NatalChartData(BaseModel):
    """Complete natal chart data optimized for LLM interpretation."""
    chart_type: ChartType
    datetime_utc: str = Field(description="UTC datetime in format 'YYYY-MM-DD HH:MM'")
    location_lat: float = Field(ge=-90, le=90)
    location_lon: float = Field(ge=-180, le=180)
    angles: ChartAngles
    planets: list[PlanetPosition]
    houses: list[HouseCusp] = Field(min_length=12, max_length=12)
    aspects: list[AspectData]
    distributions: ChartDistributions

    class Config:
        json_schema_extra = {
            "example": {
                "chart_type": "natal",
                "datetime_utc": "1980-04-20 06:30",
                "location_lat": 25.0531,
                "location_lon": 121.526,
                "angles": {
                    "ascendant": {
                        "sign": "virgo",
                        "degree_in_sign": 19.70,
                        "absolute_degree": 159.70,
                        "position_dms": "19° ♍ 42'"
                    }
                }
            }
        }


# Rich Sun Sign Profile Models (from JSON schema)
class PlanetaryDignities(BaseModel):
    """Planetary dignities for a sign."""
    exaltation: str = Field(description="Planet that expresses most powerfully in this sign")
    detriment: str = Field(description="Planet that faces challenges in this sign")
    fall: str = Field(description="Planet at its weakest expression in this sign")


class Correspondences(BaseModel):
    """Esoteric correspondences for a sign."""
    tarot: str = Field(description="Major Arcana tarot card correspondence")
    colors: list[str] = Field(description="Colors that resonate with this sign's energy")
    gemstones: list[str] = Field(description="Crystals and stones aligned with the sign")
    metal: str = Field(description="Metal associated with the sign's energy")
    day_of_week: str = Field(description="Day of the week ruled by this sign's planet")
    lucky_numbers: list[int] = Field(description="Numbers that carry favorable energy for this sign")


class HealthTendencies(BaseModel):
    """Health patterns for a sign."""
    strengths: str = Field(description="Natural health advantages for this sign")
    vulnerabilities: str = Field(description="Physical areas requiring attention and care")
    wellness_advice: str = Field(description="Guidance for maintaining optimal health (informational only, not medical advice)")


class CompatibilityEntry(BaseModel):
    """Single compatibility pairing."""
    sign: str
    reason: str


class CompatibilityOverview(BaseModel):
    """Relationship compatibility patterns."""
    same_sign: str = Field(description="Compatibility with the same sign")
    most_compatible: list[CompatibilityEntry] = Field(description="Signs with natural harmony and ease")
    challenging: list[CompatibilityEntry] = Field(description="Signs requiring extra effort and understanding")
    growth_oriented: list[CompatibilityEntry] = Field(description="Signs that catalyze personal evolution through complementary differences")


class LoveAndRelationships(BaseModel):
    """Love and relationship patterns."""
    style: str = Field(description="How this sign approaches romantic relationships")
    needs: str = Field(description="Core relationship requirements")
    gives: str = Field(description="What this sign brings to partnerships")
    challenges: str = Field(description="Common relationship obstacles")
    attracts: str = Field(description="Type of partners naturally drawn to this sign")
    communication_style: str = Field(description="How this sign communicates with partners")


class FamilyAndFriendships(BaseModel):
    """Family and friendship patterns."""
    friendship_style: str = Field(description="How this sign shows up in platonic relationships")
    parenting_style: str = Field(description="Approach to raising children")
    childhood_needs: str = Field(description="What this sign needed as a child")
    family_role: str = Field(description="Typical position within family dynamics")
    sibling_dynamics: str = Field(description="How this sign relates to siblings")


class PathAndProfession(BaseModel):
    """Career and professional patterns."""
    career_strengths: list[str] = Field(description="Professional domains where this sign naturally excels")
    work_style: str = Field(description="How this sign approaches daily work")
    leadership_approach: str = Field(description="Management and leadership tendencies")
    ideal_work_environment: str = Field(description="Optimal professional settings")
    growth_area: str = Field(description="Professional development focus areas")


class PersonalGrowthAndWellbeing(BaseModel):
    """Personal growth patterns."""
    growth_path: str = Field(description="Key areas for personal development")
    healing_modalities: list[str] = Field(description="Therapeutic approaches aligned with this sign")
    stress_triggers: str = Field(description="Common sources of overwhelm")
    stress_relief_practices: str = Field(description="Restorative activities for this sign")
    mindfulness_approach: str = Field(description="Meditation and presence practices suited to this sign's nature")


class FinanceAndAbundance(BaseModel):
    """Financial patterns."""
    money_mindset: str = Field(description="Core beliefs about finances")
    earning_style: str = Field(description="How this sign makes money")
    spending_patterns: str = Field(description="Financial habits and tendencies")
    abundance_lesson: str = Field(description="Growth edge around money")
    financial_advisory_note: str = Field(description="Disclaimer for financial information")


class LifePurposeAndSpirituality(BaseModel):
    """Spiritual patterns."""
    spiritual_path: str = Field(description="Natural approach to meaning and transcendence")
    soul_mission: str = Field(description="Higher purpose themes")
    spiritual_practices: list[str] = Field(description="Spiritual modalities that resonate")
    connection_to_divine: str = Field(description="How this sign experiences the sacred")


class HomeAndEnvironment(BaseModel):
    """Home and environment patterns."""
    home_needs: str = Field(description="Ideal living space qualities")
    decorating_style: str = Field(description="Aesthetic preferences")
    location_preferences: str = Field(description="Geographic tendencies")
    relationship_to_space: str = Field(description="How this sign relates to their living space")
    seasonal_home_adjustments: str = Field(description="Seasonal adaptations to home environment")


class DecisionsAndCrossroads(BaseModel):
    """Decision-making patterns."""
    decision_making_style: str = Field(description="How this sign approaches choices")
    decision_tips: str = Field(description="Strategies to improve decision quality")
    when_stuck: str = Field(description="Strategy when facing obstacles")
    crisis_response: str = Field(description="Behavior during turning points")
    advice_for_major_choices: str = Field(description="Guidance for important decisions")


class DomainProfiles(BaseModel):
    """All 8 life domain profiles."""
    love_and_relationships: LoveAndRelationships
    family_and_friendships: FamilyAndFriendships
    path_and_profession: PathAndProfession
    personal_growth_and_wellbeing: PersonalGrowthAndWellbeing
    finance_and_abundance: FinanceAndAbundance
    life_purpose_and_spirituality: LifePurposeAndSpirituality
    home_and_environment: HomeAndEnvironment
    decisions_and_crossroads: DecisionsAndCrossroads


class SunSignProfile(BaseModel):
    """Complete sun sign profile from JSON file."""
    sign: str = Field(description="Name of the zodiac sign")
    dates: str = Field(description="Date range when the Sun transits this sign")
    symbol: str = Field(description="Traditional symbol representing the sign")
    glyph: str = Field(description="Unicode astrological glyph for the sign")
    element: Element = Field(description="Elemental classification of the sign")
    modality: Modality = Field(description="The sign's mode of expression and action style")
    polarity: str = Field(description="Energetic polarity - extroverted or introverted orientation")
    ruling_planet: str = Field(description="The planet that governs this sign")
    ruling_planet_glyph: str = Field(description="Unicode glyph for the ruling planet")
    planetary_dignities: PlanetaryDignities
    body_parts_ruled: list[str] = Field(description="Physical body areas associated with and governed by this sign")
    correspondences: Correspondences
    keywords: list[str] = Field(description="Core descriptive keywords capturing the sign's essence")
    positive_traits: list[str] = Field(description="Constructive qualities and strengths naturally expressed by this sign")
    shadow_traits: list[str] = Field(description="Challenging patterns and underdeveloped expressions of the sign's energy")
    life_lesson: str = Field(description="Primary evolutionary lesson this sign is here to learn")
    evolutionary_goal: str = Field(description="Highest expression and developmental aim for this sign")
    mythology: str = Field(description="Mythological stories and archetypes connected to this sign")
    seasonal_association: str = Field(description="Connection to natural cycles and seasonal energies in the Northern Hemisphere")
    archetypal_roles: list[str] = Field(description="Universal archetypal patterns embodied by this sign")
    health_tendencies: HealthTendencies
    compatibility_overview: CompatibilityOverview
    summary: str = Field(description="Concise overview capturing the essence of the sign")
    domain_profiles: DomainProfiles

    @field_validator('element', mode='before')
    @classmethod
    def convert_element(cls, v: str) -> Element:
        """Convert string to Element enum (case-insensitive)."""
        if isinstance(v, Element):
            return v
        return Element(v.lower())

    @field_validator('modality', mode='before')
    @classmethod
    def convert_modality(cls, v: str) -> Modality:
        """Convert string to Modality enum (case-insensitive)."""
        if isinstance(v, Modality):
            return v
        return Modality(v.lower())


def get_sun_sign(birth_date: str) -> ZodiacSign:
    """
    Calculate sun sign from birth date.

    Args:
        birth_date: Date string in format "YYYY-MM-DD"

    Returns:
        ZodiacSign enum value

    Raises:
        ValueError: If birth_date format is invalid

    Example:
        >>> get_sun_sign("1990-06-15")
        ZodiacSign.GEMINI
        >>> get_sun_sign("1990-04-15")
        ZodiacSign.ARIES
    """
    # Parse the date (raises ValueError if invalid format)
    dt = datetime.strptime(birth_date, "%Y-%m-%d")
    month = dt.month
    day = dt.day

    # Sun sign date ranges (using approximate tropical zodiac dates)
    if (month == 3 and day >= 21) or (month == 4 and day <= 19):
        return ZodiacSign.ARIES
    elif (month == 4 and day >= 20) or (month == 5 and day <= 20):
        return ZodiacSign.TAURUS
    elif (month == 5 and day >= 21) or (month == 6 and day <= 20):
        return ZodiacSign.GEMINI
    elif (month == 6 and day >= 21) or (month == 7 and day <= 22):
        return ZodiacSign.CANCER
    elif (month == 7 and day >= 23) or (month == 8 and day <= 22):
        return ZodiacSign.LEO
    elif (month == 8 and day >= 23) or (month == 9 and day <= 22):
        return ZodiacSign.VIRGO
    elif (month == 9 and day >= 23) or (month == 10 and day <= 22):
        return ZodiacSign.LIBRA
    elif (month == 10 and day >= 23) or (month == 11 and day <= 21):
        return ZodiacSign.SCORPIO
    elif (month == 11 and day >= 22) or (month == 12 and day <= 21):
        return ZodiacSign.SAGITTARIUS
    elif (month == 12 and day >= 22) or (month == 1 and day <= 19):
        return ZodiacSign.CAPRICORN
    elif (month == 1 and day >= 20) or (month == 2 and day <= 18):
        return ZodiacSign.AQUARIUS
    else:  # (month == 2 and day >= 19) or (month == 3 and day <= 20)
        return ZodiacSign.PISCES


def get_sun_sign_profile(sun_sign: ZodiacSign) -> Optional[SunSignProfile]:
    """
    Load comprehensive sun sign profile from JSON file.

    Args:
        sun_sign: ZodiacSign enum value

    Returns:
        SunSignProfile object with complete profile data, or None if file doesn't exist
        or parsing fails.

    Example:
        >>> profile = get_sun_sign_profile(ZodiacSign.ARIES)
        >>> profile.sign
        'Aries'
        >>> profile.element
        Element.FIRE
        >>> profile.domain_profiles.love_and_relationships.style
        'Direct, passionate, spontaneous'
    """
    # Path to signs directory (relative to this file, within functions/)
    signs_dir = Path(__file__).parent / "signs"
    sign_file = signs_dir / f"{sun_sign.value}.json"

    if not sign_file.exists():
        return None

    try:
        # Read and parse JSON file
        content = sign_file.read_text()
        data = json.loads(content)
        return SunSignProfile(**data)
    except Exception:
        # Return None if any parsing errors occur
        return None


def get_astro_chart(
    utc_dt: str,
    lat: float,
    lon: float,
    chart_type: ChartType = ChartType.NATAL
) -> NatalChartData:
    """
    Generate natal chart data formatted for LLM interpretation.

    This function leverages the natal library's Data object which automatically
    calculates all astrological data including planets, houses, aspects, and
    distributions. The data is then structured into type-safe Pydantic models.

    Args:
        utc_dt: UTC datetime string in format "YYYY-MM-DD HH:MM"
        lat: Latitude in decimal degrees (-90 to 90)
        lon: Longitude in decimal degrees (-180 to 180)
        chart_type: Type of chart - "natal" for birth chart, "transit" for current sky

    Returns:
        NatalChartData: Validated chart data ready for LLM consumption

    Example:
        >>> chart = get_chart_data_for_llm("1980-04-20 06:30", 25.0531, 121.526)
        >>> print(chart.planets[0].name)
        'sun'
        >>> print(chart.angles.ascendant.sign)
        'virgo'
    """
    # Create natal Data object - this calculates everything automatically
    data = Data(
        name="User",
        utc_dt=utc_dt,
        lat=lat,
        lon=lon
    )

    # Extract planet positions
    planets = [
        PlanetPosition(
            name=planet.name,
            symbol=planet.symbol,
            position_dms=planet.signed_dms,
            sign=planet.sign.name,
            degree_in_sign=round(planet.signed_deg + planet.minute / 60, 2),
            absolute_degree=round(planet.degree, 2),
            house=data.house_of(planet),
            speed=round(planet.speed, 4),
            retrograde=planet.retro,
            element=planet.sign.element,
            modality=planet.sign.modality
        )
        for planet in data.planets
    ]

    # Extract house cusps
    houses = [
        HouseCusp(
            number=house.value,
            sign=house.sign.name,
            degree_in_sign=round(house.degree % 30, 2),
            absolute_degree=round(house.degree, 2),
            ruler=house.ruler,
            ruler_sign=house.ruler_sign,
            ruler_house=house.ruler_house,
            classic_ruler=house.classic_ruler,
            classic_ruler_sign=house.classic_ruler_sign,
            classic_ruler_house=house.classic_ruler_house
        )
        for house in data.houses
    ]

    # Extract aspects
    aspects = [
        AspectData(
            body1=aspect.body1.name,
            body2=aspect.body2.name,
            aspect_type=aspect.aspect_member.name,
            aspect_symbol=aspect.aspect_member.symbol,
            exact_degree=aspect.aspect_member.value,
            orb=round(aspect.orb, 2),
            applying=aspect.applying
        )
        for aspect in data.aspects
    ]

    # Extract the four angles
    angles = ChartAngles(
        ascendant=AnglePosition(
            sign=data.asc.sign.name,
            degree_in_sign=round(data.asc.signed_deg + data.asc.minute / 60, 2),
            absolute_degree=round(data.asc.degree, 2),
            position_dms=data.asc.signed_dms
        ),
        imum_coeli=AnglePosition(
            sign=data.ic.sign.name,
            degree_in_sign=round(data.ic.signed_deg + data.ic.minute / 60, 2),
            absolute_degree=round(data.ic.degree, 2),
            position_dms=data.ic.signed_dms
        ),
        descendant=AnglePosition(
            sign=data.dsc.sign.name,
            degree_in_sign=round(data.dsc.signed_deg + data.dsc.minute / 60, 2),
            absolute_degree=round(data.dsc.degree, 2),
            position_dms=data.dsc.signed_dms
        ),
        midheaven=AnglePosition(
            sign=data.mc.sign.name,
            degree_in_sign=round(data.mc.signed_deg + data.mc.minute / 60, 2),
            absolute_degree=round(data.mc.degree, 2),
            position_dms=data.mc.signed_dms
        )
    )

    # Calculate element distribution
    elements = {"fire": 0, "earth": 0, "air": 0, "water": 0}
    modalities = {"cardinal": 0, "fixed": 0, "mutable": 0}

    for planet in data.planets:
        elements[planet.sign.element] += 1
        modalities[planet.sign.modality] += 1

    # Get quadrant counts
    quadrant_counts = [len(q) for q in data.quadrants]

    distributions = ChartDistributions(
        elements=ElementDistribution(**elements),
        modalities=ModalityDistribution(**modalities),
        quadrants=QuadrantDistribution(
            first=quadrant_counts[0],
            second=quadrant_counts[1],
            third=quadrant_counts[2],
            fourth=quadrant_counts[3]
        ),
        hemispheres=HemisphereDistribution(
            northern=quadrant_counts[0] + quadrant_counts[3],
            southern=quadrant_counts[1] + quadrant_counts[2],
            eastern=quadrant_counts[0] + quadrant_counts[1],
            western=quadrant_counts[2] + quadrant_counts[3]
        )
    )

    # Return validated Pydantic model
    return NatalChartData(
        chart_type=chart_type,
        datetime_utc=utc_dt,
        location_lat=lat,
        location_lon=lon,
        angles=angles,
        planets=planets,
        houses=houses,
        aspects=aspects,
        distributions=distributions
    )


def compute_birth_chart(
    birth_date: str,
    birth_time: Optional[str] = None,
    birth_timezone: Optional[str] = None,
    birth_lat: Optional[float] = None,
    birth_lon: Optional[float] = None
) -> Tuple[dict, bool]:
    """
    Compute natal chart from birth info.

    Args:
        birth_date: Date string "YYYY-MM-DD"
        birth_time: Time string "HH:MM" in local time (optional)
        birth_timezone: IANA timezone e.g. "America/New_York" (optional)
        birth_lat: Birth location latitude (optional)
        birth_lon: Birth location longitude (optional)

    Returns:
        Tuple of (chart_data_dict, exact_chart_bool)
        - chart_data_dict: Complete NatalChartData as dict
        - exact_chart_bool: True if time+location provided, False if approximate

    Approximate chart (V1, no birth time):
        - Uses noon UTC (12:00)
        - Uses coordinates (0.0, 0.0)
        - Sun sign and planetary positions accurate
        - Houses/angles not meaningful

    Exact chart (V2+, with birth time):
        - Converts local time to UTC using timezone
        - Uses actual birth coordinates
        - All data accurate including houses/angles

    Example:
        >>> # V1: Approximate chart
        >>> chart, exact = compute_birth_chart("1990-06-15")
        >>> exact
        False
        >>> chart['chart_type']
        'natal'

        >>> # V2: Exact chart
        >>> chart, exact = compute_birth_chart(
        ...     "1990-06-15",
        ...     birth_time="14:30",
        ...     birth_timezone="America/New_York",
        ...     birth_lat=40.7128,
        ...     birth_lon=-74.0060
        ... )
        >>> exact
        True
    """
    # Check if we have full birth info for exact chart
    has_full_info = all([
        birth_time is not None,
        birth_timezone is not None,
        birth_lat is not None,
        birth_lon is not None
    ])

    if has_full_info:
        # V2+: Exact chart with full birth info
        # TODO: Convert local time to UTC using timezone (needs pytz)
        # For now, assume birth_time is already in UTC format
        # This will be properly implemented when we add timezone support
        utc_dt = f"{birth_date} {birth_time}"
        lat = birth_lat
        lon = birth_lon
        exact_chart = True
    else:
        # V1: Approximate chart (noon UTC at 0,0)
        utc_dt = f"{birth_date} 12:00"
        lat = 0.0
        lon = 0.0
        exact_chart = False

    # Generate natal chart using get_astro_chart
    chart = get_astro_chart(
        utc_dt=utc_dt,
        lat=lat,
        lon=lon,
        chart_type=ChartType.NATAL
    )

    # Return as dict
    return chart.model_dump(), exact_chart


def summarize_transits(transit_chart: dict, sun_sign: ZodiacSign) -> str:
    """
    Extract key transit aspects relevant to a sun sign for LLM context.

    Focuses on the most impactful transits:
    - Sun aspects (everyone feels these - core identity energy)
    - Moon aspects (emotional tone of the day)
    - Mercury/Venus/Mars aspects (daily affairs - communication, love, action)
    - Major outer planet aspects (Jupiter, Saturn, Uranus, Neptune, Pluto)

    Args:
        transit_chart: NatalChartData dict from compute_birth_chart() with chart_type="transit"
        sun_sign: ZodiacSign enum value

    Returns:
        Human-readable summary of key transits for LLM prompt context

    Example:
        >>> transit_data, _ = compute_birth_chart("2025-10-17", birth_time="12:00")
        >>> summary = summarize_transits(transit_data, ZodiacSign.TAURUS)
        >>> print(summary)
        "Sun in Libra (balance, partnerships). Moon in Scorpio (deep emotions, transformation)..."
    """
    # Extract planets for easy access
    planets = {p["name"]: p for p in transit_chart["planets"]}
    aspects = transit_chart["aspects"]

    # Build summary parts
    parts = []

    # 1. Sun position (sets the overall tone)
    sun = planets.get(Planet.SUN.value)
    if sun:
        parts.append(f"Sun in {sun['sign'].title()} at {sun['degree_in_sign']:.1f}°")

    # 2. Moon position (emotional climate)
    moon = planets.get(Planet.MOON.value)
    if moon:
        parts.append(f"Moon in {moon['sign'].title()} at {moon['degree_in_sign']:.1f}°")

    # 3. Key aspects involving personal planets (Sun, Moon, Mercury, Venus, Mars)
    personal_planets = [
        Planet.SUN.value,
        Planet.MOON.value,
        Planet.MERCURY.value,
        Planet.VENUS.value,
        Planet.MARS.value
    ]
    key_aspects = []

    for aspect in aspects:
        body1 = aspect["body1"]
        body2 = aspect["body2"]
        aspect_type = aspect["aspect_type"]
        orb = aspect["orb"]

        # Filter for tight aspects (orb < 3°) involving personal planets
        if orb < 3.0:
            if body1 in personal_planets or body2 in personal_planets:
                # Format: "Venus trine Neptune (2.1° orb)"
                symbol = aspect["aspect_symbol"]
                key_aspects.append(
                    f"{body1.title()} {aspect_type} {body2.title()} "
                    f"({symbol}, {orb:.1f}° orb)"
                )

    # Limit to top 5 most relevant aspects
    if key_aspects:
        parts.append("Key aspects: " + "; ".join(key_aspects[:5]))

    # 4. Retrograde planets (notable when personal planets are retrograde)
    retrogrades = []
    for planet_name in personal_planets:
        planet = planets.get(planet_name)
        if planet and planet["retrograde"]:
            retrogrades.append(f"{planet_name.title()} Rx")

    if retrogrades:
        parts.append("Retrograde: " + ", ".join(retrogrades))

    # Join all parts with ". "
    return ". ".join(parts) + "."