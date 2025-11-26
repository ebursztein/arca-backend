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
)


def test_group_v2_validation():
    """Test that all 17 non-overview meters are mapped."""
    assert validate_group_v2_complete()


def test_group_v2_count():
    """Test that we have exactly 5 groups with 17 total meters."""
    assert len(GROUP_V2_METERS) == 5
    assert len(METER_TO_GROUP_V2) == 17

    # Verify total meter count
    total_meters = sum(len(meters) for meters in GROUP_V2_METERS.values())
    assert total_meters == 17


def test_group_v2_sizes():
    """Test that each group has the expected number of meters."""
    assert len(GROUP_V2_METERS[MeterGroupV2.MIND]) == 3
    assert len(GROUP_V2_METERS[MeterGroupV2.HEART]) == 3
    assert len(GROUP_V2_METERS[MeterGroupV2.BODY]) == 3
    assert len(GROUP_V2_METERS[MeterGroupV2.INSTINCTS]) == 4
    assert len(GROUP_V2_METERS[MeterGroupV2.GROWTH]) == 4


def test_no_duplicates():
    """Test that no meter appears in multiple groups."""
    all_meters = []
    for meters in GROUP_V2_METERS.values():
        all_meters.extend(meters)

    assert len(all_meters) == len(set(all_meters)), "Duplicate meters found"


def test_overview_meters_excluded():
    """Test that overview meters are not in MeterGroupV2."""
    # Overview meters are handled separately in V2 and not part of the enum
    # Just verifying they aren't in the mapping
    for meter in METER_TO_GROUP_V2:
        assert meter not in ["overall_intensity", "overall_harmony"]


def test_get_group_v2():
    """Test get_group_v2 function."""
    assert get_group_v2(Meter.CLARITY) == MeterGroupV2.MIND
    assert get_group_v2(Meter.CONNECTIONS) == MeterGroupV2.HEART
    assert get_group_v2(Meter.ENERGY) == MeterGroupV2.BODY
    assert get_group_v2(Meter.INTUITION) == MeterGroupV2.INSTINCTS
    assert get_group_v2(Meter.AMBITION) == MeterGroupV2.GROWTH


def test_get_meters_in_group_v2():
    """Test get_meters_in_group_v2 function."""
    mind_meters = get_meters_in_group_v2(MeterGroupV2.MIND)
    assert len(mind_meters) == 3
    assert Meter.CLARITY in mind_meters
    assert Meter.FOCUS in mind_meters
    assert Meter.COMMUNICATION in mind_meters


def test_display_names():
    """Test display names for all groups."""
    assert get_group_v2_display_name(MeterGroupV2.MIND) == "Mind"
    assert get_group_v2_display_name(MeterGroupV2.HEART) == "Heart"
    assert get_group_v2_display_name(MeterGroupV2.BODY) == "Body"
    assert get_group_v2_display_name(MeterGroupV2.INSTINCTS) == "Instincts"
    assert get_group_v2_display_name(MeterGroupV2.GROWTH) == "Growth"


def test_specific_meter_mappings():
    """Test specific important meter mappings."""
    # Mind group
    assert get_group_v2(Meter.CLARITY) == MeterGroupV2.MIND
    assert get_group_v2(Meter.FOCUS) == MeterGroupV2.MIND
    assert get_group_v2(Meter.COMMUNICATION) == MeterGroupV2.MIND

    # Heart group
    assert get_group_v2(Meter.CONNECTIONS) == MeterGroupV2.HEART
    assert get_group_v2(Meter.RESILIENCE) == MeterGroupV2.HEART
    assert get_group_v2(Meter.VULNERABILITY) == MeterGroupV2.HEART

    # Body group
    assert get_group_v2(Meter.ENERGY) == MeterGroupV2.BODY
    assert get_group_v2(Meter.DRIVE) == MeterGroupV2.BODY
    assert get_group_v2(Meter.STRENGTH) == MeterGroupV2.BODY

    # Instincts group
    assert get_group_v2(Meter.VISION) == MeterGroupV2.INSTINCTS
    assert get_group_v2(Meter.FLOW) == MeterGroupV2.INSTINCTS
    assert get_group_v2(Meter.INTUITION) == MeterGroupV2.INSTINCTS
    assert get_group_v2(Meter.CREATIVITY) == MeterGroupV2.INSTINCTS

    # Growth group
    assert get_group_v2(Meter.MOMENTUM) == MeterGroupV2.GROWTH
    assert get_group_v2(Meter.AMBITION) == MeterGroupV2.GROWTH
    assert get_group_v2(Meter.EVOLUTION) == MeterGroupV2.GROWTH
    assert get_group_v2(Meter.CIRCLE) == MeterGroupV2.GROWTH


if __name__ == "__main__":
    print("Running MeterGroupV2 tests...")
    print()

    test_group_v2_validation()
    print("Group V2 validation passed")

    test_group_v2_count()
    print("Group counts correct (5 groups, 17 meters)")

    test_group_v2_sizes()
    print("Individual group sizes correct")

    test_no_duplicates()
    print("No duplicate meters")

    test_overview_meters_excluded()
    print("Overview meters excluded")

    test_get_group_v2()
    print("get_group_v2() works")

    test_get_meters_in_group_v2()
    print("get_meters_in_group_v2() works")

    test_display_names()
    print("Display names correct")

    test_specific_meter_mappings()
    print("All specific meter mappings correct")

    print()
    print("All tests passed!")
    print()
    print("Meter distribution:")
    for group, meters in GROUP_V2_METERS.items():
        print(f"  {get_group_v2_display_name(group)}: {len(meters)} meters")
