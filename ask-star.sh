#!/bin/bash
# Test Ask the Stars endpoint

curl -X POST "https://us-central1-arca-baf77.cloudfunctions.net/ask_the_stars" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dev_arca_2025" \
  -d '{
    "user_id": "integration_test_user",
    "question": "How will be my day",
    "horoscope_date": "2025-11-27"
  }'
