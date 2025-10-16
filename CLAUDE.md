# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

arca-backend is the backend service for a daily tarot and astrology app that provides personalized spiritual guidance through AI-powered readings. The app helps users navigate real-life situations (relationships, career, life transitions) through the lens of ancient spiritual practices.

**Core Functionality:**
- LLM-driven personalized tarot and astrology readings
- Theme tracking and pattern recognition across user journeys
- Evolving insights that adapt to user patterns and growth
- Journey documentation and synthesized insights over time

**Backend Architecture:**
- **Firebase Cloud Functions** - Serverless functions for all backend logic
- **Firestore** - NoSQL database for user data, readings, themes, and journey history
- **Firebase Authentication** - User auth and session management

**Key Technologies:**
- `natal` - Astrology calculations (birth charts, transits, aspects)
- `rich` - Terminal output formatting for development
- LLM integration (to be implemented) for generating personalized readings
- Python runtime for Cloud Functions

**Target Platform:** iOS app (this is the backend service)

## Development Environment

- **Package Manager**: Uses `uv` for dependency management (NOT pip)
- **Python Version**: 3.13+
- **Virtual Environment**: `.venv` directory (managed by uv)

## Common Commands

### Package Management
```bash
# Add a new package
uv add <package-name>

# Add a dev dependency
uv add --dev <package-name>

# Sync dependencies
uv sync
```

### Running Code
```bash
# Run the main script
python hello.py

# Or with uv
uv run hello.py
```

### Testing
```bash
# Run tests directly with pytest
pytest

# Run a single test file
pytest path/to/test_file.py

# Run a specific test
pytest path/to/test_file.py::test_function_name
```

## Project Structure

Currently in early development. Firebase-based architecture:

**Firestore Collections (Data Layer):**
- `users/{userId}` - User document with birth data, preferences, profile information
  - `entries/` (subcollection) - Journal entries with tarot/astrology readings
  - `insights/` (subcollection) - Consolidated themes, patterns, synthesized spiritual insights
- `memory/{userId}` - Server-side only personalization data (what we know about the user for LLM context, NOT accessible to user)

**Cloud Functions (Backend Logic):**
- **Callable functions** (invoked via Firebase SDK from iOS):
  - Generate tarot/astrology readings (using `natal` for calculations, LLM for interpretation)
  - Create journal entries
  - Retrieve user profile and insights
  - Query journal history

- **Firestore triggers** (automated background processing):
  - `onEntryCreate` - When journal entry is created, extract themes and update insights
  - `onInsightUpdate` - Update memory collection with patterns for LLM personalization
  - Theme tracking and evolution analysis across entries
  - Journey synthesis for ongoing spiritual narrative

**API Design:**
- iOS app calls functions directly via Firebase SDK (no REST endpoints)
- No real-time listeners - data fetched on demand
- Background triggers consolidate insights and memory asynchronously
- Memory collection has strict security rules (server-side only, never exposed to client)

## Design Principles

**Brand Voice & Positioning:**
- Elevated and sacred (not transactional or fortune-telling)
- Transformational framing (spiritual evolution, not problem-solving)
- Personal and intimate (tailored to individual journeys)
- Ancient wisdom meets modern life
- Accessible to everyone, not gatekept

**Personalization Strategy:**
- LLM responses must feel mystical and intuitive, like the app "knows" the user
- Surface recurring themes organically (e.g., boundaries, self-worth, career courage)
- Connect dots across readings to show how situations relate
- Adapt guidance depth based on user's spiritual journey progression
- Never explicitly mention AI/technology to users - maintain mystical framing

**User Experience Goals:**
- Users should feel understood and validated
- Reframe everyday concerns as opportunities for growth
- Create a sacred daily practice, not just an app check-in
- Document and reflect spiritual evolution over time

## Important Notes

- Never commit changes to git (user preference)
- Always use `uv` commands instead of `pip` for package management
- Call pytest directly rather than through other test runners
