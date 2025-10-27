# 🌟 Astro Meters - Comprehensive Technical Specification v2.0



---

## 1. Executive Summary

### Purpose
Astro Meters is a quantitative astrological analysis system that translates complex planetary transits into actionable insights through dual-metric scoring and domain-specific meters.

### Core Innovation
- **Dual-Metric System**: Separates intensity (DTI) from quality (HQS) for nuanced interpretation
- **Three-Tier Explainability**: From casual users to advanced practitioners
- **Empirically Calibrated**: Uses historical data distribution rather than theoretical maximums
- **Domain-Specific Meters**: 18 specialized gauges covering cognitive, emotional, physical, and life domains

### Design Principles
1. **Transparency**: Every meter value must be explainable down to constituent aspects
2. **Personalization**: Adapts to individual chart patterns and user-reported sensitivities
3. **Actionability**: Provides timing advice and forecasts, not just current state
4. **Scientific Rigor**: Mathematically sound, empirically validated, reproducible

---

## 2. Core Algorithm

The system is built on two primary metrics that work in tandem:

### 2.1 Dual Transit Influence (DTI) - Intensity Score

**DTI measures the total magnitude of astrological activity, regardless of nature.**

```
DTI = Σ(Wᵢ × Pᵢ)
```

Where:
- **Wᵢ** = Weightage Factor (inherent importance of the natal point)
- **Pᵢ** = Transit Power (current strength of the transiting planet's aspect)

**Interpretation**: DTI answers "How much is happening?" A high DTI indicates a period of significant astrological activity requiring attention and energy.

### 2.2 Harmonic Quality Score (HQS) - Harmony Score

**HQS measures the nature (supportive vs. challenging) of that intensity.**

```
HQS = Σ(Wᵢ × Pᵢ × Qᵢ)
```

Where:
- **Qᵢ** = Quality Factor (aspect harmonic nature)

**Interpretation**: HQS answers "What type of intensity?" Positive HQS indicates growth through flow; negative HQS indicates growth through friction.

### 2.3 Component Breakdown

#### A. Weightage Factor (Wᵢ)

Represents the natal point's importance in the chart.

| Factor | Weight Contribution | Calculation Method |
|--------|-------------------|-------------------|
| **Natal Planet Type** | 3-10 points | Sun/Moon: 10<br>Mercury/Venus/Mars: 7<br>Jupiter/Saturn: 5<br>Uranus/Neptune/Pluto: 3 |
| **Essential Dignity** | -5 to +5 points | Domicile: +5<br>Exaltation: +4<br>Neutral: 0<br>Detriment: -5<br>Fall: -4 |
| **House Position** | 1-3 multiplier | Angular (1,4,7,10): ×3<br>Succedent (2,5,8,11): ×2<br>Cadent (3,6,9,12): ×1 |
| **Chart Ruler Bonus** | +5 points | If planet rules Ascendant |
| **Personal Sensitivity** | 0.5-2.0 multiplier | User-reported (default: 1.0) |

**Formula**:
```
Wᵢ = (Planet_Base + Dignity_Score + Ruler_Bonus) × House_Multiplier × Sensitivity_Factor
```

**Example Calculation**:
```
Natal Sun in Leo (Domicile) in 10th House (Angular), Chart Ruler
Wᵢ = (10 + 5 + 5) × 3 × 1.0 = 60
```

#### B. Transit Power (Pᵢ)

Measures the current strength of a transiting aspect.

| Factor | Impact | Range/Values |
|--------|--------|-------------|
| **Aspect Type** | Base intensity | Conjunction: 10<br>Opposition: 9<br>Square: 8<br>Trine: 6<br>Sextile: 4 |
| **Orb Tightness** | Distance penalty | Linear decay from 100% (exact) to 0% (max orb) |
| **Applying/Separating** | Direction modifier | Applying: ×1.3<br>Exact (within 0.5°): ×1.5<br>Separating: ×0.7 |
| **Stationary** | Station bonus | Within 5 days of direction change: ×1.8 |
| **Transit Planet Weight** | Planet importance | Outer (U/N/P): ×1.5<br>Social (J/S): ×1.2<br>Inner (Su/Me/V/Ma/Mo): ×1.0 |

**Formula**:
```
Pᵢ = Aspect_Base × Orb_Factor × Direction_Mod × Station_Mod × Transit_Weight
```

**Orb Factor Calculation**:
```python
def calculate_orb_factor(deviation, max_orb):
    """Linear decay from exact to maximum orb."""
    return max(0, 1 - (deviation / max_orb))
```

**Direction Modifier Logic**:
```python
def get_direction_modifier(today_deviation, tomorrow_deviation):
    """Determine if aspect is applying, exact, or separating."""
    if today_deviation <= 0.5:
        return 1.5  # Exact
    elif tomorrow_deviation < today_deviation:
        return 1.3  # Applying
    else:
        return 0.7  # Separating
```

**Example Calculation**:
```
Transit Saturn square Natal Sun
- Aspect: Square (8)
- Orb: 2° from exact 90° (max orb 9°)
- Orb Factor: 1 - (2/9) = 0.778
- Direction: Applying (×1.3)
- Station: Not stationary (×1.0)
- Transit Weight: Social planet (×1.2)

Pᵢ = 8 × 0.778 × 1.3 × 1.0 × 1.2 = 9.70
```

#### C. Quality Factor (Qᵢ)

Differentiates the experiential nature of aspects.

| Aspect Type | Quality Factor (Qᵢ) | Interpretation |
|------------|--------------------|--------------  |
| **Trine (△)** | +1.0 | Flow, ease, natural talent expression |
| **Sextile (⚹)** | +1.0 | Opportunity, requires some initiative |
| **Square (□)** | -1.0 | Friction, growth through challenge |
| **Opposition (☍)** | -1.0 | Tension, awareness through polarity |
| **Conjunction (☌)** | *Dynamic* | Depends on planet combination (see below) |

**Conjunction Quality Logic**:
```python
def get_conjunction_quality(transiting_planet, natal_planet):
    """Conjunctions inherit the combined nature of planets involved."""

    benefics = {'Venus', 'Jupiter'}
    malefics = {'Mars', 'Saturn'}
    transformational = {'Uranus', 'Neptune', 'Pluto'}
    luminaries = {'Sun', 'Moon'}

    t_benefic = transiting_planet in benefics
    n_benefic = natal_planet in benefics
    t_malefic = transiting_planet in malefics
    n_malefic = natal_planet in malefics

    # Double benefic: harmonious
    if t_benefic and n_benefic:
        return +0.8

    # Double malefic: intensely challenging
    if t_malefic and n_malefic:
        return -0.8

    # Benefic conjunct malefic: mitigating influence
    if (t_benefic and n_malefic) or (t_malefic and n_benefic):
        return +0.2

    # Outer planet conjunctions: transformational (neutral with tension)
    if transiting_planet in transformational:
        return -0.3  # Slight tension due to disruption

    # Luminaries or Mercury/Mars: context-dependent, default neutral
    return 0.0
```

### 2.4 Normalization to Meter Scale (0-100)

#### The Empirical Calibration Imperative

> ⚠️ **CRITICAL: DO NOT USE THEORETICAL MAXIMUMS**
>
> Theoretical maximums (e.g., "if all planets were conjunct in domicile in the 1st house") are meaningless. Real-world distributions have long tails and must be empirically determined.

**Calibration Process**:

1. **Dataset Collection**
   - Minimum 10,000 diverse natal charts
   - Recommended: 50,000+ charts across demographics, birth locations, and time periods

2. **Historical Calculation**
   - For each chart, calculate DTI and HQS for every day over 20-30 years
   - Store: `{chart_id, date, dti, hqs, breakdown_by_planet}`

3. **Distribution Analysis**
   ```python
   # Analyze the distribution
   dti_scores = [score['dti'] for score in all_historical_scores]
   hqs_positive = [score['hqs'] for score in all_historical_scores if score['hqs'] > 0]
   hqs_negative = [abs(score['hqs']) for score in all_historical_scores if score['hqs'] < 0]

   # Set normalization thresholds at 99th percentile
   DTI_MAX = np.percentile(dti_scores, 99.0)
   HQS_MAX_POSITIVE = np.percentile(hqs_positive, 99.0)
   HQS_MAX_NEGATIVE = np.percentile(hqs_negative, 99.0)
   ```

4. **Compression Function for Outliers**
   ```python
   def normalize_with_soft_ceiling(raw_score, max_value, target_scale=100):
       """Apply logarithmic compression beyond expected maximum."""
       if raw_score <= max_value:
           return (raw_score / max_value) * target_scale
       else:
           # Compress outliers beyond 99th percentile
           excess = raw_score - max_value
           compressed_excess = 10 * math.log10(1 + excess / max_value)
           return min(target_scale, target_scale + compressed_excess)
   ```

**Normalization Formulas**:

```python
# Intensity Meter (0-100)
Intensity_Meter = normalize_with_soft_ceiling(DTI, DTI_MAX, 100)

# Harmony Meter (0-100, where 0=challenging, 50=neutral, 100=harmonious)
if HQS >= 0:
    Harmony_Meter = 50 + normalize_with_soft_ceiling(HQS, HQS_MAX_POSITIVE, 50)
else:
    Harmony_Meter = 50 - normalize_with_soft_ceiling(abs(HQS), HQS_MAX_NEGATIVE, 50)
```

### 2.5 Meter Interpretation Matrix

| Intensity | Harmony | Interpretation | User Guidance |
|-----------|---------|---------------|--------------|
| 0-30 | Any | **Quiet Period** | Low astrological activity. Good for rest, routine, integration. |
| 31-50 | 70-100 | **Gentle Flow** | Mild supportive energy. Incremental progress feels natural. |
| 31-50 | 0-30 | **Minor Friction** | Small irritations or obstacles. Manageable with awareness. |
| 51-70 | 70-100 | **Productive Flow** | Optimal state: noticeable energy + ease. Prime time for action. |
| 51-70 | 30-70 | **Mixed Dynamics** | Complex period with both opportunities and challenges. Navigate carefully. |
| 51-70 | 0-30 | **Moderate Challenge** | Noticeable friction. Growth through persistence. |
| 71-85 | 70-100 | **Peak Opportunity** | Rare alignment. Major positive potential. Act on important goals. |
| 71-85 | 30-70 | **Intense Mixed** | High pressure with both gifts and tests. Pivotal period. |
| 71-85 | 0-30 | **High Challenge** | Intense difficulty. Resilience required. Major lessons available. |
| 86-100 | 70-100 | **Exceptional Grace** | Extremely rare. Life-changing positive potential. |
| 86-100 | 0-30 | **Crisis/Breakthrough** | Extremely rare. Major transformation, often through upheaval. |

---

## 3. Natal Chart Quantification

### 3.1 Element Balance Calculation

Quantifies the distribution of Fire, Earth, Air, and Water energies.

**Sign-Element Mapping**:
- **Fire**: Aries, Leo, Sagittarius → Initiative, inspiration, enthusiasm
- **Earth**: Taurus, Virgo, Capricorn → Stability, practicality, manifestation
- **Air**: Gemini, Libra, Aquarius → Communication, ideas, social connection
- **Water**: Cancer, Scorpio, Pisces → Emotion, intuition, depth

**Weighted Point System**:
| Chart Point | Weight | Rationale |
|------------|--------|-----------|
| Sun | 3.0 | Core identity and vitality |
| Moon | 3.0 | Emotional nature and needs |
| Ascendant | 2.5 | Self-presentation and approach to life |
| Mercury | 2.0 | Mental processing and communication |
| Venus | 2.0 | Values and relational style |
| Mars | 2.0 | Drive and assertion method |
| Jupiter | 1.5 | Growth and expansion style |
| Saturn | 1.5 | Structure and discipline approach |
| Uranus | 1.0 | Innovation and change style |
| Neptune | 1.0 | Spirituality and ideals |
| Pluto | 1.0 | Transformation and power dynamics |

**Calculation**:
```python
def calculate_element_balance(natal_chart):
    """Calculate natal element distribution."""
    elements = {'Fire': 0, 'Earth': 0, 'Air': 0, 'Water': 0}

    weights = {
        'Sun': 3.0, 'Moon': 3.0, 'Ascendant': 2.5,
        'Mercury': 2.0, 'Venus': 2.0, 'Mars': 2.0,
        'Jupiter': 1.5, 'Saturn': 1.5,
        'Uranus': 1.0, 'Neptune': 1.0, 'Pluto': 1.0
    }

    for point, weight in weights.items():
        sign = natal_chart.get_sign(point)
        element = get_element_for_sign(sign)
        elements[element] += weight

    # Convert to percentages
    total = sum(elements.values())
    return {elem: (value / total) * 100 for elem, value in elements.items()}
```

**Interpretation Thresholds**:
| Element % | Classification | Meaning |
|-----------|----------------|---------|
| < 15% | **Deficient** | Compensatory behaviors likely; area of growth |
| 15-30% | **Moderate** | Balanced, integrated expression |
| > 30% | **Dominant** | Primary mode of operation; potential excess |

### 3.2 Planetary Dignity Scoring

Measures how "comfortable" a planet is in its zodiac sign position.

**Dignity Table**:

| Planet | Domicile (+5) | Exaltation (+4) | Detriment (-5) | Fall (-4) |
|--------|--------------|----------------|---------------|-----------|
| **Sun** | Leo | Aries | Aquarius | Libra |
| **Moon** | Cancer | Taurus | Capricorn | Scorpio |
| **Mercury** | Gemini, Virgo | Virgo (15°) | Sagittarius, Pisces | Pisces (15°) |
| **Venus** | Taurus, Libra | Pisces | Scorpio, Aries | Virgo |
| **Mars** | Aries, Scorpio | Capricorn | Libra, Taurus | Cancer |
| **Jupiter** | Sagittarius, Pisces | Cancer | Gemini, Virgo | Capricorn |
| **Saturn** | Capricorn, Aquarius | Libra | Cancer, Leo | Aries |

**Calculation**:
```python
def calculate_dignity_score(planet, sign, degree):
    """Return dignity score for a planet in a sign."""
    dignity_table = load_dignity_table()

    if sign in dignity_table[planet]['domicile']:
        return 5
    elif sign in dignity_table[planet]['exaltation']:
        # Check degree for precise exaltations (e.g., Sun at 19° Aries)
        if check_exaltation_degree(planet, sign, degree):
            return 4
    elif sign in dignity_table[planet]['detriment']:
        return -5
    elif sign in dignity_table[planet]['fall']:
        return -4
    else:
        return 0  # Peregrine (neutral)
```

**Aggregate Dignity Score**:
```python
def calculate_chart_dignity_total(natal_chart):
    """Sum of all planetary dignities, weighted by planet importance."""
    total = 0
    weights = {'Sun': 3, 'Moon': 3, 'Mercury': 2, 'Venus': 2, 'Mars': 2,
               'Jupiter': 1.5, 'Saturn': 1.5}

    for planet, weight in weights.items():
        dignity = calculate_dignity_score(
            planet,
            natal_chart.get_sign(planet),
            natal_chart.get_degree(planet)
        )
        total += dignity * weight

    return total
```

**Interpretation**:
- **Positive Total (>20)**: Planets generally well-placed; innate ease in life expression
- **Near Zero (-10 to +10)**: Mixed; balance of strengths and challenges
- **Negative Total (<-20)**: Planets in challenge; growth through overcoming adversity

### 3.3 House System & Angular Importance

**Recommended House System**:
- **Primary**: Placidus (most widely used, time-sensitive)
- **Fallback**: Whole Sign (for extreme latitudes >60° or when birth time uncertain within 1 hour)

**Trigger for Fallback**:
```python
def select_house_system(latitude, birth_time_accuracy):
    """Choose appropriate house system based on chart conditions."""
    if abs(latitude) > 60 or birth_time_accuracy > 60:  # minutes uncertain
        return 'whole_sign'
    else:
        # Check for extreme house distortions in Placidus
        houses = calculate_placidus_houses(latitude, ...)
        house_sizes = [houses[i+1] - houses[i] for i in range(12)]

        if max(house_sizes) > 60 or min(house_sizes) < 15:
            return 'whole_sign'  # Placidus too distorted
        return 'placidus'
```

**House Classification**:

| Type | Houses | Multiplier | Significance | Keywords |
|------|--------|-----------|-------------|----------|
| **Angular** | 1, 4, 7, 10 | ×3.0 | Maximum visibility and impact | Action, prominence, outward expression |
| **Succedent** | 2, 5, 8, 11 | ×2.0 | Stabilization and resource building | Values, resources, consolidation |
| **Cadent** | 3, 6, 9, 12 | ×1.0 | Mental and transitional processes | Adaptation, learning, preparation |

**Special Considerations**:
- Planets within 5° of an angle (Asc/IC/Dsc/MC) receive the angular multiplier even if technically in a cadent house
- Retrograde planets in angular houses: reduce multiplier by 0.5 (e.g., ×3.0 becomes ×2.5)

### 3.4 Chart Ruler Identification

The chart ruler is the planet that rules the Ascendant sign.

**Rulership Table (Traditional)**:
| Sign | Ruler | Modern Co-Ruler |
|------|-------|----------------|
| Aries | Mars | - |
| Taurus | Venus | - |
| Gemini | Mercury | - |
| Cancer | Moon | - |
| Leo | Sun | - |
| Virgo | Mercury | - |
| Libra | Venus | - |
| Scorpio | Mars | Pluto |
| Sagittarius | Jupiter | - |
| Capricorn | Saturn | - |
| Aquarius | Saturn | Uranus |
| Pisces | Jupiter | Neptune |

**Implementation**:
```python
def identify_chart_ruler(natal_chart):
    """Return the chart ruler(s) based on Ascendant sign."""
    asc_sign = natal_chart.get_sign('Ascendant')

    rulership = {
        'Aries': ['Mars'],
        'Taurus': ['Venus'],
        'Gemini': ['Mercury'],
        'Cancer': ['Moon'],
        'Leo': ['Sun'],
        'Virgo': ['Mercury'],
        'Libra': ['Venus'],
        'Scorpio': ['Mars', 'Pluto'],  # Traditional + modern
        'Sagittarius': ['Jupiter'],
        'Capricorn': ['Saturn'],
        'Aquarius': ['Saturn', 'Uranus'],
        'Pisces': ['Jupiter', 'Neptune']
    }

    return rulership[asc_sign]

def apply_chart_ruler_bonus(natal_chart, planet_weights):
    """Add +5 bonus to chart ruler(s) weightage."""
    rulers = identify_chart_ruler(natal_chart)

    for ruler in rulers:
        planet_weights[ruler] += 5

    return planet_weights
```

---

## 4. Transit Intensity Scoring

### 4.1 Aspect Detection Algorithm

**Angular Separation Calculation**:
```python
def calculate_angular_separation(long1, long2):
    """Calculate shortest arc between two zodiacal longitudes."""
    diff = abs(long1 - long2)

    # Take shorter arc around the circle
    if diff > 180:
        diff = 360 - diff

    return diff
```

**Aspect Detection with Orb**:

| Aspect | Symbol | Exact Angle | Major Orbs | Minor Orbs | Base Intensity |
|--------|--------|------------|-----------|-----------|---------------|
| **Conjunction** | ☌ | 0° | Sun/Moon: ±10°<br>Planets: ±8° | Outer planets: ±6° | 10 |
| **Opposition** | ☍ | 180° | Sun/Moon: ±10°<br>Planets: ±8° | Outer planets: ±6° | 9 |
| **Square** | □ | 90° | Sun/Moon: ±8°<br>Planets: ±7° | Outer planets: ±5° | 8 |
| **Trine** | △ | 120° | Sun/Moon: ±8°<br>Planets: ±7° | Outer planets: ±5° | 6 |
| **Sextile** | ⚹ | 60° | Sun/Moon: ±6°<br>Planets: ±5° | Outer planets: ±4° | 4 |

**Orb Determination Logic**:
```python
def get_max_orb(aspect_type, natal_planet, transiting_planet):
    """Determine maximum orb based on planets involved."""
    luminaries = {'Sun', 'Moon'}
    outer_planets = {'Uranus', 'Neptune', 'Pluto'}

    # Wider orbs for major aspects
    if aspect_type in ['conjunction', 'opposition']:
        if natal_planet in luminaries or transiting_planet in luminaries:
            return 10.0
        elif transiting_planet in outer_planets:
            return 6.0
        else:
            return 8.0

    # Medium orbs for square and trine
    elif aspect_type in ['square', 'trine']:
        if natal_planet in luminaries or transiting_planet in luminaries:
            return 8.0
        elif transiting_planet in outer_planets:
            return 5.0
        else:
            return 7.0

    # Tight orbs for sextile
    elif aspect_type == 'sextile':
        if natal_planet in luminaries:
            return 6.0
        elif transiting_planet in outer_planets:
            return 4.0
        else:
            return 5.0
```

**Aspect Detection Function**:
```python
def detect_aspects(transit_longitude, natal_longitude, transit_planet, natal_planet):
    """Detect all active aspects within orb."""
    angle = calculate_angular_separation(transit_longitude, natal_longitude)

    aspect_angles = {
        'conjunction': 0,
        'sextile': 60,
        'square': 90,
        'trine': 120,
        'opposition': 180
    }

    detected_aspects = []

    for aspect_name, exact_angle in aspect_angles.items():
        deviation = abs(angle - exact_angle)
        max_orb = get_max_orb(aspect_name, natal_planet, transit_planet)

        if deviation <= max_orb:
            detected_aspects.append({
                'type': aspect_name,
                'exact_angle': exact_angle,
                'actual_angle': angle,
                'deviation': deviation,
                'max_orb': max_orb,
                'orb_percentage': (deviation / max_orb) * 100
            })

    return detected_aspects
```

### 4.2 Orb Factor Calculation

**Linear Decay Model**:
```python
def calculate_orb_factor(deviation, max_orb):
    """
    Calculate aspect strength based on orb tightness.
    Returns 1.0 at exact, declining linearly to 0.0 at max orb.
    """
    if deviation > max_orb:
        return 0.0

    return 1.0 - (deviation / max_orb)
```

**Visual Representation**:
```
Aspect Strength by Orb
  1.0 |●
      |  ●
  0.8 |    ●
      |      ●
  0.6 |        ●
      |          ●
  0.4 |            ●
      |              ●
  0.2 |                ●
      |                  ●
  0.0 |___________________●
      0°  1°  2°  3°  4°  5°  6°  7°  8°
           Deviation from Exact
```

### 4.3 Applying vs. Separating Modifier

**Detection Method**:
```python
def get_aspect_direction_modifier(transit_planet, natal_planet, current_date):
    """
    Determine if aspect is applying, exact, or separating.
    Applying aspects are forming; separating aspects are waning.
    """
    # Calculate current deviation
    current_aspect = detect_aspects(
        get_planet_position(transit_planet, current_date),
        get_planet_position(natal_planet, 'natal'),
        transit_planet,
        natal_planet
    )[0]  # Assume we're checking a known aspect

    current_dev = current_aspect['deviation']

    # Calculate tomorrow's deviation
    tomorrow = current_date + timedelta(days=1)
    tomorrow_aspect = detect_aspects(
        get_planet_position(transit_planet, tomorrow),
        get_planet_position(natal_planet, 'natal'),
        transit_planet,
        natal_planet
    )[0]

    tomorrow_dev = tomorrow_aspect['deviation']

    # Determine status
    if current_dev <= 0.5:
        return {'status': 'exact', 'modifier': 1.5}
    elif tomorrow_dev < current_dev:
        return {'status': 'applying', 'modifier': 1.3}
    else:
        return {'status': 'separating', 'modifier': 0.7}
```

**Psychological Interpretation**:

| Status | Modifier | Energy Quality | User Guidance |
|--------|----------|---------------|--------------|
| **Applying** | ×1.3 | Building, intensifying, anticipatory | Prepare for upcoming themes; energy is gathering |
| **Exact** | ×1.5 | Peak, culmination, maximum clarity | Aspect's nature fully manifests; pivotal moment |
| **Separating** | ×0.7 | Waning, releasing, integrating | Process and integrate lessons; energy receding |

### 4.4 Transiting Planet Weight

**Duration-Based Weighting**:

| Planet Group | Planets | Weight | Avg Aspect Duration | Significance |
|-------------|---------|--------|-------------------|-------------|
| **Outer** | Pluto, Neptune, Uranus | ×1.5 | Months to years | Generational, transformational, slow-burn |
| **Social** | Saturn, Jupiter | ×1.2 | Weeks to months | Structural, growth, social-level changes |
| **Inner** | Sun, Mercury, Venus, Mars | ×1.0 | Days to weeks | Personal, immediate, fast-moving |
| **Lunar** | Moon | ×0.8 | Hours to 2 days | Emotional, fleeting, mood-setting |

**Rationale**: Longer-duration transits have more time to manifest tangibly and require sustained attention, thus their impact is weighted more heavily.

```python
def get_transit_planet_weight(planet):
    """Return multiplier based on planet's orbital speed."""
    weights = {
        'Pluto': 1.5,
        'Neptune': 1.5,
        'Uranus': 1.5,
        'Saturn': 1.2,
        'Jupiter': 1.2,
        'Mars': 1.0,
        'Venus': 1.0,
        'Mercury': 1.0,
        'Sun': 1.0,
        'Moon': 0.8
    }
    return weights.get(planet, 1.0)
```

### 4.5 Retrograde & Station Considerations

**Retrograde Periods**:
- Can trigger the same aspect **3 times** (direct, retrograde, direct again)
- Each pass has a different psychological flavor:
  1. **First Pass (Direct)**: Initial encounter with theme
  2. **Second Pass (Retrograde)**: Review, revise, go deeper
  3. **Third Pass (Direct)**: Integration, final resolution

**Station Intensity Boost**:
```python
def calculate_station_modifier(transit_planet, date):
    """
    Amplify transit power when planet is stationary.
    Station = within 5 days of direction change.
    """
    station_dates = get_station_dates(transit_planet, date.year)

    for station_date in station_dates:
        days_from_station = abs((date - station_date).days)

        if days_from_station <= 5:
            # Peak at exact station, declining over 5 days
            station_factor = 1.8 - (0.12 * days_from_station)  # 1.8 to 1.2
            return station_factor

    return 1.0  # Not stationary
```

**Why Stations Matter**:
- Planet appears nearly motionless in the sky
- Psychological experience: theme becomes inescapable, "stuck," requiring deep processing
- Often correlates with external events crystallizing or coming to a head

### 4.6 Complete Transit Power Calculation

**Bringing It All Together**:
```python
def calculate_transit_power(transit_data, natal_data, date):
    """
    Calculate Pᵢ for a single transit aspect.

    Args:
        transit_data: {planet, longitude, ...}
        natal_data: {planet, longitude, ...}
        date: datetime object for calculation

    Returns:
        float: Transit Power (Pᵢ)
    """
    # Step 1: Detect aspect
    aspects = detect_aspects(
        transit_data['longitude'],
        natal_data['longitude'],
        transit_data['planet'],
        natal_data['planet']
    )

    if not aspects:
        return 0.0

    # Take strongest aspect if multiple detected
    aspect = min(aspects, key=lambda a: a['deviation'])

    # Step 2: Base intensity
    aspect_base = {
        'conjunction': 10,
        'opposition': 9,
        'square': 8,
        'trine': 6,
        'sextile': 4
    }[aspect['type']]

    # Step 3: Orb factor
    orb_factor = calculate_orb_factor(aspect['deviation'], aspect['max_orb'])

    # Step 4: Direction modifier
    direction = get_aspect_direction_modifier(
        transit_data['planet'],
        natal_data['planet'],
        date
    )
    direction_mod = direction['modifier']

    # Step 5: Station modifier
    station_mod = calculate_station_modifier(transit_data['planet'], date)

    # Step 6: Transit planet weight
    transit_weight = get_transit_planet_weight(transit_data['planet'])

    # Calculate final Pᵢ
    P_i = aspect_base * orb_factor * direction_mod * station_mod * transit_weight

    return P_i
```

---

## 5. Meter Taxonomy & Specifications

### 5.1 Meter Categories Overview

```
Astro Meters Taxonomy
│
├── 🌍 Global Meters (2)
│   ├── Overall Intensity
│   └── Overall Harmony
│
├── 🔥 Element Meters (4)
│   ├── Fire Energy
│   ├── Earth Energy
│   ├── Air Energy
│   └── Water Energy
│
├── 🧠 Cognitive Meters (3)
│   ├── Mental Clarity
│   ├── Decision Quality
│   └── Communication Flow
│
├── ❤️ Emotional Meters (3)
│   ├── Emotional Intensity
│   ├── Relationship Harmony
│   └── Emotional Resilience
│
├── ⚡ Physical/Action Meters (3)
│   ├── Physical Energy
│   ├── Conflict Risk
│   └── Motivation Drive
│
├── 🎯 Life Domain Meters (4)
│   ├── Career Ambition
│   ├── Opportunity Window
│   ├── Challenge Intensity
│   └── Transformation Pressure
│
└── 🔮 Specialized Meters (4)
    ├── Intuition Spirituality
    ├── Innovation Breakthroughs
    ├── Karmic Lessons
    └── Social Collective Energy
```

**Total: 23 Meters** (expandable architecture)

---

### 5.2 Global Meters

#### 5.2.1 Overall Intensity Gauge

**Purpose**: Measures the total magnitude of astrological activity, regardless of nature.

**Calculation**:
```python
def calculate_overall_intensity(natal_chart, transit_chart, date):
    """Calculate total DTI across all transits."""
    total_dti = 0
    aspect_breakdown = []

    for t_planet in TRANSIT_PLANETS:
        for n_planet in NATAL_PLANETS:
            W_i = calculate_weightage(natal_chart, n_planet)
            P_i = calculate_transit_power(
                transit_chart[t_planet],
                natal_chart[n_planet],
                date
            )

            if P_i > 0:  # Aspect detected
                contribution = W_i * P_i
                total_dti += contribution

                aspect_breakdown.append({
                    'aspect': f"{t_planet} {aspect_symbol} {n_planet}",
                    'contribution': contribution,
                    'percentage': 0  # Calculate after total known
                })

    # Calculate contribution percentages
    for aspect in aspect_breakdown:
        aspect['percentage'] = (aspect['contribution'] / total_dti) * 100

    # Normalize to 0-100
    intensity_meter = normalize_with_soft_ceiling(total_dti, DTI_MAX, 100)

    return {
        'meter_value': intensity_meter,
        'raw_dti': total_dti,
        'aspect_breakdown': sorted(aspect_breakdown,
                                   key=lambda x: x['contribution'],
                                   reverse=True)
    }
```

**Display**:
```
╔════════════════════════════════════╗
║  🌍 OVERALL INTENSITY              ║
║  ████████░░░░░░░░░░ 72/100         ║
║                                    ║
║  Activity Level: HIGH              ║
║  Active Aspects: 12                ║
║  Top Contributors:                 ║
║  • Saturn □ Sun (18%)              ║
║  • Jupiter △ Venus (14%)           ║
║  • Pluto ☍ Mercury (12%)           ║
╚════════════════════════════════════╝
```

**Interpretation Ranges**:
| Meter Range | Label | Meaning | Advice |
|------------|-------|---------|--------|
| 0-25 | **Quiet** | Minimal activity | Rest, integrate, routine maintenance |
| 26-50 | **Moderate** | Normal background activity | Standard operations, incremental progress |
| 51-75 | **High** | Significant activity | Pay attention, things are moving |
| 76-90 | **Very High** | Intense activity (top 5%) | Major themes active, strategic focus |
| 91-100 | **Extreme** | Rare intensity (top 1%) | Life-defining period, all hands on deck |

---

#### 5.2.2 Overall Harmony Meter

**Purpose**: Measures the net supportive vs. challenging quality of current transits.

**Calculation**:
```python
def calculate_overall_harmony(natal_chart, transit_chart, date):
    """Calculate total HQS across all transits."""
    total_hqs = 0
    supportive_dti = 0
    challenging_dti = 0
    aspect_breakdown = []

    for t_planet in TRANSIT_PLANETS:
        for n_planet in NATAL_PLANETS:
            W_i = calculate_weightage(natal_chart, n_planet)
            P_i = calculate_transit_power(
                transit_chart[t_planet],
                natal_chart[n_planet],
                date
            )
            Q_i = get_quality_factor(aspect_type, t_planet, n_planet)

            if P_i > 0:
                contribution = W_i * P_i * Q_i
                total_hqs += contribution

                # Track supportive vs challenging separately
                if Q_i > 0:
                    supportive_dti += W_i * P_i
                elif Q_i < 0:
                    challenging_dti += W_i * P_i

                aspect_breakdown.append({
                    'aspect': f"{t_planet} {aspect_symbol} {n_planet}",
                    'contribution': contribution,
                    'quality': 'supportive' if Q_i > 0 else 'challenging' if Q_i < 0 else 'neutral'
                })

    # Normalize to 0-100 scale
    if total_hqs >= 0:
        harmony_meter = 50 + normalize_with_soft_ceiling(total_hqs, HQS_MAX_POSITIVE, 50)
    else:
        harmony_meter = 50 - normalize_with_soft_ceiling(abs(total_hqs), HQS_MAX_NEGATIVE, 50)

    return {
        'meter_value': harmony_meter,
        'raw_hqs': total_hqs,
        'supportive_vs_challenging_ratio': supportive_dti / max(challenging_dti, 1),
        'aspect_breakdown': aspect_breakdown
    }
```

**Display**:
```
╔════════════════════════════════════╗
║  🌈 OVERALL HARMONY                ║
║  ░░░░░░░░████████████ 38/100       ║
║  Challenging ◄────────► Supportive ║
║                                    ║
║  Quality: CHALLENGING              ║
║  Supportive: 3 aspects             ║
║  Challenging: 7 aspects            ║
║  Neutral: 2 aspects                ║
║                                    ║
║  Net Effect: Growth through        ║
║  friction and obstacles            ║
╚════════════════════════════════════╝
```

**Interpretation Ranges**:
| Meter Range | Label | Meaning | Experience |
|------------|-------|---------|-----------|
| 0-20 | **Very Challenging** | Heavy difficult aspects | High friction, obstacles, tests |
| 21-40 | **Challenging** | Net difficult influence | Requires effort, lessons prominent |
| 41-60 | **Mixed/Neutral** | Balance of both | Opportunities and challenges coexist |
| 61-80 | **Supportive** | Net harmonious influence | Flow, ease, natural unfolding |
| 81-100 | **Very Supportive** | Predominantly harmonious | Grace, luck, things fall into place |

---

### 5.3 Element Balance Meters

These four meters show the current distribution of elemental energy (natal + transit blend).

#### Calculation Formula
```python
def calculate_element_meter(element, natal_chart, transit_chart):
    """
    Blend natal and transit element distributions.
    70% natal (your baseline) + 30% current transits (temporary influence)
    """
    natal_element_pct = calculate_element_balance(natal_chart)[element]
    transit_element_pct = calculate_element_balance(transit_chart)[element]

    blended_pct = (0.7 * natal_element_pct) + (0.3 * transit_element_pct)

    # Determine if currently elevated or suppressed
    deviation = transit_element_pct - natal_element_pct

    return {
        'meter_value': blended_pct,
        'natal_baseline': natal_element_pct,
        'transit_current': transit_element_pct,
        'deviation': deviation,
        'status': 'elevated' if deviation > 5 else 'suppressed' if deviation < -5 else 'normal'
    }
```

#### 5.3.1 Fire Energy Meter

**Keywords**: Initiative, enthusiasm, inspiration, courage, impulsiveness

**Governing Planets**: Sun, Mars, Jupiter (in fire signs)

**Display**:
```
🔥 FIRE ENERGY: ████████░░ 42%
   Natal Baseline: 35%
   Current Transits: +7% (Elevated)

   Mars transiting Aries is boosting your
   natural fire. Good time for bold action
   but watch for impulsiveness.
```

**Interpretation**:
| Level | State | Guidance |
|-------|-------|----------|
| < 15% | **Deficient** | May lack motivation; cultivate passion, take small risks |
| 15-30% | **Balanced** | Healthy initiative without recklessness |
| > 30% | **Elevated** | High drive; channel productively, avoid burnout |

#### 5.3.2 Earth Energy Meter

**Keywords**: Stability, practicality, manifestation, patience, stubbornness

**Governing Planets**: Venus, Saturn (in earth signs)

**Interpretation**:
| Level | State | Guidance |
|-------|-------|----------|
| < 15% | **Deficient** | May be ungrounded; add structure, focus on tangible results |
| 15-30% | **Balanced** | Practical without rigidity |
| > 30% | **Elevated** | Highly grounded; productive for building, but watch for inertia |

#### 5.3.3 Air Energy Meter

**Keywords**: Communication, ideas, social connection, logic, detachment

**Governing Planets**: Mercury, Venus (in Gemini/Libra), Saturn (in Aquarius)

**Interpretation**:
| Level | State | Guidance |
|-------|-------|----------|
| < 15% | **Deficient** | May struggle with objectivity; engage in dialogue, learn |
| 15-30% | **Balanced** | Clear thinking and communication |
| > 30% | **Elevated** | Mental hyperactivity; excellent for networking but ground emotions |

#### 5.3.4 Water Energy Meter

**Keywords**: Emotion, intuition, empathy, depth, sensitivity

**Governing Planets**: Moon, Neptune, Pluto (in water signs)

**Interpretation**:
| Level | State | Guidance |
|-------|-------|----------|
| < 15% | **Deficient** | May feel disconnected emotionally; engage with feelings, creativity |
| 15-30% | **Balanced** | Emotional intelligence without overwhelm |
| > 30% | **Elevated** | Deep sensitivity; protect energy, honor intuition, create boundaries |

---

### 5.4 Cognitive Meters

#### 5.4.1 Mental Clarity Meter

**Purpose**: Measures the ease or difficulty of thinking, concentration, and mental processing.

**Driving Factors**:
- **Primary**: All aspects to natal Mercury
- **Secondary**: 3rd house transits, aspects to natal 3rd house ruler
- **Modifiers**: Mercury retrograde (×0.6 to clarity)

**Calculation**:
```python
def calculate_mental_clarity(natal_chart, transit_chart, date):
    """Calculate mental clarity from Mercury aspects."""
    mercury_dti = 0
    mercury_hqs = 0

    # All transits to natal Mercury
    for t_planet in TRANSIT_PLANETS:
        W_i = calculate_weightage(natal_chart, 'Mercury')
        P_i = calculate_transit_power(
            transit_chart[t_planet],
            natal_chart['Mercury'],
            date
        )
        Q_i = get_quality_factor(aspect_type, t_planet, 'Mercury')

        mercury_dti += W_i * P_i
        mercury_hqs += W_i * P_i * Q_i

    # Check if Mercury is retrograde
    if transit_chart['Mercury']['retrograde']:
        mercury_dti *= 0.8
        mercury_hqs *= 0.6  # Rx reduces clarity more than intensity

    intensity = normalize_with_soft_ceiling(mercury_dti, DTI_MAX_MERCURY, 100)

    if mercury_hqs >= 0:
        clarity = 50 + normalize_with_soft_ceiling(mercury_hqs, HQS_MAX_MERCURY_POS, 50)
    else:
        clarity = 50 - normalize_with_soft_ceiling(abs(mercury_hqs), HQS_MAX_MERCURY_NEG, 50)

    return {
        'intensity': intensity,
        'clarity': clarity,
        'interpretation': interpret_mental_clarity(intensity, clarity),
        'top_aspects': get_top_mercury_aspects(natal_chart, transit_chart, date)
    }
```

**Interpretation Matrix**:
| Intensity | Clarity | State | Guidance |
|-----------|---------|-------|----------|
| Low | Any | **Mental Quiet** | Low cognitive demands; good for rest |
| Moderate | High (70+) | **Sharp Focus** | Excellent for learning, writing, decisions |
| Moderate | Low (0-30) | **Scattered** | Brain fog; simplify tasks, avoid major choices |
| High | High (70+) | **Genius Mode** | Peak mental performance; tackle complex problems |
| High | Low (0-30) | **Overload** | Mental stress, confusion; step back, rest |

**Display Example**:
```
╔════════════════════════════════════╗
║  🧠 MENTAL CLARITY                 ║
║  Intensity: ██████░░░░ 58/100      ║
║  Clarity:   ████░░░░░░ 35/100      ║
║                                    ║
║  State: SCATTERED                  ║
║                                    ║
║  Top Influences:                   ║
║  ⚠️ Saturn □ Mercury (-42)         ║
║    Concentration difficulties,     ║
║    mental blocks. Double-check     ║
║    details.                        ║
║                                    ║
║  ⚠️ Neptune ☍ Mercury (-28)        ║
║    Confusion, idealization.        ║
║    Avoid assumptions.              ║
║                                    ║
║  ✓ Jupiter △ Mercury (+18)         ║
║    Some optimistic thinking,       ║
║    but overwhelmed by challenges.  ║
║                                    ║
║  Advice: Not ideal for important   ║
║  decisions or complex work. Focus  ║
║  on routine tasks. Rest your mind. ║
╚════════════════════════════════════╝
```

#### 5.4.2 Decision Quality Meter

**Purpose**: Measures the astrological favorability for making important choices.

**Driving Factors**:
- **Mercury**: Clarity of thought
- **Jupiter**: Wisdom, perspective, confidence
- **Saturn**: Discipline, realism (positive in moderation)
- **Neptune**: Idealization risk (negative)
- **Uranus**: Impulsiveness risk (moderate negative)

**Calculation**:
```python
def calculate_decision_quality(natal_chart, transit_chart, date):
    """
    Synthesize factors that support or undermine good decision-making.
    """
    # Base from Mental Clarity
    clarity_score = calculate_mental_clarity(natal_chart, transit_chart, date)['clarity']

    # Jupiter aspects: add confidence and perspective
    jupiter_contribution = 0
    for n_planet in ['Sun', 'Mercury', 'Jupiter']:  # Key decision planets
        jupiter_contribution += calculate_aspect_hqs('Jupiter', n_planet, ...)

    # Saturn aspects: add realism (good in moderation)
    saturn_contribution = 0
    for n_planet in ['Mercury', 'Sun']:
        aspect_hqs = calculate_aspect_hqs('Saturn', n_planet, ...)
        # Saturn is good for decisions in small doses
        if abs(aspect_hqs) < 30:  # Moderate influence
            saturn_contribution += abs(aspect_hqs) * 0.5  # Positive effect
        else:  # Heavy Saturn
            saturn_contribution += aspect_hqs  # Can be too pessimistic

    # Neptune aspects: subtract (idealization, confusion)
    neptune_penalty = 0
    for n_planet in ['Mercury', 'Sun', 'Jupiter']:
        neptune_penalty += abs(calculate_aspect_hqs('Neptune', n_planet, ...))

    # Uranus aspects: subtract if hard aspects (impulsiveness)
    uranus_penalty = 0
    uranus_aspects = get_planet_aspects('Uranus', natal_chart, transit_chart)
    for aspect in uranus_aspects:
        if aspect['quality'] < 0:  # Hard aspects
            uranus_penalty += abs(aspect['contribution']) * 0.7

    # Synthesize
    raw_score = (clarity_score * 0.4 +  # 40% weight
                 jupiter_contribution * 0.3 +  # 30% weight
                 saturn_contribution * 0.2 -   # 20% weight
                 neptune_penalty * 0.15 -      # 15% penalty
                 uranus_penalty * 0.10)        # 10% penalty

    decision_quality = max(0, min(100, raw_score))

    return {
        'meter_value': decision_quality,
        'components': {
            'clarity': clarity_score,
            'jupiter': jupiter_contribution,
            'saturn': saturn_contribution,
            'neptune_risk': neptune_penalty,
            'uranus_risk': uranus_penalty
        },
        'recommendation': generate_decision_advice(decision_quality)
    }
```

**Interpretation**:
| Range | Quality | Recommendation |
|-------|---------|---------------|
| 0-30 | **Poor** | Delay major decisions if possible; high risk of regret |
| 31-50 | **Fair** | Proceed with caution; seek advice; give extra time |
| 51-70 | **Good** | Reasonable time for decisions; trust your process |
| 71-85 | **Excellent** | Clarity and wisdom align; good time for important choices |
| 86-100 | **Optimal** | Rare window of peak judgment; act on major decisions |

#### 5.4.3 Communication Flow Meter

**Purpose**: Measures ease of expression, understanding, and interpersonal communication.

**Driving Factors**:
- **Mercury**: Core communication planet
- **Venus**: Diplomatic expression, likability
- **Mars**: Assertiveness (positive if harmonious, negative if hard aspects)
- **3rd House transits**: Immediate environment and communication

**Calculation**:
```python
def calculate_communication_flow(natal_chart, transit_chart, date):
    """Assess ease of communication and expression."""

    # Mercury flow
    mercury_hqs = get_planet_total_hqs('Mercury', natal_chart, transit_chart)

    # Venus smoothing effect
    venus_hqs = get_planet_total_hqs('Venus', natal_chart, transit_chart)

    # Mars: check for conflict aspects
    mars_aspects = get_planet_aspects('Mars', natal_chart, transit_chart)
    mars_conflict_risk = sum(abs(a['contribution']) for a in mars_aspects if a['quality'] < 0)

    # 3rd house activity
    third_house_activity = calculate_house_transit_activity(natal_chart, transit_chart, 3)

    # Synthesize
    flow_score = (mercury_hqs * 0.5 +           # 50% Mercury
                  venus_hqs * 0.25 +            # 25% Venus
                  third_house_activity * 0.15 - # 15% 3rd house
                  mars_conflict_risk * 0.3)     # 30% penalty for Mars conflict

    communication_meter = normalize_hqs(flow_score)

    return {
        'meter_value': communication_meter,
        'conflict_risk': 'high' if mars_conflict_risk > 40 else 'moderate' if mars_conflict_risk > 20 else 'low',
        'best_use': generate_communication_advice(communication_meter, mars_conflict_risk)
    }
```

**Interpretation**:
| Range | Flow | Advice |
|-------|------|--------|
| 0-30 | **Blocked** | High misunderstanding risk; be extra clear, avoid hard conversations |
| 31-50 | **Restricted** | Some friction; choose words carefully, be patient |
| 51-70 | **Smooth** | Normal communication; generally understood |
| 71-85 | **Excellent** | Eloquence and clarity; good for presentations, negotiations |
| 86-100 | **Masterful** | Peak expression; charisma and understanding align perfectly |

---

### 5.5 Emotional Meters

#### 5.5.1 Emotional Intensity Meter

**Purpose**: Measures the depth and strength of emotional experiences.

**Driving Factors**:
- **Moon**: Primary emotional body
- **Venus**: Relational feelings
- **Neptune**: Sensitivity, empathy, vulnerability
- **Pluto**: Deep/intense emotions
- **4th House & 8th House transits**

**Calculation**:
```python
def calculate_emotional_intensity(natal_chart, transit_chart, date):
    """Calculate depth and strength of emotional experiences."""

    # Moon intensity (primary factor)
    moon_dti = get_planet_total_dti('Moon', natal_chart, transit_chart)
    moon_hqs = get_planet_total_hqs('Moon', natal_chart, transit_chart)

    # Venus emotional component
    venus_dti = get_planet_total_dti('Venus', natal_chart, transit_chart)

    # Pluto deepening effect (intensity, not necessarily challenge)
    pluto_to_moon = get_specific_aspect_dti('Pluto', 'Moon', natal_chart, transit_chart)
    pluto_to_venus = get_specific_aspect_dti('Pluto', 'Venus', natal_chart, transit_chart)
    pluto_factor = pluto_to_moon + pluto_to_venus

    # Neptune sensitivity amplifier
    neptune_to_moon = get_specific_aspect_dti('Neptune', 'Moon', natal_chart, transit_chart)
    neptune_factor = neptune_to_moon * 1.3  # Neptune amplifies emotional sensitivity

    # Calculate total intensity
    total_intensity = (moon_dti * 0.5 +       # 50% Moon
                       venus_dti * 0.2 +      # 20% Venus
                       pluto_factor * 0.2 +   # 20% Pluto
                       neptune_factor * 0.1)  # 10% Neptune

    intensity_meter = normalize_with_soft_ceiling(total_intensity, DTI_MAX_EMOTIONAL, 100)
    harmony_meter = normalize_hqs(moon_hqs)  # Moon HQS represents emotional ease/difficulty

    return {
        'intensity': intensity_meter,
        'harmony': harmony_meter,
        'interpretation': interpret_emotional_state(intensity_meter, harmony_meter),
        'dominant_transit': get_strongest_emotional_transit(natal_chart, transit_chart)
    }
```

**Interpretation Matrix**:
| Intensity | Harmony | State | Experience |
|-----------|---------|-------|-----------|
| Low | Any | **Calm** | Emotional quiet; stable, possibly numb |
| Moderate | High | **Content** | Pleasant emotional state; emotional flow |
| Moderate | Low | **Unsettled** | Mild emotional discomfort; process feelings |
| High | High | **Deeply Moved** | Profound joy, love, gratitude; peak positive emotion |
| High | Low | **Turbulent** | Intense difficult emotions; grief, anger, fear |
| Very High | High | **Ecstatic** | Rare; overwhelming positive emotion |
| Very High | Low | **Crisis** | Emotional overwhelm; support needed |

#### 5.5.2 Relationship Harmony Meter

**Purpose**: Measures ease and positivity in relationships (romantic, close friendships, partnerships).

**Driving Factors**:
- **Venus**: Love, affection, relational ease
- **7th House transits**: Partnerships
- **Moon-Venus aspects**: Emotional compatibility feeling
- **Mars-Venus aspects**: Attraction and friction

**Calculation**:
```python
def calculate_relationship_harmony(natal_chart, transit_chart, date):
    """Assess current relational energy and harmony."""

    # Venus harmony (primary)
    venus_hqs = get_planet_total_hqs('Venus', natal_chart, transit_chart)

    # 7th house activity (partnerships)
    seventh_house_hqs = calculate_house_transit_hqs(natal_chart, transit_chart, 7)

    # Jupiter to Venus (generosity, expansion in love)
    jupiter_venus = get_specific_aspect_hqs('Jupiter', 'Venus', natal_chart, transit_chart)

    # Saturn to Venus (commitment but also restriction)
    saturn_venus = get_specific_aspect_contribution('Saturn', 'Venus', natal_chart, transit_chart)
    # Saturn to Venus in easy aspects = commitment; hard aspects = distance

    # Mars to Venus (passion or conflict)
    mars_venus = get_specific_aspect_contribution('Mars', 'Venus', natal_chart, transit_chart)

    # Neptune to Venus (romance or illusion)
    neptune_venus_hqs = get_specific_aspect_hqs('Neptune', 'Venus', natal_chart, transit_chart)
    neptune_factor = neptune_venus_hqs * 0.7  # Some caution for idealization

    # Synthesize
    harmony_score = (venus_hqs * 0.4 +
                     seventh_house_hqs * 0.2 +
                     jupiter_venus * 0.15 +
                     saturn_venus * 0.1 +
                     mars_venus * 0.1 +
                     neptune_factor * 0.05)

    relationship_meter = normalize_hqs(harmony_score)

    return {
        'meter_value': relationship_meter,
        'themes': identify_relationship_themes(natal_chart, transit_chart),
        'advice': generate_relationship_advice(relationship_meter, themes)
    }
```

**Interpretation**:
| Range | State | Guidance |
|-------|-------|----------|
| 0-30 | **Strained** | High conflict or distance; address issues gently, seek perspective |
| 31-50 | **Challenging** | Some friction; patience and communication needed |
| 51-70 | **Stable** | Normal relational energy; no major ups or downs |
| 71-85 | **Harmonious** | Ease and affection; good time for bonding, romance |
| 86-100 | **Blissful** | Exceptional relational grace; deepen connections, celebrate |

#### 5.5.3 Emotional Resilience Meter

**Purpose**: Measures capacity to handle stress, bounce back from difficulty, and maintain emotional boundaries.

**Driving Factors**:
- **Moon-Saturn aspects**: Emotional boundaries, structure
- **Sun aspects**: Core vitality and sense of self
- **Mars energy**: Fighting spirit
- **12th house transits**: (Negative effect; withdrawal, dissolution)

**Calculation**:
```python
def calculate_emotional_resilience(natal_chart, transit_chart, date):
    """Assess emotional strength and capacity to handle stress."""

    # Saturn to Moon: boundaries and structure (challenging but strengthening)
    saturn_moon = get_specific_aspect_contribution('Saturn', 'Moon', natal_chart, transit_chart)
    # Moderate Saturn-Moon builds resilience; heavy can deplete
    if abs(saturn_moon) < 40:
        resilience_from_saturn = abs(saturn_moon) * 0.8  # Strengthening
    else:
        resilience_from_saturn = saturn_moon  # Can be draining if too heavy

    # Sun vitality (core strength)
    sun_hqs = get_planet_total_hqs('Sun', natal_chart, transit_chart)

    # Mars fighting spirit (especially harmonious aspects)
    mars_positive = sum(a['contribution'] for a in get_planet_aspects('Mars', natal_chart, transit_chart)
                       if a['quality'] > 0)

    # Jupiter optimism boost
    jupiter_hqs = get_planet_total_hqs('Jupiter', natal_chart, transit_chart)

    # 12th house penalty (dissolution, loss of boundaries)
    twelfth_house_activity = calculate_house_transit_activity(natal_chart, transit_chart, 12)
    twelfth_penalty = twelfth_house_activity * -0.5

    # Neptune to Moon penalty (dissolves boundaries)
    neptune_moon_penalty = abs(get_specific_aspect_dti('Neptune', 'Moon', natal_chart, transit_chart)) * -0.4

    # Synthesize
    resilience_score = (sun_hqs * 0.3 +
                        resilience_from_saturn * 0.25 +
                        mars_positive * 0.2 +
                        jupiter_hqs * 0.15 +
                        twelfth_penalty +
                        neptune_moon_penalty)

    resilience_meter = normalize_hqs(resilience_score)

    return {
        'meter_value': resilience_meter,
        'capacity': 'high' if resilience_meter > 70 else 'moderate' if resilience_meter > 40 else 'low',
        'advice': generate_resilience_advice(resilience_meter)
    }
```

**Interpretation**:
| Range | Capacity | Guidance |
|-------|----------|----------|
| 0-30 | **Vulnerable** | Easily overwhelmed; prioritize self-care, minimize stress |
| 31-50 | **Moderate** | Can handle normal stress but not excessive; pace yourself |
| 51-70 | **Solid** | Good emotional strength; can navigate challenges |
| 71-85 | **Strong** | High capacity; able to support self and others |
| 86-100 | **Exceptional** | Rare emotional fortitude; can handle major challenges |

---

### 5.6 Physical/Action Meters

#### 5.6.1 Physical Energy Meter

**Purpose**: Measures vitality, physical stamina, and readiness for activity/exercise.

**Driving Factors**:
- **Mars**: Primary physical energy planet
- **Sun**: Vitality
- **1st House transits**: Physical body
- **6th House transits**: Health and daily function

**Calculation**:
```python
def calculate_physical_energy(natal_chart, transit_chart, date):
    """Assess physical vitality and energy levels."""

    # Mars energy (primary)
    mars_dti = get_planet_total_dti('Mars', natal_chart, transit_chart)
    mars_hqs = get_planet_total_hqs('Mars', natal_chart, transit_chart)

    # Sun vitality
    sun_dti = get_planet_total_dti('Sun', natal_chart, transit_chart)

    # Jupiter to Mars: energy expansion
    jupiter_mars = get_specific_aspect_hqs('Jupiter', 'Mars', natal_chart, transit_chart)

    # Saturn to Mars: energy restriction (can be disciplined or depleting)
    saturn_mars_hqs = get_specific_aspect_hqs('Saturn', 'Mars', natal_chart, transit_chart)

    # 1st house activity (physical body)
    first_house_dti = calculate_house_transit_activity(natal_chart, transit_chart, 1)

    # Calculate intensity
    energy_intensity = (mars_dti * 0.5 +
                        sun_dti * 0.3 +
                        first_house_dti * 0.2)

    # Calculate quality
    energy_quality = (mars_hqs * 0.4 +
                      jupiter_mars * 0.3 +
                      saturn_mars_hqs * 0.2)

    energy_meter = normalize_with_soft_ceiling(energy_intensity, DTI_MAX_PHYSICAL, 100)
    quality_meter = normalize_hqs(energy_quality)

    return {
        'energy_level': energy_meter,
        'quality': quality_meter,
        'interpretation': interpret_physical_energy(energy_meter, quality_meter),
        'exercise_recommendation': recommend_exercise(energy_meter, quality_meter)
    }
```

**Interpretation Matrix**:
| Energy | Quality | State | Recommendations |
|--------|---------|-------|----------------|
| Low | Any | **Low Energy** | Rest, gentle movement, sleep |
| Moderate | High | **Steady** | Regular exercise, moderate intensity |
| Moderate | Low | **Sluggish** | Light movement to stimulate, avoid overexertion |
| High | High | **Vigorous** | Ideal for intense exercise, physical projects |
| High | Low | **Agitated** | Channelneeded; beware overexertion or accidents |
| Very High | High | **Peak** | Exceptional stamina; athletic performance favored |
| Very High | Low | **Restless** | High energy but frustrated; safe outlets crucial |

**Display Example**:
```
╔════════════════════════════════════╗
║  ⚡ PHYSICAL ENERGY                ║
║  Level:   ████████░░ 78/100        ║
║  Quality: ██████████ 88/100        ║
║                                    ║
║  State: VIGOROUS                   ║
║                                    ║
║  ✓ Mars △ Sun (+45)                ║
║    Excellent vitality and drive.   ║
║                                    ║
║  ✓ Jupiter ⚹ Mars (+32)            ║
║    Energy expansive and optimistic.║
║                                    ║
║  Exercise: IDEAL TIME              ║
║  Perfect for intense workouts,     ║
║  sports, physical challenges.      ║
║  You'll feel strong and resilient. ║
╚════════════════════════════════════╝
```

#### 5.6.2 Conflict Risk Meter

**Purpose**: Measures likelihood of arguments, accidents, and aggressive encounters.

**Driving Factors**:
- **Mars hard aspects**: Especially to Sun, Moon, Mercury, Ascendant
- **Uranus hard aspects**: Sudden disruptions, accidents
- **Pluto hard aspects**: Power struggles
- **8th house transits**: Intensity and control issues

**Calculation**:
```python
def calculate_conflict_risk(natal_chart, transit_chart, date):
    """Assess risk of conflict, accidents, and aggression."""

    # Mars hard aspects (primary factor)
    mars_aspects = get_planet_aspects('Mars', natal_chart, transit_chart)
    mars_conflict = sum(abs(a['contribution']) for a in mars_aspects if a['quality'] < 0)

    # Uranus hard aspects (suddenness, accidents)
    uranus_aspects = get_planet_aspects('Uranus', natal_chart, transit_chart)
    uranus_risk = sum(abs(a['contribution']) for a in uranus_aspects if a['quality'] < 0) * 1.2

    # Pluto hard aspects (power struggles)
    pluto_aspects = get_planet_aspects('Pluto', natal_chart, transit_chart)
    pluto_risk = sum(abs(a['contribution']) for a in pluto_aspects if a['quality'] < 0) * 0.8

    # 7th house hard transits (relationship conflict)
    seventh_house_challenging = calculate_house_challenging_transits(natal_chart, transit_chart, 7)

    # Total risk
    total_risk = mars_conflict + uranus_risk + pluto_risk + seventh_house_challenging

    risk_meter = normalize_with_soft_ceiling(total_risk, CONFLICT_RISK_MAX, 100)

    # Identify primary risk type
    risk_breakdown = {
        'mars': mars_conflict,
        'uranus': uranus_risk,
        'pluto': pluto_risk,
        'relationship': seventh_house_challenging
    }
    primary_risk = max(risk_breakdown, key=risk_breakdown.get)

    return {
        'meter_value': risk_meter,
        'primary_risk_type': primary_risk,
        'specific_risks': analyze_specific_risks(natal_chart, transit_chart),
        'mitigation_advice': generate_conflict_mitigation(risk_meter, primary_risk)
    }
```

**Interpretation**:
| Range | Risk Level | Guidance |
|-------|-----------|----------|
| 0-20 | **Low** | Normal interactions; no special precautions |
| 21-40 | **Mild** | Minor irritations possible; practice patience |
| 41-60 | **Moderate** | Noticeable friction; avoid provocative situations |
| 61-80 | **High** | Elevated conflict risk; choose battles, drive carefully |
| 81-100 | **Very High** | Major conflict potential; minimize risk exposure, stay calm |

**Risk Type Guidance**:
- **Mars-dominant**: Anger, impulsiveness → Count to 10, avoid confrontations
- **Uranus-dominant**: Accidents, sudden events → Drive carefully, double-check details
- **Pluto-dominant**: Power struggles, manipulation → Set boundaries, don't engage in control games
- **Relationship (7th)**: Partnership conflict → Communicate clearly, seek mediation if needed

#### 5.6.3 Motivation & Drive Meter

**Purpose**: Measures ambition, initiative, and will to pursue goals.

**Driving Factors**:
- **Mars**: Action and assertion
- **Sun**: Willpower and identity-driven motivation
- **Jupiter**: Enthusiasm and expansion desire
- **10th House transits**: Career ambition
- **Saturn aspects**: Discipline (positive) vs. discouragement (negative)

**Calculation**:
```python
def calculate_motivation_drive(natal_chart, transit_chart, date):
    """Assess initiative, ambition, and drive."""

    # Mars drive
    mars_dti = get_planet_total_dti('Mars', natal_chart, transit_chart)
    mars_hqs = get_planet_total_hqs('Mars', natal_chart, transit_chart)

    # Sun willpower
    sun_dti = get_planet_total_dti('Sun', natal_chart, transit_chart)

    # Jupiter enthusiasm
    jupiter_to_sun = get_specific_aspect_hqs('Jupiter', 'Sun', natal_chart, transit_chart)
    jupiter_to_mars = get_specific_aspect_hqs('Jupiter', 'Mars', natal_chart, transit_chart)
    jupiter_boost = jupiter_to_sun + jupiter_to_mars

    # Saturn discipline vs. discouragement
    saturn_to_mars = get_specific_aspect_hqs('Saturn', 'Mars', natal_chart, transit_chart)
    saturn_to_sun = get_specific_aspect_hqs('Saturn', 'Sun', natal_chart, transit_chart)
    saturn_factor = (saturn_to_mars + saturn_to_sun) * 0.5  # Can be either

    # 10th house career ambition
    tenth_house_activity = calculate_house_transit_activity(natal_chart, transit_chart, 10)

    # Calculate drive intensity
    drive_intensity = (mars_dti * 0.4 +
                       sun_dti * 0.3 +
                       tenth_house_activity * 0.2)

    # Calculate drive quality (enthusiasm vs. frustration)
    drive_quality = (mars_hqs * 0.3 +
                     jupiter_boost * 0.4 +
                     saturn_factor * 0.3)

    drive_meter = normalize_with_soft_ceiling(drive_intensity, DTI_MAX_DRIVE, 100)
    quality_meter = normalize_hqs(drive_quality)

    return {
        'drive_level': drive_meter,
        'quality': quality_meter,
        'interpretation': interpret_motivation(drive_meter, quality_meter),
        'goal_recommendation': recommend_goal_action(drive_meter, quality_meter)
    }
```

**Interpretation Matrix**:
| Drive | Quality | State | Recommendations |
|-------|---------|-------|----------------|
| Low | Any | **Low Motivation** | Rest period; don't force action, wait for renewed energy |
| Moderate | High | **Steady Progress** | Good for consistent effort, routine work |
| Moderate | Low | **Frustrated** | Desire to act but obstacles; adjust approach, be patient |
| High | High | **Highly Motivated** | Excellent for ambitious goals, starting projects |
| High | Low | **Striving/Blocked** | High ambition but facing resistance; persist strategically |
| Very High | High | **Peak Ambition** | Rare; exceptional window for major initiatives |
| Very High | Low | **Driven but Thwarted** | Intense desire meeting major obstacles; careful not to burn out |

---

### 5.7 Life Domain Meters

#### 5.7.1 Career & Ambition Meter

**Purpose**: Measures focus, opportunity, and recognition in professional life.

**Driving Factors**:
- **10th House transits**: Career house
- **Midheaven (MC) aspects**: Public standing
- **Sun aspects**: Identity and recognition
- **Saturn aspects**: Responsibility, authority
- **Jupiter aspects**: Growth, opportunity

**Calculation**:
```python
def calculate_career_ambition(natal_chart, transit_chart, date):
    """Assess career focus and opportunity."""

    # 10th house activity
    tenth_house_dti = calculate_house_transit_activity(natal_chart, transit_chart, 10)
    tenth_house_hqs = calculate_house_transit_hqs(natal_chart, transit_chart, 10)

    # MC aspects
    mc_dti = get_point_total_dti('Midheaven', natal_chart, transit_chart)
    mc_hqs = get_point_total_hqs('Midheaven', natal_chart, transit_chart)

    # Saturn (responsibility, tests, achievement)
    saturn_tenth = get_planet_aspects_to_house('Saturn', natal_chart, transit_chart, 10)
    saturn_mc = get_specific_aspect_hqs('Saturn', 'Midheaven', natal_chart, transit_chart)
    saturn_career = saturn_tenth + saturn_mc

    # Jupiter (opportunity, expansion)
    jupiter_tenth = get_planet_aspects_to_house('Jupiter', natal_chart, transit_chart, 10)
    jupiter_mc = get_specific_aspect_hqs('Jupiter', 'Midheaven', natal_chart, transit_chart)
    jupiter_career = jupiter_tenth + jupiter_mc

    # Sun (recognition)
    sun_mc = get_specific_aspect_hqs('Sun', 'Midheaven', natal_chart, transit_chart)

    # Calculate intensity
    career_intensity = (tenth_house_dti * 0.4 +
                        mc_dti * 0.3 +
                        abs(saturn_career) * 0.2 +
                        abs(jupiter_career) * 0.1)

    # Calculate opportunity quality
    career_quality = (tenth_house_hqs * 0.3 +
                      mc_hqs * 0.2 +
                      saturn_career * 0.25 +  # Can be challenge or achievement
                      jupiter_career * 0.15 +
                      sun_mc * 0.1)

    career_meter = normalize_with_soft_ceiling(career_intensity, DTI_MAX_CAREER, 100)
    opportunity_meter = normalize_hqs(career_quality)

    return {
        'career_focus': career_meter,
        'opportunity_quality': opportunity_meter,
        'phase': identify_career_phase(career_meter, opportunity_meter),
        'advice': generate_career_advice(career_meter, opportunity_meter, natal_chart, transit_chart)
    }
```

**Career Phase Interpretation**:
| Focus | Opportunity | Phase | Guidance |
|-------|------------|-------|----------|
| Low | Any | **Background** | Career not emphasized; focus elsewhere |
| Moderate | High | **Growth** | Good time for advancement, asking for more |
| Moderate | Low | **Challenge** | Extra effort required; prove yourself |
| High | High | **Breakthrough** | Major career opportunity; act on ambitions |
| High | Low | **Pressure** | High demands, recognition but also tests; persevere |
| Very High | High | **Peak Recognition** | Rare; career-defining moment; major achievement |
| Very High | Low | **Crisis/Reckoning** | Intense career challenge; restructuring needed |

#### 5.7.2 Opportunity Window Meter

**Purpose**: Measures overall luck, expansion potential, and timing for new ventures.

**Driving Factors**:
- **Jupiter transits**: Primary luck and expansion planet
- **Venus transits**: Attracting ease and resources
- **Sun transits**: Vitality and visibility
- **Nodes**: Karmic timing
- **2nd House**: Financial resources
- **11th House**: Networks and support

**Calculation**:
```python
def calculate_opportunity_window(natal_chart, transit_chart, date):
    """Assess timing for expansion and new ventures."""

    # Jupiter (primary opportunity planet)
    jupiter_dti = get_planet_total_dti('Jupiter', natal_chart, transit_chart)
    jupiter_hqs = get_planet_total_hqs('Jupiter', natal_chart, transit_chart)

    # Venus (attraction, ease)
    venus_hqs = get_planet_total_hqs('Venus', natal_chart, transit_chart)

    # North Node conjunctions (karmic opportunity)
    north_node_dti = get_point_total_dti('North Node', natal_chart, transit_chart)

    # 11th house (networks, support)
    eleventh_house_hqs = calculate_house_transit_hqs(natal_chart, transit_chart, 11)

    # 2nd house (financial resources)
    second_house_hqs = calculate_house_transit_hqs(natal_chart, transit_chart, 2)

    # Sun (visibility, confidence)
    sun_hqs = get_planet_total_hqs('Sun', natal_chart, transit_chart)

    # Calculate opportunity intensity
    opportunity_intensity = (jupiter_dti * 0.5 +
                             north_node_dti * 0.3 +
                             jupiter_hqs * 0.2)  # Strong Jupiter aspects count as intensity

    # Calculate opportunity quality
    opportunity_quality = (jupiter_hqs * 0.4 +
                           venus_hqs * 0.2 +
                           eleventh_house_hqs * 0.15 +
                           second_house_hqs * 0.15 +
                           sun_hqs * 0.1)

    opportunity_meter = normalize_with_soft_ceiling(opportunity_intensity, DTI_MAX_OPPORTUNITY, 100)
    quality_meter = normalize_hqs(opportunity_quality)

    # Check for particularly auspicious alignments
    auspicious_markers = detect_auspicious_alignments(natal_chart, transit_chart)

    return {
        'opportunity_level': opportunity_meter,
        'quality': quality_meter,
        'timing': assess_opportunity_timing(opportunity_meter, quality_meter),
        'auspicious_markers': auspicious_markers,
        'advice': generate_opportunity_advice(opportunity_meter, quality_meter)
    }
```

**Timing Interpretation**:
| Opportunity | Quality | Timing | Action Guidance |
|------------|---------|--------|----------------|
| Low | Any | **Not Emphasized** | Normal period; maintain, don't force expansion |
| Moderate | High | **Favorable** | Good time to pursue opportunities that arise |
| Moderate | Low | **Mixed** | Some openings but proceed carefully; research first |
| High | High | **Excellent** | Strong timing for launches, investments, risk-taking |
| High | Low | **Inflated** | Enthusiasm present but beware overconfidence or deception |
| Very High | High | **Golden** | Rare; exceptional opportunity window; act decisively |
| Very High | Low | **Illusory** | False opportunities or overreach risk; extra discernment needed |

**Auspicious Markers** (bonus indicators):
- Jupiter trine Sun: +15 to opportunity
- Venus trine Jupiter: +12 to opportunity
- North Node conjunct Jupiter: +20 to opportunity
- Jupiter in natal 2nd, 9th, or 11th house: +10 to opportunity

#### 5.7.3 Challenge & Lesson Intensity Meter

**Purpose**: Measures the strength of difficulties, tests, and growth-through-adversity themes.

**Driving Factors**:
- **Saturn transits**: Primary challenge and lesson planet
- **Pluto transits**: Transformation through breakdown
- **Chiron transits**: Healing through wounding
- **12th House transits**: Isolation, endings
- **South Node**: Karmic release

**Calculation**:
```python
def calculate_challenge_intensity(natal_chart, transit_chart, date):
    """Assess difficulty and lesson intensity."""

    # Saturn (primary challenge planet)
    saturn_dti = get_planet_total_dti('Saturn', natal_chart, transit_chart)
    saturn_hqs = get_planet_total_hqs('Saturn', natal_chart, transit_chart)

    # Pluto (transformation, breakdown)
    pluto_dti = get_planet_total_dti('Pluto', natal_chart, transit_chart)

    # Chiron (wounding and healing)
    chiron_dti = get_planet_total_dti('Chiron', natal_chart, transit_chart)

    # 12th house (isolation, loss)
    twelfth_house_challenging = calculate_house_challenging_transits(natal_chart, transit_chart, 12)

    # South Node (karmic release, often through difficulty)
    south_node_dti = get_point_total_dti('South Node', natal_chart, transit_chart)

    # Calculate challenge intensity
    challenge_intensity = (saturn_dti * 0.4 +
                           pluto_dti * 0.3 +
                           chiron_dti * 0.15 +
                           twelfth_house_challenging * 0.1 +
                           south_node_dti * 0.05)

    # Note: We use Saturn HQS as "quality" but invert the meaning
    # Negative Saturn = obvious challenges
    # Positive Saturn = constructive discipline (still effortful but rewarding)
    challenge_quality = -saturn_hqs  # Invert: negative HQS becomes "harder" challenge

    challenge_meter = normalize_with_soft_ceiling(challenge_intensity, DTI_MAX_CHALLENGE, 100)

    # Identify lesson type
    lesson_themes = identify_lesson_themes(natal_chart, transit_chart)

    return {
        'challenge_level': challenge_meter,
        'lesson_themes': lesson_themes,
        'growth_potential': calculate_growth_potential(challenge_meter, lesson_themes),
        'support_advice': generate_challenge_support(challenge_meter, lesson_themes)
    }
```

**Challenge Interpretation**:
| Challenge Level | Meaning | Guidance |
|----------------|---------|----------|
| 0-20 | **Minimal** | Few major tests; relative ease |
| 21-40 | **Mild** | Some obstacles; manageable with effort |
| 41-60 | **Moderate** | Clear challenges; discipline and persistence required |
| 61-80 | **Significant** | Major tests; resilience crucial; support helpful |
| 81-100 | **Intense** | Rare; life-defining challenges; deep growth potential; seek support |

**Lesson Theme Examples**:
- **Saturn to Sun**: Identity tests, authority issues, self-discipline
- **Saturn to Moon**: Emotional maturity, dealing with limitations, responsibility
- **Pluto to Venus**: Relationship transformation, confronting control/power in love
- **Saturn in 4th**: Family responsibility, home restructuring
- **Chiron to Ascendant**: Healing identity wounds, self-acceptance

#### 5.7.4 Transformation Pressure Meter

**Purpose**: Measures the intensity of deep change, upheaval, and evolutionary pressure.

**Driving Factors**:
- **Pluto transits**: Death/rebirth, power, deep psychological change
- **Uranus transits**: Sudden upheaval, liberation, revolution
- **Neptune transits**: Dissolution, spiritual awakening
- **8th House transits**: Transformation, crisis, shared resources

**Calculation**:
```python
def calculate_transformation_pressure(natal_chart, transit_chart, date):
    """Assess evolutionary and upheaval pressure."""

    # Pluto (deepest transformation)
    pluto_dti = get_planet_total_dti('Pluto', natal_chart, transit_chart)
    pluto_hqs = get_planet_total_hqs('Pluto', natal_chart, transit_chart)

    # Uranus (sudden change, breakthroughs/breakdowns)
    uranus_dti = get_planet_total_dti('Uranus', natal_chart, transit_chart)
    uranus_hqs = get_planet_total_hqs('Uranus', natal_chart, transit_chart)

    # Neptune (dissolution, transcendence)
    neptune_dti = get_planet_total_dti('Neptune', natal_chart, transit_chart)

    # 8th house (transformation, crisis)
    eighth_house_activity = calculate_house_transit_activity(natal_chart, transit_chart, 8)

    # Calculate transformation intensity
    transformation_intensity = (pluto_dti * 0.45 +
                                uranus_dti * 0.35 +
                                neptune_dti * 0.15 +
                                eighth_house_activity * 0.05)

    # Transformation quality (is change flowing or violent?)
    transformation_quality = (pluto_hqs * 0.5 +
                              uranus_hqs * 0.5)

    transformation_meter = normalize_with_soft_ceiling(transformation_intensity,
                                                       DTI_MAX_TRANSFORMATION, 100)
    quality_meter = normalize_hqs(transformation_quality)

    # Identify specific transformation type
    transformation_type = identify_transformation_type(natal_chart, transit_chart)

    return {
        'pressure_level': transformation_meter,
        'quality': quality_meter,
        'type': transformation_type,
        'interpretation': interpret_transformation(transformation_meter, quality_meter, transformation_type),
        'advice': generate_transformation_guidance(transformation_meter, quality_meter)
    }
```

**Transformation Interpretation Matrix**:
| Pressure | Quality | Experience | Guidance |
|---------|---------|-----------|----------|
| Low | Any | **Stable** | No major transformation; integrate past changes |
| Moderate | High | **Evolutionary** | Gradual positive transformation; flow with change |
| Moderate | Low | **Disruptive** | Uncomfortable change; resistance creates friction |
| High | High | **Breakthrough** | Major positive transformation; trust the process |
| High | Low | **Crisis** | Intense upheaval; survival mode; seek support |
| Very High | High | **Quantum Leap** | Rare; profound positive transformation; life-changing |
| Very High | Low | **Breakdown** | Rare; major life crisis; complete restructuring; therapy recommended |

**Transformation Types**:
- **Pluto-dominant**: Psychological, power dynamics, death/rebirth
- **Uranus-dominant**: Sudden change, liberation, awakening
- **Neptune-dominant**: Spiritual, dissolution of ego, confusion/enlightenment
- **8th House**: Resources, intimacy, shared power

---

### 5.8 Specialized Meters

#### 5.8.1 Intuition & Spirituality Meter

**Purpose**: Measures psychic sensitivity, spiritual awareness, and connection to subtle realms.

**Driving Factors**:
- **Neptune transits**: Primary spirituality planet
- **Moon transits**: Intuitive receptivity
- **12th House transits**: Transcendence, connection to collective unconscious
- **Pisces/Cancer/Scorpio emphasis**: Water signs enhance intuition

**Calculation**:
```python
def calculate_intuition_spirituality(natal_chart, transit_chart, date):
    """Assess intuitive and spiritual sensitivity."""

    # Neptune (spirituality, psychic openness)
    neptune_dti = get_planet_total_dti('Neptune', natal_chart, transit_chart)

    # Moon (intuitive receptivity)
    moon_to_neptune = get_specific_aspect_dti('Neptune', 'Moon', natal_chart, transit_chart)
    moon_sensitivity = moon_to_neptune * 1.4  # Moon-Neptune is highly intuitive

    # 12th house (spiritual, transcendent)
    twelfth_house_dti = calculate_house_transit_activity(natal_chart, transit_chart, 12)

    # 9th house (higher mind, spirituality)
    ninth_house_dti = calculate_house_transit_activity(natal_chart, transit_chart, 9)

    # Uranus to Neptune or Moon (sudden spiritual openings)
    uranus_spiritual = (get_specific_aspect_dti('Uranus', 'Neptune', natal_chart, transit_chart) +
                       get_specific_aspect_dti('Uranus', 'Moon', natal_chart, transit_chart))

    # Calculate intuition intensity
    intuition_intensity = (neptune_dti * 0.4 +
                           moon_sensitivity * 0.3 +
                           twelfth_house_dti * 0.15 +
                           ninth_house_dti * 0.1 +
                           uranus_spiritual * 0.05)

    intuition_meter = normalize_with_soft_ceiling(intuition_intensity, DTI_MAX_INTUITION, 100)

    return {
        'meter_value': intuition_meter,
        'sensitivity_level': assess_sensitivity(intuition_meter),
        'practices_favored': recommend_spiritual_practices(intuition_meter, natal_chart, transit_chart),
        'grounding_advice': generate_grounding_advice(intuition_meter)
    }
```

**Interpretation**:
| Level | Sensitivity | Experience | Practices |
|-------|------------|-----------|-----------|
| 0-30 | **Low** | Grounded, practical, less receptive | Meditation basics, start small |
| 31-50 | **Moderate** | Occasional intuitive hits | Journaling dreams, nature connection |
| 51-70 | **Heightened** | Frequent intuition, synchronicities | Meditation, divination, energy work |
| 71-85 | **High** | Strong psychic sensitivity | Deep spiritual practice, protection work |
| 86-100 | **Extreme** | Overwhelming sensitivity, boundary loss | Grounding essential, limit stimulation |

#### 5.8.2 Innovation & Breakthroughs Meter

**Purpose**: Measures potential for sudden insights, inventions, and paradigm shifts.

**Driving Factors**:
- **Uranus transits**: Awakening, innovation, sudden change
- **Mercury aspects**: Mental breakthroughs
- **11th House**: Future vision, technology
- **Aquarius emphasis**: Innovative sign

**Calculation**:
```python
def calculate_innovation_breakthroughs(natal_chart, transit_chart, date):
    """Assess potential for sudden insights and innovation."""

    # Uranus (innovation, breakthroughs)
    uranus_dti = get_planet_total_dti('Uranus', natal_chart, transit_chart)

    # Uranus-Mercury (mental breakthroughs)
    uranus_mercury = get_specific_aspect_dti('Uranus', 'Mercury', natal_chart, transit_chart) * 1.5

    # Uranus-Sun (identity breakthroughs, awakening)
    uranus_sun = get_specific_aspect_dti('Uranus', 'Sun', natal_chart, transit_chart) * 1.2

    # 11th house (future, innovation, groups)
    eleventh_house_dti = calculate_house_transit_activity(natal_chart, transit_chart, 11)

    # Jupiter-Uranus (expansion of innovation)
    jupiter_uranus = get_specific_aspect_dti('Jupiter', 'Uranus', natal_chart, transit_chart)

    # Calculate innovation potential
    innovation_intensity = (uranus_dti * 0.4 +
                            uranus_mercury * 0.3 +
                            uranus_sun * 0.15 +
                            eleventh_house_dti * 0.1 +
                            jupiter_uranus * 0.05)

    innovation_meter = normalize_with_soft_ceiling(innovation_intensity, DTI_MAX_INNOVATION, 100)

    # Identify breakthrough type
    breakthrough_area = identify_breakthrough_area(natal_chart, transit_chart)

    return {
        'meter_value': innovation_meter,
        'breakthrough_potential': assess_breakthrough_potential(innovation_meter),
        'area': breakthrough_area,
        'advice': generate_innovation_advice(innovation_meter, breakthrough_area)
    }
```

**Interpretation**:
| Level | Potential | Experience | Guidance |
|-------|----------|-----------|----------|
| 0-30 | **Low** | Conventional thinking | Routine, stability favored |
| 31-50 | **Moderate** | Some new ideas | Open to alternatives |
| 51-70 | **Active** | Frequent insights | Experiment, try new approaches |
| 71-85 | **High** | Breakthrough territory | Major insights possible; document ideas |
| 86-100 | **Revolutionary** | Paradigm-shifting potential | Life-changing realization; act on it |

**Breakthrough Areas**:
- Mercury: Communication, learning, writing
- Sun: Identity, life direction
- Moon: Emotional patterns, needs
- Venus: Relationships, values
- Mars: Action methods, assertiveness

#### 5.8.3 Karmic Lessons Meter

**Purpose**: Measures intensity of soul-level lessons and past-pattern resolution.

**Driving Factors**:
- **Nodes (North/South) transits**: Karmic axis
- **Chiron transits**: Healing old wounds
- **Saturn transits**: Karmic responsibility
- **12th House**: Past, unconscious patterns
- **4th House**: Family karma

**Calculation**:
```python
def calculate_karmic_lessons(natal_chart, transit_chart, date):
    """Assess karmic lesson and healing intensity."""

    # North Node transits (evolutionary path)
    north_node_dti = get_point_total_dti('North Node', natal_chart, transit_chart)

    # South Node transits (release, past patterns)
    south_node_dti = get_point_total_dti('South Node', natal_chart, transit_chart)

    # Chiron (wounded healer, core wounds)
    chiron_dti = get_planet_total_dti('Chiron', natal_chart, transit_chart)

    # Saturn (karmic lessons, responsibility)
    saturn_karmic = get_planet_total_dti('Saturn', natal_chart, transit_chart) * 0.6  # Partial weight

    # 12th house (past, unconscious)
    twelfth_house_dti = calculate_house_transit_activity(natal_chart, transit_chart, 12)

    # 4th house (family, roots)
    fourth_house_dti = calculate_house_transit_activity(natal_chart, transit_chart, 4)

    # Calculate karmic intensity
    karmic_intensity = (north_node_dti * 0.25 +
                        south_node_dti * 0.25 +
                        chiron_dti * 0.25 +
                        saturn_karmic * 0.15 +
                        twelfth_house_dti * 0.05 +
                        fourth_house_dti * 0.05)

    karmic_meter = normalize_with_soft_ceiling(karmic_intensity, DTI_MAX_KARMIC, 100)

    # Identify specific lesson themes
    lesson_themes = identify_karmic_themes(natal_chart, transit_chart)

    return {
        'meter_value': karmic_meter,
        'lesson_intensity': assess_lesson_intensity(karmic_meter),
        'themes': lesson_themes,
        'guidance': generate_karmic_guidance(karmic_meter, lesson_themes),
        'healing_opportunities': identify_healing_opportunities(natal_chart, transit_chart)
    }
```

**Interpretation**:
| Level | Intensity | Experience | Guidance |
|-------|----------|-----------|----------|
| 0-30 | **Minimal** | Few soul-level lessons active | Integration time; live your learning |
| 31-50 | **Moderate** | Some patterns surfacing | Notice repeating themes; journal |
| 51-70 | **Active** | Clear karmic themes | Therapy, shadow work, healing practices |
| 71-85 | **Strong** | Major soul lessons | Deep healing work; past-life themes may emerge |
| 86-100 | **Profound** | Intense karmic reckoning | Life-purpose clarity; major healing; support crucial |

**Karmic Theme Examples**:
- North Node conjunct Venus: Learning to love and value self
- South Node conjunct Sun: Releasing old identity
- Chiron conjunct Moon: Healing mother wound, emotional neglect
- Saturn in 4th: Resolving family karma

#### 5.8.4 Social & Collective Energy Meter

**Purpose**: Measures connection to collective currents, social consciousness, and zeitgeist.

**Driving Factors**:
- **Outer planets (Uranus/Neptune/Pluto)**: Generational themes
- **11th House transits**: Groups, humanity, social causes
- **Aquarius/Pisces emphasis**: Collective signs
- **Saturn-Jupiter cycle**: Social structures

**Calculation**:
```python
def calculate_social_collective_energy(natal_chart, transit_chart, date):
    """Assess connection to collective and social currents."""

    # Outer planets (slow-moving, affect generations)
    uranus_dti = get_planet_total_dti('Uranus', natal_chart, transit_chart)
    neptune_dti = get_planet_total_dti('Neptune', natal_chart, transit_chart)
    pluto_dti = get_planet_total_dti('Pluto', natal_chart, transit_chart)

    outer_planet_total = uranus_dti + neptune_dti + pluto_dti

    # 11th house (groups, social consciousness)
    eleventh_house_dti = calculate_house_transit_activity(natal_chart, transit_chart, 11)

    # Jupiter-Saturn cycle (social change markers)
    jupiter_saturn_aspects = get_specific_aspect_dti('Jupiter', 'Saturn', natal_chart, transit_chart)

    # Aquarius/Pisces emphasis in transits
    aquarius_pisces_emphasis = calculate_sign_emphasis(transit_chart, ['Aquarius', 'Pisces'])

    # Calculate collective connection
    collective_intensity = (outer_planet_total * 0.4 +
                            eleventh_house_dti * 0.3 +
                            jupiter_saturn_aspects * 0.2 +
                            aquarius_pisces_emphasis * 0.1)

    collective_meter = normalize_with_soft_ceiling(collective_intensity, DTI_MAX_COLLECTIVE, 100)

    # Identify collective themes
    collective_themes = identify_collective_themes(transit_chart, date)

    return {
        'meter_value': collective_meter,
        'connection_level': assess_collective_connection(collective_meter),
        'themes': collective_themes,
        'social_guidance': generate_social_guidance(collective_meter, collective_themes),
        'activism_potential': assess_activism_timing(collective_meter, natal_chart, transit_chart)
    }
```

**Interpretation**:
| Level | Connection | Experience | Guidance |
|-------|-----------|-----------|----------|
| 0-30 | **Personal Focus** | Individual concerns dominate | Focus on personal life |
| 31-50 | **Aware** | Notice social trends | Stay informed, contribute moderately |
| 51-70 | **Engaged** | Feel collective currents | Join groups, social causes |
| 71-85 | **Activated** | Strong social consciousness | Activism, community leadership |
| 86-100 | **Revolutionary** | Embodying collective change | Major social contribution; agent of change |

---

## 6. Explainability Architecture

The three-tier system ensures users at all levels understand their meter readings.

### 6.1 Tier 1: Top Contributing Aspects

**Purpose**: Immediate understanding of what's driving a meter reading.

**Display Format**:
```python
class MeterExplanation:
    def tier1_explanation(self, meter_value, top_aspects):
        """
        Simple, visual explanation.

        Structure:
        - Current meter value with visual gauge
        - Top 3-5 contributing aspects
        - Each aspect shows:
          * Aspect description
          * Contribution value (signed)
          * Orb and status
          * Plain-language interpretation
        - Overall interpretation
        - Actionable advice
        """
        return {
            'meter_value': meter_value,
            'visual': generate_gauge_visual(meter_value),
            'state_label': get_state_label(meter_value),
            'top_contributors': [
                {
                    'aspect': 'Transit Saturn square Natal Sun',
                    'symbol': '♄ □ ☉',
                    'contribution': -45,
                    'orb': '2°15\'',
                    'status': 'applying',
                    'interpretation': 'Authority challenges and self-discipline tests. Your sense of identity and confidence may feel constrained.',
                    'timeline': 'Building for next 3 days, exact on Oct 29'
                },
                # ... more aspects
            ],
            'baseline_comparison': {
                'your_typical': 65,
                'current': meter_value,
                'delta': meter_value - 65,
                'percentile': '15th percentile (lower than 85% of your days)'
            },
            'interpretation': 'Your Physical Energy is currently lower than usual due to challenging Saturn aspects. This is a time for rest and disciplined recovery rather than pushing hard.',
            'advice': [
                'Prioritize rest and recovery',
                'Avoid overcommitment',
                'Focus on steady, sustainable effort',
                'Challenge will ease after Oct 29'
            ]
        }
```

**Visual Example**:
```
╔════════════════════════════════════════════════╗
║  ⚡ PHYSICAL ENERGY                            ║
║  ████░░░░░░░░░░░░░░ 42/100                     ║
║  State: SLUGGISH                               ║
║                                                ║
║  🔻 Top Challenges:                            ║
║  ────────────────────────────────────────────  ║
║  ⚠️  Saturn □ Sun (-45)                        ║
║      2°15' orb | Applying                      ║
║      Authority challenges, self-discipline     ║
║      tests. Identity and confidence feel       ║
║      constrained. Exact in 3 days (Oct 29).    ║
║                                                ║
║  ⚠️  Mars ☍ Mars (-32)                         ║
║      4°30' orb | Separating                    ║
║      Energy scattered, frustration easing.     ║
║      Push-pull between action and restraint.   ║
║                                                ║
║  🔺 Supporting Factors:                        ║
║  ────────────────────────────────────────────  ║
║  ✓  Jupiter ⚹ Sun (+18)                        ║
║      Optimism and support, but overwhelmed     ║
║      by challenges.                            ║
║                                                ║
║  📊 Compared to Your Baseline:                 ║
║  Your typical: 65/100                          ║
║  Current: 42/100 (-23)                         ║
║  Percentile: 15th (lower than 85% of days)     ║
║                                                ║
║  💡 Interpretation:                            ║
║  Your physical energy is significantly lower   ║
║  than usual due to challenging Saturn aspects. ║
║  This is a time for rest and disciplined       ║
║  recovery rather than pushing hard.            ║
║                                                ║
║  🎯 Advice:                                    ║
║  • Prioritize rest and recovery                ║
║  • Avoid overcommitment                        ║
║  • Focus on steady, sustainable effort         ║
║  • Challenge will ease after Oct 29            ║
╚════════════════════════════════════════════════╝
        [View Detailed Breakdown] [7-Day Forecast]
```

### 6.2 Tier 2: Mathematical Breakdown

**Purpose**: For users who want to understand the calculation mechanics.

**Display Format**:
```python
def tier2_explanation(self, meter_name, natal_chart, transit_chart, date):
    """
    Detailed mathematical breakdown.

    Shows:
    - Complete DTI and HQS calculations
    - All active aspects (not just top ones)
    - Component scores (W, P, Q for each)
    - Normalization process
    - Historical context
    """

    # Calculate all aspects
    all_aspects = calculate_all_aspects(natal_chart, transit_chart, date)

    # Break down each aspect
    aspect_breakdowns = []
    total_dti = 0
    total_hqs = 0

    for aspect in all_aspects:
        W_i = aspect['weightage']
        P_i = aspect['transit_power']
        Q_i = aspect['quality']

        dti_contribution = W_i * P_i
        hqs_contribution = W_i * P_i * Q_i

        total_dti += dti_contribution
        total_hqs += hqs_contribution

        aspect_breakdowns.append({
            'aspect': aspect['description'],
            'components': {
                'W_i': {
                    'value': W_i,
                    'calculation': f"({aspect['planet_base']} + {aspect['dignity']}) × {aspect['house_mult']} × {aspect['sensitivity']}"
                },
                'P_i': {
                    'value': P_i,
                    'calculation': f"{aspect['aspect_base']} × {aspect['orb_factor']:.2f} × {aspect['direction_mod']} × {aspect['station_mod']} × {aspect['transit_weight']}"
                },
                'Q_i': {
                    'value': Q_i,
                    'rationale': aspect['quality_rationale']
                }
            },
            'dti_contribution': dti_contribution,
            'hqs_contribution': hqs_contribution
        })

    # Normalization
    normalized_intensity = normalize_with_soft_ceiling(total_dti, DTI_MAX, 100)
    normalized_harmony = normalize_hqs(total_hqs, HQS_MAX_POSITIVE, HQS_MAX_NEGATIVE)

    return {
        'raw_scores': {
            'total_dti': total_dti,
            'total_hqs': total_hqs
        },
        'normalized_scores': {
            'intensity': normalized_intensity,
            'harmony': normalized_harmony
        },
        'normalization_parameters': {
            'dti_max': DTI_MAX,
            'hqs_max_positive': HQS_MAX_POSITIVE,
            'hqs_max_negative': HQS_MAX_NEGATIVE,
            'source': '99th percentile from 50,000 charts over 25 years'
        },
        'all_aspects': aspect_breakdowns,
        'formula_summary': """
            DTI = Σ(Wᵢ × Pᵢ)
            HQS = Σ(Wᵢ × Pᵢ × Qᵢ)

            Where:
            Wᵢ = (Planet_Base + Dignity + Ruler_Bonus) × House_Mult × Sensitivity
            Pᵢ = Aspect_Base × Orb_Factor × Direction_Mod × Station_Mod × Transit_Weight
            Qᵢ = Quality Factor (+1.0, -1.0, or dynamic for conjunctions)
        """
    }
```

**Visual Example (Expandable Section)**:
```
╔════════════════════════════════════════════════╗
║  📐 MATHEMATICAL BREAKDOWN                     ║
║                                                ║
║  Total DTI = 487.3                             ║
║  Total HQS = -245.8                            ║
║                                                ║
║  Normalization:                                ║
║  DTI_MAX = 1200 (99th percentile)              ║
║  Intensity = (487.3 / 1200) × 100 = 40.6       ║
║                                                ║
║  HQS_MAX_NEGATIVE = 800                        ║
║  Harmony = 50 - (245.8 / 800) × 50 = 34.6      ║
║                                                ║
║  ════════════════════════════════════════════  ║
║  ASPECT CONTRIBUTIONS:                         ║
║  ════════════════════════════════════════════  ║
║                                                ║
║  1. Transit Saturn □ Natal Sun                 ║
║     W_i = (10 + 5) × 3 × 1.0 = 45              ║
║         = (Sun_base + Domicile) × Angular      ║
║                                                ║
║     P_i = 8 × 0.75 × 1.3 × 1.0 × 1.2 = 9.36    ║
║         = Square × Orb(2.25°) × Applying       ║
║           × No_station × Social_planet         ║
║                                                ║
║     Q_i = -1.0 (Square aspect)                 ║
║                                                ║
║     DTI contribution: 45 × 9.36 = 421.2        ║
║     HQS contribution: 421.2 × (-1.0) = -421.2  ║
║                                                ║
║  2. Transit Jupiter △ Natal Venus              ║
║     W_i = (7 + 5) × 2 × 1.0 = 24               ║
║     P_i = 6 × 0.88 × 1.3 × 1.0 × 1.2 = 8.23    ║
║     Q_i = +1.0 (Trine aspect)                  ║
║                                                ║
║     DTI contribution: 24 × 8.23 = 197.5        ║
║     HQS contribution: 197.5 × 1.0 = +197.5     ║
║                                                ║
║  [Expand to see all 8 active aspects]          ║
║                                                ║
║  ════════════════════════════════════════════  ║
║  Historical Context:                           ║
║  Your DTI range over past year: 120 - 950      ║
║  Your HQS range over past year: -600 to +700   ║
║  Current DTI (487) is at 48th percentile       ║
║  Current HQS (-246) is at 28th percentile      ║
║  (More challenging than 72% of your days)      ║
╚════════════════════════════════════════════════╝
```

### 6.3 Tier 3: Historical Context & Predictive (Premium)

**Purpose**: Show how current reading compares to personal history and what's coming.

**Features**:
1. **Personal Percentile Ranking**
   - "Your Mental Clarity is in the **lowest 15%** compared to the past 2 years"

2. **Historical Timeline Comparison**
   - "Last time this meter was this low: **June 2023** during Saturn-Mercury square"
   - Show timeline graph with current reading marked

3. **Pattern Recognition**
   - "You typically experience low Physical Energy during Saturn hard aspects. Average duration: 12 days."

4. **Predictive Forecast**
   - 7-day, 30-day, 90-day meter trends
   - "Physical Energy will peak on **Nov 3** (Jupiter trine Sun exact)"
   - "Next major dip expected **Dec 15-22** (Mars retrograde square Natal Mars)"

5. **Cycle Awareness**
   - "You're currently in a **Saturn square phase** (peaks every ~7 years). Last one: 2016."

**Implementation**:
```python
class HistoricalContextEngine:
    def __init__(self, user_id, natal_chart):
        self.user_id = user_id
        self.natal_chart = natal_chart
        self.historical_db = load_user_history(user_id)

    def get_percentile_ranking(self, meter_name, current_value):
        """Where does current reading rank in user's history?"""
        historical_values = self.historical_db.get_meter_history(meter_name, days=730)  # 2 years
        percentile = scipy.stats.percentileofscore(historical_values, current_value)

        return {
            'percentile': percentile,
            'interpretation': self.interpret_percentile(percentile),
            'historical_range': {
                'min': min(historical_values),
                'max': max(historical_values),
                'mean': np.mean(historical_values),
                'median': np.median(historical_values)
            }
        }

    def find_similar_periods(self, meter_name, current_aspects, threshold=0.8):
        """Find past periods with similar astrological signatures."""
        current_signature = extract_aspect_signature(current_aspects)

        similar_periods = []
        for past_date in self.historical_db.all_dates:
            past_aspects = calculate_aspects(self.natal_chart, get_transit_chart(past_date))
            past_signature = extract_aspect_signature(past_aspects)

            similarity = cosine_similarity(current_signature, past_signature)

            if similarity >= threshold:
                similar_periods.append({
                    'date': past_date,
                    'similarity': similarity,
                    'meter_value': self.historical_db.get_meter_value(meter_name, past_date),
                    'user_notes': self.historical_db.get_user_notes(past_date)
                })

        return sorted(similar_periods, key=lambda x: x['similarity'], reverse=True)[:5]

    def forecast_meter(self, meter_name, days_ahead=30):
        """Predict meter values based on upcoming transits."""
        forecasts = []

        for day in range(1, days_ahead + 1):
            future_date = datetime.now() + timedelta(days=day)
            future_value = calculate_meter(meter_name, self.natal_chart, get_transit_chart(future_date))

            forecasts.append({
                'date': future_date,
                'value': future_value,
                'change_from_today': future_value - current_value
            })

        # Identify peaks and troughs
        peak = max(forecasts, key=lambda x: x['value'])
        trough = min(forecasts, key=lambda x: x['value'])

        return {
            'daily_forecast': forecasts,
            'peak': peak,
            'trough': trough,
            'trend': calculate_trend(forecasts),
            'key_dates': identify_key_transition_dates(forecasts)
        }

    def identify_cycles(self, meter_name):
        """Identify recurring patterns in meter behavior."""
        # Analyze historical data for cycles
        values = self.historical_db.get_meter_history(meter_name, days=3650)  # 10 years

        # FFT to detect periodic cycles
        fft = np.fft.fft(values)
        frequencies = np.fft.fftfreq(len(values))

        # Find dominant cycles
        dominant_frequencies = find_peaks(np.abs(fft))
        cycles = [1/freq for freq in frequencies[dominant_frequencies] if freq > 0]

        # Interpret cycles (e.g., Saturn cycle ~29 years, Jupiter cycle ~12 years)
        interpreted_cycles = interpret_astrological_cycles(cycles)

        return {
            'detected_cycles': cycles,
            'astrological_interpretation': interpreted_cycles,
            'current_phase': determine_current_phase_in_cycle(cycles, values)
        }
```

**Visual Example**:
```
╔════════════════════════════════════════════════╗
║  📊 HISTORICAL CONTEXT & FORECAST              ║
║                                                ║
║  Current Reading: 42/100                       ║
║  Your Typical Range: 55-75                     ║
║  Percentile: 15th (lower than 85% of days)     ║
║                                                ║
║  ════════════════════════════════════════════  ║
║  SIMILAR PAST PERIODS:                         ║
║  ════════════════════════════════════════════  ║
║                                                ║
║  📅 June 2023 (92% similar)                    ║
║     Physical Energy: 38/100                    ║
║     Saturn square Sun (same aspect!)           ║
║     Your notes: "Felt exhausted, took week off"║
║     Duration: 14 days until improvement        ║
║                                                ║
║  📅 September 2021 (87% similar)               ║
║     Physical Energy: 44/100                    ║
║     Saturn opposite Mars                       ║
║     Duration: 10 days                          ║
║                                                ║
║  ════════════════════════════════════════════  ║
║  7-DAY FORECAST:                               ║
║  ════════════════════════════════════════════  ║
║                                                ║
║  Oct 27: 42 → 40 (slight decline)              ║
║  Oct 28: 40 → 38 (approaching exact)           ║
║  Oct 29: 38 (Saturn-Sun exact) ⚠️ TROUGH      ║
║  Oct 30: 38 → 42 (beginning separation)        ║
║  Oct 31: 42 → 47 (improving)                   ║
║  Nov 1:  47 → 54 (significant improvement)     ║
║  Nov 2:  54 → 58 (back to baseline)            ║
║                                                ║
║  📈 TREND: Declining for 3 days, then rising   ║
║                                                ║
║  🔮 KEY INSIGHTS:                              ║
║  • Lowest point: Oct 29 (38/100)               ║
║  • Back to baseline: Nov 2                     ║
║  • Based on past patterns, expect gradual      ║
║    recovery over 5 days                        ║
║  • Next peak: Nov 15 (Jupiter trine Sun)       ║
║                                                ║
║  ════════════════════════════════════════════  ║
║  CYCLE AWARENESS:                              ║
║  ════════════════════════════════════════════  ║
║                                                ║
║  You're in a **Saturn square cycle**           ║
║  • Occurs every ~7 years                       ║
║  • Last occurrence: March 2016                 ║
║  • Theme: Identity restructuring, discipline   ║
║  • Duration: ~3 months (with 3 exact passes)   ║
║  • You're at pass 2 of 3                       ║
║                                                ║
║  Historical pattern: Your Physical Energy      ║
║  drops 15-25 points during Saturn hard         ║
║  aspects to Sun. Average duration: 12 days.    ║
╚════════════════════════════════════════════════╝
```

---





### 7.2 Project Structure

```
astro_meters/
│
├── README.md
├── requirements.txt
├── setup.py
│
├── config/
│   ├── weights.yaml              # All numerical parameters
│   ├── dignities.yaml            # Planetary dignity tables
│   ├── aspects.yaml              # Aspect definitions and orbs
│   └── normalization.yaml        # Calibration parameters
│
├── astro_meters/
│   ├── __init__.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── ephemeris.py          # Swiss Ephemeris wrapper
│   │   ├── natal_chart.py        # Natal chart calculation and storage
│   │   ├── transits.py           # Transit calculation
│   │   ├── aspects.py            # Aspect detection and analysis
│   │   ├── scoring.py            # DTI and HQS calculation engine
│   │   └── normalization.py      # Normalization and calibration
│   │
│   ├── calculators/
│   │   ├── __init__.py
│   │   ├── weightage.py          # W_i calculation
│   │   ├── transit_power.py      # P_i calculation
│   │   ├── quality.py            # Q_i calculation
│   │   ├── elements.py           # Element balance
│   │   ├── dignities.py          # Planetary dignity scoring
│   │   └── houses.py             # House system calculations
│   │
│   ├── meters/
│   │   ├── __init__.py
│   │   ├── base_meter.py         # Abstract base class for all meters
│   │   ├── global_meters.py      # Overall intensity/harmony
│   │   ├── element_meters.py     # Fire/Earth/Air/Water
│   │   ├── cognitive_meters.py   # Mental clarity, decision, communication
│   │   ├── emotional_meters.py   # Emotional intensity, relationship, resilience
│   │   ├── physical_meters.py    # Physical energy, conflict, motivation
│   │   ├── domain_meters.py      # Career, opportunity, challenge, transformation
│   │   └── specialized_meters.py # Intuition, innovation, karmic, social
│   │
│   ├── explainability/
│   │   ├── __init__.py
│   │   ├── tier1.py              # Top contributors, simple explanation
│   │   ├── tier2.py              # Mathematical breakdown
│   │   ├── tier3.py              # Historical context and prediction
│   │   ├── interpretation.py     # Natural language generation
│   │   └── advice_engine.py      # Actionable guidance generation
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── chart.py              # NatalChart, TransitChart models
│   │   ├── aspect.py             # Aspect data model
│   │   ├── meter_reading.py      # MeterReading model
│   │   └── user_profile.py       # User preferences and sensitivities
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── schema.py             # Database schema definitions
│   │   ├── repositories.py       # Data access layer
│   │   └── historical.py         # Historical data storage and retrieval
│   │
│   ├── calibration/
│   │   ├── __init__.py
│   │   ├── data_collection.py    # Gather calibration dataset
│   │   ├── distribution.py       # Analyze score distributions
│   │   └── parameters.py         # Generate normalization parameters
│   │
│   └── utils/
│       ├── __init__.py
│       ├── date_utils.py         # Date/time handling
│       ├── degree_utils.py       # Zodiacal degree calculations
│       ├── caching.py            # Caching layer for performance
│       └── validation.py         # Input validation
│
├── tests/
│   ├── __init__.py
│   ├── test_aspects.py
│   ├── test_scoring.py
│   ├── test_meters.py
│   └── test_explainability.py
│
├── scripts/
│   ├── calibrate.py              # Run calibration process
│   ├── backfill_history.py       # Calculate historical data
│   └── benchmark.py              # Performance testing
│
```
### 7.3 Configuration Management

**`config/weights.yaml` Example**:
```yaml
# Planet Base Weights
planet_base_weights:
  Sun: 10
  Moon: 10
  Mercury: 7
  Venus: 7
  Mars: 7
  Jupiter: 5
  Saturn: 5
  Uranus: 3
  Neptune: 3
  Pluto: 3

# Essential Dignity Scores
essential_dignity:
  domicile: 5
  exaltation: 4
  neutral: 0
  detriment: -5
  fall: -4

# House Multipliers
house_multipliers:
  angular: 3.0      # Houses 1, 4, 7, 10
  succedent: 2.0    # Houses 2, 5, 8, 11
  cadent: 1.0       # Houses 3, 6, 9, 12

# Chart Ruler Bonus
chart_ruler_bonus: 5

# Aspect Base Intensities
aspect_base_intensity:
  conjunction: 10
  opposition: 9
  square: 8
  trine: 6
  sextile: 4

# Direction Modifiers
direction_modifiers:
  exact: 1.5        # Within 0.5° of exact
  applying: 1.3     # Getting closer
  separating: 0.7   # Moving apart

# Station Multipliers
station:
  max_days: 5       # Days from station to apply bonus
  max_multiplier: 1.8
  min_multiplier: 1.2

# Transit Planet Weights
transit_planet_weights:
  outer:            # Pluto, Neptune, Uranus
    multiplier: 1.5
  social:           # Saturn, Jupiter
    multiplier: 1.2
  inner:            # Mars, Venus, Mercury, Sun
    multiplier: 1.0
  lunar:            # Moon
    multiplier: 0.8

# Quality Factors
quality_factors:
  trine: 1.0
  sextile: 1.0
  square: -1.0
  opposition: -1.0
  conjunction:      # Dynamic based on planets
    double_benefic: 0.8
    double_malefic: -0.8
    mixed: 0.2
    transformational: -0.3
    default: 0.0

# Benefic/Malefic Classifications
planet_classifications:
  benefics:
    - Venus
    - Jupiter
  malefics:
    - Mars
    - Saturn
  transformational:
    - Uranus
    - Neptune
    - Pluto
  luminaries:
    - Sun
    - Moon

# Retrograde Modifiers
retrograde:
  mercury_clarity_penalty: 0.6
  general_intensity_mod: 0.8

# Element Weights
element_weights:
  Sun: 3.0
  Moon: 3.0
  Ascendant: 2.5
  Mercury: 2.0
  Venus: 2.0
  Mars: 2.0
  Jupiter: 1.5
  Saturn: 1.5
  Uranus: 1.0
  Neptune: 1.0
  Pluto: 1.0

# Normalization Parameters (from calibration)
normalization:
  dti_max: 1200.0
  hqs_max_positive: 850.0
  hqs_max_negative: 800.0

  # Meter-specific maxes
  meter_specific:
    mental_clarity:
      dti_max: 450.0
      hqs_max_pos: 320.0
      hqs_max_neg: 350.0

    physical_energy:
      dti_max: 520.0
      hqs_max_pos: 380.0
      hqs_max_neg: 290.0

    # ... (all other meters)

# Interpretation Thresholds
interpretation_thresholds:
  intensity:
    quiet: [0, 25]
    moderate: [26, 50]
    high: [51, 75]
    very_high: [76, 90]
    extreme: [91, 100]

  harmony:
    very_challenging: [0, 20]
    challenging: [21, 40]
    mixed: [41, 60]
    supportive: [61, 80]
    very_supportive: [81, 100]
```

### 7.4 Key Classes & Methods

#### 7.4.1 Core Scoring Engine

```python
# astro_meters/core/scoring.py

from typing import List, Dict, Tuple
import numpy as np

class AspectContribution(BaseModel):
    """Single aspect's contribution to DTI and HQS."""
    transit_planet: str
    natal_planet: str
    aspect_type: str
    orb: float
    W_i: float
    P_i: float
    Q_i: float
    dti_contribution: float
    hqs_contribution: float
    interpretation: str


class ScoreCalculator:
    """Core DTI and HQS calculation engine."""

    def __init__(self, natal_chart, config):
        self.natal_chart = natal_chart
        self.config = config
        self.weightage_calc = WeightageCalculator(natal_chart, config)
        self.transit_power_calc = TransitPowerCalculator(config)
        self.quality_calc = QualityCalculator(config)

    def calculate_scores(
        self,
        transit_chart,
        date,
        meter_filter=None
    ) -> Tuple[float, float, List[AspectContribution]]:
        """
        Calculate total DTI and HQS scores.

        Args:
            transit_chart: Current planetary positions
            date: Datetime for calculation
            meter_filter: Optional function to filter aspects by meter type

        Returns:
            (total_dti, total_hqs, aspect_breakdown)
        """
        total_dti = 0.0
        total_hqs = 0.0
        aspect_breakdown = []

        # Iterate through all planet combinations
        for t_planet in self.config.transit_planets:
            for n_planet in self.config.natal_planets:
                # Detect aspects
                aspects = self.detect_aspects(
                    transit_chart[t_planet],
                    self.natal_chart[n_planet],
                    t_planet,
                    n_planet
                )

                for aspect in aspects:
                    # Calculate components
                    W_i = self.weightage_calc.calculate(n_planet)
                    P_i = self.transit_power_calc.calculate(
                        aspect,
                        t_planet,
                        date
                    )
                    Q_i = self.quality_calc.calculate(
                        aspect['type'],
                        t_planet,
                        n_planet
                    )

                    # Apply meter filter if provided
                    if meter_filter and not meter_filter(t_planet, n_planet, aspect):
                        continue

                    # Calculate contributions
                    dti_contrib = W_i * P_i
                    hqs_contrib = W_i * P_i * Q_i

                    total_dti += dti_contrib
                    total_hqs += hqs_contrib

                    # Store breakdown
                    aspect_breakdown.append(AspectContribution(
                        transit_planet=t_planet,
                        natal_planet=n_planet,
                        aspect_type=aspect['type'],
                        orb=aspect['deviation'],
                        W_i=W_i,
                        P_i=P_i,
                        Q_i=Q_i,
                        dti_contribution=dti_contrib,
                        hqs_contribution=hqs_contrib,
                        interpretation=self.generate_interpretation(
                            t_planet, n_planet, aspect, Q_i
                        )
                    ))

        return total_dti, total_hqs, aspect_breakdown

    def normalize_scores(
        self,
        dti: float,
        hqs: float,
        meter_type: str = 'overall'
    ) -> Tuple[float, float]:
        """
        Normalize raw scores to 0-100 scales.

        Args:
            dti: Raw DTI score
            hqs: Raw HQS score
            meter_type: Specific meter for targeted normalization

        Returns:
            (intensity_meter, harmony_meter)
        """
        # Get normalization parameters
        if meter_type == 'overall':
            dti_max = self.config['normalization']['dti_max']
            hqs_max_pos = self.config['normalization']['hqs_max_positive']
            hqs_max_neg = self.config['normalization']['hqs_max_negative']
        else:
            meter_params = self.config['normalization']['meter_specific'].get(meter_type)
            dti_max = meter_params['dti_max']
            hqs_max_pos = meter_params['hqs_max_pos']
            hqs_max_neg = meter_params['hqs_max_neg']

        # Normalize intensity (0-100)
        intensity_meter = self._normalize_with_soft_ceiling(dti, dti_max, 100)

        # Normalize harmony (0-100, where 50 is neutral)
        if hqs >= 0:
            harmony_meter = 50 + self._normalize_with_soft_ceiling(
                hqs, hqs_max_pos, 50
            )
        else:
            harmony_meter = 50 - self._normalize_with_soft_ceiling(
                abs(hqs), hqs_max_neg, 50
            )

        return intensity_meter, harmony_meter

    def _normalize_with_soft_ceiling(
        self,
        raw_score: float,
        max_value: float,
        target_scale: float
    ) -> float:
        """Apply logarithmic compression for outliers beyond expected max."""
        if raw_score <= max_value:
            return (raw_score / max_value) * target_scale
        else:
            # Compress outliers beyond 99th percentile
            excess = raw_score - max_value
            compressed_excess = (target_scale * 0.1) * np.log10(1 + excess / max_value)
            return min(target_scale, target_scale + compressed_excess)
```

#### 7.4.2 Meter Base Class

```python
# astro_meters/meters/base_meter.py

from abc import ABC, abstractmethod
from typing import Dict, Any, List

class MeterReading(BaseModel):
    """Result of a meter calculation."""
    meter_name: str
    date: datetime
    intensity: float
    harmony: float
    state_label: str
    interpretation: str
    advice: List[str]
    top_aspects: List[AspectContribution]
    raw_scores: Dict[str, float]


class BaseMeter(ABC):
    """Abstract base class for all meters."""

    def __init__(self, natal_chart, config):
        self.natal_chart = natal_chart
        self.config = config
        self.score_calculator = ScoreCalculator(natal_chart, config)

    @abstractmethod
    def get_meter_name(self) -> str:
        """Return the name of this meter."""
        pass

    @abstractmethod
    def filter_aspects(self, t_planet, n_planet, aspect) -> bool:
        """
        Determine if an aspect should be included in this meter.

        Returns:
            True if aspect is relevant to this meter
        """
        pass

    @abstractmethod
    def interpret(self, intensity: float, harmony: float, aspects: List) -> str:
        """Generate natural language interpretation."""
        pass

    @abstractmethod
    def generate_advice(self, intensity: float, harmony: float, aspects: List) -> List[str]:
        """Generate actionable advice."""
        pass

    def calculate(self, transit_chart, date) -> MeterReading:
        """
        Calculate this meter's reading for a given date.

        Returns:
            MeterReading object with all calculated values
        """
        # Calculate scores with meter-specific filtering
        total_dti, total_hqs, aspect_breakdown = self.score_calculator.calculate_scores(
            transit_chart,
            date,
            meter_filter=self.filter_aspects
        )

        # Normalize
        intensity, harmony = self.score_calculator.normalize_scores(
            total_dti,
            total_hqs,
            meter_type=self.get_meter_name()
        )

        # Sort aspects by contribution
        top_aspects = sorted(
            aspect_breakdown,
            key=lambda a: abs(a.dti_contribution),
            reverse=True
        )[:5]  # Top 5

        # Generate interpretation and advice
        interpretation = self.interpret(intensity, harmony, top_aspects)
        advice = self.generate_advice(intensity, harmony, top_aspects)

        # Determine state label
        state_label = self.get_state_label(intensity, harmony)

        return MeterReading(
            meter_name=self.get_meter_name(),
            date=date,
            intensity=intensity,
            harmony=harmony,
            state_label=state_label,
            interpretation=interpretation,
            advice=advice,
            top_aspects=top_aspects,
            raw_scores={
                'dti': total_dti,
                'hqs': total_hqs
            }
        )

    def get_state_label(self, intensity: float, harmony: float) -> str:
        """Map intensity and harmony to a state label."""
        # Override in subclasses for meter-specific labels
        thresholds = self.config['interpretation_thresholds']

        if intensity < 40:
            return "Quiet"
        elif intensity < 70:
            if harmony > 70:
                return "Flowing"
            elif harmony < 30:
                return "Challenging"
            else:
                return "Mixed"
        else:  # High intensity
            if harmony > 70:
                return "Peak Opportunity"
            elif harmony < 30:
                return "High Pressure"
            else:
                return "Intense Mixed"
```

#### 7.4.3 Specific Meter Example: Mental Clarity

```python
# astro_meters/meters/cognitive_meters.py

class MentalClarityMeter(BaseMeter):
    """Measures mental clarity and cognitive function."""

    def get_meter_name(self) -> str:
        return "mental_clarity"

    def filter_aspects(self, t_planet, n_planet, aspect) -> bool:
        """Include aspects to Mercury, 3rd house, and 3rd house ruler."""
        # Primary: aspects to natal Mercury
        if n_planet == 'Mercury':
            return True

        # Secondary: aspects to 3rd house planets
        third_house_planets = self.natal_chart.get_house_planets(3)
        if n_planet in third_house_planets:
            return True

        # Tertiary: aspects to 3rd house ruler
        third_house_ruler = self.natal_chart.get_house_ruler(3)
        if n_planet == third_house_ruler:
            return True

        return False

    def interpret(self, intensity: float, harmony: float, aspects: List) -> str:
        """Generate mental clarity interpretation."""

        # Check for Mercury retrograde
        is_mercury_rx = aspects[0].transit_planet == 'Mercury' and \
                       self.is_retrograde('Mercury', aspects[0].date)

        if intensity < 40:
            base = "Your mind is quiet right now with low mental demand."
        elif intensity < 70:
            if harmony > 70:
                base = "Your mental clarity is excellent. Thinking is sharp and communication flows easily."
            elif harmony < 30:
                base = "Your mental clarity is significantly reduced. Brain fog, confusion, or communication difficulties are likely."
            else:
                base = "Your mental state is mixed with both clear moments and foggy periods."
        else:  # High intensity
            if harmony > 70:
                base = "You're in a state of peak mental performance. Exceptional clarity, insight, and communication."
            elif harmony < 30:
                base = "Your mind is under significant stress. Mental overload, scattered thinking, or major miscommunications are likely."
            else:
                base = "Intense mental activity with both breakthroughs and challenges."

        # Add Mercury retrograde note if applicable
        if is_mercury_rx:
            base += " Note: Mercury is retrograde, which can add review and revision themes."

        # Add top aspect context
        top_aspect = aspects[0]
        base += f"\n\nPrimary influence: {top_aspect.interpretation}"

        return base

    def generate_advice(self, intensity: float, harmony: float, aspects: List) -> List[str]:
        """Generate mental clarity advice."""
        advice = []

        if intensity < 40:
            advice.append("Low mental demand period - good for rest and integration")
        elif intensity < 70:
            if harmony > 70:
                advice.extend([
                    "Excellent time for important conversations",
                    "Good for learning, writing, and complex problem-solving",
                    "Make important decisions with confidence"
                ])
            elif harmony < 30:
                advice.extend([
                    "Avoid important decisions if possible",
                    "Double-check details and communications",
                    "Give yourself extra time for mental tasks",
                    "Rest your mind - reduce information overload"
                ])
            else:
                advice.extend([
                    "Mixed mental energy - proceed thoughtfully",
                    "Important decisions: give yourself extra time",
                    "Be clear in communications to avoid misunderstanding"
                ])
        else:  # High intensity
            if harmony > 70:
                advice.extend([
                    "Peak mental performance - act on your insights",
                    "Ideal for presentations, negotiations, creative work",
                    "Major mental breakthroughs possible",
                    "Document your ideas - they're valuable"
                ])
            elif harmony < 30:
                advice.extend([
                    "Mental overload risk - prioritize and simplify",
                    "Not the time for major decisions",
                    "High misunderstanding/argument risk - be extra careful",
                    "Consider postponing difficult conversations",
                    "Rest and recovery crucial"
                ])
            else:
                advice.extend([
                    "Intense mental period - both insights and challenges",
                    "Proceed with important matters but take extra time",
                    "Balance mental work with rest periods"
                ])

        # Add specific aspect advice
        top_aspect = aspects[0]
        if 'Saturn' in [top_aspect.transit_planet, top_aspect.natal_planet]:
            advice.append("Saturn influence: Focus on disciplined, structured thinking")
        if 'Neptune' in [top_aspect.transit_planet, top_aspect.natal_planet]:
            advice.append("Neptune influence: Watch for idealization or confusion")
        if 'Uranus' in [top_aspect.transit_planet, top_aspect.natal_planet]:
            advice.append("Uranus influence: Expect sudden insights or disruptions")

        return advice

    def get_state_label(self, intensity: float, harmony: float) -> str:
        """Mental clarity-specific state labels."""
        if intensity < 40:
            return "QUIET"
        elif intensity < 70:
            if harmony > 70:
                return "SHARP FOCUS"
            elif harmony < 30:
                return "SCATTERED"
            else:
                return "MIXED"
        else:
            if harmony > 70:
                return "GENIUS MODE"
            elif harmony < 30:
                return "OVERLOAD"
            else:
                return "INTENSE"
```


```

---

## 8. Validation & Calibration

### 8.1 Calibration Process

**Step 1: Dataset Collection**
```python
# scripts/calibrate.py

def collect_calibration_dataset(num_charts=50000):
    """
    Generate diverse dataset of natal charts.

    Strategy:
    - Historical births: 1900-2025
    - Geographic diversity: All continents
    - Time diversity: All hours of day
    - Demographic diversity: Various life stages
    """
    charts = []

    for i in range(num_charts):
        # Random birth time within constraints
        birth_date = generate_random_date(
            start_year=1900,
            end_year=2025
        )

        birth_location = generate_random_location(
            ensure_global_distribution=True
        )

        # Calculate chart
        chart = calculate_natal_chart(birth_date, birth_location)
        charts.append(chart)

        if i % 1000 == 0:
            print(f"Generated {i}/{num_charts} charts...")

    return charts
```

**Step 2: Historical Analysis**
```python
def calculate_historical_scores(charts, years=25):
    """
    Calculate DTI and HQS for each chart over a long period.

    Args:
        charts: List of natal charts
        years: Number of years to analyze

    Returns:
        DataFrame with all scores
    """
    all_scores = []

    for chart_idx, chart in enumerate(charts):
        start_date = datetime(2000, 1, 1)
        end_date = start_date + timedelta(days=365*years)

        current_date = start_date
        while current_date <= end_date:
            # Calculate transits for this date
            transit_chart = calculate_transit_chart(current_date)

            # Calculate all meter scores
            for meter_name in ALL_METERS:
                meter = MeterFactory.create(meter_name, chart, config)
                reading = meter.calculate(transit_chart, current_date)

                all_scores.append({
                    'chart_id': chart_idx,
                    'date': current_date,
                    'meter': meter_name,
                    'dti': reading.raw_scores['dti'],
                    'hqs': reading.raw_scores['hqs'],
                    'intensity': reading.intensity,
                    'harmony': reading.harmony
                })

            # Progress
            current_date += timedelta(days=1)

        if chart_idx % 100 == 0:
            print(f"Processed {chart_idx}/{len(charts)} charts...")

    return pd.DataFrame(all_scores)
```

**Step 3: Distribution Analysis**
```python
def analyze_score_distributions(scores_df):
    """
    Analyze distributions and set normalization parameters.

    Returns:
        Dictionary of normalization parameters for each meter
    """
    normalization_params = {}

    for meter_name in scores_df['meter'].unique():
        meter_scores = scores_df[scores_df['meter'] == meter_name]

        # DTI distribution
        dti_scores = meter_scores['dti'].values
        dti_99th = np.percentile(dti_scores, 99.0)
        dti_max = dti_99th * 1.1  # Add 10% buffer

        # HQS distributions (separate for positive and negative)
        hqs_scores = meter_scores['hqs'].values
        hqs_positive = hqs_scores[hqs_scores > 0]
        hqs_negative = np.abs(hqs_scores[hqs_scores < 0])

        hqs_99th_pos = np.percentile(hqs_positive, 99.0) if len(hqs_positive) > 0 else 100
        hqs_99th_neg = np.percentile(hqs_negative, 99.0) if len(hqs_negative) > 0 else 100

        hqs_max_pos = hqs_99th_pos * 1.1
        hqs_max_neg = hqs_99th_neg * 1.1

        normalization_params[meter_name] = {
            'dti_max': float(dti_max),
            'hqs_max_pos': float(hqs_max_pos),
            'hqs_max_neg': float(hqs_max_neg),
            'dataset_size': len(meter_scores),
            'calibration_date': datetime.now().isoformat()
        }

        # Visualize distributions
        plot_distribution(dti_scores, f"{meter_name}_DTI", dti_max)
        plot_distribution(hqs_positive, f"{meter_name}_HQS_Positive", hqs_max_pos)
        plot_distribution(hqs_negative, f"{meter_name}_HQS_Negative", hqs_max_neg)

    return normalization_params

def plot_distribution(scores, title, threshold):
    """Plot score distribution with threshold marked."""
    import matplotlib.pyplot as plt

    plt.figure(figsize=(10, 6))
    plt.hist(scores, bins=100, alpha=0.7, edgecolor='black')
    plt.axvline(threshold, color='red', linestyle='--', linewidth=2, label=f'99th %ile: {threshold:.1f}')
    plt.xlabel('Score')
    plt.ylabel('Frequency')
    plt.title(f'Distribution: {title}')
    plt.legend()
    plt.savefig(f'calibration_{title}.png')
    plt.close()
```

**Step 4: Update Configuration**
```python
def update_normalization_config(normalization_params):
    """Write normalization parameters to config file."""
    config_path = 'config/normalization.yaml'

    with open(config_path, 'w') as f:
        yaml.dump(normalization_params, f, default_flow_style=False)

    print(f"Normalization parameters saved to {config_path}")
```

### 8.2 Validation Metrics

**Test Against Known Transits**:
```python
def validate_against_known_transits():
    """
    Test system against well-documented astrological periods.

    Examples:
    - Saturn Return (age ~29): Should show high Challenge meter
    - Jupiter Return (age ~12, 24): Should show high Opportunity meter
    - Uranus Opposition (age ~42): Should show high Transformation meter
    """
    test_cases = [
        {
            'name': 'Saturn Return',
            'birth_date': datetime(1990, 1, 1, 12, 0),
            'test_date': datetime(2019, 1, 1),  # ~29 years later
            'expected_meters': {
                'challenge_intensity': {'min': 60, 'max': 100},
                'transformation_pressure': {'min': 50, 'max': 100}
            }
        },
        {
            'name': 'Jupiter Return',
            'birth_date': datetime(1990, 1, 1, 12, 0),
            'test_date': datetime(2002, 1, 1),  # ~12 years later
            'expected_meters': {
                'opportunity_window': {'min': 60, 'max': 100}
            }
        },
        # Add more test cases
    ]

    results = []

    for test in test_cases:
        chart = calculate_natal_chart(test['birth_date'], default_location)
        transit_chart = calculate_transit_chart(test['test_date'])

        for meter_name, expected_range in test['expected_meters'].items():
            meter = MeterFactory.create(meter_name, chart, config)
            reading = meter.calculate(transit_chart, test['test_date'])

            passed = expected_range['min'] <= reading.intensity <= expected_range['max']

            results.append({
                'test': test['name'],
                'meter': meter_name,
                'expected_min': expected_range['min'],
                'expected_max': expected_range['max'],
                'actual': reading.intensity,
                'passed': passed
            })

    # Report
    df = pd.DataFrame(results)
    print(df)
    print(f"\nValidation Pass Rate: {df['passed'].mean() * 100:.1f}%")

    return df
```


---

## 9. User Experience Guidelines

### 9.1 Dashboard Layout

**Primary View (At-a-Glance) in main screen**:
```
┌─────────────────────────────────────────────────────────────┐
│  🌍 ASTROLOGICAL WEATHER                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Overall Intensity: ████████░░░░░░░░ 72/100  HIGH          │
│  Overall Harmony:   ████░░░░░░░░░░░░ 38/100  CHALLENGING   │
│                                                             │
│  ⚡ Major Transits Active:                                 │
│  ⚠️  Saturn □ Sun: Identity tests, discipline required     │
│  ✓  Jupiter △ Venus: Relationship growth, joy             │
│  ⚠️  Mars ☍ Mars: Conflict risk, energy scattered         │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  YOUR METERS TODAY:                                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🧠 Mental      ████████░░ 65  │  ❤️  Emotional  ███░░░░░░░ 35 │
│  ⚡ Physical    ████░░░░░░ 42  │  🎯 Career      ████████░░ 72 │
│  🔮 Spiritual   ███████░░░ 68  │  💰 Opportunity ███████░░░ 71 │
│                                                             │
│     [View All 23 Meters]    [Forecast]    [History]        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Individual Meter View** (Mental Clarity example shown in Section 5.4.1)


### 9.4 Mobile Optimization

**Key Considerations**:
- **Vertical Scroll First**: Dashboard adapts to vertical layout
- **Tap Targets**: Minimum 44x44pt for touch interactions
- **Progressive Disclosure**: Top-level overview → tap for details
- **Offline Support**: Cache recent readings for offline viewing
- **Push Notifications**: Optional alerts for major transit peaks



### 9.6 Educational Content

**In-App Tooltips**:
- Hover/tap any planet, aspect, or house for instant definition
- Example: "Saturn (♄): Planet of discipline, structure, and lessons"

**Learn More Links**:
- Link to blog posts/videos explaining concepts in depth
- "Why does Saturn square Sun feel challenging?" → Article

**Glossary**:
- Searchable glossary of astrological terms
- Plain-language definitions

---

## 10. Appendix

### 10.1 Aspect Orb Reference Table

| Aspect | Exact Angle | Sun/Moon Orb | Inner Planet Orb | Social Planet Orb | Outer Planet Orb |
|--------|------------|-------------|-----------------|-------------------|------------------|
| Conjunction | 0° | ±10° | ±8° | ±8° | ±6° |
| Opposition | 180° | ±10° | ±8° | ±8° | ±6° |
| Square | 90° | ±8° | ±7° | ±7° | ±5° |
| Trine | 120° | ±8° | ±7° | ±7° | ±5° |
| Sextile | 60° | ±6° | ±5° | ±5° | ±4° |

### 10.2 Planetary Dignity Reference

See Section 3.2 for complete table.

### 10.3 House Cusp Calculation (Placidus)

Formula for Placidus house cusps at latitude φ:
```
tan(H) = tan(L) × sin(ε) / (cos(ε) × cos(φ) + sin(φ) × tan(D))
```
Where:
- H = House cusp longitude
- L = Local Sidereal Time
- ε = Obliquity of ecliptic (~23.44°)
- φ = Geographic latitude
- D = Declination of point


**Technical Implementation**:
- Swiss Ephemeris documentation: https://www.astro.com/swisseph/
- *Programming for Astrologers* by Jeffrey Kishner