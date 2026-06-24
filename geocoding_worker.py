import requests
from logger import logger
from db_config import GEOCODING_API
from dbManager import batch_update_event_coordinates, get_detail_location_from_events
import time


def geocode_parse_address_by_local_nominatim(address_string:str) -> dict | None:
    """
    Use local Nominatim service to geocode an address.
    """
    url = "http://localhost:8080/search.php"
    params = {
        "q": address_string,
        "format": "json",
        "limit": 1
    }
    headers = {"User-Agent": "my_geocoder_app"} 
    coordinates = {} # store latitude and longitude

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=5)
        print("RESP:", resp.status_code)
        if resp.status_code == 200:
            data = resp.json()
            if data:
                coordinates={
                    "latitude": float(data[0]["lat"]),
                    "longitude": float(data[0]["lon"])
                }
                return coordinates
            else:
                print("data:", data)
        else:
            logger.error(f"Geocoding failed: {resp.status_code} - {resp.text}")
        return None
    except Exception as e:
        logger.error(f"Error during geocoding: {e}", exc_info=True)
        return None
    
def geocode_parse_address_by_google_api(address_string: str) -> dict | None:
    """
    Use the Google Geocoding API to geocode an address.
    """
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": address_string,
        "key":GEOCODING_API
    }
    coordinates = {} # store latitude and longitude
    try:
        resp = requests.get(url, params=params, timeout=5)
        if resp.ok:
            data = resp.json()
            try:
                location = data["results"][0]["geometry"]["location"]
                coordinates = {
                    "latitude": location['lat'],
                    "longitude": location['lng']
                }
                return coordinates
            except (IndexError, KeyError):
                logger.error(f"Geocoding failed: {address_string}, API return status: {data.get('status')}")
                return None
        else:
            logger.error(f"Geocoding failed: {resp.status_code}")

    except Exception as e:
        logger.error(f"Error during geocoding: {e}", exc_info=True)
        return None

def unified_geocoding(address_string: str) -> dict | None:
    """
    Unified Geocoding:
    1. Prioritizes the local Nominatim container for address resolution (zero cost, high speed).
    2. Automatically and seamlessly falls back to the Google Geocoding API if the local service 
    fails to resolve the address or goes offline (high-precision backup line of defense).
    """
    if not address_string or not address_string.strip():
        logger.warning("Empty address received in geocoding_worker")
        return None
    address_string = address_string.strip()

    logger.info(f"Trying Local Nominatim for address: {address_string}")
    coordinates = geocode_parse_address_by_local_nominatim(address_string)

    if coordinates:
        logger.info(f"🚀 Successfully geocoded by Local Nominatim: {coordinates}")
        return coordinates
    
    logger.warning(f"⚠️ Local Nominatim failed or return empty. Falling back to Google API for: {address_string}")
    coordinates = geocode_parse_address_by_google_api(address_string)

    if coordinates:
        logger.info(f"🚀 Successfully geocoded by Google API: {coordinates}")
        return coordinates
    
    logger.error(f"❌ All geocoding methods failed for address: {address_string}")
    return None

def geocoding_worker():
    
    batch_data = []
    detail_locations = get_detail_location_from_events()
    if not detail_locations:
        logger.info("No event need to parse the geocoding")
        return 
    logger.info(f"Start handling the geocoding task, a total of {len(detail_locations)} items... ")
    for detail_location in detail_locations:
        event_id = detail_location.get('id')
        address = detail_location.get('detail_location')
        detail_location_geocoding = unified_geocoding(address)
        
        if detail_location_geocoding:
            lat = detail_location_geocoding.get('latitude', None)
            lng = detail_location_geocoding.get('longitude', None)
            batch_data.append((lat, lng, event_id))
        
        if len(batch_data) >= 100:
            logger.info("The queue has reached 100 entries and is currently undergoing phased batch writing")
            is_success = batch_update_event_coordinates(batch_data)

            if not is_success:
                logger.warning("The batch update failed! Retrying once after 2 seconds...")
                time.sleep(2)
                is_success = batch_update_event_coordinates(batch_data)
            if not is_success:
                logger.error("CRITICAL: Batch update failed twice!")
            
            # Clear the data in the batch_data.
            batch_data.clear()
    if batch_data:
        logger.info(f"The last batch data is being written, The total is {len(batch_data)} items...")
        batch_update_event_coordinates(batch_data)
    logger.info("🎉 All geocoding task has been completed!")












