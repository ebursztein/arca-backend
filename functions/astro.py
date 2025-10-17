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
            absolute_degree=round(planet.degree, 2),
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
                name="north node",
                symbol=north_node.symbol if hasattr(north_node, 'symbol') else "☊",
                position_dms=north_node.signed_dms,
                sign=north_node.sign.name,
                degree_in_sign=round(north_node.signed_deg + north_node.minute / 60, 2),
                absolute_degree=round(north_node.degree, 2),
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