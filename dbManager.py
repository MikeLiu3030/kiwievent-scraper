# dbManager.py
import json
import os
from dbconnect import  get_db_connection
from logger import logger
from typing import Any, List, Dict
from utils import parse_normalized_date, parse_normalized_time
def import_json_to_mysql(json_file_path:str) -> None:
    # 1. check if the file exist.
    if not os.path.exists(json_file_path):
        logger.error(f"Error: Can't find the file {json_file_path}")
        return
    # 2. Read json file
    logger.info(f"Loading the local file: {json_file_path}")
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data: List[Dict[str, Any]] = json.load(f)

    with get_db_connection() as conn:
        cursor = conn.cursor(buffered=True)

        # collect all dates, Using "execudemany"  to insert the database at the end 
        all_dates_rows = []

        # calculator for region, city, event
        region_count = 0
        city_count = 0
        event_count = 0

        for region in data:
            region_name = region.get("region_name")
            if not region_name:
                continue            

            #check if region has been existed
            cursor.execute("SELECT id FROM event_regions WHERE name=%s", (region_name,))
            region_res = cursor.fetchone()
            if region_res:
                region_id = region_res[0]
            else:
                # write event_regions
                cursor.execute(
                    "INSERT INTO event_regions (name, link, img_url) VALUES (%s, %s, %s)",
                    (region_name, region.get("region_link"), region.get("region_img_url"))
                )
                region_id = cursor.lastrowid # Get the current region id
                region_count += 1

            for city in region.get('city_data', []):
                city_name = city.get("city_name")
                if not city_name:
                    continue

                # check if the city has been existed in database.
                cursor.execute("SELECT id FROM event_cities WHERE region_id = %s AND name = %s",
                               (region_id, city_name))
                city_res = cursor.fetchone()
                if city_res:
                    city_id = city_res[0]
                else:
                    # write event_cities
                    cursor.execute(
                        "INSERT INTO event_cities (region_id, name, link, img_url) VALUES (%s, %s, %s, %s)",
                        (region_id, city_name, city.get("city_link"), city.get("city_img_url"))
                    )
                    city_id = cursor.lastrowid # Get current city id
                    city_count += 1
                
                for event in city.get("event_data", []):
                    event_title = event.get("title")
                    if not event_title:
                        continue

                    cursor.execute("SELECT id FROM event_events WHERE city_id = %s AND title = %s",
                        (city_id, event_title))
                    event_res = cursor.fetchone()

                    if event_res:
                        event_id = event_res[0]
                    else:                    
                        cursor.execute(
                        """INSERT INTO event_events
                        (city_id, title, category, description_html, main_image_url,
                        full_address_image_url, price, target_groups, event_detail_link, circle, rough_location, detail_location)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                        (
                            city_id, 
                            event_title, 
                            event.get('category'),
                            event.get('description_html'), 
                            event.get('main_image_url'),
                            event.get('full_address_image_url'), 
                            event.get('price'),
                            event.get('target_groups'), 
                            event.get('event_detail_link'),
                            event.get('circle'),
                            event.get('rough_location'),
                            event.get('detail_address')
                        )
                        )
                        event_id = cursor.lastrowid
                        event_count += 1

                    # Handle dates and time level: after cleaning, store temporarily and do not write immediately
                    for date_info in event.get('dates', []):
                        raw_date_str = date_info.get("date")
                        raw_time_str = date_info.get("time")

                        norm_date = parse_normalized_date(raw_date_str) # Normalize raw date str to stander date type
                        norm_time = parse_normalized_time(raw_time_str) # Normalize raw time str to stander time type

                        cursor.execute(
                            """SELECT id FROM event_dates 
                               WHERE event_id = %s AND normalized_date = %s AND normalized_time = %s""",
                            (event_id, norm_date, norm_time)
                        )
                        exsited_rows = cursor.fetchall()

                        if exsited_rows:
                            continue # if this date have existed, then skip this date.

                        all_dates_rows.append((
                            event_id,
                            raw_date_str,
                            raw_time_str,
                            norm_date,
                            norm_time
                        ))
        
        if all_dates_rows:
            cursor.executemany(
                """INSERT INTO event_dates
                (event_id, event_date_raw, event_time_raw, normalized_date, normalized_time)
                VALUES (%s, %s, %s, %s, %s)""",
                all_dates_rows
            )
            
        logger.info("=== 📥 Data entry report ===")
        logger.info(f"✨ New regions: {region_count} ")
        logger.info(f"✨ New cities: {city_count}")
        logger.info(f"✨ New events: {event_count}")
        logger.info(f"✨ Batch inserted dates: {len(all_dates_rows)}")
        logger.info("✨ All data has been written to the database!")
        logger.info("=======================")        
        cursor.close()
    


def insert_eventbrite_events(events: List[Dict[str, Any]]) -> None:
    with get_db_connection() as conn:
        cursor = conn.cursor(buffered=True)
        insert_count = 0
        skip_count = 0

        for event in events:
            title = event.get('title')
            if not title:
                continue

            # Check if the event already exists (use link as unique identifier)
            cursor.execute(
                "SELECT id FROM event_eventbrite WHERE event_detail_link = %s",
                (event.get('event_detail_link'),)
            )
            if cursor.fetchone():
                skip_count += 1
                continue

            cursor.execute(
                """INSERT INTO event_eventbrite
                (title, category, image_url, address, price, event_detail_link, circle, event_time_raw, rough_location, description_html)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    title,
                    event.get('category'),
                    event.get('image_url'),
                    event.get('address'),
                    event.get('price'),
                    event.get('event_detail_link'),
                    event.get('circle'),
                    event.get('event_time_raw'),
                    event.get('rough_location'),
                    event.get('description_html'),
                )
            )
            insert_count += 1

        logger.info("=== 📥 Eventbrite Data entry report ===")
        logger.info(f"✨ New events inserted: {insert_count}")
        logger.info(f"⏭️  Skipped (already exists): {skip_count}")
        logger.info("=======================================")
        cursor.close()

def get_detail_location_from_events() -> List[Dict[str, Any]] | None:
    
    sql = """
        SELECT id, detail_location
        FROM event_events
        WHERE latitude IS NULL 
          AND longitude IS NULL
          AND detail_location IS NOT NULL
          AND TRIM(DETAIL_LOCATION) != ''
    """
    try: 
        with get_db_connection() as conn:
            cursor = conn.cursor(buffered=True, dictionary=True)
            cursor.execute(sql)
            res = cursor.fetchall()
            return res if res else None
    except Exception as e:
        logger.error(f"Extract data failure: {e}")
        return None
        

def batch_update_event_coordinates(events_coordinates:List[Dict[str, Any]]) -> bool:
    """
    event_coordinates: [(latitude, longitude, id), (latitude, longitude, id)]
    """
    sql = """
        UPDATE event_events
        SET latitude = %s,
            longitude = %s
        WHERE id = %s
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(buffered=True)
            cursor.executemany(sql, events_coordinates)
            conn.commit()
            logger.info(f"Successfully Update! {cursor.rowcount} items event coordinates!")
            return True
    except Exception as e:
        logger.error(f"The batch update of the database failed!: {e}", exc_info=True)
        return False



