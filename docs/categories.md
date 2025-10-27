# 🗺️ Astro Meters: Complete Mapping Documentation

## Overview

This document defines the organizational structure of the 23 Astro Meters, grouped into a hierarchical taxonomy designed for intuitive navigation and meaningful thematic coherence.

---

## 📐 Architecture Principles

### **Three-Tier Hierarchy**

```
Level 1: SUPER-GROUPS (5 domains)
    └─ Level 2: GROUPS (9 categories)
        └─ Level 3: METERS (23 individual gauges)
```

### **Design Goals**
1. **Intuitive Navigation**: Users can quickly locate relevant meters
2. **Thematic Coherence**: Related meters are grouped together
3. **Progressive Disclosure**: Overview → Detail → Specialization
4. **Balanced Distribution**: No group feels orphaned or overcrowded

---

## 🏗️ Complete Mapping Structure

### **LEVEL 1: SUPER-GROUPS** (5 Domains)

| Super-Group | Description | Meter Count | User Journey Stage |
|-------------|-------------|-------------|-------------------|
| **📊 OVERVIEW** | High-level dashboard summary | 2 | Entry point |
| **🧠 INNER WORLD** | Internal states, feelings, thoughts | 6 | Self-awareness |
| **💪 OUTER WORLD** | Actions, career, physical expression | 5 | External engagement |
| **🌱 EVOLUTION** | Growth, challenges, transformation | 3 | Development |
| **🔮 DEEPER DIMENSIONS** | Elements, spirituality, collective | 7 | Depth & context |

---

### **LEVEL 2 & 3: GROUPS AND METERS**

---

## 📊 SUPER-GROUP 1: OVERVIEW
**Purpose**: Immediate snapshot of overall astrological weather
**When to Check**: Daily, first thing
**User Value**: "What's the energy like today?"

### Group: OVERVIEW (2 meters)

| Meter | Code | Measures | Primary Planets | Range Interpretation |
|-------|------|----------|----------------|---------------------|
| **Overall Intensity** | `overall_intensity` | Magnitude of all astrological activity | All transiting planets | 0-30: Quiet<br>31-60: Moderate<br>61-85: High<br>86-100: Extreme |
| **Overall Harmony** | `overall_harmony` | Net supportive vs. challenging quality | All aspects (HQS) | 0-30: Challenging<br>31-60: Mixed<br>61-100: Supportive |

**Visual Display**: Side-by-side gauges with color coding
**Key Insight**: These two metrics together tell the day's story—intensity × quality = experience

---

## 🧠 SUPER-GROUP 2: INNER WORLD
**Purpose**: Understanding internal states—thoughts, feelings, and inner resources
**When to Check**: Morning (planning mode) or when feeling off-center
**User Value**: "How am I doing inside?"

---

### Group: MIND (3 meters)
**Focus**: Cognitive function, communication, decision-making

| Meter | Code | Measures | Primary Planets | Key Aspects Tracked |
|-------|------|----------|----------------|---------------------|
| **Mental Clarity** | `mental_clarity` | Thinking sharpness, focus, mental fog | Mercury | Mercury to all planets<br>3rd house transits |
| **Decision Quality** | `decision_quality` | Judgment reliability, wisdom access | Mercury, Jupiter, Saturn, Neptune | Mercury clarity +<br>Jupiter confidence +<br>Saturn realism ±<br>Neptune confusion - |
| **Communication Flow** | `communication_flow` | Expression ease, being understood | Mercury, Venus, Mars | Mercury (thought) +<br>Venus (diplomacy) +<br>Mars (assertion/conflict) ± |

**Use Cases**:
- 🟢 High Mental Clarity + High Decision Quality = Sign contracts, make big choices
- 🔴 Low Mental Clarity + Low Decision Quality = Delay important decisions
- 🟡 Mixed = Proceed cautiously, get second opinions

---

### Group: EMOTIONS (3 meters)
**Focus**: Emotional life, relationships, and inner resilience

| Meter | Code | Measures | Primary Planets | Key Aspects Tracked |
|-------|------|----------|----------------|---------------------|
| **Emotional Intensity** | `emotional_intensity` | Depth and strength of feelings | Moon, Venus, Pluto, Neptune | Moon transits (daily mood)<br>Venus (affection)<br>Pluto (depth/crisis)<br>Neptune (sensitivity) |
| **Relationship Harmony** | `relationship_harmony` | Ease in partnerships and connections | Venus, Mars, 7th house | Venus harmony<br>Mars attraction/friction<br>7th house activation |
| **Emotional Resilience** | `emotional_resilience` | Capacity to handle stress and bounce back | Moon, Saturn, Sun | Moon-Saturn (boundaries)<br>Sun vitality<br>Mars fighting spirit<br>Jupiter optimism |

**Interplay**:
```
High Emotional Intensity + Low Resilience = Overwhelm risk
High Emotional Intensity + High Resilience = Capacity to process deep feelings
Low Intensity + Low Resilience = Fragility even in quiet times
```

**Use Cases**:
- 🟢 High Resilience = Good time to tackle difficult emotional work
- 🔴 Low Resilience = Prioritize self-care, minimize stress
- ❤️ High Relationship Harmony = Deep conversations, quality time
- ⚠️ Low Relationship Harmony = Give space, avoid triggering topics

---

## 💪 SUPER-GROUP 3: OUTER WORLD
**Purpose**: Engagement with external reality—body, action, career, opportunities
**When to Check**: When planning activities, career moves, physical pursuits
**User Value**: "What should I DO today?"

---

### Group: BODY (3 meters)
**Focus**: Physical energy, action-taking, conflict management

| Meter | Code | Measures | Primary Planets | Key Aspects Tracked |
|-------|------|----------|----------------|---------------------|
| **Physical Energy** | `physical_energy` | Vitality, stamina, physical readiness | Sun, Mars, 1st house | Mars (primary drive)<br>Sun (core vitality)<br>Jupiter-Mars (expansion)<br>Saturn-Mars (depletion) |
| **Conflict Risk** | `conflict_risk` | Likelihood of arguments, accidents, aggression | Mars, Uranus, Pluto | Mars hard aspects<br>Uranus (accidents)<br>Pluto (power struggles)<br>7th house conflicts |
| **Motivation Drive** | `motivation_drive` | Ambition, initiative, will to pursue goals | Mars, Sun, Jupiter, 10th house | Mars (action impulse)<br>Sun (willpower)<br>Jupiter (enthusiasm)<br>Saturn (discipline/drag) |

**Use Cases**:
- 💪 High Physical Energy + Low Conflict Risk = Ideal for intense workouts, ambitious projects
- ⚠️ High Conflict Risk = Drive carefully, avoid provocative situations, count to 10
- 🔥 High Motivation + High Physical Energy = Launch initiatives, tackle big goals
- 😴 Low Motivation + Low Physical Energy = Rest day, gentle activities only

---

### Group: CAREER (2 meters)
**Focus**: Professional life, ambition, opportunities

| Meter | Code | Measures | Primary Planets | Key Aspects Tracked |
|-------|------|----------|----------------|---------------------|
| **Career Ambition** | `career_ambition` | Professional focus, recognition, achievement | Saturn, Jupiter, Sun, Mars, 10th house, MC | 10th house transits<br>MC aspects<br>Saturn (responsibility/tests)<br>Jupiter (opportunity)<br>Sun (recognition) |
| **Opportunity Window** | `opportunity_window` | Timing for expansion, luck, new ventures | Jupiter, Venus, Sun, North Node, 2nd/11th houses | Jupiter primary<br>Venus (attraction)<br>North Node (karmic timing)<br>2nd house (resources)<br>11th house (networks) |

**Decision Matrix**:

| Career Ambition | Opportunity Window | Action |
|----------------|-------------------|--------|
| High | High | **GOLDEN WINDOW**: Ask for raise, launch business, take big swings |
| High | Low | Effort without reward; work hard but don't expect immediate results |
| Low | High | Opportunities arrive but lack drive to pursue; motivate yourself |
| Low | Low | Maintenance mode; steady, no major career moves |

**Use Cases**:
- 🎯 Career Ambition at 80+ = Ask for promotion, present to leadership
- 🍀 Opportunity Window at 80+ = Network, pitch ideas, invest
- ⚠️ Career Ambition at 90+ but Harmony <30 = Career crisis; restructuring needed

---

## 🌱 SUPER-GROUP 4: EVOLUTION
**Purpose**: Growth through challenge, transformation, and breakthrough
**When to Check**: During difficult periods or when seeking growth insights
**User Value**: "What am I learning? Where am I growing?"

### Group: EVOLUTION (3 meters)
**Focus**: Challenge, transformation, innovation

| Meter | Code | Measures | Primary Planets | Key Aspects Tracked |
|-------|------|----------|----------------|---------------------|
| **Challenge Intensity** | `challenge_intensity` | Difficulty level, tests, lessons | Saturn, Pluto, Chiron, 12th house, South Node | Saturn (primary teacher)<br>Pluto (breakdown/rebirth)<br>Chiron (wounding/healing)<br>12th house (isolation)<br>South Node (release) |
| **Transformation Pressure** | `transformation_pressure` | Evolutionary push, upheaval, rebirth | Pluto, Uranus, Neptune, 8th house | Pluto (death/rebirth)<br>Uranus (revolution)<br>Neptune (dissolution)<br>8th house (crisis) |
| **Innovation Breakthrough** | `innovation_breakthrough` | Sudden insights, paradigm shifts, awakening | Uranus, 11th house | Uranus primary<br>Uranus-Mercury (mental breakthroughs)<br>Uranus-Sun (identity awakening)<br>11th house (future vision) |

**Philosophical Framework**:

```
Challenge → Transformation → Innovation
   ↓              ↓              ↓
  Test        Death/Rebirth  New Paradigm
  Lesson      Pressure        Insight
  Saturn      Pluto/Uranus    Uranus
```

**Use Cases**:
- 🏔️ High Challenge Intensity = Life is testing you; dig deep, seek support
- 🦋 High Transformation Pressure = You're being reborn; surrender to the process
- 💡 High Innovation = Breakthrough territory; document insights, act on revelations
- 🌱 All three high simultaneously = **Major life crossroads**: Old self dying, new self emerging through crisis-driven insight

**Timing Advice**:
- Peak Challenge (80-100) = Don't make it harder; simplify, ask for help, therapy
- Peak Transformation (80-100) = Trust the upheaval; what's breaking down needs to
- Peak Innovation (80-100) = Act on insights immediately; rare window

---

## 🔮 SUPER-GROUP 5: DEEPER DIMENSIONS
**Purpose**: Foundational energies, spiritual awareness, and collective currents
**When to Check**: When seeking deeper context or spiritual perspective
**User Value**: "What's happening beneath the surface? What's the bigger picture?"

---

### Group: ELEMENTS (4 meters)
**Focus**: Temperament balance, elemental energy distribution

| Meter | Code | Measures | Element | Keywords | Planetary Rulers |
|-------|------|----------|---------|----------|-----------------|
| **Fire Energy** | `fire_energy` | Initiative, inspiration, enthusiasm | Fire (Aries/Leo/Sagittarius) | Action, courage, passion, impulsiveness | Sun, Mars, Jupiter in fire signs |
| **Earth Energy** | `earth_energy` | Grounding, practicality, manifestation | Earth (Taurus/Virgo/Capricorn) | Stability, resources, patience, rigidity | Venus, Saturn in earth signs |
| **Air Energy** | `air_energy` | Mental activity, communication, social connection | Air (Gemini/Libra/Aquarius) | Ideas, objectivity, dialogue, detachment | Mercury, Venus, Saturn in air signs |
| **Water Energy** | `water_energy` | Emotions, intuition, depth | Water (Cancer/Scorpio/Pisces) | Feelings, empathy, sensitivity, moodiness | Moon, Neptune, Pluto in water signs |

**Calculation Method**:
```
Element_Current = (0.7 × Natal_Element%) + (0.3 × Transit_Element%)
Deviation = Transit% - Natal%
Status = Elevated (>+5%), Suppressed (<-5%), or Normal
```

**Interpretation Matrix**:

| Element | Low (<20%) | Balanced (20-35%) | High (>35%) |
|---------|-----------|------------------|------------|
| **Fire** | Lack motivation, need inspiration | Healthy initiative | Impulsive, restless, burnout risk |
| **Earth** | Ungrounded, impractical | Stable and productive | Rigid, stuck, overly material |
| **Air** | Isolated, subjective | Clear thinking | Overthinking, scattered, detached |
| **Water** | Emotionally disconnected | Emotionally intelligent | Overwhelmed, overly sensitive, boundary loss |

**Use Cases**:
- 🔥 Fire Elevated = Channel into exercise, creative projects, bold action
- 🌍 Earth Elevated = Focus on finances, building, physical world
- 💨 Air Elevated = Network, learn, communicate, socialize
- 🌊 Water Elevated = Process emotions, creative expression, spiritual practice
- **Multiple elements low**: May feel off-balance or disconnected

**Practical Application**:
```
If Earth is at 10% (low):
→ You may neglect practical matters, finances, physical health
→ Remedy: Force yourself to budget, organize, attend to body

If Fire is at 50% (high):
→ You're full of ideas and initiative but may burn out
→ Remedy: Pace yourself, finish what you start, rest
```

---

### Group: SPIRITUAL (2 meters)
**Focus**: Soul-level awareness, karmic themes, spiritual sensitivity

| Meter | Code | Measures | Primary Planets | Key Aspects Tracked |
|-------|------|----------|----------------|---------------------|
| **Intuition/Spirituality** | `intuition_spirituality` | Psychic sensitivity, spiritual openness, connection to subtle realms | Neptune, Moon, 12th/9th houses | Neptune-Moon (high sensitivity)<br>Neptune transits<br>12th house (transcendence)<br>9th house (higher mind)<br>Uranus-Neptune (spiritual awakening) |
| **Karmic Lessons** | `karmic_lessons` | Soul-growth themes, past-pattern resolution | North Node, South Node, Saturn, Chiron | North Node (evolutionary path)<br>South Node (release old patterns)<br>Saturn (karmic responsibility)<br>Chiron (core wound healing)<br>4th/12th house (past) |

**Spiritual Development Path**:

```
Low Karmic Lessons + Low Intuition = Integration period; live your learning
Moderate Karmic + High Intuition = Lessons arrive with spiritual awareness to process them
High Karmic + Low Intuition = Lessons feel harsh; cultivate awareness through meditation/therapy
High Karmic + High Intuition = Major soul-growth opportunity; profound transformation possible
```

**Use Cases**:
- 🔮 High Intuition = Trust gut feelings, practice divination, creative/artistic flow
- ⚠️ Very High Intuition (>85) = Overwhelm risk; ground yourself, create boundaries
- 🎓 High Karmic Lessons = Pay attention to repeating patterns; therapy valuable
- 🙏 Both High = Spiritual breakthrough territory; this is why you incarnated

**Practices by Level**:

| Intuition Level | Recommended Practices |
|----------------|----------------------|
| 0-30 (Low) | Meditation basics, journaling, nature walks |
| 31-60 (Moderate) | Dream work, oracle cards, creative expression |
| 61-80 (High) | Deep meditation, energy work, spiritual study |
| 81-100 (Extreme) | **Grounding critical**: Limit stimulation, eat well, physical exercise, protection practices |

---

### Group: COLLECTIVE (1 meter)
**Focus**: Connection to societal currents and collective consciousness

| Meter | Code | Measures | Primary Planets | Key Aspects Tracked |
|-------|------|----------|----------------|---------------------|
| **Social Collective** | `social_collective` | Attunement to zeitgeist, social consciousness, generational themes | Uranus, Neptune, Pluto, Saturn-Jupiter cycle, 11th house | Outer planet transits (slow-moving generational)<br>11th house (groups, humanity)<br>Saturn-Jupiter (social structures)<br>Aquarius/Pisces emphasis |

**Interpretation Levels**:

| Range | Connection Level | Experience | Guidance |
|-------|-----------------|------------|----------|
| 0-30 | Personal Focus | Individual concerns dominate; unaware of collective | Focus on personal life; not your time for activism |
| 31-60 | Aware | Notice social trends; mild engagement | Stay informed, contribute moderately |
| 61-80 | Engaged | Feel collective currents strongly | Join groups, social causes, community leadership |
| 81-100 | Revolutionary | Embodying collective change | Major social contribution; you're an agent of transformation |

**Historical Context**:
- Major social movements (civil rights, environmental activism) correlate with high collective activation in many charts simultaneously
- When outer planets (Uranus/Neptune/Pluto) make major aspects to personal planets, individuals "plug into" collective evolution

**Use Cases**:
- 🌍 High Social Collective = Your work/voice matters to society; think bigger than self
- 🏠 Low Social Collective = Personal life needs attention; not every day is about the world
- 📊 Track this alongside major world events to see your personal connection to history

---

## 🗂️ Technical Mapping Reference

### **Enum Definition** (for code implementation)

```python
from enum import Enum

class SuperGroup(Enum):
    """Level 1: Major domains"""
    OVERVIEW = "overview"
    INNER_WORLD = "inner_world"
    OUTER_WORLD = "outer_world"
    EVOLUTION = "evolution"
    DEEPER_DIMENSIONS = "deeper_dimensions"

class MeterGroup(Enum):
    """Level 2: Thematic categories"""
    # OVERVIEW super-group
    OVERVIEW = "overview"

    # INNER_WORLD super-group
    MIND = "mind"
    EMOTIONS = "emotions"

    # OUTER_WORLD super-group
    BODY = "body"
    CAREER = "career"

    # EVOLUTION super-group
    EVOLUTION = "evolution"

    # DEEPER_DIMENSIONS super-group
    ELEMENTS = "elements"
    SPIRITUAL = "spiritual"
    COLLECTIVE = "collective"

# Mapping: Meter → Group → Super-Group
METER_HIERARCHY = {
    # OVERVIEW
    'overall_intensity': (MeterGroup.OVERVIEW, SuperGroup.OVERVIEW),
    'overall_harmony': (MeterGroup.OVERVIEW, SuperGroup.OVERVIEW),

    # INNER WORLD → MIND
    'mental_clarity': (MeterGroup.MIND, SuperGroup.INNER_WORLD),
    'decision_quality': (MeterGroup.MIND, SuperGroup.INNER_WORLD),
    'communication_flow': (MeterGroup.MIND, SuperGroup.INNER_WORLD),

    # INNER WORLD → EMOTIONS
    'emotional_intensity': (MeterGroup.EMOTIONS, SuperGroup.INNER_WORLD),
    'relationship_harmony': (MeterGroup.EMOTIONS, SuperGroup.INNER_WORLD),
    'emotional_resilience': (MeterGroup.EMOTIONS, SuperGroup.INNER_WORLD),

    # OUTER WORLD → BODY
    'physical_energy': (MeterGroup.BODY, SuperGroup.OUTER_WORLD),
    'conflict_risk': (MeterGroup.BODY, SuperGroup.OUTER_WORLD),
    'motivation_drive': (MeterGroup.BODY, SuperGroup.OUTER_WORLD),

    # OUTER WORLD → CAREER
    'career_ambition': (MeterGroup.CAREER, SuperGroup.OUTER_WORLD),
    'opportunity_window': (MeterGroup.CAREER, SuperGroup.OUTER_WORLD),

    # EVOLUTION
    'challenge_intensity': (MeterGroup.EVOLUTION, SuperGroup.EVOLUTION),
    'transformation_pressure': (MeterGroup.EVOLUTION, SuperGroup.EVOLUTION),
    'innovation_breakthrough': (MeterGroup.EVOLUTION, SuperGroup.EVOLUTION),

    # DEEPER DIMENSIONS → ELEMENTS
    'fire_energy': (MeterGroup.ELEMENTS, SuperGroup.DEEPER_DIMENSIONS),
    'earth_energy': (MeterGroup.ELEMENTS, SuperGroup.DEEPER_DIMENSIONS),
    'air_energy': (MeterGroup.ELEMENTS, SuperGroup.DEEPER_DIMENSIONS),
    'water_energy': (MeterGroup.ELEMENTS, SuperGroup.DEEPER_DIMENSIONS),

    # DEEPER DIMENSIONS → SPIRITUAL
    'intuition_spirituality': (MeterGroup.SPIRITUAL, SuperGroup.DEEPER_DIMENSIONS),
    'karmic_lessons': (MeterGroup.SPIRITUAL, SuperGroup.DEEPER_DIMENSIONS),

    # DEEPER DIMENSIONS → COLLECTIVE
    'social_collective': (MeterGroup.COLLECTIVE, SuperGroup.DEEPER_DIMENSIONS),
}
```

---

## 📋 Summary Statistics

| Category | Count |
|----------|-------|
| **Total Meters** | 23 |
| **Super-Groups** | 5 |
| **Groups** | 9 |
| **Largest Group** | ELEMENTS (4 meters) |
| **Smallest Groups** | COLLECTIVE (1 meter) |
| **Average Meters per Group** | 2.6 |

**Distribution by Super-Group**:
- 📊 OVERVIEW: 2 (9%)
- 🧠 INNER WORLD: 6 (26%)
- 💪 OUTER WORLD: 5 (22%)
- 🌱 EVOLUTION: 3 (13%)
- 🔮 DEEPER DIMENSIONS: 7 (30%)

---

**End of Mapping Documentation**

This structure balances **accessibility** (clear top-level overview) with **depth** (specialized meters for advanced users) while maintaining **thematic coherence** throughout the hierarchy.