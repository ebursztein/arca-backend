"""
Shared Firebase Secret Parameters.

This module centralizes all SecretParam declarations to avoid duplicate
parameter errors. Firebase only allows each secret to be declared once
per project.

Usage:
    from secrets import GEMINI_API_KEY, POSTHOG_API_KEY
"""

from firebase_functions import params

GEMINI_API_KEY = params.SecretParam("GEMINI_API_KEY")
POSTHOG_API_KEY = params.SecretParam("POSTHOG_API_KEY")
