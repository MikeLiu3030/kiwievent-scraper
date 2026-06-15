
# app.py
import time
from logger import logger
from dbManager import import_json_to_mysql, insert_eventbrite_events
from event_crawler import run_event_crawler
from jsonManager import save_data_to_json
from eventbrite_crawler import run_eventbrite_scraper

def main():
    try:
        start_time = time.perf_counter()
         # --- Whats-on.co.nz crawler ---
        base_url = "https://www.whats-on.co.nz"
        logger.info("Start Crawler Task...")
        
        # start crawling data
        data = run_event_crawler(base_url)


        if data:
            # Store data to a json file
            filepath = save_data_to_json(data)
               
            # Store data to a database from json file.
            import_json_to_mysql(filepath)
            
        else:
            logger.info("\nUnsuccessful!!!!!!!!")
            
          # --- Eventbrite crawler ---
        logger.info("Starting Eventbrite crawler...")
        eventbrite_data = run_eventbrite_scraper()
        if eventbrite_data:
            insert_eventbrite_events(eventbrite_data)
        else:
            logger.warning("Eventbrite crawler returned no data.")


        end_time = time.perf_counter()
        # Calculate total time 
        total_seconds = end_time - start_time
        minutes, seconds = divmod(total_seconds, 60)        
        logger.info("All is Successful!!!!!")
        logger.info(f"🎉Task has been completed, total time:{int(minutes)} Minutes {seconds:.2f} Seconds")

    except Exception as e:
        logger.error(f"Occur an error:{e}",exc_info=True)
if __name__ == "__main__":
    main()
