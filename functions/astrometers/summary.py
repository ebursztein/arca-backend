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

from .meters import AllMetersReading, MeterReading, QualityLabel, MetricTrend, ChangeRate


def _symbol_for_trend(trend: MetricTrend) -> str:
    """Convert MetricTrend to visual symbol."""
    if trend.change_rate == ChangeRate.STABLE:
        return "→"

    if trend.direction.value in ["improving", "increasing"]:
        return "↑↑" if trend.change_rate == ChangeRate.RAPID else "↑"
    elif trend.direction.value in ["worsening", "decreasing"]:
        return "↓↓" if trend.change_rate == ChangeRate.RAPID else "↓"
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
    meters_yesterday: AllMetersReading = None  # DEPRECATED: trends now built-in
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
        meters_today: Today's complete meter readings (with trends already calculated)
        meters_yesterday: DEPRECATED - no longer needed, trends are built into meters_today

    Returns:
        str: Formatted markdown tables ready for LLM prompt

    Note:
        As of Oct 2025, trends are automatically calculated by get_meters() and included
        in each MeterReading as TrendData objects. The meters_yesterday parameter is
        kept for backward compatibility but is not used.
    """

    today_readings = _get_all_meter_readings(meters_today)

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

            # Text descriptions (for LLM)
            harmony_trend_text = f"{harmony_t.direction.value} ({harmony_t.change_rate.value})"
            intensity_trend_text = f"{intensity_t.direction.value} ({intensity_t.change_rate.value})"
            unified_trend_text = f"{unified_t.direction.value} ({unified_t.change_rate.value})"

            # Symbols (for visual scanning)
            harmony_trend = _symbol_for_trend(harmony_t)
            intensity_trend = _symbol_for_trend(intensity_t)
            unified_trend = _symbol_for_trend(unified_t)

            # Change rate (use harmony as primary)
            change_rate = harmony_t.change_rate.value

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
            'name': today.meter_name,
            'unified_score': today.unified_score,
            'intensity': today.intensity,
            'harmony': today.harmony,
            'state': today.state_label,
            'interpretation': today.interpretation,
            'unified_delta': unified_delta,
            'intensity_delta': intensity_delta,
            'harmony_delta': harmony_delta,
            'unified_trend': unified_trend,
            'intensity_trend': intensity_trend,
            'harmony_trend': harmony_trend,
            # Text descriptions for LLM understanding
            'unified_trend_text': unified_trend_text,
            'intensity_trend_text': intensity_trend_text,
            'harmony_trend_text': harmony_trend_text,
            'change_rate': change_rate,
            'yesterday_unified_score': yesterday_unified,
            'yesterday_intensity': yesterday_intensity,
            'yesterday_harmony': yesterday_harmony,
        })

    # ========================================================================
    # HELPER: Build consistent table row with hierarchical structure
    # ========================================================================
    def build_meter_row(rank: str, meter: dict) -> list:
        """Build a consistent row format for all meter tables."""
        # Extract just the change_rate (pace) from trend text
        # "improving (rapid)" -> "rapid"
        def extract_pace(trend_text: str) -> str:
            if '(' in trend_text and ')' in trend_text:
                return trend_text.split('(')[1].split(')')[0]
            return "stable"

        unified_pace = extract_pace(meter['unified_trend_text'])
        intensity_pace = extract_pace(meter['intensity_trend_text'])
        harmony_pace = extract_pace(meter['harmony_trend_text'])

        return [
            rank,
            meter['name'],
            meter['state'],                                                   # State label (moved next to meter)
            f"{meter['unified_score']:.1f}",                                 # Unified value
            f"{meter['unified_delta']:+.1f} {unified_pace}",                 # Unified trend: delta + pace
            f"{meter['intensity']:.1f}",                                     # Intensity value
            f"{meter['intensity_delta']:+.1f} {intensity_pace}",            # Intensity trend: delta + pace
            f"{meter['harmony']:.1f}",                                       # Harmony value
            f"{meter['harmony_delta']:+.1f} {harmony_pace}",                # Harmony trend: delta + pace
        ]

    # Build hierarchical header using rich with section headers
    def build_table_with_section_headers(data_rows, section_title=""):
        """Build beautiful ASCII table with merged section headers."""

        # Build custom header with merged cells
        output = ""
        if section_title:
            output += f"\n{'═' * 130}\n"
            output += f"{section_title.center(130)}\n"
            output += f"{'═' * 130}\n"

        # Top header row (9 columns: Rank, Meter, State, Overall, Overall Trend, I, I Trend, H, H Trend)
        top_line = "┌" + "─" * 6 + "┬" + "─" * 24 + "┬" + "─" * 20 + "┬"
        top_line += "─" * 23 + "┬" + "─" * 23 + "┬" + "─" * 23 + "┐\n"

        merged_header = "│" + " Rank ".center(6) + "│" + " Meter ".center(24) + "│" + " State ".center(20) + "│"
        merged_header += " ──── OVERALL ──── ".center(23) + "│"
        merged_header += " ──── INTENSITY ──── ".center(23) + "│"
        merged_header += " ──── HARMONY ──── ".center(23) + "│\n"

        # Sub-header row
        sub_line = "├" + "─" * 6 + "┼" + "─" * 24 + "┼" + "─" * 20 + "┼"
        sub_line += "─" * 7 + "┬" + "─" * 15 + "┼"
        sub_line += "─" * 7 + "┬" + "─" * 15 + "┼"
        sub_line += "─" * 7 + "┬" + "─" * 15 + "┤\n"

        sub_header = "│" + " " * 6 + "│" + " " * 24 + "│" + " " * 20 + "│"
        sub_header += " Val ".center(7) + "│" + " Trend ".center(15) + "│"
        sub_header += " Val ".center(7) + "│" + " Trend ".center(15) + "│"
        sub_header += " Val ".center(7) + "│" + " Trend ".center(15) + "│\n"

        output += top_line + merged_header + sub_line + sub_header

        # Data rows
        data_line = "├" + "─" * 6 + "┼" + "─" * 24 + "┼" + "─" * 20 + "┼"
        data_line += "─" * 7 + "┼" + "─" * 15 + "┼"
        data_line += "─" * 7 + "┼" + "─" * 15 + "┼"
        data_line += "─" * 7 + "┼" + "─" * 15 + "┤\n"

        output += data_line

        for i, row in enumerate(data_rows):
            row_str = "│"
            row_str += str(row[0]).center(6) + "│"   # Rank
            row_str += f" {str(row[1]):<23}│"        # Meter (left-aligned)
            row_str += f" {str(row[2]):<19}│"        # State (left-aligned)
            row_str += str(row[3]).rjust(7) + "│"    # Overall Value
            row_str += f" {str(row[4]):<14}│"        # Overall Trend (delta + pace)
            row_str += str(row[5]).rjust(7) + "│"    # I-Val
            row_str += f" {str(row[6]):<14}│"        # I-Trend (delta + pace)
            row_str += str(row[7]).rjust(7) + "│"    # H-Val
            row_str += f" {str(row[8]):<14}│\n"      # H-Trend (delta + pace)
            output += row_str

        # Bottom border
        bottom_line = "└" + "─" * 6 + "┴" + "─" * 24 + "┴" + "─" * 20 + "┴"
        bottom_line += "─" * 7 + "┴" + "─" * 15 + "┴"
        bottom_line += "─" * 7 + "┴" + "─" * 15 + "┴"
        bottom_line += "─" * 7 + "┴" + "─" * 15 + "┘\n"
        output += bottom_line

        return output

    # Start with empty output (legend moved to static prompt for caching)
    output = ""

    # ========================================================================
    # TABLE 1: OVERALL SCORE (Using built-in TrendData)
    # ========================================================================

    # Find overall_intensity and overall_harmony in meter_data
    overall_meters = [m for m in meter_data if m['name'] in ['overall_intensity', 'overall_harmony']]

    if overall_meters:
        overall_rows = [build_meter_row("", m) for m in overall_meters]
        output += build_table_with_section_headers(overall_rows, "OVERALL SCORE")
        output += "\n"

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
