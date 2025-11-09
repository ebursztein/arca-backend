# Horoscope Templates

This directory contains Jinja2 templates for LLM prompt generation.

## Active Templates (Daily Horoscope)

These templates are used in production for the single-prompt daily horoscope system:

### `daily_static.j2`
- System instructions and style guidelines
- Shared across all users
- **Cacheable** - same for everyone, changes infrequently

### `daily_dynamic.j2`
- Daily transit data
- Astrometers readings
- Meter group data
- **Not cacheable** - changes daily

### `personalization.j2`
- User-specific context (natal chart, sun sign profile, memory)
- Shared between all horoscope types
- **Not cacheable** - memory updates frequently as users interact with the app

**Composition:**
```
Daily Horoscope Prompt = daily_static + daily_dynamic + personalization
```

## Archived Templates (Detailed Horoscope - DEPRECATED)

These templates are kept for reference only and are NOT used in the current implementation:

### `detailed_static.j2` ⚠️ ARCHIVED
- Original system instructions for two-prompt architecture
- Kept for historical reference

### `detailed_dynamic.j2` ⚠️ ARCHIVED
- Original dynamic template for detailed life domain predictions
- Kept for historical reference

**Historical Context:**
The original architecture used a two-prompt system:
1. Fast daily horoscope (Prompt 1) - implemented
2. Detailed horoscope with 9 life domains (Prompt 2) - deprecated

The current implementation consolidates everything into a single prompt for better user experience and cost efficiency.

## Implementation Notes

- Templates are loaded via Jinja2 `FileSystemLoader`
- All templates support full Jinja2 syntax (filters, conditionals, loops)
- Path: `functions/templates/horoscope/`
- Loaded in: `functions/llm.py`
