# event_crawler.py
import requests
import time
import random

from requests.adapters import HTTPAdapter
from urllib3 import Retry
from bs4 import BeautifulSoup
from urllib.parse import urljoin, parse_qs, unquote, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from logger import logger
# Create global Session and configure automatic retry.
session = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504]
)
session.mount("https://", HTTPAdapter(max_retries=retry_strategy))
session.headers.update({
    "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
})

# parse original image url
def parse_original_image_url(img_src):
    # Parse URL path and query parameter
    parsed_url = urlparse(img_src)

    # Get the value of 'url' parameter
    query_params = parse_qs(parsed_url.query)
    original_url_encoded = query_params.get('url', [None])[0]
    
    if original_url_encoded:
        return unquote(original_url_encoded)
    return img_src

# Get the details of an event on the event page
def get_full_event_details(detail_url):
    # Add random sleep
    time.sleep(random.uniform(0.3, 1.2))
    
    try:
        response = session.get(detail_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')

        # 1. Extract the main content on the right side.
        # Event classification
        category_tag = soup.select_one('div.inline-flex.bg-primary')
        category = category_tag.get_text(strip=True) if category_tag else "N/A"
        
        # 2. Extract Event big image source link
        img_tag = soup.select_one('div.rounded-lg img')        
        image_url = parse_original_image_url(img_tag['src']) if img_tag else "N/A"

        # 3. Extract event description
        description_tag = soup.find('div', class_="event-description")
        description_html = description_tag.decode_contents().strip() if description_tag else "N/A"


        # 4. Parse Event Details card
        card = soup.find('div', attrs={"data-slot":"card"})

        dates = []
        full_address_image_url = "N/A"
        price = "N/A"
        target_groups = ""

        if card:
            # Find the details in the content area
            rows = card.select('div.flex.items-start.gap-3')

            for row in rows:
                # Determine what data this line is by looking for the name of the internal SVG icon class
                svg = row.find('svg')
                if not svg:
                    continue
                svg_class = "".join(svg.get("class", []))

                # a. handle date (lucide-caledar)
                if 'lucide-calendar' in svg_class:
                    date_containers = row.select('div.space-y-2 > div')
                    for dc in date_containers:
                        d = dc.find('div', class_='font-medium').get_text(strip=True) if dc.find('div', class_='font-medium') else ""
                        t = dc.get_text(strip=True).replace(d, "").strip()
                        dates.append({"date":d, "time":t})

                # b. handle address image(lucide-map-pin)
                elif 'lucide-map-pin' in svg_class:
                    # Extract slug from detail_url and construct the image url
                    slug = detail_url.rstrip('/').split('/')[-1]
                    if slug:
                        generated_api_path = f"/api/events/{slug}/address"
                        full_address_image_url = urljoin("https://www.whats-on.co.nz", generated_api_path)

                # c. Handle price
                elif 'lucide-dollar-sign' in svg_class:
                    price = row.get_text(strip=True)

                # d. Handle targe group (lucide-users)
                elif 'lucide-users' in svg_class:
                    tags = [t.get_text(strip=True) for t in row.find_all('div', class_='bg-secondary')]
                    target_groups = ",".join(tags)
        
        return {
            "category":category,
            "main_image_url":image_url,
            "description_html":description_html,
            "dates":dates, # this data is an list[].
            "price":price,
            "full_address_image_url":full_address_image_url,
            "target_groups":target_groups
        }          
    except Exception as e:
        logger.error(f"Occur an error:{e}",exc_info=True)
        return None

def get_event(list_url):
    try:
        # send request
        response = session.get(list_url, timeout=10)
        response.raise_for_status() 

        # init parser
        soup = BeautifulSoup(response.text, 'lxml')

        # locate all card event
        cards = soup.find_all('div', attrs={"data-slot":"card"})
        event_data = []
        basic_items = [] # Temporarily store basic information

        for card in cards:
            # extract details of link
            # find the <a> tag from parent tag
            parent_a = card.find_parent('a', href=True)
            if not parent_a:
                continue
            relative_link = parent_a['href'] if parent_a else ""

            # Check if this card is the true event
            if "/event/" not in relative_link:
                continue
            full_link = urljoin(list_url, relative_link)

            # Extract title
            title_tag = card.find('h3')
            title = title_tag.get_text(strip=True) if title_tag else "N/A"

            
            # Extract meta data (date, circle, price, site)
            info_container = card.find('div', class_='space-y-1.5')
            if not info_container:
                continue
            
            # Extract details of container
            details = info_container.find_all('div', class_="flex items-center gap-1.5")
            # Define a internal function to extract exact words from span tag
            def get_val(index):
                if len(details) > index:
                    span = details[index].find('span')
                    return span.get_text(strip=True) if span else details[index].get_text(strip=True)
                return "N/A"
            # Extract date circle price site
            
            # Remove the date and use the time of the event details
            # raw_date = get_val(0)
            # date = re.sub(r'at(?=\d)', ', ', raw_date) 
            circle = get_val(1)
            location = get_val(3)

            basic_items.append({
                "title":title,
                "event_detail_link":full_link,
                "circle":circle,
                "rough_location":location

            })

        # *******Start multiple threads*******
        # max_workers=5
        with ThreadPoolExecutor(max_workers=5) as executor:
            # submit task to threadpool, passing full_link to get_full_event_details
            
            # Dictionary comprehension: bind each future object to its corresponding basic_item
            future_to_item = {
                executor.submit(get_full_event_details, item["event_detail_link"]): item for item in basic_items
            }

            # as_completed
            for future in as_completed(future_to_item):
                item = future_to_item[future]
                try:
                    detail_res = future.result() # Get parsed result of detail page
                    if not detail_res:
                        detail_res = {
                            "category":"N/A",
                            "main_image_url":"N/A",
                            "description_html":"N/A",
                            "dates":[],
                            "price":"N/A",
                            "full_address_image_url":"N/A",
                            "target_groups":"",
                        }
                    
                    # Combine basic_item and details_res
                    full_item = {**item, **detail_res}
                    event_data.append(full_item)
                    logger.info(f"{item['title']}...Finished!!")
                except Exception as e:
                    logger.error(f"{item['title']} occur an error:{e}")                    
            
        return event_data

    except Exception as e:
        logger.error(f"Occur an error:{e}",exc_info=True)
        return []
    
def get_city(region_url):
    # Add random sleep
    time.sleep(random.uniform(2.0, 4.0))    
    try:
        # send request
        response = session.get(region_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')

        # Get city cards
        cards = soup.find_all('div', attrs={"data-slot":"card"})
        city_data = []

        for card in cards:
            parent_a = card.find_parent('a', href=True)
            if not parent_a:
                continue
            city_relative_link = parent_a['href']
            city_link = urljoin(region_url, city_relative_link)

            #GET city image
            city_img_tag = card.find('img')
            city_img_url = parse_original_image_url(city_img_tag['src']) if city_img_tag else "N/A"

            # Get city name
            city_name_tag = card.find('div', attrs={"data-slot":"card-title"})
            city_name = "N/A"
            if city_name_tag:
                city_full_name = city_name_tag.find_all(string=True, recursive=False) 
                city_name = "".join(city_full_name) if city_full_name else "N/A"

            # Get events in an city
            event_data = get_event(city_link)
            # Construct full return value in city
            item = {
                "city_link":city_link,
                "city_img_url":city_img_url,
                "city_name":city_name,
                "event_data": event_data
            }
            city_data.append(item)
        logger.info(f"\n{city_name} has been completed!")

        return city_data

    except Exception as e:
        logger.error(f"Occur an error:{e}",exc_info=True)
        return []

def get_region(base_url):
    try:
        # send request
        response = session.get(base_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')

        # Get cards from  base_url
        cards = soup.find_all('div', attrs={'data-slot':'card'})
        region_data = []
        
        for card in cards:
            # Get a tag from parent tag
            parent_a = card.find_parent('a', href=True)
            if not parent_a:
                continue 
            # Get region reletive link
            region_reletive_link = parent_a['href']
            # Get region link 
            region_link = urljoin(base_url, region_reletive_link)

            # Get region image
            region_img_tag = card.find('img')
            region_img_url = parse_original_image_url(region_img_tag['src']) if region_img_tag else "N/A"

            # Get full region name
            region_name_tag = card.find('div', attrs={"data-slot":"card-title"})
            region_name = "N/A"
            if region_name_tag:
                region_full_name = region_name_tag.find_all(string=True, recursive=False) 
                region_name = "".join(region_full_name) if region_full_name else "N/A"
        
            city_data = get_city(region_link)
            # Construct full return value in region       
            item = {
                "region_name":region_name,
                "region_link":region_link,
                "region_img_url":region_img_url,
                "city_data":city_data
            }
            region_data.append(item)
        return region_data 

    except Exception as e:
        logger.error(f"Occur an error:{e}",exc_info=True)
        return []
    

def run_event_crawler(base_url):
    try:
        return get_region(base_url)
    except Exception as e:
        logger.error(f"Occur an error: {e}")