
# app.py
import time
from logger import logger
from dbManager import import_json_to_mysql
from event_crawler import run_event_crawler
from jsonManager import save_data_to_json

def main():
    try:
        base_url = "https://www.whats-on.co.nz"
        start_time = time.perf_counter()
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
