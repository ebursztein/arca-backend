# Astrometers V2 Sprint Plan

**Goal**: Bring implementation from 40% spec compliance to 90%+ full-featured production system

**Current State**: V1 Prototype (all 23 meters functional, simplified calculations)

**Target State**: Production-grade system with full weighting, empirical calibration, and meter-specific synthesis

**Estimated Effort**: 6-8 sprints (12-16 weeks)

---

## Executive Summary

### Current Implementation (V1)
- ✅ All 23 meters present with correct taxonomy
- ✅ Basic DTI/HQS framework functional
- ✅ Excellent interpretations and user experience
- ⚠️ Simplified weighting (no dignity, chart ruler, sensitivity)
- ⚠️ No empirical calibration (uses theoretical maximums)
- ⚠️ Missing weighted synthesis formulas for most meters
- ⚠️ Incomplete house transit integration

### Gap Analysis Summary

| Component | V1 Status | V2 Target | Priority |
|-----------|-----------|-----------|----------|
| **Core Algorithm** | 40% | 100% | CRITICAL |
| **Weightage Factor (Wᵢ)** | 30% | 100% | CRITICAL |
| **Transit Power (Pᵢ)** | 60% | 100% | CRITICAL |
| **Quality Factor (Qᵢ)** | 70% | 100% | HIGH |
| **Normalization** | 40% | 100% | CRITICAL |
| **Meter Formulas** | 35% | 90% | HIGH |
| **House Transits** | 30% | 80% | MEDIUM |
| **Interpretations** | 85% | 95% | LOW |

---

## Sprint Breakdown

### Sprint 1: Core Algorithm Enhancement (2 weeks)
**Goal**: Implement full Weightage Factor (Wᵢ) and Transit Power (Pᵢ) calculations

#### Tasks

**1.1 Essential Dignity System**
- [ ] Create `dignity_tables.py` with complete dignity assignments
  - Domicile: +5 (Sun in Leo, Moon in Cancer, etc.)
  - Exaltation: +4 (Sun in Aries, Moon in Taurus, etc.)
  - Detriment: -5 (Sun in Aquarius, Moon in Capricorn, etc.)
  - Fall: -4 (Sun in Libra, Moon in Scorpio, etc.)
- [ ] Update `calculate_weightage()` to include dignity score
- [ ] Add tests for all 10 planets × 12 signs = 120 combinations

**1.2 Chart Ruler Bonus**
- [ ] Add `calculate_chart_ruler()` logic (already exists, verify)
- [ ] Add +5 bonus in `calculate_weightage()` when planet rules ascendant
- [ ] Test: Leo Asc → Sun gets +5, Scorpio Asc → Pluto gets +5

**1.3 Personal Sensitivity Factor**
- [ ] Add `sensitivity: float = 1.0` field to `TransitAspect` dataclass
- [ ] Update `calculate_weightage()` to apply sensitivity multiplier
- [ ] Add validation: sensitivity must be 0.5-2.0

**1.4 Direction Modifier Enhancement**
- [ ] Update `get_direction_modifier()` in `transit_power.py`:
  - Applying (tomorrow < today): ×1.3
  - Exact (deviation ≤ 0.5°): ×1.5
  - Separating (tomorrow > today): ×0.7
- [ ] Verify existing implementation matches spec

**1.5 Station Detection**
- [ ] Add `days_from_station` calculation for retrograde planets
- [ ] Add `calculate_station_modifier()` implementation:
  - Within 5 days of station: ×1.8
  - Linear decay from day 0 (station) to day 5 (normal)
- [ ] Add station data to transit chart calculations

**Deliverable**: Enhanced `core.py` with full Wᵢ and Pᵢ calculations

**Testing**:
- Add 50+ tests for dignity scoring
- Add 20+ tests for chart ruler detection
- Add 30+ tests for station detection
- Verify DTI values increase by 20-40% with full weighting

---

### Sprint 2: Quality Factor & Conjunction Logic (1 week)
**Goal**: Implement dynamic conjunction quality based on planet combinations

#### Tasks

**2.1 Conjunction Quality Logic**
- [ ] Update `calculate_quality_factor()` in `quality.py`
- [ ] Implement spec's logic:
  ```python
  benefics = {Planet.VENUS, Planet.JUPITER}
  malefics = {Planet.MARS, Planet.SATURN}
  transformational = {Planet.URANUS, Planet.NEPTUNE, Planet.PLUTO}

  # Double benefic: +0.8 (Jupiter conjunct Venus)
  # Double malefic: -0.8 (Mars conjunct Saturn)
  # Benefic + malefic: +0.2 (Venus conjunct Mars - mitigating)
  # Outer planet: -0.3 (Pluto conjunct Sun - transformational tension)
  # Default: 0.0 (Sun conjunct Mercury - context-dependent)
  ```
- [ ] Add comprehensive test suite for all planet pairs

**2.2 Quality Factor Testing**
- [ ] Test all conjunction combinations (10 planets × 10 planets = 100 pairs)
- [ ] Verify hard aspects remain -1.0
- [ ] Verify soft aspects remain +1.0
- [ ] Add edge case tests

**Deliverable**: Enhanced `quality.py` with dynamic conjunction logic

**Testing**:
- 100 conjunction pair tests
- Verify HQS values shift appropriately
- Compare before/after for sample charts

---

### Sprint 3: Empirical Calibration System (2-3 weeks)
**Goal**: Replace theoretical maximums with empirically-derived percentiles

#### Tasks

**3.1 Historical Data Collection**
- [ ] Create `calibration/` directory
- [ ] Generate 10,000-50,000 sample natal charts
  - Diverse birth years (1950-2020)
  - Diverse locations (global coverage)
  - Random birth times (0-23 hours)
- [ ] Store in `calibration/natal_charts.json`

**3.2 Historical Calculation Pipeline**
- [ ] Create `calibration/calculate_historical.py`
- [ ] For each chart, calculate DTI/HQS for:
  - Every day from 2000-2030 (30 years × 365 days = 10,950 calculations per chart)
  - Store: `{chart_id, date, dti, hqs, aspect_count}`
- [ ] Use multiprocessing to parallelize (10k charts × 11k days = 110M calculations)
- [ ] Store results in `calibration/historical_scores.parquet` (compressed)

**3.3 Distribution Analysis**
- [ ] Create `calibration/analyze_distributions.py`
- [ ] Calculate percentiles:
  ```python
  DTI_P50 = np.percentile(dti_scores, 50)  # Median
  DTI_P75 = np.percentile(dti_scores, 75)  # High
  DTI_P90 = np.percentile(dti_scores, 90)  # Very high
  DTI_P95 = np.percentile(dti_scores, 95)  # Top 5%
  DTI_P99 = np.percentile(dti_scores, 99)  # Extreme (top 1%)

  HQS_P01 = np.percentile(hqs_scores, 1)   # Very challenging
  HQS_P10 = np.percentile(hqs_scores, 10)  # Challenging
  HQS_P50 = np.percentile(hqs_scores, 50)  # Neutral
  HQS_P90 = np.percentile(hqs_scores, 90)  # Supportive
  HQS_P99 = np.percentile(hqs_scores, 99)  # Very supportive
  ```
- [ ] Generate distribution plots (histograms, PDFs)
- [ ] Store calibration constants in `calibration/constants.json`

**3.4 Normalization Update**
- [ ] Create `normalize_with_empirical()` function in `normalization.py`
- [ ] Implement soft ceiling for outliers beyond P99:
  ```python
  def normalize_with_soft_ceiling(value, p99_value, max_output):
      if value <= p99_value:
          return (value / p99_value) * max_output
      else:
          # Logarithmic compression for outliers
          excess = value - p99_value
          compressed = math.log10(1 + excess) * (max_output * 0.1)
          return min(max_output, (p99_value / p99_value) * max_output + compressed)
  ```
- [ ] Update all meters to use empirical calibration
- [ ] Add fallback to theoretical max if calibration data missing

**3.5 Calibration Validation**
- [ ] Run 1,000 random charts through both V1 and V2
- [ ] Compare intensity/harmony distributions
- [ ] Verify "Extreme" label appears for ~1% of cases
- [ ] Verify "Very High" label appears for ~5% of cases

**Deliverable**:
- `calibration/` directory with historical data
- `calibration/constants.json` with empirical percentiles
- Updated `normalization.py` with empirical functions

**Testing**:
- Verify percentile accuracy on validation set
- Ensure outliers are properly compressed
- Test edge cases (zero activity, extreme activity)

---

### Sprint 4: Meter-Specific Weighted Synthesis (2-3 weeks)
**Goal**: Implement weighted formulas for complex meters

#### Tasks

**4.1 Cognitive Meters Enhancement**

**Mental Clarity** (currently 70% complete)
- [ ] Add 3rd house transit component (15% weight)
- [ ] Add 3rd house ruler aspects (10% weight)
- [ ] Update Mercury Rx logic:
  ```python
  if mercury_rx:
      dti *= 0.8      # Intensity slightly reduced
      hqs *= 0.6      # Clarity significantly reduced
  ```

**Decision Quality** (currently 30% complete)
- [ ] Implement weighted synthesis:
  ```python
  clarity_score = calculate_mental_clarity().clarity  # 40% weight
  jupiter_contrib = calculate_aspects(Jupiter, [Sun, Mercury, Jupiter])  # 30%
  saturn_contrib = calculate_saturn_wisdom()  # 20% (nuanced)
  neptune_penalty = calculate_aspects(Neptune, [Mercury, Sun, Jupiter])  # -15%
  uranus_penalty = calculate_uranus_impulsiveness()  # -10%

  raw_score = (clarity_score * 0.4 +
               jupiter_contrib * 0.3 +
               saturn_contrib * 0.2 -
               neptune_penalty * 0.15 -
               uranus_penalty * 0.10)
  ```
- [ ] Implement Saturn nuance: moderate Saturn (+), heavy Saturn (-)
- [ ] Filter Uranus to hard aspects only for impulsiveness

**Communication Flow** (currently 40% complete)
- [ ] Implement weighted synthesis:
  ```python
  mercury_hqs * 0.5 +           # 50% Mercury
  venus_hqs * 0.25 +            # 25% Venus (diplomacy)
  third_house_activity * 0.15 - # 15% 3rd house
  mars_conflict_risk * 0.3      # -30% Mars conflict penalty
  ```
- [ ] Add 3rd house transit calculation
- [ ] Add explicit Mars conflict penalty

**4.2 Emotional Meters Enhancement**

**Emotional Intensity** (currently 50% complete)
- [ ] Implement weighted synthesis:
  ```python
  moon_dti * 0.5 +       # 50% Moon
  venus_dti * 0.2 +      # 20% Venus
  pluto_factor * 0.2 +   # 20% Pluto (deepening)
  neptune_factor * 0.1   # 10% Neptune (×1.3 sensitivity amplifier)
  ```
- [ ] Add Neptune sensitivity amplifier (×1.3)
- [ ] Add 4th/8th house transit components

**Relationship Harmony** (currently 40% complete)
- [ ] Implement weighted synthesis:
  ```python
  venus_hqs * 0.4 +
  seventh_house_hqs * 0.2 +
  jupiter_venus * 0.15 +      # Generosity/expansion
  saturn_venus * 0.1 +        # Commitment or restriction
  mars_venus * 0.1 +          # Passion or conflict
  neptune_factor * 0.05       # Romance or illusion (×0.7 reality check)
  ```
- [ ] Add planet-to-planet interaction weights
- [ ] Add Neptune reality check (×0.7 factor)

**Emotional Resilience** (currently 35% complete)
- [ ] Implement Saturn-Moon nuance:
  ```python
  if abs(saturn_moon_hqs) < 40:
      # Moderate Saturn-Moon builds structure
      resilience_from_saturn = abs(saturn_moon_hqs) * 0.8
  else:
      # Heavy Saturn-Moon can deplete
      resilience_from_saturn = saturn_moon_hqs
  ```
- [ ] Add weighted synthesis:
  ```python
  sun_hqs * 0.3 +
  resilience_from_saturn * 0.25 +
  mars_positive * 0.2 +       # Only harmonious Mars aspects
  jupiter_hqs * 0.15 +
  twelfth_penalty * -0.5 +    # 12th house isolation
  neptune_moon_penalty * -0.4 # Boundary dissolution
  ```
- [ ] Filter Mars to positive aspects only
- [ ] Add 12th house penalty calculation
- [ ] Add Neptune-Moon boundary penalty

**4.3 Physical/Action Meters Enhancement**

**Physical Energy** (currently 50% complete)
- [ ] Implement separate intensity and quality:
  ```python
  intensity = mars_dti * 0.5 + sun_dti * 0.3 + first_house_dti * 0.2
  quality = mars_hqs * 0.4 + jupiter_mars * 0.3 + saturn_mars_hqs * 0.2
  ```
- [ ] Add 1st house transit component
- [ ] Add 6th house (health) component
- [ ] Add Jupiter-Mars expansion factor
- [ ] Add Saturn-Mars discipline/depletion factor

**Conflict Risk** (currently 60% complete)
- [ ] Implement multi-factor risk:
  ```python
  total_risk = (mars_conflict +
                uranus_risk * 1.2 +         # Accidents, sudden events
                pluto_risk * 0.8 +          # Power struggles
                seventh_house_challenging)  # Partnership conflict
  ```
- [ ] Add Uranus sudden event component
- [ ] Add Pluto power struggle component
- [ ] Add 7th house conflict component
- [ ] Add risk type identification (Mars/Uranus/Pluto dominant)

**Motivation Drive** (currently 40% complete)
- [ ] Implement separate intensity and quality:
  ```python
  intensity = mars_dti * 0.4 + sun_dti * 0.3 + tenth_house_activity * 0.2
  quality = mars_hqs * 0.3 + jupiter_boost * 0.4 + saturn_factor * 0.3
  ```
- [ ] Add Sun willpower component
- [ ] Add 10th house ambition component
- [ ] Calculate Jupiter "boost" (Jupiter to Sun/Mars)
- [ ] Implement Saturn dual nature (discipline vs discouragement)

**4.4 Life Domain Meters Enhancement**

**Career Ambition** (currently 30% complete)
- [ ] Implement comprehensive formula:
  ```python
  intensity = (tenth_house_dti * 0.4 +
               mc_dti * 0.3 +              # Midheaven aspects
               abs(saturn_career) * 0.2 +
               abs(jupiter_career) * 0.1)

  quality = (tenth_house_hqs * 0.3 +
             mc_hqs * 0.2 +
             saturn_career * 0.25 +        # Challenge or achievement
             jupiter_career * 0.15 +       # Opportunity
             sun_mc * 0.1)                 # Recognition
  ```
- [ ] Add MC (Midheaven) aspect calculation
- [ ] Add Sun-MC recognition factor
- [ ] Add 7-state career phase matrix

**Opportunity Window** (currently 40% complete)
- [ ] Implement multi-factor formula:
  ```python
  intensity = (jupiter_dti * 0.5 +
               north_node_dti * 0.3 +      # Karmic opportunity
               jupiter_hqs * 0.2)

  quality = (jupiter_hqs * 0.4 +
             venus_hqs * 0.2 +             # Attraction, ease
             eleventh_house_hqs * 0.15 +  # Networks
             second_house_hqs * 0.15 +    # Resources
             sun_hqs * 0.1)               # Visibility
  ```
- [ ] Add North Node karmic timing
- [ ] Add Venus attraction factor
- [ ] Add 11th house networking
- [ ] Add 2nd house resources
- [ ] Add auspicious alignment detection

**Challenge Intensity** (currently 35% complete)
- [ ] Implement comprehensive formula:
  ```python
  saturn_dti * 0.4 +
  pluto_dti * 0.3 +
  chiron_dti * 0.15 +           # Wounding/healing
  twelfth_house_challenging * 0.1 +
  south_node_dti * 0.05         # Karmic release
  ```
- [ ] Add Chiron (wounded healer) if available in chart data
- [ ] Add 12th house isolation/endings
- [ ] Add South Node karmic release
- [ ] Add lesson theme identification

**Transformation Pressure** (currently 30% complete)
- [ ] Implement separate intensity and quality:
  ```python
  intensity = (pluto_dti * 0.45 +
               uranus_dti * 0.35 +
               neptune_dti * 0.15 +
               eighth_house_activity * 0.05)

  quality = pluto_hqs * 0.5 + uranus_hqs * 0.5
  ```
- [ ] Add 8th house (crisis, transformation) component
- [ ] Identify transformation type (Pluto/Uranus/Neptune dominant)

**4.5 Specialized Meters Enhancement**

**Intuition/Spirituality** (currently 40% complete)
- [ ] Implement comprehensive formula:
  ```python
  neptune_dti * 0.4 +
  moon_sensitivity * 0.3 +      # Moon-Neptune ×1.4 amplifier
  twelfth_house_dti * 0.15 +
  ninth_house_dti * 0.1 +       # Higher mind
  uranus_spiritual * 0.05       # Sudden openings
  ```
- [ ] Add Moon-Neptune sensitivity amplifier (×1.4)
- [ ] Add 9th house higher mind component
- [ ] Add Uranus spiritual awakening component
- [ ] Add grounding advice for high sensitivity

**Innovation/Breakthroughs** (currently 35% complete)
- [ ] Implement focused formula:
  ```python
  uranus_dti * 0.4 +
  uranus_mercury * 0.3 +        # Mental breakthroughs ×1.5
  uranus_sun * 0.15 +           # Identity breakthroughs ×1.2
  eleventh_house_dti * 0.1 +    # Future vision
  jupiter_uranus * 0.05         # Expansion of innovation
  ```
- [ ] Add Uranus-Mercury focus (×1.5 amplifier)
- [ ] Add Uranus-Sun focus (×1.2 amplifier)
- [ ] Add 11th house future vision
- [ ] Add Jupiter-Uranus expansion
- [ ] Identify breakthrough area (which planet aspected)

**Karmic Lessons** (currently 30% complete)
- [ ] Implement comprehensive formula:
  ```python
  north_node_dti * 0.25 +
  south_node_dti * 0.25 +       # Release past
  chiron_dti * 0.25 +           # Core wounds
  saturn_karmic * 0.15 +        # ×0.6 partial weight
  twelfth_house_dti * 0.05 +
  fourth_house_dti * 0.05       # Family karma
  ```
- [ ] Add South Node (release, past patterns)
- [ ] Add Chiron if available
- [ ] Add 12th house (unconscious, past)
- [ ] Add 4th house (family, roots)
- [ ] Add karmic theme identification

**Social/Collective** (currently 35% complete)
- [ ] Implement comprehensive formula:
  ```python
  outer_planet_total * 0.4 +
  eleventh_house_dti * 0.3 +
  jupiter_saturn_aspects * 0.2 + # Social change markers
  aquarius_pisces_emphasis * 0.1 # Collective signs
  ```
- [ ] Add Jupiter-Saturn cycle consideration
- [ ] Add Aquarius/Pisces emphasis calculation
- [ ] Add collective theme identification

**Deliverable**: Enhanced `meters.py` with all weighted synthesis formulas

**Testing**:
- 50+ tests for weighted synthesis calculations
- Verification that weights sum to 1.0
- Comparison of V1 vs V2 meter values
- Edge case testing (missing components, extreme values)

---

### Sprint 5: House Transit Integration (1 week)
**Goal**: Add house transit calculations where specified

#### Tasks

**5.1 House Transit Calculator**
- [ ] Create `calculate_house_transits()` function
- [ ] For each house, calculate total DTI/HQS from planets transiting that house
- [ ] Return dict: `{1: {dti, hqs}, 2: {dti, hqs}, ..., 12: {dti, hqs}}`

**5.2 Integrate House Transits**
- [ ] Mental Clarity → 3rd house
- [ ] Communication Flow → 3rd house
- [ ] Physical Energy → 1st house (body), 6th house (health)
- [ ] Career Ambition → 10th house
- [ ] Opportunity Window → 11th house (networks), 2nd house (resources)
- [ ] Challenge Intensity → 12th house (isolation)
- [ ] Transformation → 8th house (crisis)
- [ ] Intuition → 12th house (unconscious), 9th house (spiritual)
- [ ] Innovation → 11th house (future)
- [ ] Karmic Lessons → 12th house (past), 4th house (roots)
- [ ] Social/Collective → 11th house (community)

**5.3 MC/IC/DSC/ASC Aspects**
- [ ] Extend aspect detection to include angles
- [ ] Career Ambition → MC aspects
- [ ] Relationship Harmony → DSC (7th house cusp) aspects
- [ ] Physical Energy → ASC aspects
- [ ] Karmic Lessons → IC aspects (family, roots)

**Deliverable**: House transit integration across 11 meters

**Testing**:
- Verify house calculations are accurate
- Test edge cases (empty houses, multiple planets in house)
- Validate angle aspect detection

---

### Sprint 6: Advanced Features & Polish (1-2 weeks)
**Goal**: Implement nice-to-have features from spec

#### Tasks

**6.1 Dynamic Orbs**
- [ ] Update `get_max_orb()` in `constants.py` to use variable orbs:
  ```python
  # Conjunction/Opposition:
  # Luminary involved: 10°
  # Outer planet transit: 6°
  # Default: 8°

  # Square/Trine:
  # Luminary involved: 8°
  # Outer planet transit: 5°
  # Default: 7°

  # Sextile:
  # Luminary involved: 6°
  # Outer planet transit: 4°
  # Default: 5°
  ```
- [ ] Update aspect detection to use dynamic orbs

**6.2 Auspicious Alignment Detection**
- [ ] Create `detect_auspicious_alignments()` function
- [ ] Patterns to detect:
  - Grand Trine (3 planets in trine)
  - Kite (Grand Trine + opposition)
  - Stellium (3+ planets in same sign)
  - Venus-Jupiter conjunction (classic benefit)
  - Sun-Jupiter trine (peak confidence)
- [ ] Add bonus scores to relevant meters

**6.3 Transformation Type Detection**
- [ ] For Transformation Pressure meter, identify dominant type:
  - Pluto > 60% → "Death/Rebirth"
  - Uranus > 60% → "Revolutionary Change"
  - Neptune > 60% → "Dissolution/Surrender"
  - Mixed → "Multi-Layered Transformation"

**6.4 Conflict Type Identification**
- [ ] For Conflict Risk meter, identify primary source:
  - Mars hard aspects → "Direct confrontation"
  - Uranus hard aspects → "Sudden disruption"
  - Pluto hard aspects → "Power struggles"
  - 7th house → "Partnership conflict"

**6.5 Career Phase Matrix**
- [ ] Implement 7-state career phase system:
  1. **Quiet** (low intensity)
  2. **Building** (moderate intensity, supportive)
  3. **Breakthrough** (high intensity, very supportive)
  4. **Challenge** (moderate intensity, challenging)
  5. **Crisis** (high intensity, very challenging)
  6. **Plateau** (moderate intensity, neutral)
  7. **Transition** (high transformation pressure)

**Deliverable**: Advanced features and refined interpretations

**Testing**:
- Test auspicious alignment detection on known configurations
- Verify transformation type identification
- Validate career phase matrix logic

---

### Sprint 7: Testing & Validation (1 week)
**Goal**: Comprehensive testing and quality assurance

#### Tasks

**7.1 Unit Test Expansion**
- [ ] Achieve 90%+ code coverage across all modules
- [ ] Add edge case tests:
  - No aspects detected
  - All hard aspects
  - All soft aspects
  - Extreme DTI values (>1000)
  - Extreme HQS values (±500)
  - Missing chart data (no houses, no angles)

**7.2 Integration Testing**
- [ ] Test complete meter calculation pipeline:
  - Load natal chart
  - Load transit chart
  - Calculate all 23 meters
  - Verify all fields populated
  - Check interpretation quality
- [ ] Test with diverse charts:
  - Different sun signs
  - Different ascendants
  - Different birth times
  - Different eras (1950s, 1980s, 2000s births)

**7.3 Regression Testing**
- [ ] Create benchmark charts (10 representative examples)
- [ ] Store V2 meter values as baseline
- [ ] Add regression test suite to prevent future breaks

**7.4 Performance Testing**
- [ ] Measure meter calculation time (target: <100ms per meter)
- [ ] Measure full 23-meter calculation time (target: <2s)
- [ ] Profile and optimize hotspots
- [ ] Add caching for repeated calculations

**7.5 Comparison Study**
- [ ] Run 1,000 random charts through V1 and V2
- [ ] Compare distributions:
  - Intensity ranges (Quiet/Moderate/High/Very High/Extreme)
  - Harmony ranges (Very Challenging/Challenging/Mixed/Supportive/Very Supportive)
  - Top aspects accuracy
- [ ] Document differences and improvements

**Deliverable**: Comprehensive test suite and performance benchmarks

---

### Sprint 8: Documentation & Examples (1 week)
**Goal**: Complete documentation for V2 features

#### Tasks

**8.1 Technical Documentation**
- [ ] Update `astrometers.md` with implementation notes
- [ ] Document calibration process in `calibration/README.md`
- [ ] Add architecture diagram showing all components
- [ ] Document all weighted synthesis formulas
- [ ] Add API reference for all public functions

**8.2 Usage Examples**
- [ ] Create `examples/` directory
- [ ] Add example: "Calculate all meters for a chart"
- [ ] Add example: "Weighted synthesis explained"
- [ ] Add example: "Understanding empirical calibration"
- [ ] Add example: "Comparing V1 vs V2 results"

**8.3 Migration Guide**
- [ ] Create `MIGRATION.md` for V1 → V2
- [ ] Document breaking changes
- [ ] Provide compatibility shims if needed
- [ ] Add changelog

**8.4 User-Facing Documentation**
- [ ] Write interpretation guide for each meter
- [ ] Explain what each meter measures
- [ ] Provide real-world examples
- [ ] Add FAQ section

**Deliverable**: Complete documentation suite

---

## Implementation Priorities

### CRITICAL (Must Have for V2)
1. **Empirical Calibration** (Sprint 3)
   - Blocks "top 1%", "top 5%" claims
   - Core scientific rigor requirement
2. **Full Weightage Factor** (Sprint 1)
   - Dignity, chart ruler, house multipliers
   - Major accuracy improvement
3. **Transit Power Enhancement** (Sprint 1)
   - Direction modifier, station detection
   - Timing accuracy critical
4. **Quality Factor Refinement** (Sprint 2)
   - Dynamic conjunction logic
   - Nuanced interpretation

### HIGH (Should Have for V2)
5. **Weighted Synthesis Formulas** (Sprint 4)
   - Meter-specific planet weights
   - Significantly improves accuracy
6. **House Transit Integration** (Sprint 5)
   - Adds missing context
   - Better domain-specific readings

### MEDIUM (Nice to Have for V2)
7. **Dynamic Orbs** (Sprint 6)
   - Polish and refinement
8. **Auspicious Alignments** (Sprint 6)
   - Enhanced user experience
9. **Advanced Type Detection** (Sprint 6)
   - More specific guidance

### LOW (Future Enhancement)
10. **User Sensitivity Tracking** (Post-V2)
    - Requires user feedback loop
11. **Historical Accuracy Validation** (Post-V2)
    - Requires user reports
12. **Machine Learning Calibration** (V3+)
    - Adaptive percentiles

---

## Success Criteria

### Quantitative Metrics
- [ ] 90%+ spec compliance (up from 40%)
- [ ] 90%+ code coverage
- [ ] All 23 meters calculate in <2 seconds
- [ ] "Extreme" label appears for ~1% of test cases
- [ ] "Very High" label appears for ~5% of test cases
- [ ] HQS neutral (45-55) appears for ~40% of test cases

### Qualitative Metrics
- [ ] Meter values feel more accurate than V1
- [ ] Interpretations are more nuanced
- [ ] Advice is more specific and actionable
- [ ] Top aspects better explain the reading
- [ ] System handles edge cases gracefully

### Technical Metrics
- [ ] No breaking API changes for V1 users
- [ ] Full backward compatibility maintained
- [ ] Performance improved or maintained
- [ ] Memory usage optimized
- [ ] Error handling comprehensive

---

## Risk Mitigation

### Risk 1: Calibration Dataset Size
**Problem**: Generating 110M calculations may take days
**Mitigation**:
- Use multiprocessing (40+ cores)
- Start with 10k charts, expand if needed
- Cache intermediate results
- Use sampling for validation

### Risk 2: Breaking Changes
**Problem**: V2 meter values will differ from V1
**Mitigation**:
- Maintain V1 compatibility mode
- Add version flag to API
- Document differences clearly
- Provide migration tools

### Risk 3: Complexity Creep
**Problem**: Weighted synthesis adds many parameters
**Mitigation**:
- Unit test each component
- Document all weights clearly
- Provide debug mode showing calculations
- Keep formulas in separate functions

### Risk 4: Performance Degradation
**Problem**: More calculations = slower runtime
**Mitigation**:
- Profile before optimization
- Cache repeated calculations
- Optimize hotspots only
- Use vectorized operations where possible

---

## Dependencies

### Code Dependencies
- Existing `core.py` module with DTI/HQS calculations
- Existing `normalization.py` module
- Existing `astro.py` module for chart data

### Data Dependencies
- Access to ephemeris data (Swiss Ephemeris via natal library)
- Birth chart generation capability
- Historical date calculations (2000-2030)

### External Dependencies
- `numpy` for percentile calculations
- `pandas` or `polars` for data analysis
- `multiprocessing` for parallel computation
- `pytest` for testing

---

## Timeline Estimates

### Aggressive Timeline (12 weeks)
- Sprint 1: Core Algorithm (2 weeks)
- Sprint 2: Quality Factor (1 week)
- Sprint 3: Calibration (2 weeks)
- Sprint 4: Weighted Synthesis (3 weeks)
- Sprint 5: House Transits (1 week)
- Sprint 6: Advanced Features (1 week)
- Sprint 7: Testing (1 week)
- Sprint 8: Documentation (1 week)

### Conservative Timeline (16 weeks)
- Add 1 week buffer to each sprint
- Add 2 weeks for calibration data generation
- Add 1 week for integration testing

### Recommended Approach
- Start with Sprints 1-2 (foundations)
- Run Sprint 3 in parallel (calibration is independent)
- Tackle Sprint 4 in phases (one meter category per week)
- Combine Sprints 7-8 (testing and docs together)

---

## Post-V2 Roadmap

### V2.1: User Sensitivity Integration
- Track user feedback on meter accuracy
- Build user-specific sensitivity profiles
- Adjust weightage factors based on reports

### V2.2: Predictive Features
- Add "upcoming peaks" to each meter
- Show intensity/harmony trends (next 7/30 days)
- Detect auspicious windows for specific activities

### V2.3: Compatibility Analysis
- Compare two charts
- Calculate synastry meters
- Show relationship dynamics

### V3: Machine Learning Enhancement
- Train on user-reported accuracy
- Adaptive normalization based on feedback
- Personalized interpretation styles

---

## Notes

### Technical Debt from V1
- Simplified weighting (resolved in Sprint 1)
- Theoretical maximums (resolved in Sprint 3)
- Missing house transits (resolved in Sprint 5)
- Generic synthesis (resolved in Sprint 4)

### Architectural Decisions
- Keep V1 compatibility mode
- Add version flag to all functions
- Maintain separate calibration data
- Document all breaking changes

### Testing Strategy
- Test-driven development for new features
- Regression tests against V1 baseline
- Integration tests for full pipeline
- Performance benchmarks for optimization

---

## Appendix A: V1 vs V2 Comparison

### V1 Implementation (Current)
```python
# Simple filtering + standard calculation
def calculate_mental_clarity_meter(all_aspects, date, transit_chart):
    mercury_aspects = filter_aspects_by_natal_planet(all_aspects, [Planet.MERCURY])
    reading = calculate_meter_score(mercury_aspects, "mental_clarity", date)

    if mercury_retrograde(transit_chart):
        reading.harmony *= 0.6

    return reading
```

### V2 Target Implementation
```python
# Weighted synthesis + empirical calibration
def calculate_mental_clarity_meter(all_aspects, date, transit_chart, natal_chart, house_transits):
    # Primary: Mercury aspects (60%)
    mercury_aspects = filter_aspects_by_natal_planet(all_aspects, [Planet.MERCURY])
    mercury_score = calculate_astrometers(mercury_aspects)

    # Secondary: 3rd house transits (15%)
    third_house_score = house_transits[3]

    # Tertiary: 3rd house ruler aspects (10%)
    third_ruler = get_house_ruler(natal_chart, 3)
    ruler_aspects = filter_aspects_by_natal_planet(all_aspects, [third_ruler])
    ruler_score = calculate_astrometers(ruler_aspects)

    # Weighted synthesis
    total_dti = (mercury_score.dti * 0.6 +
                 third_house_score['dti'] * 0.15 +
                 ruler_score.dti * 0.10)

    total_hqs = (mercury_score.hqs * 0.6 +
                 third_house_score['hqs'] * 0.15 +
                 ruler_score.hqs * 0.10)

    # Mercury retrograde modifier
    if is_mercury_retrograde(transit_chart):
        total_dti *= 0.8
        total_hqs *= 0.6

    # Empirical normalization
    intensity = normalize_with_empirical(total_dti, 'mercury_dti_p99', 100)
    harmony = normalize_harmony_empirical(total_hqs, 'mercury_hqs_p01', 'mercury_hqs_p99', 100)

    # Enhanced interpretation
    interpretation = generate_mental_clarity_interpretation(intensity, harmony, mercury_rx=is_mercury_retrograde(transit_chart))

    return MeterReading(
        meter_name="mental_clarity",
        intensity=intensity,
        harmony=harmony,
        interpretation=interpretation,
        # ... full explainability
    )
```

---

## Appendix B: Calibration Constants Format

### `calibration/constants.json`
```json
{
  "version": "2.0",
  "generated_date": "2025-10-26",
  "dataset_size": 50000,
  "date_range": "2000-01-01 to 2030-12-31",

  "dti_percentiles": {
    "p01": 5.2,
    "p05": 12.8,
    "p10": 21.4,
    "p25": 45.3,
    "p50": 98.7,
    "p75": 167.2,
    "p90": 256.8,
    "p95": 342.1,
    "p99": 521.4
  },

  "hqs_percentiles": {
    "p01": -187.3,
    "p05": -112.6,
    "p10": -78.4,
    "p25": -32.1,
    "p50": 2.4,
    "p75": 38.7,
    "p90": 89.2,
    "p95": 134.6,
    "p99": 213.8
  },

  "mercury_dti_percentiles": {
    "p50": 15.3,
    "p75": 28.7,
    "p90": 45.2,
    "p95": 62.8,
    "p99": 98.4
  },

  "mercury_hqs_percentiles": {
    "p01": -42.1,
    "p05": -28.3,
    "p50": 0.8,
    "p95": 31.2,
    "p99": 54.7
  }

  # ... similar for all meter-specific percentiles
}
```

---

## Appendix C: Quick Reference

### Sprint Completion Checklist

**Sprint 1: Core Algorithm**
- [ ] Dignity scoring implemented (120 tests)
- [ ] Chart ruler bonus added
- [ ] Sensitivity factor integrated
- [ ] Direction modifier verified
- [ ] Station detection working
- [ ] DTI values increase 20-40% vs V1

**Sprint 2: Quality Factor**
- [ ] Conjunction logic implemented (100 pair tests)
- [ ] All planet combinations tested
- [ ] HQS values shift appropriately

**Sprint 3: Calibration**
- [ ] 10k+ natal charts generated
- [ ] 110M+ calculations completed
- [ ] Percentiles calculated and stored
- [ ] Normalization functions updated
- [ ] Validation tests pass

**Sprint 4: Weighted Synthesis**
- [ ] All 23 meters have weighted formulas
- [ ] Weights sum to 1.0 (verified)
- [ ] House components integrated
- [ ] Planet interaction rules implemented
- [ ] 50+ synthesis tests passing

**Sprint 5: House Transits**
- [ ] House transit calculator working
- [ ] 11 meters updated with house components
- [ ] Angle aspects detected
- [ ] Tests passing

**Sprint 6: Advanced Features**
- [ ] Dynamic orbs implemented
- [ ] Auspicious alignments detected
- [ ] Type identification working
- [ ] Career phase matrix implemented

**Sprint 7: Testing**
- [ ] 90%+ code coverage
- [ ] Edge cases covered
- [ ] Integration tests passing
- [ ] Performance benchmarks met
- [ ] Regression tests created

**Sprint 8: Documentation**
- [ ] Technical docs updated
- [ ] Examples created
- [ ] Migration guide written
- [ ] User docs complete

---

**END OF V2 SPRINT PLAN**

*Last Updated: 2025-10-26*
*Document Version: 1.0*
*Target Completion: Q1 2026*
