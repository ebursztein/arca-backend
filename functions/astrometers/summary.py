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

from .meters import AllMetersReading, MeterReading, QualityLabel
from .normalization import get_intensity_label, get_harmony_label


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
    """Extract all 23 meter readings from AllMetersReading object."""
    return [
        meters.overall_intensity,
        meters.overall_harmony,
        meters.fire_energy,
        meters.earth_energy,
        meters.air_energy,
        meters.water_energy,
        meters.mental_clarity,
        meters.decision_quality,
        meters.communication_flow,
        meters.emotional_intensity,
        meters.relationship_harmony,
        meters.emotional_resilience,
        meters.physical_energy,
        meters.conflict_risk,
        meters.motivation_drive,
        meters.career_ambition,
        meters.opportunity_window,
        meters.challenge_intensity,
        meters.transformation_pressure,
        meters.intuition_spirituality,
        meters.innovation_breakthrough,
        meters.karmic_lessons,
        meters.social_collective,
    ]


def daily_meters_summary(
    meters_today: AllMetersReading,
    meters_yesterday: AllMetersReading
) -> str:
    """
    Generate compact markdown summary table for daily horoscope LLM prompt.

    ALL TABLES USE THE SAME CONSISTENT FORMAT:
    Rank | Meter | Intensity | Harmony | Quality | State | Trend | Change

    Creates ranked tables showing:
    - Overall unified score with trend
    - Top 5 most active meters (highest intensity)
    - Top 5 most challenging meters (lowest harmony)
    - Top 3 flowing meters (high intensity + high harmony)
    - Fastest changing meters (biggest deltas)
    - Quiet meters (very low activity)

    Args:
        meters_today: Today's complete meter readings
        meters_yesterday: Yesterday's complete meter readings

    Returns:
        str: Formatted markdown tables ready for LLM prompt
    """

    today_readings = _get_all_meter_readings(meters_today)
    yesterday_readings = _get_all_meter_readings(meters_yesterday)

    # Build lookup for yesterday's scores
    yesterday_map = {m.meter_name: m for m in yesterday_readings}

    # Calculate deltas and trends for each meter
    meter_data = []
    for today in today_readings:
        yesterday = yesterday_map.get(today.meter_name)

        # Calculate deltas for all three scores
        unified_delta = today.unified_score - yesterday.unified_score if yesterday else 0
        intensity_delta = today.intensity - yesterday.intensity if yesterday else 0
        harmony_delta = today.harmony - yesterday.harmony if yesterday else 0

        # Use existing label functions from normalization module
        intensity_label = get_intensity_label(today.intensity)
        harmony_label = get_harmony_label(today.harmony)

        meter_data.append({
            'name': today.meter_name,
            'unified_score': today.unified_score,
            'intensity': today.intensity,
            'harmony': today.harmony,
            'intensity_label': intensity_label,
            'harmony_label': harmony_label,
            'quality': today.unified_quality.value,
            'state': today.state_label,
            'interpretation': today.interpretation,
            'unified_delta': unified_delta,
            'intensity_delta': intensity_delta,
            'harmony_delta': harmony_delta,
            'unified_trend': _calculate_trend_indicator(unified_delta),
            'intensity_trend': _calculate_trend_indicator(intensity_delta),
            'harmony_trend': _calculate_trend_indicator(harmony_delta),
            'change_rate': _calculate_change_rate(intensity_delta),
            'yesterday_unified_score': yesterday.unified_score if yesterday else 0,
            'yesterday_intensity': yesterday.intensity if yesterday else 0,
            'yesterday_harmony': yesterday.harmony if yesterday else 0,
        })

    # ========================================================================
    # HELPER: Build consistent table row with hierarchical structure
    # ========================================================================
    def build_meter_row(rank: str, meter: dict) -> list:
        """Build a consistent row format for all meter tables."""
        # Use pre-calculated unified trend from meter_data
        unified_trend = f"{meter['unified_trend']} {meter['unified_delta']:+.1f}"

        return [
            rank,
            meter['name'],
            f"{meter['unified_score']:.1f}",  # Overall value
            unified_trend,                     # Overall trend
            meter['quality'].upper(),          # Overall quality
            meter['state'],
            # Intensity section: Value | Trend | Label
            f"{meter['intensity']:.1f}",
            f"{meter['intensity_trend']} {meter['intensity_delta']:+.1f}",
            meter['intensity_label'],
            # Harmony section: Value | Trend | Label
            f"{meter['harmony']:.1f}",
            f"{meter['harmony_trend']} {meter['harmony_delta']:+.1f}",
            meter['harmony_label'],
        ]

    # Build hierarchical header using rich with section headers
    def build_table_with_section_headers(data_rows, section_title=""):
        """Build beautiful ASCII table with merged section headers."""

        # Build custom header with merged cells
        output = ""
        if section_title:
            output += f"\n{'═' * 160}\n"
            output += f"{section_title.center(160)}\n"
            output += f"{'═' * 160}\n"

        # Top header row (merged section headers for Overall and sub-sections)
        top_line = "┌" + "─" * 6 + "┬" + "─" * 24 + "┬" + "─" * 30 + "┬" + "─" * 20 + "┬"
        top_line += "─" * 31 + "┬" + "─" * 31 + "┐\n"

        merged_header = "│" + " Rank ".center(6) + "│" + " Meter ".center(24) + "│"
        merged_header += " ────── OVERALL ────── ".center(30) + "│" + " State ".center(20) + "│"
        merged_header += " ──── INTENSITY ──── ".center(31) + "│"
        merged_header += " ──── HARMONY ──── ".center(31) + "│\n"

        # Sub-header row
        sub_line = "├" + "─" * 6 + "┼" + "─" * 24 + "┼" + "─" * 7 + "┬" + "─" * 12 + "┬" + "─" * 9 + "┼" + "─" * 20 + "┼"
        sub_line += "─" * 7 + "┬" + "─" * 12 + "┬" + "─" * 10 + "┼"
        sub_line += "─" * 7 + "┬" + "─" * 12 + "┬" + "─" * 10 + "┤\n"

        sub_header = "│" + " " * 6 + "│" + " " * 24 + "│"
        sub_header += " Value ".center(7) + "│" + " Trend ".center(12) + "│" + " Quality ".center(9) + "│" + " " * 20 + "│"
        sub_header += " Val ".center(7) + "│" + " Trend ".center(12) + "│" + " Label ".center(10) + "│"
        sub_header += " Val ".center(7) + "│" + " Trend ".center(12) + "│" + " Label ".center(10) + "│\n"

        output += top_line + merged_header + sub_line + sub_header

        # Data rows
        data_line = "├" + "─" * 6 + "┼" + "─" * 24 + "┼" + "─" * 7 + "┼" + "─" * 12 + "┼" + "─" * 9 + "┼" + "─" * 20 + "┼"
        data_line += "─" * 7 + "┼" + "─" * 12 + "┼" + "─" * 10 + "┼"
        data_line += "─" * 7 + "┼" + "─" * 12 + "┼" + "─" * 10 + "┤\n"

        output += data_line

        for i, row in enumerate(data_rows):
            row_str = "│"
            row_str += str(row[0]).center(6) + "│"   # Rank
            row_str += f" {str(row[1]):<23}│"        # Meter (left-aligned)
            row_str += str(row[2]).rjust(7) + "│"    # Overall Value
            row_str += f" {str(row[3]):<11}│"        # Overall Trend
            row_str += f" {str(row[4]):<8}│"         # Overall Quality
            row_str += f" {str(row[5]):<19}│"        # State (left-aligned)
            row_str += str(row[6]).rjust(7) + "│"    # I-Val
            row_str += f" {str(row[7]):<11}│"        # I-Trend
            row_str += f" {str(row[8]):<9}│"         # I-Label
            row_str += str(row[9]).rjust(7) + "│"    # H-Val
            row_str += f" {str(row[10]):<11}│"       # H-Trend
            row_str += f" {str(row[11]):<9}│\n"      # H-Label
            output += row_str

        # Bottom border
        bottom_line = "└" + "─" * 6 + "┴" + "─" * 24 + "┴" + "─" * 7 + "┴" + "─" * 12 + "┴" + "─" * 9 + "┴" + "─" * 20 + "┴"
        bottom_line += "─" * 7 + "┴" + "─" * 12 + "┴" + "─" * 10 + "┴"
        bottom_line += "─" * 7 + "┴" + "─" * 12 + "┴" + "─" * 10 + "┘\n"
        output += bottom_line

        return output

    # ========================================================================
    # TABLE 1: OVERALL SCORE
    # ========================================================================

    overall_delta = meters_today.overall_unified_score - (
        meters_yesterday.overall_unified_score if meters_yesterday else 0
    )
    overall_trend = _calculate_trend_indicator(overall_delta)
    overall_change_rate = _calculate_change_rate(overall_delta)

    # Build overall score table with rich
    overall_table = Table(title="OVERALL SCORE", show_header=True, header_style="bold yellow", border_style="yellow")
    overall_table.add_column("Metric", style="cyan", width=25)
    overall_table.add_column("Value", style="yellow", width=50)

    overall_table.add_row('Today Score', f"{meters_today.overall_unified_score:.1f}/100")
    overall_table.add_row('Yesterday Score', f"{meters_yesterday.overall_unified_score:.1f}/100")
    overall_table.add_row('Change', f"{overall_trend} {overall_delta:+.1f} ({overall_change_rate})")
    overall_table.add_row('Quality', meters_today.overall_unified_quality.value.upper())
    overall_table.add_row('Date', meters_today.date.strftime('%Y-%m-%d'))

    # Add separator and breakdown
    overall_table.add_row('', '')  # Empty row as separator

    # Overall Intensity breakdown
    intensity_today = meters_today.overall_intensity.intensity
    intensity_yesterday = meters_yesterday.overall_intensity.intensity if meters_yesterday else 0
    intensity_delta = intensity_today - intensity_yesterday
    intensity_trend = _calculate_trend_indicator(intensity_delta)
    overall_table.add_row(
        '  Intensity',
        f"{intensity_today:.1f}/100 ({meters_today.overall_intensity.state_label}) {intensity_trend} {intensity_delta:+.1f}"
    )

    # Overall Harmony breakdown
    harmony_today = meters_today.overall_harmony.harmony
    harmony_yesterday = meters_yesterday.overall_harmony.harmony if meters_yesterday else 0
    harmony_delta = harmony_today - harmony_yesterday
    harmony_trend = _calculate_trend_indicator(harmony_delta)
    overall_table.add_row(
        '  Harmony',
        f"{harmony_today:.1f}/100 ({meters_today.overall_harmony.state_label}) {harmony_trend} {harmony_delta:+.1f}"
    )

    console = Console(file=StringIO(), width=200)
    console.print(overall_table)
    output = "\n" + console.file.getvalue() + "\n"

    # ========================================================================
    # TABLE 2: TOP 5 MOST ACTIVE (Highest Intensity)
    # ========================================================================

    # Filter out meta-meters (overall_intensity, overall_harmony) - they're in OVERALL SCORE section
    individual_meters = [m for m in meter_data if m['name'] not in ['overall_intensity', 'overall_harmony']]

    # Track which meters have been shown (for deduplication)
    shown_meters = set()

    sorted_by_intensity = sorted(individual_meters, key=lambda x: x['intensity'], reverse=True)
    top_5_active = sorted_by_intensity[:5]

    active_table = [build_meter_row(f"#{i}", m) for i, m in enumerate(top_5_active, 1)]
    shown_meters.update(m['name'] for m in top_5_active)

    output += build_table_with_section_headers(active_table, "MOST ACTIVE (Highest Intensity)")
    output += "\n"

    # ========================================================================
    # TABLE 3: MOST CHALLENGING (Lowest Harmony)
    # ========================================================================

    # Filter out meters with intensity < 20 (too quiet to be challenging)
    # Exclude meta-meters AND already-shown meters
    active_meters = [m for m in individual_meters
                     if m['intensity'] >= 20 and m['name'] not in shown_meters]
    sorted_by_harmony = sorted(active_meters, key=lambda x: x['harmony'])
    top_5_challenging = sorted_by_harmony[:5]

    if top_5_challenging:
        challenging_table = [build_meter_row(f"#{i}", m) for i, m in enumerate(top_5_challenging, 1)]
        shown_meters.update(m['name'] for m in top_5_challenging)

        output += build_table_with_section_headers(challenging_table, "MOST CHALLENGING (Lowest Harmony, Active Only)")
        output += "\n"

    # ========================================================================
    # TABLE 4: TOP FLOWING (High Intensity + High Harmony)
    # ========================================================================

    # Score = intensity * (harmony/100) to balance both factors
    # Exclude meta-meters AND already-shown meters
    flowing_meters = [m for m in individual_meters
                      if m['intensity'] >= 40 and m['name'] not in shown_meters]
    for m in flowing_meters:
        m['flow_score'] = m['intensity'] * (m['harmony'] / 100)

    sorted_by_flow = sorted(flowing_meters, key=lambda x: x['flow_score'], reverse=True)
    top_3_flowing = sorted_by_flow[:3]

    if top_3_flowing:
        flowing_table = [build_meter_row(f"#{i}", m) for i, m in enumerate(top_3_flowing, 1)]
        shown_meters.update(m['name'] for m in top_3_flowing)

        output += build_table_with_section_headers(flowing_table, "TOP FLOWING (High Intensity + High Harmony)")
        output += "\n"

    # ========================================================================
    # TABLE 5: FASTEST CHANGING (Biggest Intensity Movement)
    # ========================================================================

    # Exclude meta-meters AND already-shown meters
    remaining_meters = [m for m in individual_meters if m['name'] not in shown_meters]
    sorted_by_delta = sorted(remaining_meters, key=lambda x: abs(x['intensity_delta']), reverse=True)
    fastest_changing = sorted_by_delta[:6]

    if fastest_changing:
        changing_table = [build_meter_row(f"#{i}", m) for i, m in enumerate(fastest_changing, 1)]
        shown_meters.update(m['name'] for m in fastest_changing)

        output += build_table_with_section_headers(changing_table, "FASTEST CHANGING (Biggest Intensity Movement)")
        output += "\n"

    # ========================================================================
    # TABLE 6: QUIET METERS (Low Activity)
    # ========================================================================

    # Exclude meta-meters AND already-shown meters from quiet list
    quiet_meters = [m for m in individual_meters
                    if m['intensity'] < 20 and m['name'] not in shown_meters]
    quiet_names = [m['name'] for m in quiet_meters]

    if quiet_names:
        output += "\n## QUIET METERS (Intensity < 20)\n\n"
        output += ", ".join(quiet_names)
        output += "\n"

    # ========================================================================
    # TABLE 7: KEY ASPECTS (Top 5)
    # ========================================================================

    if meters_today.key_aspects:
        aspects_table = Table(
            title="KEY ASPECTS (Major Transits Affecting Multiple Meters)",
            show_header=True,
            header_style="bold magenta",
            border_style="magenta"
        )

        aspects_table.add_column("Rank", style="dim", width=6)
        aspects_table.add_column("Transit", style="cyan", width=45)
        aspects_table.add_column("DTI", justify="right", style="green", width=8)
        aspects_table.add_column("HQS", justify="right", style="blue", width=8)
        aspects_table.add_column("Meters", justify="right", style="yellow", width=8)
        aspects_table.add_column("Affected", style="dim", width=80)  # Increased width for full list

        for i, ka in enumerate(meters_today.key_aspects[:5], 1):
            aspects_table.add_row(
                f"#{i}",
                ka.description,
                f"{ka.aspect.dti_contribution:.1f}",
                f"{ka.aspect.hqs_contribution:+.1f}",
                str(ka.meter_count),
                ", ".join(ka.affected_meters)  # Show ALL affected meters, no truncation
            )

        console = Console(file=StringIO(), width=250)  # Wider console for full meter lists
        console.print(aspects_table)
        output += "\n" + console.file.getvalue() + "\n"

    return output
