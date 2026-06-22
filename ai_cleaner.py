# ai_cleaner.py
from openai import OpenAI
from logger import logger
from db_config import OPENAI_API_KEY

client = OpenAI(
    api_key=OPENAI_API_KEY,
)

def clean_event_duration(time_raw: str) -> str:
    """Use OpenAI to extract event duration from raw time string."""
    if not time_raw or time_raw == 'N/A':
        return 'N/A'
    
    prompt = f"""Extract the duration of this event from the time string below.
Return ONLY a number followed by 'h', like '5h', '2h', '1.5h'.
If the event spans multiple days, calculate total hours.
If you cannot determine the duration, return 'N/A'.

Time string: {time_raw}"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        result = response.choices[0].message.content.strip()
        logger.info(f"Duration cleaned: {time_raw} -> {result}")
        return result
    except Exception as e:
        logger.error(f"OpenAI error cleaning duration: {e}")
        return 'N/A'


def clean_rough_location(address_raw: str) -> str:
    """Use OpenAI to extract rough location from raw address string."""
    if not address_raw or address_raw == 'N/A':
        return 'N/A'
    
    prompt = f"""Extract the location from this address string.
Return ONLY the city or suburb and city, like 'Parnell, Auckland' or 'Auckland' or 'Wellington'.
If there is a recognizable NZ city or suburb, return it.
If you cannot determine any location, return 'N/A'.

Address string: {address_raw}"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        result = response.choices[0].message.content.strip()
        logger.info(f"Location cleaned: {address_raw} -> {result}")
        return result
    except Exception as e:
        logger.error(f"OpenAI error cleaning location: {e}")
        return 'N/A'
    
    
