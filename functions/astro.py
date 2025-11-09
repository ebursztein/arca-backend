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


class CelestialBody(str, Enum):
    """
    Celestial body enumeration including planets and chart angles.

    Used for aspects which can occur between any combination of planets and angles.
    """
    # Planets
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

    # Chart Angles
    ASCENDANT = "asc"
    IMUM_COELI = "ic"
    DESCENDANT = "dsc"
    MIDHEAVEN = "mc"


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


class House(int, Enum):
    """
    House enumeration with meanings.

    Houses represent different life areas in astrology.
    In whole sign houses, each sign occupies one complete house.
    """
    FIRST = 1
    SECOND = 2
    THIRD = 3
    FOURTH = 4
    FIFTH = 5
    SIXTH = 6
    SEVENTH = 7
    EIGHTH = 8
    NINTH = 9
    TENTH = 10
    ELEVENTH = 11
    TWELFTH = 12

    @property
    def meaning(self) -> str:
        """Get the life area meaning for this house."""
        meanings = {
            1: "self, identity, appearance",
            2: "money, values, resources",
            3: "communication, siblings, short trips",
            4: "home, family, roots",
            5: "creativity, romance, children",
            6: "health, work, daily routines",
            7: "partnerships, relationships",
            8: "transformation, shared resources, intimacy",
            9: "travel, philosophy, higher learning",
            10: "career, public image, goals",
            11: "friendships, groups, hopes",
            12: "spirituality, solitude, unconscious"
        }
        return meanings[self.value]

    @property
    def ordinal(self) -> str:
        """Get the ordinal representation (1st, 2nd, 3rd, etc.)."""
        n = self.value
        if 11 <= n <= 13:
            return f"{n}th"
        else:
            return f"{n}{['th', 'st', 'nd', 'rd', 'th', 'th', 'th', 'th', 'th', 'th'][n % 10]}"


# Planet ruler mappings for each zodiac sign (Modern Astrology)
SIGN_RULERS = {
    ZodiacSign.ARIES: Planet.MARS,
    ZodiacSign.TAURUS: Planet.VENUS,
    ZodiacSign.GEMINI: Planet.MERCURY,
    ZodiacSign.CANCER: Planet.MOON,
    ZodiacSign.LEO: Planet.SUN,
    ZodiacSign.VIRGO: Planet.MERCURY,
    ZodiacSign.LIBRA: Planet.VENUS,
    ZodiacSign.SCORPIO: Planet.PLUTO,      # Modern ruler (traditional: Mars)
    ZodiacSign.SAGITTARIUS: Planet.JUPITER,
    ZodiacSign.CAPRICORN: Planet.SATURN,
    ZodiacSign.AQUARIUS: Planet.URANUS,    # Modern ruler (traditional: Saturn)
    ZodiacSign.PISCES: Planet.NEPTUNE      # Modern ruler (traditional: Jupiter)
}

# Pydantic Models for Chart Data
class PlanetPosition(BaseModel):
    """A planet's position and metadata."""
    name: Planet
    symbol: str
    position_dms: str = Field(description="Formatted position like '15° ♈ 23'")
    sign: ZodiacSign
    degree_in_sign: float = Field(ge=0, lt=30)
    absolute_degree: float = Field(ge=0, lt=360)
    house: int = Field(ge=1, le=12)
    speed: float
    retrograde: bool
    element: Element
    modality: Modality

    @field_validator('name', mode='before')
    @classmethod
    def convert_name(cls, v) -> Planet:
        """Convert string to Planet enum (case-insensitive)."""
        if isinstance(v, Planet):
            return v
        return Planet(v.lower())

    @field_validator('sign', mode='before')
    @classmethod
    def convert_sign(cls, v) -> ZodiacSign:
        """Convert string to ZodiacSign enum (case-insensitive)."""
        if isinstance(v, ZodiacSign):
            return v
        return ZodiacSign(v.lower())


class HouseCusp(BaseModel):
    """A house cusp with ruler information."""
    number: int = Field(ge=1, le=12)
    sign: ZodiacSign
    degree_in_sign: float = Field(ge=0, lt=30)
    absolute_degree: float = Field(ge=0, lt=360)
    ruler: Planet
    ruler_sign: ZodiacSign
    ruler_house: int = Field(ge=1, le=12)
    classic_ruler: Planet
    classic_ruler_sign: ZodiacSign
    classic_ruler_house: int = Field(ge=1, le=12)

    @field_validator('sign', 'ruler_sign', 'classic_ruler_sign', mode='before')
    @classmethod
    def convert_zodiac_sign(cls, v) -> ZodiacSign:
        """Convert string to ZodiacSign enum (case-insensitive)."""
        if isinstance(v, ZodiacSign):
            return v

        # Map unicode symbols to zodiac signs (natal library may return just symbols)
        symbol_map = {
            '♈': ZodiacSign.ARIES,
            '♉': ZodiacSign.TAURUS,
            '♊': ZodiacSign.GEMINI,
            '♋': ZodiacSign.CANCER,
            '♌': ZodiacSign.LEO,
            '♍': ZodiacSign.VIRGO,
            '♎': ZodiacSign.LIBRA,
            '♏': ZodiacSign.SCORPIO,
            '♐': ZodiacSign.SAGITTARIUS,
            '♑': ZodiacSign.CAPRICORN,
            '♒': ZodiacSign.AQUARIUS,
            '♓': ZodiacSign.PISCES
        }

        # Check if it's just a symbol
        v_str = str(v).strip()
        if v_str in symbol_map:
            return symbol_map[v_str]

        # natal library may return "♓ pisces", extract just the text part
        if ' ' in v_str:
            v_str = v_str.split()[-1]

        # Try to extract sign name from lowercase text
        for sign in ZodiacSign:
            if sign.value in v_str.lower():
                return sign

        # If nothing matched, try direct conversion
        return ZodiacSign(v_str.lower())

    @field_validator('ruler', 'classic_ruler', mode='before')
    @classmethod
    def convert_planet(cls, v) -> Planet:
        """Convert string to Planet enum (case-insensitive)."""
        if isinstance(v, Planet):
            return v
        return Planet(v.lower())


class AspectData(BaseModel):
    """An aspect between two celestial bodies (planets or angles)."""
    body1: CelestialBody
    body2: CelestialBody
    aspect_type: AspectType
    aspect_symbol: str
    exact_degree: int = Field(description="Exact degree of aspect (0, 60, 90, 120, 180)")
    orb: float = Field(ge=0, description="Orb in degrees from exact")
    applying: bool = Field(description="True if applying, False if separating")

    @field_validator('body1', 'body2', mode='before')
    @classmethod
    def convert_body(cls, v) -> CelestialBody:
        """Convert string to CelestialBody enum (case-insensitive)."""
        if isinstance(v, CelestialBody):
            return v
        return CelestialBody(v.lower())


class AnglePosition(BaseModel):
    """Position of one of the four angles (Asc, IC, Dsc, MC)."""
    sign: ZodiacSign
    degree_in_sign: float = Field(ge=0, lt=30)
    absolute_degree: float = Field(ge=0, lt=360)
    position_dms: str = Field(description="Formatted position like '15° ♈ 23'")

    @field_validator('sign', mode='before')
    @classmethod
    def convert_sign(cls, v) -> ZodiacSign:
        """Convert string to ZodiacSign enum (case-insensitive)."""
        if isinstance(v, ZodiacSign):
            return v
        return ZodiacSign(v.lower())


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
    # Filter to only supported planets (natal library may return other bodies)
    supported_planet_names = {p.value for p in Planet}
    planets = [
        PlanetPosition(
            name=planet.name,
            symbol=planet.symbol,
            position_dms=planet.signed_dms,
            sign=planet.sign.name,
            degree_in_sign=round(planet.signed_deg + planet.minute / 60, 2),
            absolute_degree=min(round(planet.degree % 360, 2), 359.99),
            house=data.house_of(planet),
            speed=round(planet.speed, 4),
            retrograde=planet.retro,
            element=planet.sign.element,
            modality=planet.sign.modality
        )
        for planet in data.planets
        if planet.name in supported_planet_names
    ]

    # Manually add North Node (calculated point, not in data.planets list)
    if hasattr(data, 'asc_node'):
        north_node = data.asc_node
        planets.append(
            PlanetPosition(
                name="north node",  # type: ignore[arg-type]
                symbol=north_node.symbol if hasattr(north_node, 'symbol') else "☊",
                position_dms=north_node.signed_dms,
                sign=north_node.sign.name,
                degree_in_sign=round(north_node.signed_deg + north_node.minute / 60, 2),
                absolute_degree=min(round(north_node.degree % 360, 2), 359.99),
                house=data.house_of(north_node),
                speed=round(north_node.speed, 4),
                retrograde=north_node.retro if hasattr(north_node, 'retro') else False,
                element=north_node.sign.element,
                modality=north_node.sign.modality
            )
        )

    # Extract house cusps
    houses = [
        HouseCusp(
            number=house.value,
            sign=house.sign.name,
            degree_in_sign=round(house.degree % 30, 2),
            absolute_degree=min(round(house.degree % 360, 2), 359.99),
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
    # Include all aspects (planets and angles) - filter to supported celestial bodies
    supported_body_names = {b.value for b in CelestialBody}
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
        if aspect.body1.name in supported_body_names and aspect.body2.name in supported_body_names
    ]

    # Extract the four angles
    angles = ChartAngles(
        ascendant=AnglePosition(
            sign=data.asc.sign.name,
            degree_in_sign=round(data.asc.signed_deg + data.asc.minute / 60, 2),
            absolute_degree=min(round(data.asc.degree % 360, 2), 359.99),
            position_dms=data.asc.signed_dms
        ),
        imum_coeli=AnglePosition(
            sign=data.ic.sign.name,
            degree_in_sign=round(data.ic.signed_deg + data.ic.minute / 60, 2),
            absolute_degree=min(round(data.ic.degree % 360, 2), 359.99),
            position_dms=data.ic.signed_dms
        ),
        descendant=AnglePosition(
            sign=data.dsc.sign.name,
            degree_in_sign=round(data.dsc.signed_deg + data.dsc.minute / 60, 2),
            absolute_degree=min(round(data.dsc.degree % 360, 2), 359.99),
            position_dms=data.dsc.signed_dms
        ),
        midheaven=AnglePosition(
            sign=data.mc.sign.name,
            degree_in_sign=round(data.mc.signed_deg + data.mc.minute / 60, 2),
            absolute_degree=min(round(data.mc.degree % 360, 2), 359.99),
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
    # Q1 = Houses 1-3 (NE), Q2 = Houses 4-6 (NW), Q3 = Houses 7-9 (SW), Q4 = Houses 10-12 (SE)
    quadrant_counts = [len(q) for q in data.quadrants]

    distributions = ChartDistributions(
        elements=ElementDistribution(**elements),
        modalities=ModalityDistribution(**modalities),
        quadrants=QuadrantDistribution(
            first=quadrant_counts[0],   # Houses 1-3
            second=quadrant_counts[1],  # Houses 4-6
            third=quadrant_counts[2],   # Houses 7-9
            fourth=quadrant_counts[3]   # Houses 10-12
        ),
        hemispheres=HemisphereDistribution(
            # Northern hemisphere: Houses 1-6 (below horizon) = Q1 + Q2
            northern=quadrant_counts[0] + quadrant_counts[1],
            # Southern hemisphere: Houses 7-12 (above horizon) = Q3 + Q4
            southern=quadrant_counts[2] + quadrant_counts[3],
            # Eastern hemisphere: Houses 10-3 (ascendant side/left) = Q1 + Q4
            eastern=quadrant_counts[0] + quadrant_counts[3],
            # Western hemisphere: Houses 4-9 (descendant side/right) = Q2 + Q3
            western=quadrant_counts[1] + quadrant_counts[2]
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
        assert birth_lat and birth_lon
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


def calculate_solar_house(sun_sign: str, transit_sign: str) -> House:
    """
    Calculate the Solar House for a transiting planet using whole sign houses.

    In whole sign house systems, the Sun sign always occupies the 1st house,
    and each subsequent sign occupies the next house in order.

    Args:
        sun_sign: The natal sun sign (e.g., "aries", "taurus")
        transit_sign: The sign of the transiting planet (e.g., "libra", "virgo")

    Returns:
        House enum (e.g., House.FIRST, House.SIXTH) with meaning and ordinal properties

    Examples:
        >>> house = calculate_solar_house("aries", "aries")
        >>> house.value
        1
        >>> house.ordinal
        '1st'
        >>> house.meaning
        'self, identity, appearance'

    Raises:
        ValueError: If invalid sign names are provided
    """
    sign_order = list(ZodiacSign)

    try:
        # Convert strings to enums if needed
        if isinstance(sun_sign, str):
            sun_sign_enum = ZodiacSign(sun_sign.lower())
        else:
            sun_sign_enum = sun_sign

        if isinstance(transit_sign, str):
            transit_sign_enum = ZodiacSign(transit_sign.lower())
        else:
            transit_sign_enum = transit_sign

        natal_sun_sign_index = sign_order.index(sun_sign_enum)
        transit_sign_index = sign_order.index(transit_sign_enum)
    except (ValueError, KeyError):
        raise ValueError(f"Invalid sign name provided: sun_sign={sun_sign}, transit_sign={transit_sign}")

    # Calculate house number using whole sign system
    # Distance from natal sun sign, wrapping around the zodiac
    distance = (transit_sign_index - natal_sun_sign_index) % 12

    # Add 1 to convert from 0-based distance to 1-based house number
    house_number = distance + 1

    # Return House enum
    return House(house_number)


def summarize_transits(transit_chart: dict, sun_sign: str) -> str:
    """
    Extract key transit aspects personalized to a user's sun sign for LLM context.

    Provides highly personalized transit information including:
    - Aspects between transiting planets and natal Sun position
    - Current positions of all personal planets (Sun, Moon, Mercury, Venus, Mars)
    - Positions of outer planets for context
    - Which house areas are being activated
    - Retrograde planets
    - Sign ruler positions

    Args:
        transit_chart: NatalChartData dict from compute_birth_chart() with chart_type="transit"
        sun_sign: Sun sign as string (e.g., "aries", "taurus")

    Returns:
        Personalized summary of key transits for LLM prompt context

    Example:
        >>> transit_data, _ = compute_birth_chart("2025-10-17", birth_time="12:00")
        >>> summary = summarize_transits(transit_data, "taurus")
        >>> print(summary)
        "Your Sun: Taurus. Transit Sun in Libra (6th house - health, work) ..."
    """
    # Convert sun_sign string to ZodiacSign enum if needed
    if isinstance(sun_sign, str):
        sun_sign = ZodiacSign(sun_sign.lower())

    # Extract planets for easy access
    # Note: p["name"] is now a Planet enum (str-based), so we can use it as dict key
    planets = {p["name"]: p for p in transit_chart["planets"]}

    # Build summary parts
    parts = []

    # 1. User's natal Sun sign (identity anchor)
    parts.append(f"Your Sun: {sun_sign.value.title()}")

    # 2. Calculate natal Sun position (use midpoint of sign, ~15°)
    # Map signs to absolute degrees (Aries = 0°, Taurus = 30°, etc.)
    sign_order = list(ZodiacSign)
    natal_sun_sign_index = sign_order.index(sun_sign)
    natal_sun_degree = natal_sun_sign_index * 30 + 15  # Midpoint of sign

    # 3. Transit Sun position with house and aspect to natal Sun
    transit_sun = planets.get(Planet.SUN.value)
    if transit_sun:
        transit_sun_abs = transit_sun["absolute_degree"]
        sun_sign_name = transit_sun["sign"]

        # Calculate house using whole sign system (returns House enum)
        sun_house = calculate_solar_house(sun_sign, sun_sign_name)

        # Calculate aspect to natal Sun
        degree_diff = abs(transit_sun_abs - natal_sun_degree)
        if degree_diff > 180:
            degree_diff = 360 - degree_diff

        natal_sun_aspect = None
        if degree_diff < 5:
            natal_sun_aspect = "conjunction (new beginning)"
        elif 85 <= degree_diff <= 95:
            natal_sun_aspect = "square (challenge, growth)"
        elif 115 <= degree_diff <= 125:
            natal_sun_aspect = "trine (ease, flow)"
        elif 175 <= degree_diff <= 185:
            natal_sun_aspect = "opposition (awareness, balance)"
        elif 55 <= degree_diff <= 65:
            natal_sun_aspect = "sextile (opportunity)"

        sun_part = f"Transit Sun in {sun_sign_name.title()} at {transit_sun['degree_in_sign']:.1f}° (your {sun_house.ordinal} house: {sun_house.meaning})"
        if natal_sun_aspect:
            sun_part += f" - {natal_sun_aspect} your natal Sun"
        parts.append(sun_part)

    # 4. Transit Moon position with house
    transit_moon = planets.get(Planet.MOON.value)
    if transit_moon:
        moon_sign_name = transit_moon["sign"]
        moon_house = calculate_solar_house(sun_sign, moon_sign_name)
        parts.append(f"Transit Moon in {moon_sign_name.title()} at {transit_moon['degree_in_sign']:.1f}° (your {moon_house.ordinal} house: {moon_house.meaning})")

    # 5. Personal planets positions
    personal_info = []
    for planet_name in [Planet.MERCURY.value, Planet.VENUS.value, Planet.MARS.value]:
        planet = planets.get(planet_name)
        if planet:
            sign = planet["sign"]
            degree = planet["degree_in_sign"]
            retro = " Rx" if planet["retrograde"] else ""
            personal_info.append(f"{planet_name.title()} in {sign.title()} {degree:.1f}°{retro}")

    if personal_info:
        parts.append("Personal planets: " + ", ".join(personal_info))

    # 6. Aspects to natal Sun from transiting planets
    natal_sun_aspects = []
    for planet_name in [Planet.MERCURY.value, Planet.VENUS.value, Planet.MARS.value,
                        Planet.JUPITER.value, Planet.SATURN.value]:
        planet = planets.get(planet_name)
        if planet:
            transit_degree = planet["absolute_degree"]
            degree_diff = abs(transit_degree - natal_sun_degree)
            if degree_diff > 180:
                degree_diff = 360 - degree_diff

            # Check for major aspects (tighter orbs for outer planets)
            max_orb = 5 if planet_name in [Planet.JUPITER.value, Planet.SATURN.value] else 3

            if degree_diff < max_orb:
                natal_sun_aspects.append(f"{planet_name.title()} conjunction")
            elif 87 <= degree_diff <= 93:
                natal_sun_aspects.append(f"{planet_name.title()} square")
            elif 117 <= degree_diff <= 123:
                natal_sun_aspects.append(f"{planet_name.title()} trine")
            elif 177 <= degree_diff <= 183:
                natal_sun_aspects.append(f"{planet_name.title()} opposition")
            elif 57 <= degree_diff <= 63:
                natal_sun_aspects.append(f"{planet_name.title()} sextile")

    if natal_sun_aspects:
        parts.append("Aspects to your natal Sun: " + ", ".join(natal_sun_aspects))

    # 7. Outer planets context (slow-moving, set longer-term themes)
    outer_info = []
    for planet_name in [Planet.JUPITER.value, Planet.SATURN.value, Planet.URANUS.value,
                        Planet.NEPTUNE.value, Planet.PLUTO.value]:
        planet = planets.get(planet_name)
        if planet:
            sign = planet["sign"]
            retro = " Rx" if planet["retrograde"] else ""
            outer_info.append(f"{planet_name.title()} in {sign.title()}{retro}")

    if outer_info:
        parts.append("Outer planets: " + ", ".join(outer_info))

    # 8. Sign ruler position (important for sun sign)
    ruler_planet = SIGN_RULERS.get(sun_sign)
    if ruler_planet:
        ruler_planet_name = ruler_planet.value
        if ruler_planet_name in planets:
            ruler = planets[ruler_planet_name]
            ruler_sign_name = ruler["sign"]
            ruler_house = calculate_solar_house(sun_sign, ruler_sign_name)
            retro = " (retrograde)" if ruler["retrograde"] else ""
            parts.append(f"Your ruling planet {ruler_planet_name.title()} in {ruler['sign'].title()} at {ruler['degree_in_sign']:.1f}° (your {ruler_house.ordinal} house){retro}")

    # Join all parts with ". "
    return ". ".join(parts) + "."


# =============================================================================
# Critical Degrees and Transit Speed Analysis
# =============================================================================

class CriticalDegree(str, Enum):
    """Types of critical degrees in astrology."""
    ANARETIC = "anaretic"  # 29° - crisis/completion point
    AVATAR = "avatar"      # 0° - new beginnings
    CRITICAL_CARDINAL = "critical_cardinal"  # 0°, 13°, 26° of cardinal signs


class TransitSpeed(str, Enum):
    """Speed classification for transiting planets."""
    STATIONARY = "stationary"  # Preparing to turn retrograde/direct
    SLOW = "slow"             # Moving slower than average
    AVERAGE = "average"       # Normal speed
    FAST = "fast"            # Moving faster than average


def check_critical_degrees(degree_in_sign: float, sign: ZodiacSign) -> list[tuple[CriticalDegree, str]]:
    """
    Identify critical degree positions with astrological significance.

    Critical degrees mark turning points, intensity, and significance:
    - 29° (Anaretic): Crisis, completion, urgency. Last degree before sign change.
    - 0° (Avatar): Pure essence, new beginning, potent fresh energy.
    - 0°, 13°, 26° of Cardinal signs: Action points, cardinal cross activation.

    Args:
        degree_in_sign: Degree within sign (0-29.999)
        sign: ZodiacSign enum

    Returns:
        List of (CriticalDegree enum, description) tuples

    Examples:
        >>> check_critical_degrees(29.2, ZodiacSign.SCORPIO)
        [(CriticalDegree.ANARETIC, "Crisis/completion point - urgent energy")]

        >>> check_critical_degrees(0.5, ZodiacSign.ARIES)
        [(CriticalDegree.AVATAR, "Pure beginning - potent fresh energy"),
         (CriticalDegree.CRITICAL_CARDINAL, "Cardinal point - action/initiative")]
    """
    flags = []

    # Anaretic degree (29°00' to 29°59')
    if 29.0 <= degree_in_sign < 30.0:
        flags.append((
            CriticalDegree.ANARETIC,
            f"Crisis/completion point - urgent {sign.value} energy culminating"
        ))

    # Avatar degree (0°00' to 0°59')
    if degree_in_sign < 1.0:
        flags.append((
            CriticalDegree.AVATAR,
            f"Pure beginning - potent fresh {sign.value} energy"
        ))

    # Critical degrees in cardinal signs (0°, 13°, 26°)
    cardinal_signs = {ZodiacSign.ARIES, ZodiacSign.CANCER, ZodiacSign.LIBRA, ZodiacSign.CAPRICORN}
    if sign in cardinal_signs:
        critical_points = [
            (0, 1, "initiation"),
            (13, 1, "crisis of action"),
            (26, 1, "completion/preparation")
        ]
        for critical_deg, orb, meaning in critical_points:
            if abs(degree_in_sign - critical_deg) < orb:
                flags.append((
                    CriticalDegree.CRITICAL_CARDINAL,
                    f"Cardinal point ({critical_deg}°) - {meaning}"
                ))
                break  # Only report one cardinal critical degree

    return flags


# Average daily motion for planets (degrees per day)
PLANET_AVERAGE_SPEEDS = {
    Planet.MOON: 13.2,
    Planet.SUN: 0.986,
    Planet.MERCURY: 1.0,
    Planet.VENUS: 1.0,
    Planet.MARS: 0.5,
    Planet.JUPITER: 0.083,
    Planet.SATURN: 0.033,
    Planet.URANUS: 0.014,
    Planet.NEPTUNE: 0.008,
    Planet.PLUTO: 0.006,
}


def analyze_planet_speed(planet: Planet, daily_motion: float) -> tuple[TransitSpeed, str]:
    """
    Analyze transit planet speed relative to average motion.

    Speed matters for timing:
    - Stationary: Major turning point, maximum impact
    - Slow: Lingering influence, drawn-out process
    - Fast: Quick-moving energy, brief window

    Args:
        planet: Planet enum
        daily_motion: Degrees traveled per day (negative if retrograde)

    Returns:
        Tuple of (TransitSpeed enum, description)

    Examples:
        >>> analyze_planet_speed(Planet.MARS, 0.1)
        (TransitSpeed.SLOW, "Slow Mars (0.1°/day) - lingering intensity")

        >>> analyze_planet_speed(Planet.MERCURY, -0.05)
        (TransitSpeed.STATIONARY, "Stationary Mercury (near station) - pivotal")
    """
    avg_speed = PLANET_AVERAGE_SPEEDS.get(planet, 0.5)
    abs_motion = abs(daily_motion)

    # Stationary (within 20% of zero motion)
    if abs_motion < avg_speed * 0.2:
        return (
            TransitSpeed.STATIONARY,
            f"Stationary {planet.value.title()} (near station) - pivotal turning point"
        )

    # Slow (less than 70% of average)
    elif abs_motion < avg_speed * 0.7:
        return (
            TransitSpeed.SLOW,
            f"Slow {planet.value.title()} ({abs_motion:.2f}°/day) - lingering influence"
        )

    # Fast (more than 130% of average)
    elif abs_motion > avg_speed * 1.3:
        return (
            TransitSpeed.FAST,
            f"Fast {planet.value.title()} ({abs_motion:.2f}°/day) - brief window"
        )

    # Average speed
    else:
        return (
            TransitSpeed.AVERAGE,
            f"Normal {planet.value.title()} motion ({abs_motion:.2f}°/day)"
        )


def calculate_aspect_priority(
    transit_planet: Planet,
    natal_planet: Planet,
    aspect_type: AspectType,
    orb: float,
    applying: bool,
    transit_speed: Optional[TransitSpeed] = None,
    natal_house: Optional[int] = None,
    transit_house: Optional[int] = None,
    transit_retrograde: bool = False,
    transit_sign: Optional[ZodiacSign] = None
) -> int:
    """
    Calculate priority score for a natal-transit aspect (0-100).

    Higher scores = more significant transits that deserve attention.

    Scoring factors (expert-calibrated with 9 layers):

    1. Transit planet transformation power (base points):
       - Pluto → personal: 45 points (deepest transformation)
       - Neptune/Uranus → personal: 42 points (spiritual/revolutionary)
       - Saturn → personal: 40 points (structure/lessons)
       - Jupiter → personal: 38 points (expansion/opportunity)
       - Personal → personal: 20 points (brief but impactful)
       - Moon → personal: 12 points (fleeting emotional window)

    2. Orb tightness:
       - < 0.5°: +25 points (nearly exact)
       - < 1.0°: +20 points (very tight)
       - < 2.0°: +10 points (tight)
       - < 3.0°: +5 points (moderate)

    3. Aspect type:
       - Conjunction/Square/Opposition: +15 points (hard aspects)
       - Trine: +8 points (harmonious flow)
       - Sextile: +5 points (opportunity)

    4. Applying/Separating:
       - Applying: +10 points (building energy)
       - Separating <1°: +5 points (shadow period)
       - Separating >1°: 0 points (waning)

    5. Speed classification:
       - Stationary: +15 points (major turning point)
       - Slow: +10 points (lingering influence)

    6. Retrograde context:
       - Rx hard aspects: +8 points (internalized intensity)

    7. Natal planet importance (multiplier):
       - Sun: ×1.3 (identity/ego - ego death potential)
       - Moon: ×1.25 (emotions/security - emotional core)
       - Mars: ×1.1 (action/drive)
       - Saturn: ×1.05 (structure)
       - Others: ×1.0

    8. House placement impact (multiplier):
       - Angular houses (1,4,7,10): ×1.2 (public/visible)
       - Intensity houses (8,12): ×1.15
       - Others: ×1.0

    9. Sign dignity (multiplier):
       - Rulership: ×1.1 (strongest expression)
       - Exaltation: ×1.05 (elevated)
       - Detriment: ×0.9 (challenging)
       - Fall: ×0.85 (weakest)

    Args:
        transit_planet: Transiting planet
        natal_planet: Natal planet being aspected
        aspect_type: Type of aspect
        orb: Orb in degrees
        applying: True if applying
        transit_speed: Optional speed classification
        natal_house: House of natal planet (for angular house bonus)
        transit_house: House of transit planet (optional)
        transit_retrograde: True if transit planet is retrograde
        transit_sign: Sign of transit planet (for dignity modifier)

    Returns:
        Priority score (0-100, with all modifiers applied)

    Examples:
        >>> # Pluto square Sun in 10th house (angular)
        >>> calculate_aspect_priority(
        ...     Planet.PLUTO, Planet.SUN, AspectType.SQUARE, 0.5, True,
        ...     natal_house=10
        ... )
        100  # Pluto(45) + exact(25) + hard(15) + applying(10) + Rx(8)
             # × Sun(1.3) × 10th house(1.2) = capped at 100

        >>> # Jupiter trine Saturn in Cancer (exalted)
        >>> calculate_aspect_priority(
        ...     Planet.JUPITER, Planet.SATURN, AspectType.TRINE, 0.2, True,
        ...     transit_sign=ZodiacSign.CANCER
        ... )
        88  # Jupiter(38) + exact(25) + trine(8) + applying(10)
            # × exaltation(1.05) = 85
    """
    score = 0

    # Natal planet importance weights (identity/core planets weighted higher)
    NATAL_PLANET_WEIGHT = {
        Planet.SUN: 1.3,      # Identity/life force - ego death potential
        Planet.MOON: 1.25,    # Emotions/security - emotional core
        Planet.MARS: 1.1,     # Action/drive - willpower
        Planet.MERCURY: 1.0,  # Base weight
        Planet.VENUS: 1.0,
        Planet.JUPITER: 1.0,
        Planet.SATURN: 1.05,  # Structure - slightly elevated
        Planet.URANUS: 0.95,
        Planet.NEPTUNE: 0.95,
        Planet.PLUTO: 0.95,
        Planet.NORTH_NODE: 0.9
    }

    # House placement impact (angular houses = public/visible)
    HOUSE_IMPACT = {
        1: 1.2,   # Angular houses (1st, 4th, 7th, 10th)
        4: 1.2,   # Foundation/roots
        7: 1.2,   # Partnerships/relationships
        10: 1.2,  # Career/public image
        8: 1.15,  # Transformation/intensity
        12: 1.15, # Spirituality/subconscious
        # All others default to 1.0
    }

    # Sign dignity modifiers (traditional + modern rulerships)
    DIGNITY = {
        # Traditional Rulerships (strongest expression)
        (Planet.SUN, ZodiacSign.LEO): 1.1,
        (Planet.MOON, ZodiacSign.CANCER): 1.1,
        (Planet.MERCURY, ZodiacSign.GEMINI): 1.1,
        (Planet.MERCURY, ZodiacSign.VIRGO): 1.1,
        (Planet.VENUS, ZodiacSign.TAURUS): 1.1,
        (Planet.VENUS, ZodiacSign.LIBRA): 1.1,
        (Planet.MARS, ZodiacSign.ARIES): 1.1,
        (Planet.MARS, ZodiacSign.SCORPIO): 1.1,  # Traditional (Pluto modern)
        (Planet.JUPITER, ZodiacSign.SAGITTARIUS): 1.1,
        (Planet.JUPITER, ZodiacSign.PISCES): 1.1,  # Traditional (Neptune modern)
        (Planet.SATURN, ZodiacSign.CAPRICORN): 1.1,
        (Planet.SATURN, ZodiacSign.AQUARIUS): 1.1,  # Traditional (Uranus modern)

        # Modern Rulerships (outer planets)
        (Planet.URANUS, ZodiacSign.AQUARIUS): 1.1,
        (Planet.NEPTUNE, ZodiacSign.PISCES): 1.1,
        (Planet.PLUTO, ZodiacSign.SCORPIO): 1.1,

        # Exaltations (elevated expression)
        (Planet.SUN, ZodiacSign.ARIES): 1.05,
        (Planet.MOON, ZodiacSign.TAURUS): 1.05,
        (Planet.VENUS, ZodiacSign.PISCES): 1.05,
        (Planet.MARS, ZodiacSign.CAPRICORN): 1.05,
        (Planet.JUPITER, ZodiacSign.CANCER): 1.05,
        (Planet.SATURN, ZodiacSign.LIBRA): 1.05,

        # Detriment (challenging expression - opposite rulership)
        (Planet.SUN, ZodiacSign.AQUARIUS): 0.9,
        (Planet.MOON, ZodiacSign.CAPRICORN): 0.9,
        (Planet.MERCURY, ZodiacSign.SAGITTARIUS): 0.9,
        (Planet.VENUS, ZodiacSign.ARIES): 0.9,
        (Planet.VENUS, ZodiacSign.SCORPIO): 0.9,
        (Planet.MARS, ZodiacSign.LIBRA): 0.9,
        (Planet.MARS, ZodiacSign.TAURUS): 0.9,
        (Planet.JUPITER, ZodiacSign.GEMINI): 0.9,
        (Planet.JUPITER, ZodiacSign.VIRGO): 0.9,
        (Planet.SATURN, ZodiacSign.CANCER): 0.9,
        (Planet.SATURN, ZodiacSign.LEO): 0.9,
        (Planet.URANUS, ZodiacSign.LEO): 0.9,  # Modern
        (Planet.NEPTUNE, ZodiacSign.VIRGO): 0.9,  # Modern
        (Planet.PLUTO, ZodiacSign.TAURUS): 0.9,  # Modern

        # Fall (weakest expression - opposite exaltation)
        (Planet.SUN, ZodiacSign.LIBRA): 0.85,
        (Planet.MOON, ZodiacSign.SCORPIO): 0.85,
        (Planet.MERCURY, ZodiacSign.PISCES): 0.85,  # Fall (not detriment)
        (Planet.VENUS, ZodiacSign.VIRGO): 0.85,
        (Planet.MARS, ZodiacSign.CANCER): 0.85,
        (Planet.JUPITER, ZodiacSign.CAPRICORN): 0.85,
        (Planet.SATURN, ZodiacSign.ARIES): 0.85,
    }

    # Define planet groups with transformation power hierarchy
    transformation_planets = {Planet.PLUTO, Planet.NEPTUNE}  # Deepest transformation
    structural_planets = {Planet.SATURN, Planet.URANUS}      # Major life shifts
    personal_planets = {Planet.SUN, Planet.MOON, Planet.MERCURY, Planet.VENUS, Planet.MARS}
    outer_planets = transformation_planets | structural_planets
    slow_moving = {Planet.JUPITER} | outer_planets

    # 1. Transit planet significance (weighted by transformation power)
    if transit_planet == Planet.PLUTO:
        # Pluto = most transformative, highest priority
        if natal_planet in personal_planets:
            score += 45  # Pluto → personal = deepest transformation
        else:
            score += 35  # Pluto → outer (generational)

    elif transit_planet in {Planet.NEPTUNE, Planet.URANUS}:
        # Neptune/Uranus = spiritual/revolutionary change
        if natal_planet in personal_planets:
            score += 42
        else:
            score += 32

    elif transit_planet == Planet.SATURN:
        # Saturn = structure, lessons, maturity
        if natal_planet in personal_planets:
            score += 40  # Saturn → personal = major lessons
        else:
            score += 30  # Saturn → outer

    elif transit_planet == Planet.JUPITER:
        # Jupiter transits mark expansion/opportunity windows
        if natal_planet in personal_planets:
            score += 38  # Benefic boost - important opportunities
        else:
            score += 28

    elif transit_planet == Planet.MOON:
        # Moon moves fast - brief but potent emotional windows
        if natal_planet in personal_planets:
            score += 12  # Reduced: fleeting influence
        else:
            score += 8

    elif transit_planet in personal_planets:
        # Other personal planets (Sun, Mercury, Venus, Mars)
        if natal_planet in personal_planets:
            score += 20  # Personal → personal
        else:
            score += 15  # Personal → outer

    # 2. Orb tightness (closer = more significant)
    if orb < 0.5:
        score += 25  # Nearly exact
    elif orb < 1.0:
        score += 20  # Very tight
    elif orb < 2.0:
        score += 10  # Tight
    elif orb < 3.0:
        score += 5   # Moderate

    # 3. Aspect type (hard aspects create more transformation)
    if aspect_type in {AspectType.CONJUNCTION, AspectType.SQUARE, AspectType.OPPOSITION}:
        score += 15  # Hard aspects demand action/awareness
    elif aspect_type == AspectType.TRINE:
        score += 8   # Harmonious flow
    elif aspect_type == AspectType.SEXTILE:
        score += 5   # Opportunity

    # 4. Applying vs separating (with shadow period)
    if applying:
        score += 10  # Building energy is more noticeable
    elif not applying and orb < 1.0:
        score += 5   # Still in shadow (separating but within 1°)

    # 5. Speed classification
    if transit_speed == TransitSpeed.STATIONARY:
        score += 15  # Stations are major turning points
    elif transit_speed == TransitSpeed.SLOW:
        score += 10  # Slow = lingering influence

    # 6. Retrograde context (internalized intensity)
    if transit_retrograde:
        if aspect_type in {AspectType.CONJUNCTION, AspectType.SQUARE, AspectType.OPPOSITION}:
            score += 8  # Retrograde hard aspects = internal work/revision

    # 7. Natal planet importance multiplier
    natal_weight = NATAL_PLANET_WEIGHT.get(natal_planet, 1.0)
    score = int(score * natal_weight)

    # 8. House placement impact (apply to natal house if provided)
    if natal_house:
        house_multiplier = HOUSE_IMPACT.get(natal_house, 1.0)
        score = int(score * house_multiplier)

    # 9. Sign dignity modifier (transit planet's strength in its sign)
    if transit_sign:
        dignity_multiplier = DIGNITY.get((transit_planet, transit_sign), 1.0)
        score = int(score * dignity_multiplier)

    return min(100, score)  # Cap at 100


# =============================================================================
# Natal-Transit Aspect Analysis (Personalization Core)
# =============================================================================

class NatalTransitAspect(BaseModel):
    """
    An aspect between a natal planet and a transiting planet.

    This is THE KEY to true personalization - shows what's happening
    to the user's specific chart today.

    Enhanced with priority scoring, speed analysis, and critical degree flags
    for expert-level transit interpretation.
    """
    natal_planet: Planet = Field(description="Natal planet being aspected")
    natal_sign: ZodiacSign = Field(description="Sign of natal planet")
    natal_degree: float = Field(ge=0, lt=360, description="Absolute degree of natal planet")
    natal_house: int = Field(ge=1, le=12, description="House of natal planet")

    transit_planet: Planet = Field(description="Transiting planet")
    transit_sign: ZodiacSign = Field(description="Sign of transiting planet")
    transit_degree: float = Field(ge=0, lt=360, description="Absolute degree of transiting planet")
    transit_speed: Optional[TransitSpeed] = Field(default=None, description="Speed classification (stationary/slow/average/fast)")
    transit_speed_description: Optional[str] = Field(default=None, description="Human-readable speed analysis")

    aspect_type: AspectType = Field(description="Type of aspect")
    exact_degree: int = Field(description="Exact degree of aspect (0, 60, 90, 120, 180)")
    orb: float = Field(ge=0, description="Orb in degrees from exact")
    applying: bool = Field(description="True if applying (building), False if separating (waning)")

    meaning: str = Field(description="Interpretation key for this aspect")
    priority_score: int = Field(default=0, ge=0, le=100, description="Importance score (0-100, higher = more significant)")

    # Critical degree flags
    transit_critical_degrees: list[tuple[str, str]] = Field(
        default_factory=list,
        description="Critical degrees for transit planet: [(degree_type, description), ...]"
    )
    natal_critical_degrees: list[tuple[str, str]] = Field(
        default_factory=list,
        description="Critical degrees for natal planet: [(degree_type, description), ...]"
    )

    @field_validator('natal_planet', 'transit_planet', mode='before')
    @classmethod
    def convert_planet(cls, v) -> Planet:
        """Convert string to Planet enum (case-insensitive)."""
        if isinstance(v, Planet):
            return v
        return Planet(v.lower())

    @field_validator('natal_sign', 'transit_sign', mode='before')
    @classmethod
    def convert_sign(cls, v) -> ZodiacSign:
        """Convert string to ZodiacSign enum (case-insensitive)."""
        if isinstance(v, ZodiacSign):
            return v
        return ZodiacSign(v.lower())

    @field_validator('aspect_type', mode='before')
    @classmethod
    def convert_aspect(cls, v) -> AspectType:
        """Convert string to AspectType enum (case-insensitive)."""
        if isinstance(v, AspectType):
            return v
        return AspectType(v.lower())


def find_natal_transit_aspects(
    natal_chart: dict,
    transit_chart: dict,
    orb: float = 3.0,
    sort_by_priority: bool = True
) -> list[NatalTransitAspect]:
    """
    Find aspects between natal planets and transiting planets.

    This is THE KEY to personalization - shows what's actually happening
    to the user's specific chart today.

    Enhanced with:
    - Priority scoring (importance ranking)
    - Speed analysis (stationary/slow/average/fast)
    - Critical degree detection (29°, 0°, cardinal points)

    Args:
        natal_chart: Natal chart dict from compute_birth_chart()
        transit_chart: Transit chart dict from compute_birth_chart()
        orb: Maximum orb in degrees (default 3.0)
        sort_by_priority: If True, sort by priority score (default). If False, sort by orb.

    Returns:
        List of NatalTransitAspect objects, sorted by priority (or orb if sort_by_priority=False)

    Example:
        >>> natal, _ = compute_birth_chart("1985-05-15")
        >>> transit, _ = compute_birth_chart("2025-10-17", birth_time="12:00")
        >>> aspects = find_natal_transit_aspects(natal, transit)
        >>> if aspects:
        ...     top = aspects[0]
        ...     print(f"Priority {top.priority_score}: {top.transit_planet.value} {top.aspect_type.value} natal {top.natal_planet.value}")
        'Priority 85: saturn square natal sun'
    """
    aspects_found = []

    # Create lookup dicts
    natal_planets = {p["name"]: p for p in natal_chart["planets"]}
    transit_planets = {p["name"]: p for p in transit_chart["planets"]}

    # Major aspects to check
    aspect_definitions = {
        AspectType.CONJUNCTION: (0, "fusion of energies"),
        AspectType.SEXTILE: (60, "opportunity"),
        AspectType.SQUARE: (90, "tension requiring action"),
        AspectType.TRINE: (120, "natural flow"),
        AspectType.OPPOSITION: (180, "awareness through contrast")
    }

    for natal_name, natal_planet in natal_planets.items():
        for transit_name, transit_planet in transit_planets.items():
            natal_deg = natal_planet["absolute_degree"]
            transit_deg = transit_planet["absolute_degree"]

            for aspect_type, (exact_deg, meaning) in aspect_definitions.items():
                # Calculate angle difference
                diff = abs((transit_deg - natal_deg) % 360)
                if diff > 180:
                    diff = 360 - diff

                angle_diff = abs(diff - exact_deg)

                if angle_diff <= orb:
                    # Determine if applying or separating
                    # Simplified: if transit is moving faster, it's applying
                    applying = transit_planet["speed"] > natal_planet.get("speed", 0)

                    # Analyze transit speed
                    transit_planet_enum = Planet(transit_name)
                    speed_enum, speed_desc = analyze_planet_speed(
                        transit_planet_enum,
                        transit_planet["speed"]
                    )

                    # Calculate priority score with all modifiers
                    natal_planet_enum = Planet(natal_name)
                    transit_sign_enum = ZodiacSign(transit_planet["sign"])
                    priority = calculate_aspect_priority(
                        transit_planet_enum,
                        natal_planet_enum,
                        aspect_type,
                        angle_diff,
                        applying,
                        speed_enum,
                        natal_house=natal_planet["house"],
                        transit_house=transit_planet["house"],
                        transit_retrograde=transit_planet["retrograde"],
                        transit_sign=transit_sign_enum
                    )

                    # Check critical degrees
                    natal_deg_in_sign = natal_planet["degree_in_sign"]
                    natal_sign_enum = ZodiacSign(natal_planet["sign"])
                    natal_critical = check_critical_degrees(natal_deg_in_sign, natal_sign_enum)

                    transit_deg_in_sign = transit_planet["degree_in_sign"]
                    transit_sign_enum = ZodiacSign(transit_planet["sign"])
                    transit_critical = check_critical_degrees(transit_deg_in_sign, transit_sign_enum)

                    # Convert critical degree tuples to serializable format
                    natal_critical_list = [(cd.value, desc) for cd, desc in natal_critical]
                    transit_critical_list = [(cd.value, desc) for cd, desc in transit_critical]

                    aspects_found.append(
                        NatalTransitAspect(
                            natal_planet=natal_name,
                            natal_sign=natal_planet["sign"],
                            natal_degree=natal_deg,
                            natal_house=natal_planet["house"],
                            transit_planet=transit_name,
                            transit_sign=transit_planet["sign"],
                            transit_degree=transit_deg,
                            transit_speed=speed_enum,
                            transit_speed_description=speed_desc,
                            aspect_type=aspect_type,
                            exact_degree=exact_deg,
                            orb=round(angle_diff, 2),
                            applying=applying,
                            meaning=meaning,
                            priority_score=priority,
                            natal_critical_degrees=natal_critical_list,
                            transit_critical_degrees=transit_critical_list
                        )
                    )

    # Sort by priority (highest first) or orb (tightest first)
    if sort_by_priority:
        return sorted(aspects_found, key=lambda x: (-x.priority_score, x.orb))
    else:
        return sorted(aspects_found, key=lambda x: x.orb)


def synthesize_critical_degrees(transit_chart: dict) -> dict:
    """
    Synthesize critical degree patterns across all transit planets.

    Identifies major timing alerts when multiple planets are at crisis points
    (29° anaretic) or new beginnings (0° avatar) simultaneously.

    Args:
        transit_chart: Transit chart dict

    Returns:
        Dict with synthesis, anaretic_planets, avatar_planets, and interpretation

    Example:
        >>> transit, _ = compute_birth_chart("2025-11-03", birth_time="12:00")
        >>> synthesis = synthesize_critical_degrees(transit)
        >>> print(synthesis["major_timing_alert"])
        "Three planets at crisis points simultaneously"
    """
    anaretic_planets = []
    avatar_planets = []
    cardinal_critical = []

    for planet in transit_chart["planets"]:
        degree_in_sign = planet["degree_in_sign"]
        sign = ZodiacSign(planet["sign"])
        critical_list = check_critical_degrees(degree_in_sign, sign)

        for deg_type, desc in critical_list:
            planet_name = planet["name"].title()
            if deg_type == CriticalDegree.ANARETIC:
                anaretic_planets.append({
                    "planet": planet_name,
                    "sign": sign.value.title(),
                    "degree": round(degree_in_sign, 1),
                    "description": desc
                })
            elif deg_type == CriticalDegree.AVATAR:
                avatar_planets.append({
                    "planet": planet_name,
                    "sign": sign.value.title(),
                    "degree": round(degree_in_sign, 1),
                    "description": desc
                })
            elif deg_type == CriticalDegree.CRITICAL_CARDINAL:
                cardinal_critical.append({
                    "planet": planet_name,
                    "sign": sign.value.title(),
                    "degree": round(degree_in_sign, 1),
                    "description": desc
                })

    # Synthesize interpretation - count total planets across all critical degree types
    total_critical = len(anaretic_planets) + len(avatar_planets) + len(cardinal_critical)
    anaretic_count = len(anaretic_planets)
    avatar_count = len(avatar_planets)
    cardinal_count = len(cardinal_critical)

    if total_critical >= 5:
        intensity = "MAJOR TIMING ALERT"
        interpretation = (
            f"{total_critical} planets across critical degrees simultaneously "
            f"({anaretic_count} anaretic, {avatar_count} avatar, {cardinal_count} cardinal critical). "
            "This convergence is rare and marks a profound transition week. "
        )

        if anaretic_planets:
            endings = ", ".join([f"{p['planet']} in {p['sign']}" for p in anaretic_planets])
            interpretation += f"Old patterns dying ({endings}). "

        if avatar_planets:
            beginnings = ", ".join([f"{p['planet']} in {p['sign']}" for p in avatar_planets])
            interpretation += f"New energy emerging ({beginnings}). "

        interpretation += "Navigate with awareness of endings enabling new beginnings."

    elif total_critical >= 3:
        intensity = "Significant Timing"
        interpretation = (
            f"{total_critical} planets at critical points "
            f"({anaretic_count} anaretic, {avatar_count} avatar, {cardinal_count} cardinal). "
            "Important threshold week - heightened sensitivity to timing."
        )

    elif total_critical >= 1:
        intensity = "Notable Timing"
        critical_planet = (anaretic_planets + avatar_planets + cardinal_critical)[0]
        interpretation = (
            f"{critical_planet['planet']} at {critical_planet['degree']}° "
            f"{critical_planet['sign']} marks a turning point."
        )

    else:
        intensity = None
        interpretation = "No critical degree patterns at this time."

    return {
        "intensity": intensity,
        "major_timing_alert": total_critical >= 3,
        "anaretic_planets": anaretic_planets,
        "avatar_planets": avatar_planets,
        "cardinal_critical": cardinal_critical,
        "total_count": total_critical,
        "interpretation": interpretation
    }


def ordinal_suffix(n: int) -> str:
    """
    Get proper ordinal suffix for a number.

    Args:
        n: Number (1-12 for houses)

    Returns:
        Ordinal string (1st, 2nd, 3rd, 4th, etc.)

    Examples:
        >>> ordinal_suffix(1)
        '1st'
        >>> ordinal_suffix(3)
        '3rd'
        >>> ordinal_suffix(11)
        '11th'
    """
    if 11 <= n <= 13:  # Special case: 11th, 12th, 13th
        return f"{n}th"

    last_digit = n % 10
    suffix_map = {1: 'st', 2: 'nd', 3: 'rd'}
    suffix = suffix_map.get(last_digit, 'th')
    return f"{n}{suffix}"


def get_house_context(transit_house: int, natal_house: int) -> str:
    """
    Generate house-to-house context for transit aspects.

    Describes the dynamic between the life area activated by transit
    and the natal life area being aspected.

    Args:
        transit_house: House number where transit planet is located (1-12)
        natal_house: House number where natal planet is located (1-12)

    Returns:
        Human-readable description of house-to-house dynamic

    Example:
        >>> get_house_context(11, 2)
        "Friendship/group energy (11th) influences financial security/values (2nd)"
    """
    house_meanings = {
        1: ("identity/self", "how you appear"),
        2: ("resources/values", "what you own/value"),
        3: ("communication/learning", "how you think/connect locally"),
        4: ("home/family", "your foundation/roots"),
        5: ("creativity/pleasure", "self-expression/joy"),
        6: ("health/work", "daily routines/service"),
        7: ("relationships/partnerships", "one-on-one connections"),
        8: ("transformation/shared resources", "deep change/intimacy"),
        9: ("beliefs/expansion", "philosophy/travel"),
        10: ("career/public life", "reputation/achievements"),
        11: ("community/ideals", "friendships/future vision"),
        12: ("spirituality/subconscious", "hidden realms/release")
    }

    transit_theme, transit_detail = house_meanings.get(transit_house, ("unknown", ""))
    natal_theme, natal_detail = house_meanings.get(natal_house, ("unknown", ""))

    if transit_house == natal_house:
        return f"Activating your {natal_theme} - direct impact on {natal_detail}"
    else:
        return f"{transit_theme.title()} ({ordinal_suffix(transit_house)}) influences {natal_theme} ({ordinal_suffix(natal_house)})"


def synthesize_transit_themes(aspects: list[NatalTransitAspect], top_n: int = 5) -> dict:
    """
    Synthesize themes across multiple related transits with actionable timing windows.

    Identifies patterns like:
    - Multiple planets aspecting same natal planet (convergence)
    - Same transit planet aspecting multiple natal planets (broadcast)
    - Complementary aspects (harmony vs tension themes)
    - Related house activations
    - Timing windows and peak influence periods

    Args:
        aspects: List of NatalTransitAspect objects (should be prioritized)
        top_n: Number of top aspects to analyze for themes

    Returns:
        Dict with enhanced theme_synthesis, convergence_patterns, timing_windows

    Example:
        >>> aspects = find_natal_transit_aspects(natal, transit)
        >>> themes = synthesize_transit_themes(aspects[:5])
        >>> print(themes["theme_synthesis"])
        "JUPITER MEGA-BLESSING WEEK: Jupiter sextile Sun + Jupiter trine Saturn..."
    """
    top_aspects = aspects[:top_n]

    if not top_aspects:
        return {
            "theme_synthesis": "No major aspects at this time.",
            "convergence_patterns": [],
            "harmony_tension_balance": "neutral",
            "timing_windows": []
        }

    # Count natal planets being aspected
    natal_planet_count = {}
    transit_planet_count = {}

    for aspect in top_aspects:
        natal_planet_count[aspect.natal_planet] = natal_planet_count.get(aspect.natal_planet, 0) + 1
        transit_planet_count[aspect.transit_planet] = transit_planet_count.get(aspect.transit_planet, 0) + 1

    # Find convergence (multiple transits to same natal planet)
    convergence_patterns = []
    for natal_planet, count in natal_planet_count.items():
        if count >= 2:
            related_aspects = [a for a in top_aspects if a.natal_planet == natal_planet]
            aspecting_transits = [a.transit_planet.value.title() for a in related_aspects]

            # Enhanced convergence interpretation with specific planet meanings
            planet_meanings = {
                Planet.SUN: "identity/vitality",
                Planet.MOON: "emotions/comfort needs",
                Planet.MERCURY: "thinking/communication",
                Planet.VENUS: "relationships/values",
                Planet.MARS: "action/desire",
                Planet.JUPITER: "growth/optimism",
                Planet.SATURN: "structure/discipline"
            }

            natal_meaning = planet_meanings.get(natal_planet, natal_planet.value)

            # Analyze aspect types for convergence
            aspect_qualities = []
            for asp in related_aspects:
                if asp.aspect_type in {AspectType.TRINE, AspectType.SEXTILE}:
                    aspect_qualities.append(("harmonious", asp.transit_planet))
                elif asp.aspect_type in {AspectType.SQUARE, AspectType.OPPOSITION}:
                    aspect_qualities.append(("challenging", asp.transit_planet))
                else:
                    aspect_qualities.append(("fusion", asp.transit_planet))

            # Build detailed interpretation
            detailed_interp = f"Natal {natal_planet.value.title()} ({natal_meaning}) receiving:\n"
            for qual, tplanet in aspect_qualities:
                detailed_interp += f"  • Transit {tplanet.value.title()} {aspects[0].aspect_type.value} ({qual})\n"

            convergence_patterns.append({
                "focal_planet": f"Natal {natal_planet.value.title()}",
                "focal_meaning": natal_meaning,
                "aspecting_planets": aspecting_transits,
                "aspect_details": [{"planet": tp.value, "quality": q} for q, tp in aspect_qualities],
                "count": count,
                "interpretation": f"Multiple forces converging on your {natal_meaning} - heightened focus on this life area",
                "detailed_interpretation": detailed_interp.strip()
            })

    # Analyze harmony vs tension
    harmonious = 0
    challenging = 0

    for aspect in top_aspects:
        if aspect.aspect_type in {AspectType.TRINE, AspectType.SEXTILE}:
            harmonious += 1
        elif aspect.aspect_type in {AspectType.SQUARE, AspectType.OPPOSITION}:
            challenging += 1

    if harmonious > challenging * 1.5:
        balance = "harmonious"
        balance_desc = "Flow and ease dominate - opportunities unfold naturally"
    elif challenging > harmonious * 1.5:
        balance = "challenging"
        balance_desc = "Tension and friction dominate - growth through effort required"
    else:
        balance = "mixed"
        balance_desc = "Balance of ease and challenge - navigate complexity skillfully"

    # Enhanced synthesis with specific action windows
    if len(top_aspects) >= 3:
        first = top_aspects[0]
        second = top_aspects[1]
        third = top_aspects[2]

        outer_planets = {Planet.SATURN, Planet.URANUS, Planet.NEPTUNE, Planet.PLUTO, Planet.JUPITER}

        # Check for special "mega" patterns (same transit planet multiple harmonious aspects)
        jupiter_harmonious = [a for a in top_aspects if a.transit_planet == Planet.JUPITER
                             and a.aspect_type in {AspectType.TRINE, AspectType.SEXTILE}]

        if len(jupiter_harmonious) >= 2:
            # JUPITER MEGA-BLESSING pattern
            aspects_str = " + ".join([
                f"Jupiter {a.aspect_type.value} {a.natal_planet.value.title()} ({a.natal_planet.value})"
                for a in jupiter_harmonious[:2]
            ])

            theme_synthesis = f"JUPITER MEGA-BLESSING WEEK\n{aspects_str}\n"
            theme_synthesis += "Perfect timing for: job negotiations, launching projects, making commitments that expand your world with solid foundation"

        else:
            # Regular theme synthesis
            themes = []
            for aspect in [first, second, third]:
                if aspect.transit_planet in outer_planets:
                    if aspect.aspect_type in {AspectType.TRINE, AspectType.SEXTILE}:
                        themes.append(f"{aspect.transit_planet.value.title()}-{aspect.natal_planet.value.title()} harmony")
                    elif aspect.aspect_type in {AspectType.SQUARE, AspectType.OPPOSITION}:
                        themes.append(f"{aspect.transit_planet.value.title()}-{aspect.natal_planet.value.title()} tension")
                    else:
                        themes.append(f"{aspect.transit_planet.value.title()}-{aspect.natal_planet.value.title()} fusion")

            if themes:
                theme_synthesis = " + ".join(themes[:2])

                # Add interpretation based on combination
                if "harmony" in theme_synthesis and "tension" in theme_synthesis:
                    theme_synthesis += " = Opportunity for structured growth through manageable challenge"
                elif "harmony" in theme_synthesis:
                    theme_synthesis += " = Prime time for expansion and manifestation with natural support"
                elif "tension" in theme_synthesis:
                    theme_synthesis += " = Transformation through confronting limitations and pushing boundaries"
            else:
                theme_synthesis = f"{len(top_aspects)} aspects active - complex multi-faceted period"
    else:
        # Simple case
        top = top_aspects[0]
        theme_synthesis = (
            f"Primary focus: {top.transit_planet.value.title()} {top.aspect_type.value} "
            f"natal {top.natal_planet.value.title()} - {top.meaning}"
        )

    return {
        "theme_synthesis": theme_synthesis,
        "convergence_patterns": convergence_patterns,
        "harmony_tension_balance": balance,
        "balance_description": balance_desc,
        "total_harmonious": harmonious,
        "total_challenging": challenging
    }


def get_intensity_indicator(priority_score: int, orb: float) -> str:
    """
    Generate visual intensity indicator based on priority and orb tightness.

    Returns emoji indicators showing transit strength:
    - ⚡⚡⚡ (3 bolts) = Priority 90+ OR orb < 0.5° (PEAK INFLUENCE)
    - ⚡⚡ (2 bolts) = Priority 70-89 OR orb 0.5-1.0° (STRONG)
    - ⚡ (1 bolt) = Priority 50-69 OR orb 1.0-2.0° (MODERATE)
    - · (dot) = Priority < 50 OR orb > 2.0° (BACKGROUND)

    Args:
        priority_score: Aspect priority (0-100)
        orb: Orb in degrees

    Returns:
        Intensity indicator string

    Example:
        >>> get_intensity_indicator(95, 0.35)
        '⚡⚡⚡'
        >>> get_intensity_indicator(75, 0.8)
        '⚡⚡'
    """
    if priority_score >= 90 or orb < 0.5:
        return "⚡⚡⚡"
    elif priority_score >= 70 or orb < 1.0:
        return "⚡⚡"
    elif priority_score >= 50 or orb < 2.0:
        return "⚡"
    else:
        return "·"


def get_speed_timing_details(planet: Planet, daily_motion: float, orb: float) -> dict:
    """
    Enhanced speed analysis with specific timing windows and influence duration.

    Args:
        planet: Planet enum
        daily_motion: Degrees per day
        orb: Current orb in degrees

    Returns:
        Dict with speed classification, timing description, and influence window

    Example:
        >>> get_speed_timing_details(Planet.JUPITER, 0.05, 0.35)
        {
            "speed_enum": "slow",
            "speed_description": "SLOW (Jupiter at 0.05°/day vs average 0.08°/day)",
            "timing_impact": "3-week influence window instead of normal 2 weeks",
            "peak_window": "Now through Nov 15",
            "best_use": "Long-term decisions, big commitments"
        }
    """
    from datetime import datetime, timedelta

    speed_enum, base_desc = analyze_planet_speed(planet, daily_motion)
    avg_speed = PLANET_AVERAGE_SPEEDS.get(planet, 0.5)

    # Calculate influence duration based on orb and speed
    if abs(daily_motion) > 0:
        days_to_exact = orb / abs(daily_motion)
        days_total_influence = (2.0) / abs(daily_motion)  # Assuming 2° total orb
    else:
        days_to_exact = 999  # Stationary
        days_total_influence = 999

    # Calculate dates
    today = datetime.now()
    peak_end_date = today + timedelta(days=min(days_total_influence, 60))

    result = {
        "speed_enum": speed_enum.value,
        "speed_description": base_desc,
        "timing_impact": None,
        "peak_window": None,
        "best_use": None
    }

    if speed_enum == TransitSpeed.STATIONARY:
        result["timing_impact"] = "Maximum impact - station point marks major turning point"
        result["peak_window"] = "Critical 2-week window around station"
        result["best_use"] = "Life-changing decisions, major commitments, transformation work"

    elif speed_enum == TransitSpeed.SLOW:
        # Calculate extended window
        ratio = abs(daily_motion) / avg_speed if avg_speed > 0 else 1
        normal_weeks = 2
        extended_weeks = int(normal_weeks / ratio) if ratio > 0 else normal_weeks * 2

        result["timing_impact"] = f"{extended_weeks}-week influence window instead of normal {normal_weeks} weeks"
        result["peak_window"] = f"Now through {peak_end_date.strftime('%b %d')}"
        result["best_use"] = "Long-term decisions, big commitments, sustained efforts"

    elif speed_enum == TransitSpeed.FAST:
        # Distinguish between truly fast planets and slow outer planets labeled "fast" relative to their average
        if abs(daily_motion) < 0.03:  # Very slow outer planets (Pluto, Neptune)
            # Even though "fast" for them, still moves slowly in absolute terms
            result["timing_impact"] = "Slow-burn transformation - effects unfold over weeks"
            result["peak_window"] = f"Integration window: {today.strftime('%b %d')} - {(today + timedelta(days=21)).strftime('%b %d')}"
            result["best_use"] = "Process insights, integrate changes, deep psychological work"
        else:
            result["timing_impact"] = "Brief but intense - act within days"
            result["peak_window"] = f"{today.strftime('%b %d')} - {(today + timedelta(days=7)).strftime('%b %d')}"
            result["best_use"] = "Quick opportunities, immediate actions, time-sensitive matters"

    else:  # AVERAGE
        result["timing_impact"] = "Standard influence duration"
        result["peak_window"] = f"Active through {peak_end_date.strftime('%b %d')}"
        result["best_use"] = "Normal pacing, balanced approach"

    return result


def format_transit_summary_for_ui(
    natal_chart: dict,
    transit_chart: dict,
    max_aspects: int = 5
) -> dict:
    """
    Create a formatted transit summary perfect for UI display with enhanced visuals.

    Returns a structured dict with:
    - Priority transits with intensity indicators (⚡⚡⚡)
    - Critical degree alerts
    - Retrograde status with natal chart connections
    - Speed classifications with timing windows
    - Transit positions with house meanings
    - Enhanced convergence patterns

    Args:
        natal_chart: Natal chart dict
        transit_chart: Transit chart dict
        max_aspects: Maximum number of aspects to return (default 5)

    Returns:
        Dict with formatted transit data ready for JSON serialization

    Example:
        >>> natal, _ = compute_birth_chart("1985-05-15")
        >>> transit, _ = compute_birth_chart("2025-10-17", birth_time="12:00")
        >>> summary = format_transit_summary_for_ui(natal, transit)
        >>> print(summary["priority_transits"][0]["description"])
        "⚡⚡⚡ Saturn square natal Sun (0.5° orb) - PEAK INFLUENCE"
    """
    # Find all natal-transit aspects
    aspects = find_natal_transit_aspects(natal_chart, transit_chart, orb=3.0, sort_by_priority=True)

    # Top priority transits with enhanced visuals and timing
    priority_transits = []
    for aspect in aspects[:max_aspects]:
        # Visual intensity indicator
        intensity_indicator = get_intensity_indicator(aspect.priority_score, aspect.orb)

        orb_label = "exact" if aspect.orb < 0.5 else "tight" if aspect.orb < 1.5 else "moderate"
        applying_label = "applying" if aspect.applying else "separating"

        # Enhanced description with intensity indicator
        transit_desc = f"{intensity_indicator} {aspect.transit_planet.value.title()} {aspect.aspect_type.value} natal {aspect.natal_planet.value.title()}"

        # Add intensity label for UI
        if aspect.priority_score >= 90 or aspect.orb < 0.5:
            intensity_label = "PEAK INFLUENCE"
        elif aspect.priority_score >= 70:
            intensity_label = "STRONG"
        else:
            intensity_label = None

        # Get transit planet data for speed analysis
        transit_planet_data = next(
            (p for p in transit_chart["planets"] if p["name"] == aspect.transit_planet.value),
            None
        )

        # Enhanced speed analysis with timing windows
        speed_timing = None
        if transit_planet_data:
            speed_timing = get_speed_timing_details(
                aspect.transit_planet,
                transit_planet_data["speed"],
                aspect.orb
            )

        # Add critical degree warnings
        critical_notes = []
        for deg_type, desc in aspect.transit_critical_degrees:
            critical_notes.append(desc)
        for deg_type, desc in aspect.natal_critical_degrees:
            critical_notes.append(f"Natal: {desc}")

        transit_house = transit_planet_data["house"] if transit_planet_data else None

        # Generate house context
        house_context = None
        if transit_house:
            house_context = get_house_context(transit_house, aspect.natal_house)

        priority_transits.append({
            "description": transit_desc,
            "intensity_indicator": intensity_indicator,
            "intensity_label": intensity_label,
            "priority_score": aspect.priority_score,
            "transit_planet": aspect.transit_planet.value,
            "natal_planet": aspect.natal_planet.value,
            "aspect_type": aspect.aspect_type.value,
            "orb": aspect.orb,
            "orb_label": orb_label,
            "applying": aspect.applying,
            "applying_label": applying_label,
            "speed_timing": speed_timing,
            "critical_degrees": critical_notes,
            "meaning": aspect.meaning,
            "natal_house": aspect.natal_house,
            "transit_house": transit_house,
            "house_context": house_context
        })

    # Critical degree alerts (any planet at 29° or 0°)
    critical_alerts = []
    for planet in transit_chart["planets"]:
        degree_in_sign = planet["degree_in_sign"]
        sign = ZodiacSign(planet["sign"])
        critical_list = check_critical_degrees(degree_in_sign, sign)

        for deg_type, desc in critical_list:
            if deg_type in {CriticalDegree.ANARETIC, CriticalDegree.AVATAR}:
                critical_alerts.append({
                    "planet": planet["name"].title(),
                    "type": deg_type.value,
                    "degree": degree_in_sign,
                    "sign": sign.value.title(),
                    "description": desc
                })

    # Enhanced retrograde planets with natal chart connections
    retrograde_planets = []
    natal_sun_sign = ZodiacSign(natal_chart["planets"][0]["sign"])

    for planet in transit_chart["planets"]:
        if planet["retrograde"]:
            planet_enum = Planet(planet["name"])
            speed_enum, speed_desc = analyze_planet_speed(planet_enum, planet["speed"])
            transit_sign = ZodiacSign(planet["sign"])

            # Check if retrograde is in same sign as natal Sun
            natal_connection = None
            if transit_sign == natal_sun_sign:
                natal_connection = {
                    "type": "sun_sign",
                    "message": f"⚠️ Your Sun is in {natal_sun_sign.value.title()}! This retrograde is reviewing your identity/self-expression."
                }

            # Check if retrograde is aspecting natal planets (within 3° orb)
            natal_aspects_during_rx = []
            for natal_planet in natal_chart["planets"]:
                natal_deg = natal_planet["absolute_degree"]
                transit_deg = planet["absolute_degree"]

                diff = abs((transit_deg - natal_deg) % 360)
                if diff > 180:
                    diff = 360 - diff

                if diff < 3.0:  # Within 3° orb
                    natal_aspects_during_rx.append({
                        "natal_planet": natal_planet["name"].title(),
                        "orb": round(diff, 1),
                        "message": f"Retrograde affecting your natal {natal_planet['name'].title()}"
                    })

            retrograde_planets.append({
                "planet": planet["name"].title(),
                "sign": planet["sign"].title(),
                "degree": round(planet["degree_in_sign"], 1),
                "speed_status": speed_enum.value,
                "speed_description": speed_desc,
                "natal_connection": natal_connection,
                "natal_aspects": natal_aspects_during_rx if natal_aspects_during_rx else None
            })

    # Transit planet positions with speed
    planet_positions = []
    for planet in transit_chart["planets"]:
        planet_enum = Planet(planet["name"])
        speed_enum, speed_desc = analyze_planet_speed(planet_enum, planet["speed"])

        planet_positions.append({
            "planet": planet["name"].title(),
            "sign": planet["sign"].title(),
            "degree": round(planet["degree_in_sign"], 1),
            "house": planet["house"],
            "retrograde": planet["retrograde"],
            "speed_status": speed_enum.value
        })

    # Generate synthesis
    critical_synthesis = synthesize_critical_degrees(transit_chart)
    theme_synthesis = synthesize_transit_themes(aspects, top_n=max_aspects)

    return {
        "priority_transits": priority_transits,
        "critical_degree_alerts": critical_alerts,
        "critical_degree_synthesis": critical_synthesis,
        "theme_synthesis": theme_synthesis,
        "retrograde_planets": retrograde_planets,
        "planet_positions": planet_positions,
        "total_aspects_found": len(aspects)
    }


# =============================================================================
# Lunar Phase Analysis
# =============================================================================

class LunarPhase(BaseModel):
    """Lunar phase information with actionable guidance."""
    phase_name: str = Field(description="Phase name (e.g., 'new_moon', 'waxing_crescent')")
    phase_emoji: str = Field(description="Moon emoji for this phase")
    angle: float = Field(ge=0, lt=360, description="Angle between Sun and Moon in degrees")
    illumination_percent: int = Field(ge=0, le=100, description="Percentage of moon illuminated")
    energy: str = Field(description="Energetic quality of this phase")
    ritual_suggestion: str = Field(description="Recommended activity or focus")


def calculate_lunar_phase(sun_degree: float, moon_degree: float) -> LunarPhase:
    """
    Calculate lunar phase and return actionable info.

    Args:
        sun_degree: Absolute degree of Sun (0-360)
        moon_degree: Absolute degree of Moon (0-360)

    Returns:
        LunarPhase object with phase name, emoji, and guidance

    Example:
        >>> phase = calculate_lunar_phase(180.0, 270.0)
        >>> phase.phase_name
        'last_quarter'
        >>> phase.phase_emoji
        '🌗'
    """
    # Calculate angle between Sun and Moon
    angle = (moon_degree - sun_degree) % 360

    # Define phases with their ranges
    phases = [
        (0, 45, "new_moon", "🌑", "New beginnings, fresh starts", "Plant seeds of intention"),
        (45, 90, "waxing_crescent", "🌒", "Growth, momentum building", "Take first action steps"),
        (90, 135, "first_quarter", "🌓", "Decision point, overcoming obstacles", "Push through resistance"),
        (135, 180, "waxing_gibbous", "🌔", "Refinement, almost there", "Fine-tune and adjust"),
        (180, 225, "full_moon", "🌕", "Culmination, illumination, release", "Celebrate and let go"),
        (225, 270, "waning_gibbous", "🌖", "Gratitude, sharing wisdom", "Give back, teach others"),
        (270, 315, "last_quarter", "🌗", "Reevaluation, course correction", "Release what's not working"),
        (315, 360, "waning_crescent", "🌘", "Rest, reflection, surrender", "Dream and restore")
    ]

    # Find matching phase
    for start, end, name, emoji, energy, ritual in phases:
        if start <= angle < end:
            # Calculate illumination percentage
            # Maximum illumination (100%) at 180°, minimum (0%) at 0°/360°
            illumination = int((1 - abs(angle - 180) / 180) * 100)

            return LunarPhase(
                phase_name=name,
                phase_emoji=emoji,
                angle=round(angle, 1),
                illumination_percent=illumination,
                energy=energy,
                ritual_suggestion=ritual
            )

    # Default to new moon if somehow no match
    return LunarPhase(
        phase_name="new_moon",
        phase_emoji="🌑",
        angle=0.0,
        illumination_percent=0,
        energy="New beginnings, fresh starts",
        ritual_suggestion="Plant seeds of intention"
    )


# =============================================================================
# Enhanced Transit Summary with Natal Context
# =============================================================================
# Upcoming Transits (Look-Ahead)
# =============================================================================

class TransitStatus(str, Enum):
    """Status of a transit relative to today."""
    ACTIVE = "active"  # Already within orb, ongoing
    ENTERING = "entering"  # Coming into orb (was not in orb yesterday)
    EXACT = "exact"  # Becoming exact (within 0.2° orb)
    LEAVING = "leaving"  # Moving out of orb soon


class TransitPriority(str, Enum):
    """Priority level based on planet speed and significance."""
    HIGH = "high"  # Outer planets (Saturn, Uranus, Neptune, Pluto) - slow, major life themes
    MEDIUM = "medium"  # Jupiter, Mars - intermediate speed, significant events
    LOW = "low"  # Sun, Moon, Mercury, Venus - fast-moving, daily fluctuations


class UpcomingTransit(BaseModel):
    """A significant transit (current or upcoming)."""
    date: str = Field(description="Date of transit (YYYY-MM-DD)")
    days_away: int = Field(ge=0, description="Days until this transit (0=today)")
    aspect: NatalTransitAspect = Field(description="The aspect that will occur")
    description: str = Field(description="Human-readable description")
    status: TransitStatus = Field(description="Current status of this transit")
    orb_today: float = Field(description="Orb in degrees today")
    orb_exact_date: Optional[str] = Field(default=None, description="Date when aspect becomes exact (closest orb)")
    priority: TransitPriority = Field(description="Priority level based on planet speed")
    transit_house: int = Field(ge=1, le=12, description="Solar house where transit is occurring")
    natal_house: int = Field(ge=1, le=12, description="House of natal planet being aspected")


def get_upcoming_transits(
    natal_chart: dict,
    start_date: str,
    days_ahead: int = 7
) -> list[UpcomingTransit]:
    """
    Calculate significant transits over the next N days, showing active and upcoming.

    Returns transits with status indicators:
    - ACTIVE: Already within orb today, ongoing
    - ENTERING: New aspect coming into orb (wasn't active yesterday)
    - EXACT: Becoming exact (within 0.2° orb)
    - LEAVING: Moving out of orb (separating, orb > 1.5°)

    Args:
        natal_chart: Natal chart dict from compute_birth_chart()
        start_date: Starting date (YYYY-MM-DD) - typically today
        days_ahead: Number of days to look ahead (default 7)

    Returns:
        List of all UpcomingTransit objects found in the period

    Example:
        >>> natal, _ = compute_birth_chart("1985-05-15")
        >>> transits = get_upcoming_transits(natal, "2025-10-17", days_ahead=7)
        >>> for t in transits:
        ...     print(f"Day {t.days_away}: {t.description} ({t.status.value})")
    """
    from datetime import datetime, timedelta

    base_date = datetime.strptime(start_date, "%Y-%m-%d")

    # Get yesterday's aspects to determine what's new vs ongoing
    yesterday_date = base_date - timedelta(days=1)
    yesterday_chart, _ = compute_birth_chart(
        yesterday_date.strftime("%Y-%m-%d"),
        birth_time="12:00"
    )
    yesterday_aspects = find_natal_transit_aspects(natal_chart, yesterday_chart, orb=2.0)
    yesterday_keys = {
        (a.transit_planet, a.aspect_type, a.natal_planet)
        for a in yesterday_aspects
    }

    all_transits = []
    seen_keys = set()

    # Scan all days from today through days_ahead
    for day_offset in range(0, days_ahead + 1):
        check_date = base_date + timedelta(days=day_offset)
        check_date_str = check_date.strftime("%Y-%m-%d")

        check_chart, _ = compute_birth_chart(check_date_str, birth_time="12:00")
        aspects = find_natal_transit_aspects(natal_chart, check_chart, orb=2.0)

        for aspect in aspects:
            transit_key = (aspect.transit_planet, aspect.aspect_type, aspect.natal_planet, day_offset)

            # Skip duplicates within same day
            if transit_key in seen_keys:
                continue
            seen_keys.add(transit_key)

            description = (
                f"{aspect.transit_planet.value.title()} "
                f"{aspect.aspect_type.value} your natal "
                f"{aspect.natal_planet.value.title()}"
            )

            # Determine status
            aspect_key = (aspect.transit_planet, aspect.aspect_type, aspect.natal_planet)

            if aspect.orb <= 0.2:
                status = TransitStatus.EXACT
            elif day_offset == 0 and aspect_key not in yesterday_keys:
                status = TransitStatus.ENTERING
            elif day_offset > 0 and aspect_key not in yesterday_keys:
                status = TransitStatus.ENTERING
            elif aspect.orb > 1.5 and not aspect.applying:
                status = TransitStatus.LEAVING
            else:
                status = TransitStatus.ACTIVE

            # Determine priority based on transiting planet speed
            outer_planets = {Planet.SATURN, Planet.URANUS, Planet.NEPTUNE, Planet.PLUTO}
            medium_planets = {Planet.JUPITER, Planet.MARS}

            if aspect.transit_planet in outer_planets:
                priority = TransitPriority.HIGH
            elif aspect.transit_planet in medium_planets:
                priority = TransitPriority.MEDIUM
            else:
                priority = TransitPriority.LOW

            # Calculate transit house (where the transiting planet is)
            sun_sign = ZodiacSign(natal_chart["planets"][0]["sign"])
            transit_house = calculate_solar_house(sun_sign, aspect.transit_sign)

            all_transits.append(
                UpcomingTransit(
                    date=check_date_str,
                    days_away=day_offset,
                    aspect=aspect,
                    description=description,
                    status=status,
                    orb_today=aspect.orb,
                    orb_exact_date=check_date_str if aspect.orb <= 0.2 else None,
                    priority=priority,
                    transit_house=transit_house.value,
                    natal_house=aspect.natal_house
                )
            )

    # Return all transits found
    return all_transits


# =============================================================================
# Prompt Helper Functions
# =============================================================================

def describe_chart_emphasis(distributions: dict) -> str:
    """
    Describe chart emphasis from element/modality distributions.

    Args:
        distributions: Chart distributions dict with 'elements' and 'modalities'

    Returns:
        Human-readable description of chart emphasis

    Example:
        >>> distributions = {
        ...     'elements': {'fire': 3, 'earth': 4, 'air': 2, 'water': 2},
        ...     'modalities': {'cardinal': 3, 'fixed': 5, 'mutable': 3}
        ... }
        >>> describe_chart_emphasis(distributions)
        '4 planets in Earth signs, 5 planets in Fixed mode'
    """
    elements = distributions.get('elements', {})
    modalities = distributions.get('modalities', {})

    # Find dominant element
    if elements:
        dominant_element = max(elements.items(), key=lambda x: x[1])
        element_str = f"{dominant_element[1]} planets in {dominant_element[0].title()} signs"
    else:
        element_str = "balanced elemental distribution"

    # Find dominant modality
    if modalities:
        dominant_modality = max(modalities.items(), key=lambda x: x[1])
        modality_str = f"{dominant_modality[1]} planets in {dominant_modality[0].title()} mode"
    else:
        modality_str = "balanced modal distribution"

    return f"{element_str}, {modality_str}"


def lunar_house_interpretation(house: House) -> str:
    """
    Interpret Moon's transit through a solar house.

    Args:
        house: House enum representing Moon's position

    Returns:
        Interpretation of emotional focus for this house

    Example:
        >>> lunar_house_interpretation(House.FIRST)
        'brings emotional focus to your identity and how you present yourself'
    """
    interpretations = {
        House.FIRST: "brings emotional focus to your identity and how you present yourself",
        House.SECOND: "heightens feelings about security and self-worth",
        House.THIRD: "makes communication and learning emotionally colored",
        House.FOURTH: "draws attention to home, family, and roots",
        House.FIFTH: "enlivens creativity and heart-centered expression",
        House.SIXTH: "brings emotions into daily routines and health practices",
        House.SEVENTH: "sensitizes you to partnership dynamics",
        House.EIGHTH: "deepens emotional intimacy and transformation",
        House.NINTH: "expands your emotional horizons through meaning-seeking",
        House.TENTH: "brings feelings about career and public role to the surface",
        House.ELEVENTH: "activates emotional connection to community and aspirations",
        House.TWELFTH: "calls for emotional solitude and spiritual retreat"
    }

    return interpretations.get(house, "colors your emotional experience")


def moon_sign_emotional_quality(moon_sign: ZodiacSign) -> str:
    """
    Describe emotional tone of Moon transiting through a sign.

    Args:
        moon_sign: ZodiacSign enum for Moon's position

    Returns:
        Description of emotional quality

    Example:
        >>> moon_sign_emotional_quality(ZodiacSign.ARIES)
        'impulsive, direct emotional responses and desire for action'
    """
    qualities = {
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

    return qualities.get(moon_sign, "emotional coloring")


def format_primary_aspect_details(aspect: 'NatalTransitAspect') -> str:
    """
    Format primary natal-transit aspect for detailed LLM prompt.

    Args:
        aspect: NatalTransitAspect Pydantic model

    Returns:
        Detailed formatted string for prompt

    Example:
        >>> format_primary_aspect_details(aspect)
        'Transit Saturn at 15.2° Pisces forms a square (90°) to your natal Moon...'
    """
    house = House(aspect.natal_house)

    return f"""Transit {aspect.transit_planet.value.title()} at {aspect.transit_degree:.1f}° {aspect.transit_sign.value.title()}
forms a {aspect.aspect_type.value} (exact at {aspect.exact_degree}°)
to your natal {aspect.natal_planet.value.title()} at {aspect.natal_degree:.1f}° {aspect.natal_sign.value.title()}
Located in your {house.ordinal} house ({house.meaning})

Orb: {aspect.orb}° - {"APPLYING (building to exact)" if aspect.applying else "SEPARATING (waning from exact)"}
Core meaning: {aspect.meaning}

This is your MOST SIGNIFICANT personal transit today."""