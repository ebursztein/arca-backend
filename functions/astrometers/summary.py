"""
Daily meter summary table generator for LLM prompts.

Creates compact, ranked markdown tables showing:
- Overall score with trend
- Top active/challenging meters
- Fastest changing meters
- Key aspects

Optimized for daily horoscope generation (token efficiency).
"""

from typing import List, Tuple
from datetime import datetime
from io import StringIO
from rich.console import Console
from rich.table import Table

from .meters import AllMetersReading, MeterReading, QualityLabel, TrendData


def _symbol_for_trend(trend: TrendData) -> str:
    """Convert TrendData to visual symbol."""
    if trend.change_rate == "stable":
        return "→"

    if trend.direction in ["improving", "increasing"]:
        return "↑↑" if trend.change_rate == "rapid" else "↑"
    elif trend.direction in ["worsening", "decreasing"]:
        return "↓↓" if trend.change_rate == "rapid" else "↓"
    else:
        return "→"


def _calculate_trend_indicator(delta: float) -> str:
    """
    Convert delta to visual trend indicator.

    Args:
        delta: Change in score (positive = increasing)

    Returns:
        str: ↑↑, ↑, →, ↓, or ↓↓
    """
    if delta >= 20:
        return "↑↑"
    elif delta >= 10:
        return "↑"
    elif delta <= -20:
        return "↓↓"
    elif delta <= -10:
        return "↓"
    else:
        return "→"


def _calculate_change_rate(delta: float) -> str:
    """
    Convert delta to change rate label.

    Args:
        delta: Absolute change in score

    Returns:
        str: RAPID, MODERATE, SLOW, or STABLE
    """
    abs_delta = abs(delta)
    if abs_delta >= 20:
        return "RAPID"
    elif abs_delta >= 10:
        return "MODERATE"
    elif abs_delta >= 5:
        return "SLOW"
    else:
        return "STABLE"


def _get_all_meter_readings(meters: AllMetersReading) -> List[MeterReading]:
    """Extract all 17 meter readings from AllMetersReading object."""
    return [
        # Mind (3)
        meters.mental_clarity,
        meters.focus,
        meters.communication,
        # Emotions (3)
        meters.love,
        meters.inner_stability,
        meters.sensitivity,
        # Body (3)
        meters.vitality,
        meters.drive,
        meters.wellness,
        # Spirit (4)
        meters.purpose,
        meters.connection,
        meters.intuition,
        meters.creativity,
        # Growth (4)
        meters.opportunities,
        meters.career,
        meters.growth,
        meters.social_life,
    ]


def daily_meters_summary(
    meters_today: AllMetersReading,
    meters_yesterday: AllMetersReading = None  # DEPRECATED: trends now built-in
) -> str:
    """
    Generate single comprehensive table showing ALL 17 meters with scores, trends, and top aspects.

    Shows one row per meter with:
    - Unified/Intensity/Harmony scores and trends
    - State label
    - Indicators: MA (Most Active top 5), FC (Fastest Changing top 6)
    - Top aspect driving this meter (compact format)

    Args:
        meters_today: Today's complete meter readings (with trends already calculated)
        meters_yesterday: DEPRECATED - no longer needed, trends are built into meters_today

    Returns:
        str: Single formatted table with all 17 meters ready for LLM prompt
    """

    today_readings = _get_all_meter_readings(meters_today)

    # Helper: Format aspect compactly
    def format_top_aspect(meter_reading: MeterReading) -> str:
        """Format top aspect as: T-Planet deg aspect N-Planet deg (orb H#) D:xx H:xx"""
        if not meter_reading.top_aspects:
            return "(no significant aspects)"

        asp = meter_reading.top_aspects[0]  # Top 1 aspect only

        # Aspect type abbreviations
        aspect_abbrev = {
            "square": "sq",
            "trine": "tri",
            "opposition": "opp",
            "sextile": "sxt",
            "conjunction": "cnj",
            "quincunx": "qnx"
        }
        asp_short = aspect_abbrev.get(asp.aspect_type.value, asp.aspect_type.value[:3])

        # Format: "Saturn sq Uranus (0.35° H3) D:42 H:-29"
        # Note: Degrees omitted - not stored in AspectContribution or raw_scores
        return (
            f"{asp.transit_planet.value.title()} {asp_short} "
            f"{asp.natal_planet.value.title()} "
            f"({asp.orb_deviation:.2f}° H{asp.natal_planet_house}) "
            f"D:{asp.dti_contribution:.0f} H:{asp.hqs_contribution:+.0f}"
        )

    # Build meter data using built-in TrendData objects
    meter_data = []
    for today in today_readings:
        # Use built-in trend data (calculated by get_meters automatically)
        if today.trend:
            # Get rich trend data
            harmony_t = today.trend.harmony
            intensity_t = today.trend.intensity
            unified_t = today.trend.unified_score

            # Deltas
            unified_delta = unified_t.delta
            intensity_delta = intensity_t.delta
            harmony_delta = harmony_t.delta

            # Text descriptions (for LLM) - direction and change_rate are already strings
            harmony_trend_text = f"{harmony_t.direction} ({harmony_t.change_rate})"
            intensity_trend_text = f"{intensity_t.direction} ({intensity_t.change_rate})"
            unified_trend_text = f"{unified_t.direction} ({unified_t.change_rate})"

            # Symbols (for visual scanning)
            harmony_trend = _symbol_for_trend(harmony_t)
            intensity_trend = _symbol_for_trend(intensity_t)
            unified_trend = _symbol_for_trend(unified_t)

            # Change rate (use harmony as primary)
            change_rate = harmony_t.change_rate

            # Previous values
            yesterday_unified = unified_t.previous
            yesterday_intensity = intensity_t.previous
            yesterday_harmony = harmony_t.previous
        else:
            # Fallback if no trend data (shouldn't happen with new implementation)
            unified_delta = intensity_delta = harmony_delta = 0
            harmony_trend_text = intensity_trend_text = unified_trend_text = "stable (stable)"
            unified_trend = intensity_trend = harmony_trend = "→"
            change_rate = "stable"
            yesterday_unified = yesterday_intensity = yesterday_harmony = 0

        meter_data.append({
            'meter_reading': today,  # Keep full object for aspect formatting
            'name': today.meter_name,
            'unified_score': today.unified_score,
            'intensity': today.intensity,
            'harmony': today.harmony,
            'state': today.state_label,
            'unified_delta': unified_delta,
            'intensity_delta': intensity_delta,
            'harmony_delta': harmony_delta,
            'unified_pace': unified_t.change_rate if today.trend else 'stable',
            'intensity_pace': intensity_t.change_rate if today.trend else 'stable',
            'harmony_pace': harmony_t.change_rate if today.trend else 'stable',
        })

    # ========================================================================
    # Build indicators: MA (Most Active) and FC (Fastest Changing)
    # ========================================================================
    individual_meters = [m for m in meter_data if m['name'] not in ['overall_intensity', 'overall_harmony']]

    # Sort by intensity for Most Active
    sorted_by_intensity = sorted(individual_meters, key=lambda x: x['intensity'], reverse=True)
    top_5_active_names = {m['name'] for m in sorted_by_intensity[:5]}

    # Sort by absolute intensity delta for Fastest Changing
    sorted_by_delta = sorted(individual_meters, key=lambda x: abs(x['intensity_delta']), reverse=True)
    top_6_changing_names = {m['name'] for m in sorted_by_delta[:6]}

    # Sort all meters by unified_score descending for final display
    all_meters_sorted = sorted(meter_data, key=lambda x: x['unified_score'], reverse=True)

    # ========================================================================
    # Build single comprehensive table
    # ========================================================================
    output = ""
    output += "\n" + "═" * 180 + "\n"
    output += f"ALL {len(meter_data)} METERS ({meters_today.date.strftime('%Y-%m-%d')})".center(180) + "\n"
    output += "═" * 180 + "\n"

    # Table header
    output += "┌────┬─────────────────┬──────────────────┬────────────────────────┬─────────────────────┬────────────────────┬────┬────┬──────────────────────────────────────────────┐\n"
    output += "│ ## │ Meter           │ State            │   ──── OVERALL ────    │ ──── INTENSITY ──── │ ──── HARMONY ────  │ MA │ FC │ Top Aspect                                   │\n"
    output += "│    │                 │                  │  Val  │     Trend       │  Val │    Trend      │  Val │   Trend     │    │    │                                              │\n"
    output += "├────┼─────────────────┼──────────────────┼───────┼─────────────────┼──────┼───────────────┼──────┼─────────────┼────┼────┼──────────────────────────────────────────────┤\n"

    # Data rows
    for i, meter in enumerate(all_meters_sorted, 1):
        # Indicators (4 chars wide: " ✓  " or "    ")
        ma_marker = " ✓  " if meter['name'] in top_5_active_names else "    "
        fc_marker = " ✓  " if meter['name'] in top_6_changing_names else "    "

        # Format trends
        unified_trend = f"{meter['unified_delta']:+.1f} {meter['unified_pace'][:3]}"
        intensity_trend = f"{meter['intensity_delta']:+.1f} {meter['intensity_pace'][:3]}"
        harmony_trend = f"{meter['harmony_delta']:+.1f} {meter['harmony_pace'][:3]}"

        # Format top aspect
        aspect_str = format_top_aspect(meter['meter_reading'])

        # Build row
        output += f"│{i:3d} "
        output += f"│ {meter['name']:<15}"
        output += f"│ {meter['state']:<16}"
        output += f"│ {meter['unified_score']:5.1f} "
        output += f"│ {unified_trend:<15}"
        output += f"│ {meter['intensity']:4.1f} "
        output += f"│ {intensity_trend:<13}"
        output += f"│ {meter['harmony']:4.1f} "
        output += f"│ {harmony_trend:<11}"
        output += f"│{ma_marker}"
        output += f"│{fc_marker}"
        output += f"│ {aspect_str:<44}│\n"

    # Bottom border
    output += "└────┴─────────────────┴──────────────────┴───────┴─────────────────┴──────┴───────────────┴──────┴─────────────┴────┴────┴──────────────────────────────────────────────┘\n"
    output += "\nMA = Most Active (top 5 intensity) | FC = Fastest Changing (top 6 by delta)\n"

    return output


def meter_groups_summary(meter_groups: dict) -> str:
    """
    Generate compact markdown summary table for meter groups.

    Creates a single table showing all 5 groups with aggregated scores and state labels.
    This is injected into the LLM prompt to provide group-level context alongside
    individual meter data.

    Args:
        meter_groups: Dict mapping group_name -> MeterGroupData (from build_all_meter_groups)

    Returns:
        str: Formatted markdown table ready for LLM prompt

    Example meter_groups structure:
        {
            "mind": {
                "group_name": "mind",
                "display_name": "Mind",
                "scores": {"unified_score": 75.3, "harmony": 78.0, "intensity": 72.7},
                "state": {"label": "Supportive", "quality": "supportive"},
                "interpretation": "",  # Empty, will be filled by LLM
                "trend": {"unified_score": {...}, ...} or None,
                "meter_ids": ["mental_clarity", "decision_quality", "communication_flow"]
            },
            ...
        }
    """
    if not meter_groups:
        return ""

    output = "\n"
    output += "═" * 110 + "\n"
    output += "METER GROUPS (5 Life Areas - Aggregated Scores)".center(110) + "\n"
    output += "═" * 110 + "\n"

    # Build table header
    top_line = "┌" + "─" * 15 + "┬" + "─" * 20 + "┬"
    top_line += "─" * 23 + "┬" + "─" * 23 + "┬" + "─" * 23 + "┐\n"

    merged_header = "│" + " Group ".center(15) + "│" + " State ".center(20) + "│"
    merged_header += " ──── OVERALL ──── ".center(23) + "│"
    merged_header += " ──── INTENSITY ──── ".center(23) + "│"
    merged_header += " ──── HARMONY ──── ".center(23) + "│\n"

    # Sub-header row
    sub_line = "├" + "─" * 15 + "┼" + "─" * 20 + "┼"
    sub_line += "─" * 7 + "┬" + "─" * 15 + "┼"
    sub_line += "─" * 7 + "┬" + "─" * 15 + "┼"
    sub_line += "─" * 7 + "┬" + "─" * 15 + "┤\n"

    sub_header = "│" + " " * 15 + "│" + " " * 20 + "│"
    sub_header += " Val ".center(7) + "│" + " Trend ".center(15) + "│"
    sub_header += " Val ".center(7) + "│" + " Trend ".center(15) + "│"
    sub_header += " Val ".center(7) + "│" + " Trend ".center(15) + "│\n"

    output += top_line + merged_header + sub_line + sub_header

    # Data separator
    data_line = "├" + "─" * 15 + "┼" + "─" * 20 + "┼"
    data_line += "─" * 7 + "┼" + "─" * 15 + "┼"
    data_line += "─" * 7 + "┼" + "─" * 15 + "┼"
    data_line += "─" * 7 + "┼" + "─" * 15 + "┤\n"

    output += data_line

    # Sort groups in a consistent order
    group_order = ["mind", "emotions", "body", "spirit", "growth"]

    for i, group_name in enumerate(group_order):
        if group_name not in meter_groups:
            continue

        group = meter_groups[group_name]

        # Extract scores
        scores = group["scores"]
        unified = scores["unified_score"]
        intensity = scores["intensity"]
        harmony = scores["harmony"]

        # Extract state
        state_label = group["state"]["label"]

        # Extract trends if available
        trend = group.get("trend")
        if trend:
            unified_trend = trend["unified_score"]
            intensity_trend = trend["intensity"]
            harmony_trend = trend["harmony"]

            unified_delta = unified_trend["delta"]
            intensity_delta = intensity_trend["delta"]
            harmony_delta = harmony_trend["delta"]

            unified_pace = unified_trend["change_rate"]
            intensity_pace = intensity_trend["change_rate"]
            harmony_pace = harmony_trend["change_rate"]

            unified_trend_str = f"{unified_delta:+.1f} {unified_pace}"
            intensity_trend_str = f"{intensity_delta:+.1f} {intensity_pace}"
            harmony_trend_str = f"{harmony_delta:+.1f} {harmony_pace}"
        else:
            unified_trend_str = "—"
            intensity_trend_str = "—"
            harmony_trend_str = "—"

        # Build row
        row_str = "│"
        row_str += f" {group['display_name']:<14}│"          # Group name
        row_str += f" {state_label:<19}│"                    # State label
        row_str += f"{unified:7.1f}│"                        # Overall value
        row_str += f" {unified_trend_str:<14}│"              # Overall trend
        row_str += f"{intensity:7.1f}│"                      # Intensity value
        row_str += f" {intensity_trend_str:<14}│"            # Intensity trend
        row_str += f"{harmony:7.1f}│"                        # Harmony value
        row_str += f" {harmony_trend_str:<14}│\n"            # Harmony trend
        output += row_str

    # Bottom border
    bottom_line = "└" + "─" * 15 + "┴" + "─" * 20 + "┴"
    bottom_line += "─" * 7 + "┴" + "─" * 15 + "┴"
    bottom_line += "─" * 7 + "┴" + "─" * 15 + "┴"
    bottom_line += "─" * 7 + "┴" + "─" * 15 + "┘\n"
    output += bottom_line
    output += "\n"

    return output
