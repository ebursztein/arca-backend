"""Test MeterGroupV2 hierarchy mapping."""

from astrometers.hierarchy import (
    MeterGroupV2,
    METER_TO_GROUP_V2,
    GROUP_V2_METERS,
    get_group_v2,
    get_meters_in_group_v2,
    get_group_v2_display_name,
    validate_group_v2_complete,
    Meter,
    SUPER_GROUP_METERS,
)


def test_group_v2_validation():
    """Test that all 21 non-overview meters are mapped."""
    assert validate_group_v2_complete()


def test_group_v2_count():
    """Test that we have exactly 5 groups with 21 total meters."""
    assert len(GROUP_V2_METERS) == 5
    assert len(METER_TO_GROUP_V2) == 21

    # Verify total meter count
    total_meters = sum(len(meters) for meters in GROUP_V2_METERS.values())
    assert total_meters == 21


def test_group_v2_sizes():
    """Test that each group has the expected number of meters."""
    assert len(GROUP_V2_METERS[MeterGroupV2.MIND]) == 3
    assert len(GROUP_V2_METERS[MeterGroupV2.EMOTIONS]) == 3
    assert len(GROUP_V2_METERS[MeterGroupV2.BODY]) == 3
    assert len(GROUP_V2_METERS[MeterGroupV2.SPIRIT]) == 6
    assert len(GROUP_V2_METERS[MeterGroupV2.GROWTH]) == 6


def test_no_duplicates():
    """Test that no meter appears in multiple groups."""
    all_meters = []
    for meters in GROUP_V2_METERS.values():
        all_meters.extend(meters)

    assert len(all_meters) == len(set(all_meters)), "Duplicate meters found"


def test_overview_meters_excluded():
    """Test that overview meters are not in MeterGroupV2."""
    assert Meter.OVERALL_INTENSITY not in METER_TO_GROUP_V2
    assert Meter.OVERALL_HARMONY not in METER_TO_GROUP_V2


def test_super_group_meters_excluded():
    """Test that super-group aggregate meters are not in MeterGroupV2."""
    for meter in SUPER_GROUP_METERS:
        assert meter not in METER_TO_GROUP_V2


def test_get_group_v2():
    """Test get_group_v2 function."""
    assert get_group_v2(Meter.MENTAL_CLARITY) == MeterGroupV2.MIND
    assert get_group_v2(Meter.EMOTIONAL_INTENSITY) == MeterGroupV2.EMOTIONS
    assert get_group_v2(Meter.PHYSICAL_ENERGY) == MeterGroupV2.BODY
    assert get_group_v2(Meter.FIRE_ENERGY) == MeterGroupV2.SPIRIT
    assert get_group_v2(Meter.CAREER_AMBITION) == MeterGroupV2.GROWTH


def test_get_meters_in_group_v2():
    """Test get_meters_in_group_v2 function."""
    mind_meters = get_meters_in_group_v2(MeterGroupV2.MIND)
    assert len(mind_meters) == 3
    assert Meter.MENTAL_CLARITY in mind_meters
    assert Meter.DECISION_QUALITY in mind_meters
    assert Meter.COMMUNICATION_FLOW in mind_meters


def test_display_names():
    """Test display names for all groups."""
    assert get_group_v2_display_name(MeterGroupV2.MIND) == "Mind"
    assert get_group_v2_display_name(MeterGroupV2.EMOTIONS) == "Emotions"
    assert get_group_v2_display_name(MeterGroupV2.BODY) == "Body"
    assert get_group_v2_display_name(MeterGroupV2.SPIRIT) == "Spirit"
    assert get_group_v2_display_name(MeterGroupV2.GROWTH) == "Growth"


def test_specific_meter_mappings():
    """Test specific important meter mappings."""
    # Mind group
    assert get_group_v2(Meter.MENTAL_CLARITY) == MeterGroupV2.MIND
    assert get_group_v2(Meter.DECISION_QUALITY) == MeterGroupV2.MIND
    assert get_group_v2(Meter.COMMUNICATION_FLOW) == MeterGroupV2.MIND

    # Emotions group
    assert get_group_v2(Meter.EMOTIONAL_INTENSITY) == MeterGroupV2.EMOTIONS
    assert get_group_v2(Meter.RELATIONSHIP_HARMONY) == MeterGroupV2.EMOTIONS
    assert get_group_v2(Meter.EMOTIONAL_RESILIENCE) == MeterGroupV2.EMOTIONS

    # Body group
    assert get_group_v2(Meter.PHYSICAL_ENERGY) == MeterGroupV2.BODY
    assert get_group_v2(Meter.CONFLICT_RISK) == MeterGroupV2.BODY
    assert get_group_v2(Meter.MOTIVATION_DRIVE) == MeterGroupV2.BODY

    # Spirit group (elements + spiritual meters)
    assert get_group_v2(Meter.INTUITION_SPIRITUALITY) == MeterGroupV2.SPIRIT
    assert get_group_v2(Meter.KARMIC_LESSONS) == MeterGroupV2.SPIRIT
    assert get_group_v2(Meter.FIRE_ENERGY) == MeterGroupV2.SPIRIT
    assert get_group_v2(Meter.EARTH_ENERGY) == MeterGroupV2.SPIRIT
    assert get_group_v2(Meter.AIR_ENERGY) == MeterGroupV2.SPIRIT
    assert get_group_v2(Meter.WATER_ENERGY) == MeterGroupV2.SPIRIT

    # Growth group (career + evolution + collective)
    assert get_group_v2(Meter.CAREER_AMBITION) == MeterGroupV2.GROWTH
    assert get_group_v2(Meter.OPPORTUNITY_WINDOW) == MeterGroupV2.GROWTH
    assert get_group_v2(Meter.CHALLENGE_INTENSITY) == MeterGroupV2.GROWTH
    assert get_group_v2(Meter.TRANSFORMATION_PRESSURE) == MeterGroupV2.GROWTH
    assert get_group_v2(Meter.INNOVATION_BREAKTHROUGH) == MeterGroupV2.GROWTH
    assert get_group_v2(Meter.SOCIAL_COLLECTIVE) == MeterGroupV2.GROWTH


if __name__ == "__main__":
    print("Running MeterGroupV2 tests...")
    print()

    test_group_v2_validation()
    print("✅ Group V2 validation passed")

    test_group_v2_count()
    print("✅ Group counts correct (5 groups, 21 meters)")

    test_group_v2_sizes()
    print("✅ Individual group sizes correct")

    test_no_duplicates()
    print("✅ No duplicate meters")

    test_overview_meters_excluded()
    print("✅ Overview meters excluded")

    test_super_group_meters_excluded()
    print("✅ Super-group meters excluded")

    test_get_group_v2()
    print("✅ get_group_v2() works")

    test_get_meters_in_group_v2()
    print("✅ get_meters_in_group_v2() works")

    test_display_names()
    print("✅ Display names correct")

    test_specific_meter_mappings()
    print("✅ All specific meter mappings correct")

    print()
    print("🎉 All tests passed!")
    print()
    print("Meter distribution:")
    for group, meters in GROUP_V2_METERS.items():
        print(f"  {get_group_v2_display_name(group)}: {len(meters)} meters")
