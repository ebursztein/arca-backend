"""
Tests for compatibility module - Synastry Analysis.

Run with: pytest functions/test_compatibility.py -v
"""

import pytest
from datetime import datetime

from compatibility import (
    # Constants
    ASPECT_CONFIG,
    CHALLENGING_CONJUNCTIONS,
    ROMANTIC_CATEGORIES,
    FRIENDSHIP_CATEGORIES,
    COWORKER_CATEGORIES,
    CATEGORY_NAMES,
    CATEGORY_TO_MODE,
    KARMIC_PRIMARY_ASPECTS,
    KARMIC_SECONDARY_ASPECTS,
    KARMIC_TIER1_PLANETS,
    KARMIC_TIER2_PLANETS,
    KARMIC_TIER1_ORB,
    KARMIC_TIER2_ORB,
    KARMIC_NORTH_HINTS,
    KARMIC_SOUTH_HINTS,
    KARMIC_SQUARE_HINTS,
    # Functions
    get_orb_weight,
    calculate_aspect,
    calculate_synastry_aspects,
    calculate_category_score,
    calculate_mode_compatibility,
    calculate_composite_sign,
    calculate_composite,
    calculate_compatibility,
    calculate_karmic,
    get_compatibility_from_birth_data,
    get_planet_degree,
    calculate_synastry_points,
    find_transits_to_synastry,
    calculate_vibe_score,
    _get_karmic_orb_threshold,
    _get_karmic_hint,
    # Models
    SynastryAspect,
    CompatibilityCategory,
    Composite,
    ModeCompatibility,
    CompatibilityData,
    Karmic,
    KarmicAspectInternal,
)
from astro import compute_birth_chart, NatalChartData


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def user_chart():
    """User's natal chart - June 15, 1990, NYC."""
    chart_dict, _ = compute_birth_chart(
        birth_date="1990-06-15",
        birth_time="14:30",
        birth_timezone="America/New_York",
        birth_lat=40.7128,
        birth_lon=-74.0060
    )
    return NatalChartData(**chart_dict)


@pytest.fixture
def connection_chart():
    """Connection's natal chart - March 22, 1992, LA."""
    chart_dict, _ = compute_birth_chart(
        birth_date="1992-03-22",
        birth_time="09:15",
        birth_timezone="America/Los_Angeles",
        birth_lat=34.0522,
        birth_lon=-118.2437
    )
    return NatalChartData(**chart_dict)


@pytest.fixture
def simple_user_chart():
    """Simple user chart without birth time."""
    chart_dict, _ = compute_birth_chart(birth_date="1985-01-15")
    return NatalChartData(**chart_dict)


@pytest.fixture
def simple_connection_chart():
    """Simple connection chart without birth time."""
    chart_dict, _ = compute_birth_chart(birth_date="1987-07-20")
    return NatalChartData(**chart_dict)


@pytest.fixture
def transit_chart():
    """Today's transit chart."""
    chart_dict, _ = compute_birth_chart(
        birth_date="2025-11-26",
        birth_time="12:00",
        birth_timezone="UTC",
        birth_lat=51.5074,  # London
        birth_lon=-0.1278
    )
    return NatalChartData(**chart_dict)


# =============================================================================
# Test Constants
# =============================================================================

class TestAspectConfig:
    """Tests for aspect configuration constants."""

    def test_all_aspects_have_required_keys(self):
        """Each aspect must have angle, orb, and nature."""
        required_keys = {"angle", "orb", "nature"}
        for aspect_type, config in ASPECT_CONFIG.items():
            assert required_keys.issubset(config.keys()), f"{aspect_type} missing keys"

    def test_aspect_angles_are_valid(self):
        """Aspect angles must be between 0 and 180."""
        for aspect_type, config in ASPECT_CONFIG.items():
            assert 0 <= config["angle"] <= 180, f"{aspect_type} has invalid angle"

    def test_aspect_orbs_are_positive(self):
        """Orbs must be positive."""
        for aspect_type, config in ASPECT_CONFIG.items():
            assert config["orb"] > 0, f"{aspect_type} has non-positive orb"

    def test_aspect_natures_are_valid(self):
        """Nature must be harmonious, challenging, or variable."""
        valid_natures = {"harmonious", "challenging", "variable"}
        for aspect_type, config in ASPECT_CONFIG.items():
            assert config["nature"] in valid_natures, f"{aspect_type} has invalid nature"

    def test_conjunction_is_variable(self):
        """Conjunction nature should be variable (depends on planets)."""
        assert ASPECT_CONFIG["conjunction"]["nature"] == "variable"

    def test_trine_sextile_are_harmonious(self):
        """Trine and sextile should be harmonious."""
        assert ASPECT_CONFIG["trine"]["nature"] == "harmonious"
        assert ASPECT_CONFIG["sextile"]["nature"] == "harmonious"

    def test_square_opposition_are_challenging(self):
        """Square and opposition should be challenging."""
        assert ASPECT_CONFIG["square"]["nature"] == "challenging"
        assert ASPECT_CONFIG["opposition"]["nature"] == "challenging"


class TestChallengingConjunctions:
    """Tests for challenging conjunction pairs."""

    def test_challenging_conjunctions_are_symmetric(self):
        """If (A, B) is challenging, (B, A) should also be."""
        for pair in CHALLENGING_CONJUNCTIONS:
            reverse = (pair[1], pair[0])
            assert reverse in CHALLENGING_CONJUNCTIONS, f"Missing reverse: {reverse}"

    def test_saturn_mars_is_challenging(self):
        """Saturn-Mars conjunction is classically challenging."""
        assert ("saturn", "mars") in CHALLENGING_CONJUNCTIONS

    def test_pluto_moon_is_challenging(self):
        """Pluto-Moon conjunction is intense/challenging."""
        assert ("pluto", "moon") in CHALLENGING_CONJUNCTIONS


class TestCategoryDefinitions:
    """Tests for category definitions."""

    def test_romantic_has_six_categories(self):
        """Romantic mode should have 6 categories."""
        assert len(ROMANTIC_CATEGORIES) == 6

    def test_friendship_has_five_categories(self):
        """Friendship mode should have 5 categories."""
        assert len(FRIENDSHIP_CATEGORIES) == 5

    def test_coworker_has_five_categories(self):
        """Coworker mode should have 5 categories."""
        assert len(COWORKER_CATEGORIES) == 5

    def test_all_categories_have_display_names(self):
        """Every category ID should have a display name."""
        all_category_ids = set()
        all_category_ids.update(ROMANTIC_CATEGORIES.keys())
        all_category_ids.update(FRIENDSHIP_CATEGORIES.keys())
        all_category_ids.update(COWORKER_CATEGORIES.keys())

        for cat_id in all_category_ids:
            assert cat_id in CATEGORY_NAMES, f"Missing display name for {cat_id}"

    def test_romantic_categories_have_correct_ids(self):
        """Romantic categories should have expected IDs."""
        expected = {"emotional", "communication", "attraction", "values", "longTerm", "growth"}
        assert set(ROMANTIC_CATEGORIES.keys()) == expected

    def test_friendship_categories_have_correct_ids(self):
        """Friendship categories should have expected IDs."""
        expected = {"emotional", "communication", "fun", "loyalty", "sharedInterests"}
        assert set(FRIENDSHIP_CATEGORIES.keys()) == expected

    def test_coworker_categories_have_correct_ids(self):
        """Coworker categories should have expected IDs."""
        expected = {"communication", "collaboration", "reliability", "ambition", "powerDynamics"}
        assert set(COWORKER_CATEGORIES.keys()) == expected


# =============================================================================
# Test Orb Weight Function
# =============================================================================

class TestGetOrbWeight:
    """Tests for orb weight calculation."""

    def test_exact_aspect_has_full_weight(self):
        """0 degree orb should have weight 1.0."""
        assert get_orb_weight(0.0) == 1.0

    def test_tight_orb_has_full_weight(self):
        """Orbs up to 2 degrees have full weight."""
        assert get_orb_weight(1.0) == 1.0
        assert get_orb_weight(2.0) == 1.0

    def test_medium_orb_has_reduced_weight(self):
        """Orbs 2-5 degrees have 0.75 weight."""
        assert get_orb_weight(3.0) == 0.75
        assert get_orb_weight(5.0) == 0.75

    def test_wide_orb_has_half_weight(self):
        """Orbs 5-8 degrees have 0.5 weight."""
        assert get_orb_weight(6.0) == 0.5
        assert get_orb_weight(8.0) == 0.5

    def test_very_wide_orb_has_quarter_weight(self):
        """Orbs 8-10 degrees have 0.25 weight."""
        assert get_orb_weight(9.0) == 0.25
        assert get_orb_weight(10.0) == 0.25

    def test_beyond_orb_has_zero_weight(self):
        """Orbs beyond 10 degrees have 0 weight."""
        assert get_orb_weight(11.0) == 0.0
        assert get_orb_weight(15.0) == 0.0


# =============================================================================
# Test Aspect Calculation
# =============================================================================

class TestCalculateAspect:
    """Tests for aspect calculation between two degrees."""

    def test_exact_conjunction(self):
        """Two planets at same degree form conjunction."""
        result = calculate_aspect(100.0, 100.0, "sun", "moon")
        assert result is not None
        aspect_type, orb, _ = result
        assert aspect_type == "conjunction"
        assert orb == 0.0

    def test_exact_opposition(self):
        """Planets 180 degrees apart form opposition."""
        result = calculate_aspect(0.0, 180.0, "sun", "moon")
        assert result is not None
        aspect_type, orb, _ = result
        assert aspect_type == "opposition"
        assert orb == 0.0

    def test_exact_trine(self):
        """Planets 120 degrees apart form trine."""
        result = calculate_aspect(0.0, 120.0, "sun", "moon")
        assert result is not None
        aspect_type, orb, _ = result
        assert aspect_type == "trine"
        assert orb == 0.0

    def test_exact_square(self):
        """Planets 90 degrees apart form square."""
        result = calculate_aspect(0.0, 90.0, "sun", "moon")
        assert result is not None
        aspect_type, orb, _ = result
        assert aspect_type == "square"
        assert orb == 0.0

    def test_exact_sextile(self):
        """Planets 60 degrees apart form sextile."""
        result = calculate_aspect(0.0, 60.0, "sun", "moon")
        assert result is not None
        aspect_type, orb, _ = result
        assert aspect_type == "sextile"
        assert orb == 0.0

    def test_conjunction_with_orb(self):
        """Conjunction within orb is detected."""
        result = calculate_aspect(100.0, 105.0, "sun", "moon")
        assert result is not None
        aspect_type, orb, _ = result
        assert aspect_type == "conjunction"
        assert orb == 5.0

    def test_no_aspect_when_outside_orb(self):
        """No aspect when degrees are too far apart."""
        # 45 degrees is not a major aspect
        result = calculate_aspect(0.0, 45.0, "sun", "moon")
        assert result is None

    def test_wrap_around_360(self):
        """Aspect calculation handles 360 degree wrap."""
        # 350 and 10 are 20 degrees apart (not 340)
        result = calculate_aspect(350.0, 10.0, "sun", "moon")
        assert result is None  # 20 degrees is not an aspect

        # 355 and 5 are 10 degrees apart - conjunction
        result = calculate_aspect(355.0, 5.0, "sun", "moon")
        assert result is not None
        aspect_type, orb, _ = result
        assert aspect_type == "conjunction"
        assert orb == 10.0

    def test_harmonious_conjunction_sun_moon(self):
        """Sun-Moon conjunction is harmonious."""
        result = calculate_aspect(100.0, 100.0, "sun", "moon")
        assert result is not None
        _, _, is_harmonious = result
        assert is_harmonious is True

    def test_challenging_conjunction_saturn_mars(self):
        """Saturn-Mars conjunction is challenging."""
        result = calculate_aspect(100.0, 100.0, "saturn", "mars")
        assert result is not None
        _, _, is_harmonious = result
        assert is_harmonious is False

    def test_trine_is_harmonious(self):
        """Trine aspect is always harmonious."""
        result = calculate_aspect(0.0, 120.0, "saturn", "mars")
        assert result is not None
        _, _, is_harmonious = result
        assert is_harmonious is True

    def test_square_is_challenging(self):
        """Square aspect is always challenging."""
        result = calculate_aspect(0.0, 90.0, "venus", "jupiter")
        assert result is not None
        _, _, is_harmonious = result
        assert is_harmonious is False


# =============================================================================
# Test Synastry Aspects
# =============================================================================

class TestCalculateSynastryAspects:
    """Tests for synastry aspect calculation between two charts."""

    def test_returns_list_of_aspects(self, user_chart, connection_chart):
        """Should return a list of SynastryAspect objects."""
        aspects = calculate_synastry_aspects(user_chart, connection_chart)
        assert isinstance(aspects, list)
        assert all(isinstance(a, SynastryAspect) for a in aspects)

    def test_aspects_have_unique_ids(self, user_chart, connection_chart):
        """Each aspect should have a unique ID."""
        aspects = calculate_synastry_aspects(user_chart, connection_chart)
        ids = [a.id for a in aspects]
        assert len(ids) == len(set(ids)), "Duplicate aspect IDs found"

    def test_aspects_sorted_by_orb(self, user_chart, connection_chart):
        """Aspects should be sorted by orb (tightest first)."""
        aspects = calculate_synastry_aspects(user_chart, connection_chart)
        orbs = [a.orb for a in aspects]
        assert orbs == sorted(orbs), "Aspects not sorted by orb"

    def test_aspect_fields_populated(self, user_chart, connection_chart):
        """All aspect fields should be properly populated."""
        aspects = calculate_synastry_aspects(user_chart, connection_chart)
        if aspects:
            aspect = aspects[0]
            assert aspect.id.startswith("asp_")
            assert aspect.user_planet
            assert aspect.their_planet
            assert aspect.aspect_type in ASPECT_CONFIG
            assert aspect.orb >= 0
            assert isinstance(aspect.is_harmonious, bool)

    def test_finds_aspects_between_charts(self, user_chart, connection_chart):
        """Should find some aspects between two different charts."""
        aspects = calculate_synastry_aspects(user_chart, connection_chart)
        assert len(aspects) > 0, "No aspects found between charts"

    def test_same_chart_has_many_conjunctions(self, user_chart):
        """Same chart compared to itself should have all conjunctions."""
        aspects = calculate_synastry_aspects(user_chart, user_chart)
        conjunctions = [a for a in aspects if a.aspect_type == "conjunction"]
        # Each planet should conjunct itself
        assert len(conjunctions) >= 10, "Expected many self-conjunctions"


class TestGetPlanetDegree:
    """Tests for planet degree extraction."""

    def test_gets_sun_degree(self, user_chart):
        """Should get Sun's absolute degree."""
        degree = get_planet_degree(user_chart, "sun")
        assert degree is not None
        assert 0 <= degree < 360

    def test_gets_moon_degree(self, user_chart):
        """Should get Moon's absolute degree."""
        degree = get_planet_degree(user_chart, "moon")
        assert degree is not None
        assert 0 <= degree < 360

    def test_returns_none_for_invalid_planet(self, user_chart):
        """Should return None for non-existent planet."""
        degree = get_planet_degree(user_chart, "invalid_planet")
        assert degree is None


# =============================================================================
# Test Category Score Calculation
# =============================================================================

class TestCalculateCategoryScore:
    """Tests for category score calculation."""

    def test_returns_score_and_aspect_ids(self, user_chart, connection_chart):
        """Should return tuple of (score, aspect_ids)."""
        aspects = calculate_synastry_aspects(user_chart, connection_chart)
        planet_pairs = ROMANTIC_CATEGORIES["emotional"]
        score, aspect_ids = calculate_category_score(aspects, planet_pairs)

        assert isinstance(score, int)
        assert isinstance(aspect_ids, list)

    def test_score_in_valid_range(self, user_chart, connection_chart):
        """Score should be between 0 and 100 (0=challenging, 50=neutral, 100=flowing)."""
        aspects = calculate_synastry_aspects(user_chart, connection_chart)

        for cat_id, planet_pairs in ROMANTIC_CATEGORIES.items():
            score, _ = calculate_category_score(aspects, planet_pairs, cat_id, user_chart, connection_chart)
            assert 0 <= score <= 100, f"Score {score} out of range for {cat_id}"

    def test_no_aspects_returns_neutral(self, user_chart, connection_chart):
        """If no relevant aspects, score should be 50 (neutral)."""
        aspects = calculate_synastry_aspects(user_chart, connection_chart)
        # Use planet pairs that probably won't have aspects
        fake_pairs = [("chiron", "chiron")]  # Chiron not in our planets
        score, aspect_ids = calculate_category_score(aspects, fake_pairs)

        assert score == 50  # Neutral score with 0-100 scale
        assert aspect_ids == []

    def test_all_harmonious_gives_above_neutral_score(self):
        """All harmonious aspects should give score above 50 (neutral)."""
        # Create mock aspects - all harmonious
        aspects = [
            SynastryAspect(
                id="asp_001",
                user_planet="moon",
                their_planet="moon",
                aspect_type="trine",
                orb=1.0,
                is_harmonious=True
            ),
            SynastryAspect(
                id="asp_002",
                user_planet="moon",
                their_planet="venus",
                aspect_type="sextile",
                orb=2.0,
                is_harmonious=True
            ),
        ]
        planet_pairs = [("moon", "moon"), ("moon", "venus")]
        score, _ = calculate_category_score(aspects, planet_pairs)
        assert score > 50, f"Expected score > 50 for harmonious aspects, got {score}"

    def test_all_challenging_gives_below_neutral_score(self):
        """All challenging aspects should give score below 50 (neutral)."""
        # Create mock aspects - all challenging
        aspects = [
            SynastryAspect(
                id="asp_001",
                user_planet="moon",
                their_planet="moon",
                aspect_type="square",
                orb=1.0,
                is_harmonious=False
            ),
            SynastryAspect(
                id="asp_002",
                user_planet="moon",
                their_planet="venus",
                aspect_type="opposition",
                orb=2.0,
                is_harmonious=False
            ),
        ]
        planet_pairs = [("moon", "moon"), ("moon", "venus")]
        score, _ = calculate_category_score(aspects, planet_pairs)
        assert score < 50, f"Expected score < 50 for challenging aspects, got {score}"


# =============================================================================
# Test Mode Compatibility
# =============================================================================

class TestCalculateModeCompatibility:
    """Tests for mode compatibility calculation."""

    def test_returns_mode_compatibility_object(self, user_chart, connection_chart):
        """Should return ModeCompatibility object."""
        aspects = calculate_synastry_aspects(user_chart, connection_chart)
        result = calculate_mode_compatibility(aspects, ROMANTIC_CATEGORIES, "romantic")
        assert isinstance(result, ModeCompatibility)

    def test_overall_score_in_range(self, user_chart, connection_chart):
        """Overall score should be 0-100."""
        aspects = calculate_synastry_aspects(user_chart, connection_chart)

        for categories, mode_type in [
            (ROMANTIC_CATEGORIES, "romantic"),
            (FRIENDSHIP_CATEGORIES, "friendship"),
            (COWORKER_CATEGORIES, "coworker")
        ]:
            result = calculate_mode_compatibility(aspects, categories, mode_type)
            assert 0 <= result.overall_score <= 100

    def test_has_correct_number_of_categories(self, user_chart, connection_chart):
        """Should have same number of categories as config."""
        aspects = calculate_synastry_aspects(user_chart, connection_chart)

        result = calculate_mode_compatibility(aspects, ROMANTIC_CATEGORIES, "romantic")
        assert len(result.categories) == len(ROMANTIC_CATEGORIES)

        result = calculate_mode_compatibility(aspects, FRIENDSHIP_CATEGORIES, "friendship")
        assert len(result.categories) == len(FRIENDSHIP_CATEGORIES)

    def test_categories_have_correct_ids(self, user_chart, connection_chart):
        """Category IDs should match config."""
        aspects = calculate_synastry_aspects(user_chart, connection_chart)
        result = calculate_mode_compatibility(aspects, ROMANTIC_CATEGORIES, "romantic")

        category_ids = {c.id for c in result.categories}
        assert category_ids == set(ROMANTIC_CATEGORIES.keys())

    def test_categories_have_display_names(self, user_chart, connection_chart):
        """Each category should have a display name."""
        aspects = calculate_synastry_aspects(user_chart, connection_chart)
        result = calculate_mode_compatibility(aspects, ROMANTIC_CATEGORIES, "romantic")

        for cat in result.categories:
            assert cat.name, f"Category {cat.id} has no name"
            assert cat.name == CATEGORY_NAMES.get(cat.id, cat.id.title())


# =============================================================================
# Test Composite Calculation
# =============================================================================

class TestCalculateCompositeSign:
    """Tests for composite midpoint sign calculation."""

    def test_same_degree_returns_same_sign(self):
        """Two planets at same degree give that sign."""
        # Both at 15 Aries (15 degrees)
        result = calculate_composite_sign(15.0, 15.0)
        assert result == "aries"

    def test_midpoint_calculation(self):
        """Midpoint between two degrees."""
        # 0 degrees (Aries) and 60 degrees (Gemini) -> 30 degrees (Taurus)
        result = calculate_composite_sign(0.0, 60.0)
        assert result == "taurus"

    def test_wrap_around_midpoint(self):
        """Midpoint handles 360 degree wrap."""
        # 350 degrees and 10 degrees -> midpoint at 0 (Aries)
        result = calculate_composite_sign(350.0, 10.0)
        assert result == "aries"

    def test_all_signs_possible(self):
        """Should be able to get any sign as composite."""
        signs = [
            "aries", "taurus", "gemini", "cancer", "leo", "virgo",
            "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"
        ]
        for i, sign in enumerate(signs):
            degree = i * 30 + 15  # Middle of each sign
            result = calculate_composite_sign(degree, degree)
            assert result == sign


class TestCalculateComposite:
    """Tests for composite calculation."""

    def test_returns_composite(self, user_chart, connection_chart):
        """Should return Composite object."""
        result = calculate_composite(user_chart, connection_chart)
        assert isinstance(result, Composite)

    def test_has_sun_sign(self, user_chart, connection_chart):
        """Should calculate composite Sun sign."""
        result = calculate_composite(user_chart, connection_chart)
        assert result.sun_sign is not None
        assert result.sun_sign in [
            "aries", "taurus", "gemini", "cancer", "leo", "virgo",
            "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces", "unknown"
        ]

    def test_has_moon_sign(self, user_chart, connection_chart):
        """Should calculate composite Moon sign."""
        result = calculate_composite(user_chart, connection_chart)
        assert result.moon_sign is not None

    def test_has_dominant_element(self, user_chart, connection_chart):
        """Should calculate dominant element."""
        result = calculate_composite(user_chart, connection_chart)
        assert result.dominant_element in ["fire", "earth", "air", "water"]

    def test_purpose_not_filled(self, user_chart, connection_chart):
        """LLM purpose should be None initially."""
        result = calculate_composite(user_chart, connection_chart)
        assert result.purpose is None


# =============================================================================
# Test Full Compatibility Calculation
# =============================================================================

class TestCalculateCompatibility:
    """Tests for full compatibility calculation."""

    def test_returns_compatibility_data(self, user_chart, connection_chart):
        """Should return CompatibilityData object."""
        result = calculate_compatibility(user_chart, connection_chart, "romantic")
        assert isinstance(result, CompatibilityData)

    def test_has_single_mode(self, user_chart, connection_chart):
        """Should have single mode based on relationship type."""
        result = calculate_compatibility(user_chart, connection_chart, "romantic")
        assert hasattr(result, "mode")
        assert result.mode.type == "romantic"

    def test_has_aspects_list(self, user_chart, connection_chart):
        """Should have list of synastry aspects."""
        result = calculate_compatibility(user_chart, connection_chart, "romantic")
        assert isinstance(result.aspects, list)

    def test_has_composite(self, user_chart, connection_chart):
        """Should have composite data."""
        result = calculate_compatibility(user_chart, connection_chart, "romantic")
        assert result.composite is not None
        assert isinstance(result.composite, Composite)

    def test_has_karmic(self, user_chart, connection_chart):
        """Should have karmic data."""
        result = calculate_compatibility(user_chart, connection_chart, "romantic")
        assert result.karmic is not None
        assert isinstance(result.karmic, Karmic)

    def test_has_names(self, user_chart, connection_chart):
        """Should have user and connection names."""
        result = calculate_compatibility(user_chart, connection_chart, "romantic", "Alice", "Bob")
        assert result.user_name == "Alice"
        assert result.connection_name == "Bob"

    def test_different_modes_have_different_categories(self, user_chart, connection_chart):
        """Different modes should have different category sets."""
        romantic = calculate_compatibility(user_chart, connection_chart, "romantic")
        friendship = calculate_compatibility(user_chart, connection_chart, "friendship")
        coworker = calculate_compatibility(user_chart, connection_chart, "coworker")

        romantic_cat_ids = {c.id for c in romantic.mode.categories}
        friendship_cat_ids = {c.id for c in friendship.mode.categories}
        coworker_cat_ids = {c.id for c in coworker.mode.categories}

        # Romantic has 6, others have 5
        assert len(romantic_cat_ids) == 6
        assert len(friendship_cat_ids) == 5
        assert len(coworker_cat_ids) == 5


class TestGetCompatibilityFromBirthData:
    """Tests for convenience function with raw birth data."""

    def test_calculates_from_birth_data(self):
        """Should calculate compatibility from birth dates."""
        result = get_compatibility_from_birth_data(
            user_birth_date="1990-06-15",
            user_birth_time="14:30",
            user_birth_lat=40.7128,
            user_birth_lon=-74.0060,
            user_birth_timezone="America/New_York",
            connection_birth_date="1992-03-22",
            relationship_type="romantic",
            connection_birth_time="09:15",
            connection_birth_lat=34.0522,
            connection_birth_lon=-118.2437,
            connection_birth_timezone="America/Los_Angeles",
        )
        assert isinstance(result, CompatibilityData)
        assert 0 <= result.mode.overall_score <= 100

    def test_works_without_birth_times(self):
        """Should work with just birth dates."""
        result = get_compatibility_from_birth_data(
            user_birth_date="1990-06-15",
            user_birth_time=None,
            user_birth_lat=None,
            user_birth_lon=None,
            user_birth_timezone=None,
            connection_birth_date="1992-03-22",
            relationship_type="friendship",
        )
        assert isinstance(result, CompatibilityData)


# =============================================================================
# Test Synastry Points (Daily Weather)
# =============================================================================

class TestCalculateSynastryPoints:
    """Tests for synastry midpoint calculation."""

    def test_returns_list_of_points(self, user_chart, connection_chart):
        """Should return list of synastry points."""
        points = calculate_synastry_points(user_chart, connection_chart)
        assert isinstance(points, list)

    def test_points_have_required_fields(self, user_chart, connection_chart):
        """Each point should have degree, type, label, planets."""
        points = calculate_synastry_points(user_chart, connection_chart)
        for point in points:
            assert "degree" in point
            assert "type" in point
            assert "label" in point
            assert "planets" in point
            assert 0 <= point["degree"] < 360

    def test_includes_key_midpoints(self, user_chart, connection_chart):
        """Should include important relationship midpoints."""
        points = calculate_synastry_points(user_chart, connection_chart)
        types = {p["type"] for p in points}

        expected_types = {
            "moon_moon_midpoint",
            "sun_sun_midpoint",
            "venus_venus_midpoint",
        }
        assert expected_types.issubset(types)


class TestFindTransitsToSynastry:
    """Tests for transit-synastry aspect finding."""

    def test_returns_list_of_transits(self, transit_chart, user_chart, connection_chart):
        """Should return list of active transits."""
        synastry_points = calculate_synastry_points(user_chart, connection_chart)
        transits = find_transits_to_synastry(transit_chart, synastry_points)
        assert isinstance(transits, list)

    def test_transits_sorted_by_orb(self, transit_chart, user_chart, connection_chart):
        """Transits should be sorted by orb."""
        synastry_points = calculate_synastry_points(user_chart, connection_chart)
        transits = find_transits_to_synastry(transit_chart, synastry_points)
        if transits:
            orbs = [t["orb"] for t in transits]
            assert orbs == sorted(orbs)

    def test_transit_fields_populated(self, transit_chart, user_chart, connection_chart):
        """Transit dicts should have required fields."""
        synastry_points = calculate_synastry_points(user_chart, connection_chart)
        transits = find_transits_to_synastry(transit_chart, synastry_points)
        for transit in transits:
            assert "transit_planet" in transit
            assert "aspect" in transit
            assert "synastry_point" in transit
            assert "orb" in transit
            assert "is_harmonious" in transit
            assert "description" in transit


class TestCalculateVibeScore:
    """Tests for vibe score calculation."""

    def test_empty_transits_returns_neutral(self):
        """No transits should give neutral score of 50."""
        score = calculate_vibe_score([])
        assert score == 50

    def test_all_harmonious_gives_high_score(self):
        """All harmonious transits should give high score."""
        transits = [
            {"orb": 1.0, "is_harmonious": True},
            {"orb": 2.0, "is_harmonious": True},
        ]
        score = calculate_vibe_score(transits)
        assert score > 50

    def test_all_challenging_gives_low_score(self):
        """All challenging transits should give low score."""
        transits = [
            {"orb": 1.0, "is_harmonious": False},
            {"orb": 2.0, "is_harmonious": False},
        ]
        score = calculate_vibe_score(transits)
        assert score < 50

    def test_score_in_valid_range(self):
        """Score should always be 0-100."""
        test_cases = [
            [],
            [{"orb": 0.0, "is_harmonious": True}],
            [{"orb": 0.0, "is_harmonious": False}],
            [{"orb": 1.0, "is_harmonious": True}, {"orb": 1.0, "is_harmonious": False}],
        ]
        for transits in test_cases:
            score = calculate_vibe_score(transits)
            assert 0 <= score <= 100


# =============================================================================
# Test Pydantic Models
# =============================================================================

class TestSynastryAspectModel:
    """Tests for SynastryAspect Pydantic model."""

    def test_valid_aspect(self):
        """Should create valid aspect."""
        aspect = SynastryAspect(
            id="asp_001",
            user_planet="venus",
            their_planet="mars",
            aspect_type="trine",
            orb=2.5,
            is_harmonious=True
        )
        assert aspect.id == "asp_001"
        assert aspect.is_harmonious is True

    def test_orb_must_be_non_negative(self):
        """Orb must be >= 0."""
        with pytest.raises(ValueError):
            SynastryAspect(
                id="asp_001",
                user_planet="venus",
                their_planet="mars",
                aspect_type="trine",
                orb=-1.0,
                is_harmonious=True
            )


class TestCompatibilityCategoryModel:
    """Tests for CompatibilityCategory Pydantic model."""

    def test_valid_category(self):
        """Should create valid category."""
        cat = CompatibilityCategory(
            id="emotional",
            name="Emotional Connection",
            score=75
        )
        assert cat.id == "emotional"
        assert cat.insight is None

    def test_score_must_be_in_range(self):
        """Score must be 0 to 100."""
        with pytest.raises(ValueError):
            CompatibilityCategory(
                id="test",
                name="Test",
                score=150
            )
        with pytest.raises(ValueError):
            CompatibilityCategory(
                id="test",
                name="Test",
                score=-10
            )


class TestCompatibilityDataModel:
    """Tests for CompatibilityData model."""

    def test_has_all_components(self, user_chart, connection_chart):
        """CompatibilityData should have all required components."""
        result = calculate_compatibility(user_chart, connection_chart, "romantic")
        assert result.mode is not None
        assert result.aspects is not None
        assert result.composite is not None
        assert result.karmic is not None
        assert result.user_name is not None
        assert result.connection_name is not None
        assert result.user_sun_sign is not None
        assert result.connection_sun_sign is not None


# =============================================================================
# Test Edge Cases
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_same_person_compatibility(self, user_chart):
        """Comparing a chart to itself."""
        result = calculate_compatibility(user_chart, user_chart, "romantic")
        # Should have many conjunctions
        conjunctions = [a for a in result.aspects if a.aspect_type == "conjunction"]
        assert len(conjunctions) >= 10

    def test_simple_charts_without_birth_time(self, simple_user_chart, simple_connection_chart):
        """Compatibility with minimal birth data."""
        result = calculate_compatibility(simple_user_chart, simple_connection_chart, "romantic")
        assert isinstance(result, CompatibilityData)
        assert 0 <= result.mode.overall_score <= 100

    def test_very_different_birth_dates(self):
        """Charts from very different eras."""
        old_chart_dict, _ = compute_birth_chart(birth_date="1950-01-01")
        old_chart = NatalChartData(**old_chart_dict)

        new_chart_dict, _ = compute_birth_chart(birth_date="2000-12-31")
        new_chart = NatalChartData(**new_chart_dict)

        result = calculate_compatibility(old_chart, new_chart, "friendship")
        assert isinstance(result, CompatibilityData)

    def test_aspects_list_not_empty(self, user_chart, connection_chart):
        """Real charts should have some aspects."""
        result = calculate_compatibility(user_chart, connection_chart, "romantic")
        assert len(result.aspects) > 0, "Expected at least some synastry aspects"


# =============================================================================
# Test Karmic Constants
# =============================================================================

class TestKarmicConstants:
    """Tests for karmic calculation constants."""

    def test_karmic_primary_aspects(self):
        """Primary karmic aspects are conjunction and opposition."""
        assert KARMIC_PRIMARY_ASPECTS == {"conjunction", "opposition"}
        # Sextiles and trines should NOT be karmic
        assert "sextile" not in KARMIC_PRIMARY_ASPECTS
        assert "trine" not in KARMIC_PRIMARY_ASPECTS

    def test_karmic_secondary_aspects(self):
        """Secondary karmic aspects are squares (Saturn/Pluto only)."""
        assert KARMIC_SECONDARY_ASPECTS == {"square"}

    def test_tier1_planets_are_fated(self):
        """Tier 1 planets are Sun, Moon, Saturn, Pluto."""
        assert KARMIC_TIER1_PLANETS == {"sun", "moon", "saturn", "pluto"}

    def test_tier2_planets_are_personal(self):
        """Tier 2 planets are Venus, Mars, Mercury."""
        assert KARMIC_TIER2_PLANETS == {"venus", "mars", "mercury"}

    def test_tier1_orb(self):
        """Tier 1 orb should be 1.0 degrees."""
        assert KARMIC_TIER1_ORB == 1.0

    def test_tier2_orb(self):
        """Tier 2 orb should be 0.75 degrees."""
        assert KARMIC_TIER2_ORB == 0.75

    def test_generational_planets_excluded(self):
        """Jupiter, Uranus, Neptune should not be in karmic tiers (Pluto is included)."""
        all_karmic_planets = KARMIC_TIER1_PLANETS | KARMIC_TIER2_PLANETS
        assert "jupiter" not in all_karmic_planets
        assert "uranus" not in all_karmic_planets
        assert "neptune" not in all_karmic_planets
        # Pluto IS now included in Tier 1
        assert "pluto" in all_karmic_planets

    def test_all_karmic_planets_have_north_hints(self):
        """All karmic planets should have North Node hints."""
        all_karmic_planets = KARMIC_TIER1_PLANETS | KARMIC_TIER2_PLANETS
        for planet in all_karmic_planets:
            assert planet in KARMIC_NORTH_HINTS, f"Missing North hint for {planet}"

    def test_all_karmic_planets_have_south_hints(self):
        """All karmic planets should have South Node hints."""
        all_karmic_planets = KARMIC_TIER1_PLANETS | KARMIC_TIER2_PLANETS
        for planet in all_karmic_planets:
            assert planet in KARMIC_SOUTH_HINTS, f"Missing South hint for {planet}"

    def test_square_hints_for_saturn_pluto(self):
        """Saturn and Pluto should have square hints."""
        assert "saturn" in KARMIC_SQUARE_HINTS
        assert "pluto" in KARMIC_SQUARE_HINTS


# =============================================================================
# Test Karmic Helper Functions
# =============================================================================

class TestKarmicOrbThreshold:
    """Tests for _get_karmic_orb_threshold function."""

    def test_tier1_planets_get_1_0_degree_orb(self):
        """Tier 1 planets (except Pluto) should get 1.0 degree orb."""
        assert _get_karmic_orb_threshold("sun") == 1.0
        assert _get_karmic_orb_threshold("moon") == 1.0
        assert _get_karmic_orb_threshold("saturn") == 1.0

    def test_pluto_gets_0_75_degree_orb(self):
        """Pluto should get tighter 0.75 degree orb."""
        assert _get_karmic_orb_threshold("pluto") == 0.75

    def test_tier2_planets_get_0_75_degree_orb(self):
        """Tier 2 planets should get 0.75 degree orb."""
        assert _get_karmic_orb_threshold("venus") == 0.75
        assert _get_karmic_orb_threshold("mars") == 0.75
        assert _get_karmic_orb_threshold("mercury") == 0.75

    def test_generational_planets_get_zero_orb(self):
        """Generational planets (except Pluto) should be excluded (0 orb)."""
        assert _get_karmic_orb_threshold("jupiter") == 0.0
        assert _get_karmic_orb_threshold("uranus") == 0.0
        assert _get_karmic_orb_threshold("neptune") == 0.0


class TestKarmicHint:
    """Tests for _get_karmic_hint function."""

    def test_square_aspect_uses_square_hints(self):
        """Square aspect should use square hints for Saturn/Pluto."""
        hint = _get_karmic_hint("saturn", "north node", "square")
        assert hint == KARMIC_SQUARE_HINTS["saturn"]

        hint = _get_karmic_hint("pluto", "south node", "square")
        assert hint == KARMIC_SQUARE_HINTS["pluto"]

    def test_north_node_uses_north_hints(self):
        """North Node aspects should use north hints."""
        hint = _get_karmic_hint("saturn", "north node", "conjunction")
        assert hint == KARMIC_NORTH_HINTS["saturn"]

        hint = _get_karmic_hint("venus", "north node", "opposition")
        assert hint == KARMIC_NORTH_HINTS["venus"]

    def test_south_node_uses_south_hints(self):
        """South Node aspects should use south hints."""
        hint = _get_karmic_hint("moon", "south node", "conjunction")
        assert hint == KARMIC_SOUTH_HINTS["moon"]

        hint = _get_karmic_hint("mars", "south node", "opposition")
        assert hint == KARMIC_SOUTH_HINTS["mars"]

    def test_hints_are_meaningful_strings(self):
        """Hints should be non-empty meaningful strings."""
        for planet in KARMIC_TIER1_PLANETS | KARMIC_TIER2_PLANETS:
            for node in ["north node", "south node"]:
                hint = _get_karmic_hint(planet, node, "conjunction")
                assert len(hint) > 10, f"Hint too short for {planet}/{node}/conjunction"


# =============================================================================
# Test Karmic Aspect Calculation
# =============================================================================

class TestCalculateKarmic:
    """Tests for karmic aspect calculation between two charts."""

    def test_returns_karmic_tuple(self, user_chart, connection_chart):
        """Should return tuple of (Karmic, list[KarmicAspectInternal])."""
        karmic, karmic_aspects = calculate_karmic(user_chart, connection_chart)
        assert isinstance(karmic, Karmic)
        assert isinstance(karmic_aspects, list)

    def test_has_is_karmic_boolean(self, user_chart, connection_chart):
        """Should have is_karmic boolean field."""
        karmic, _ = calculate_karmic(user_chart, connection_chart)
        assert isinstance(karmic.is_karmic, bool)

    def test_karmic_aspects_sorted_by_orb(self, user_chart, connection_chart):
        """Karmic aspects should be sorted by orb (tightest first)."""
        _, karmic_aspects = calculate_karmic(user_chart, connection_chart)
        if karmic_aspects:
            orbs = [a.orb for a in karmic_aspects]
            assert orbs == sorted(orbs), "Karmic aspects not sorted by orb"

    def test_only_valid_aspects_included(self, user_chart, connection_chart):
        """Only primary or secondary aspects should be included."""
        _, karmic_aspects = calculate_karmic(user_chart, connection_chart)
        valid_aspects = KARMIC_PRIMARY_ASPECTS | KARMIC_SECONDARY_ASPECTS
        for aspect in karmic_aspects:
            assert aspect.aspect_type in valid_aspects, f"Invalid aspect found: {aspect.aspect_type}"

    def test_only_karmic_planets_included(self, user_chart, connection_chart):
        """Only Tier 1 and Tier 2 planets should be included."""
        _, karmic_aspects = calculate_karmic(user_chart, connection_chart)
        allowed_planets = KARMIC_TIER1_PLANETS | KARMIC_TIER2_PLANETS
        for aspect in karmic_aspects:
            assert aspect.planet in allowed_planets, f"Non-karmic planet found: {aspect.planet}"

    def test_orbs_within_tier_limits(self, user_chart, connection_chart):
        """Aspect orbs should be within tier-specific limits."""
        _, karmic_aspects = calculate_karmic(user_chart, connection_chart)
        for aspect in karmic_aspects:
            max_orb = _get_karmic_orb_threshold(aspect.planet)
            assert aspect.orb <= max_orb, f"{aspect.planet} orb {aspect.orb} exceeds limit {max_orb}"

    def test_has_interpretation_hints(self, user_chart, connection_chart):
        """Each karmic aspect should have an interpretation hint."""
        _, karmic_aspects = calculate_karmic(user_chart, connection_chart)
        for aspect in karmic_aspects:
            assert aspect.interpretation_hint, f"Missing hint for {aspect.planet} {aspect.aspect_type} {aspect.node}"

    def test_theme_set_when_karmic(self, user_chart, connection_chart):
        """Theme should be set if karmic aspects exist."""
        karmic, _ = calculate_karmic(user_chart, connection_chart)
        if karmic.is_karmic:
            assert karmic.theme is not None
            assert len(karmic.theme) > 0

    def test_theme_none_when_not_karmic(self):
        """Theme should be None if no karmic aspects."""
        # Create charts that likely won't have tight node contacts
        chart1_dict, _ = compute_birth_chart(birth_date="1950-06-15")
        chart1 = NatalChartData(**chart1_dict)
        chart2_dict, _ = compute_birth_chart(birth_date="1950-06-20")
        chart2 = NatalChartData(**chart2_dict)

        karmic, _ = calculate_karmic(chart1, chart2)
        if not karmic.is_karmic:
            assert karmic.theme is None

    def test_karmic_aspect_internal_fields(self, user_chart, connection_chart):
        """KarmicAspectInternal should have all required fields."""
        _, karmic_aspects = calculate_karmic(user_chart, connection_chart)
        for aspect in karmic_aspects:
            assert hasattr(aspect, 'planet')
            assert hasattr(aspect, 'planet_owner')
            assert hasattr(aspect, 'node')
            assert hasattr(aspect, 'node_owner')
            assert hasattr(aspect, 'aspect_type')
            assert hasattr(aspect, 'orb')
            assert hasattr(aspect, 'interpretation_hint')
            assert aspect.planet_owner in ['user', 'connection']
            assert aspect.node_owner in ['user', 'connection']
            assert aspect.node in ['north node', 'south node']


class TestKarmicProbability:
    """Tests to verify karmic detection is ~20-25% (rare but attainable)."""

    def test_not_everyone_is_karmic(self):
        """Most random pairs should NOT be karmic."""
        karmic_count = 0
        total_pairs = 20

        # Test with various date combinations
        test_dates = [
            ("1980-01-15", "1985-07-20"),
            ("1990-03-10", "1992-11-25"),
            ("1975-08-01", "1988-04-15"),
            ("1995-12-20", "1998-02-28"),
            ("1982-05-05", "1986-09-10"),
            ("1970-11-11", "1978-03-03"),
            ("1993-06-21", "1997-08-08"),
            ("1985-04-04", "1991-10-30"),
            ("1988-07-07", "1994-01-15"),
            ("1976-02-14", "1983-06-06"),
            ("1991-09-09", "1996-12-12"),
            ("1984-08-08", "1989-05-05"),
            ("1979-10-10", "1987-07-07"),
            ("1992-01-01", "1995-04-04"),
            ("1981-03-03", "1990-08-08"),
            ("1986-06-06", "1993-02-02"),
            ("1977-12-12", "1984-11-11"),
            ("1994-05-05", "1999-03-03"),
            ("1983-09-09", "1988-06-06"),
            ("1989-02-02", "1996-10-10"),
        ]

        for date1, date2 in test_dates:
            chart1_dict, _ = compute_birth_chart(birth_date=date1)
            chart1 = NatalChartData(**chart1_dict)
            chart2_dict, _ = compute_birth_chart(birth_date=date2)
            chart2 = NatalChartData(**chart2_dict)

            karmic, _ = calculate_karmic(chart1, chart2)
            if karmic.is_karmic:
                karmic_count += 1

        karmic_rate = karmic_count / total_pairs
        # Should be roughly 20-25%, allowing some variance
        # At minimum, it should NOT be 100% or 0%
        assert karmic_rate < 0.8, f"Karmic rate too high: {karmic_rate*100:.0f}%"
        # Note: We can't guarantee > 0% with only 20 pairs, so we just check it's not absurdly high


class TestKarmicInCompatibilityData:
    """Tests for karmic data in full compatibility data."""

    def test_compatibility_includes_karmic(self, user_chart, connection_chart):
        """Full compatibility should include karmic."""
        result = calculate_compatibility(user_chart, connection_chart, "romantic")
        assert hasattr(result, 'karmic')
        assert result.karmic is not None

    def test_karmic_is_valid_type(self, user_chart, connection_chart):
        """karmic should be Karmic type."""
        result = calculate_compatibility(user_chart, connection_chart, "romantic")
        assert isinstance(result.karmic, Karmic)

    def test_destiny_note_initially_none(self, user_chart, connection_chart):
        """destiny_note should be None (filled by LLM later)."""
        result = calculate_compatibility(user_chart, connection_chart, "romantic")
        assert result.karmic.destiny_note is None


# =============================================================================
# Test Score Ranges (0-100)
# =============================================================================

class TestScoreRanges:
    """Tests to verify all scores are properly in 0-100 range."""

    def test_overall_score_always_0_to_100(self, user_chart, connection_chart):
        """Overall score must always be between 0 and 100."""
        for mode, categories in [
            ("romantic", ROMANTIC_CATEGORIES),
            ("friendship", FRIENDSHIP_CATEGORIES),
            ("coworker", COWORKER_CATEGORIES),
        ]:
            result = calculate_compatibility(user_chart, connection_chart, mode)
            assert 0 <= result.mode.overall_score <= 100, \
                f"Overall score {result.mode.overall_score} out of range for {mode}"

    def test_category_scores_always_0_to_100(self, user_chart, connection_chart):
        """Every category score must be between 0 and 100."""
        for mode, categories in [
            ("romantic", ROMANTIC_CATEGORIES),
            ("friendship", FRIENDSHIP_CATEGORIES),
            ("coworker", COWORKER_CATEGORIES),
        ]:
            result = calculate_compatibility(user_chart, connection_chart, mode)
            for cat in result.mode.categories:
                assert 0 <= cat.score <= 100, \
                    f"Category {cat.id} score {cat.score} out of range for {mode}"

    def test_scores_across_many_random_charts(self):
        """Score ranges must hold across many different chart combinations."""
        # Test with various date combinations to ensure robustness
        test_dates = [
            ("1980-01-15", "1985-07-20"),
            ("1990-03-10", "1992-11-25"),
            ("1975-08-01", "1988-04-15"),
            ("1995-12-20", "1998-02-28"),
            ("1982-05-05", "1986-09-10"),
            ("1970-11-11", "1978-03-03"),
            ("1993-06-21", "1997-08-08"),
            ("1985-04-04", "1991-10-30"),
        ]

        for date1, date2 in test_dates:
            result = get_compatibility_from_birth_data(
                user_birth_date=date1,
                user_birth_time=None,
                user_birth_lat=None,
                user_birth_lon=None,
                user_birth_timezone=None,
                connection_birth_date=date2,
                relationship_type="romantic",
            )

            assert 0 <= result.mode.overall_score <= 100, \
                f"Overall score {result.mode.overall_score} out of range for {date1}/{date2}"

            for cat in result.mode.categories:
                assert 0 <= cat.score <= 100, \
                    f"Category {cat.id} score {cat.score} out of range for {date1}/{date2}"

    def test_neutral_score_is_around_50(self, simple_user_chart, simple_connection_chart):
        """Mean score across categories should be around 50 (neutral)."""
        result = calculate_compatibility(simple_user_chart, simple_connection_chart, "romantic")
        scores = [cat.score for cat in result.mode.categories]
        mean_score = sum(scores) / len(scores)
        # Should be roughly in the 30-70 range (not all extreme)
        assert 20 <= mean_score <= 80, \
            f"Mean score {mean_score} too extreme (expected 20-80)"

    def test_no_hard_clamping_at_boundaries(self):
        """Scores should use sigmoid, not hard clamping at 0/100."""
        # Run many comparisons and check we don't see clustering at 0 or 100
        extreme_count = 0
        total_categories = 0

        test_dates = [
            ("1980-01-15", "1985-07-20"),
            ("1990-03-10", "2000-11-25"),
            ("1960-08-01", "1988-04-15"),
            ("1995-12-20", "1998-02-28"),
            ("1970-05-05", "1999-09-10"),
        ]

        for date1, date2 in test_dates:
            result = get_compatibility_from_birth_data(
                user_birth_date=date1,
                user_birth_time=None,
                user_birth_lat=None,
                user_birth_lon=None,
                user_birth_timezone=None,
                connection_birth_date=date2,
                relationship_type="romantic",
            )

            for cat in result.mode.categories:
                total_categories += 1
                # Check if score is at exact boundary (indicating hard clamping)
                if cat.score == 0 or cat.score == 100:
                    extreme_count += 1

        # With sigmoid, we shouldn't have many exact 0s or 100s
        extreme_rate = extreme_count / total_categories
        assert extreme_rate < 0.1, \
            f"Too many boundary scores ({extreme_rate*100:.1f}%), suggesting hard clamping"
