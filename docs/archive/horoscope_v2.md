# Horoscope V2 Design

Pivot to rely on astrometers data for horoscope generation.

Flow:
DailyHorosope:
 1. Compute astrometers readings for the day
 2. pass it with other information to the LLM prompt to generate the horoscope fields
 using as a baseline and enhanching them with an interpretation per meter
 3. Combine the astrometers and the LLM output to generate the daily horoscope returned to the user

DetailedHoroscope:
1. pass the astrometers readings for the day and the DailyHoroscope to the LLM prompt to generate a more detailed horoscope

## TODO


## Models
models.py

### DailyHoroscope(BaseModel)
-   Remove key_active_transit # we have the summary in the astrometers now
- Remove area_of_life_activated # we have the astrometers for that now
- Add astrometers and the key transists

### HoroscopeDetails
- Rework such that it is providing interpreation for each of the meters of the daily astrometers
as those will be slow otherwise.

### CompleteHoroscope
Fix to contain both DailyHoroscope and HoroscopeDetails

### Memory

- Must keep recent horoscopes in memory to provide continuity and context to the LLM
- Evenutally use it to compute the astrometers trends over time (V2)

## Prompts
prompts/horoscope/
- Remove references to removed fields and simplify the prompts
- Update the prompts to reflect the new data available from astrometers


## LLM
- Update the calls to make sure the templates receive the right data
- Update the parsing of the results to return the modified models.