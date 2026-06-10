from datetime import date, time, datetime
from typing import Optional
from logger import logger
#utils.py

# clean event_date_raw
# Translate raw date string to normalized date
def parse_normalized_date(date_raw:str) -> Optional[date]:
    if not date_raw:
        return None
    try:
        date_str = date_raw.strip()
        date_obj = datetime.strptime(date_str, "%A, %d %B %Y").date()
        print(date_obj)
        return date_obj
    except Exception as e:
        logger.error(f"Date parse failure:{e}",exc_info=True)
        return None

def parse_normalized_time(time_raw:str) -> Optional[time]:
    if not time_raw:
        return None
    try:
        time_str = time_raw.strip()
        time_obj = datetime.strptime(time_str, "%I:%M %p").time()
        print(time_obj)
        return time_obj
    except Exception as e:
        logger.error(f"Time parse failure:{e}",exc_info=True)
        return None




