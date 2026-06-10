# jsonManager.py
import os
import json
from datetime import datetime
from logger import logger

# Save data to json
def save_data_to_json(data, base_name="what's_on_events"):
    try:
        folder_name = "jsonDataFile"
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
            logger.info(f"Directory '{folder_name}' did not exist, created successfully!")
        
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{base_name}_{timestamp}.json"

        filepath = os.path.join(folder_name, filename)

        logger.info(f"\nsaving the data to the local file:{filename}...")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logger.info("Successfully save file! Json file has exported")
        return filepath
    except Exception as e:
        logger.error(f"Occur an error:{e}",exc_info=True)
        return None