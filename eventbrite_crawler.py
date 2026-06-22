

import re
import time
import random
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from logger import logger
from ai_cleaner import clean_event_duration, clean_rough_location

def scrape_eventbrite():
    url = "https://www.eventbrite.co.nz/d/new-zealand/events/"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1280, 'height': 4000})
        logger.info("Opening Eventbrite...")
        page.goto(url)
        page.wait_for_selector("section.discover-vertical-event-card", timeout=15000)
        page.wait_for_load_state("networkidle", timeout=15000)
        html = page.content()

        # Parse events from listing page first
        events = parse_events(html)
        logger.info(f"Starting to scrape {len(events)} event detail pages...")

        # Visit each event detail page
        for i, event in enumerate(events):
            logger.info(f"Scraping detail page {i+1}/{len(events)}: {event['title']}")
            event_time_raw, address_raw = scrape_event_detail(page, event['event_detail_link'])  
            event['event_time_raw'] = event_time_raw
            event['address_raw'] = address_raw
            event['circle'] = clean_event_duration(event_time_raw)
            event['rough_location'] = clean_rough_location(address_raw)
            time.sleep(1)  # Avoid sending too many requests too fast

        browser.close()
    return events

    
def parse_events(html):
    
    soup = BeautifulSoup(html, 'lxml')

    cards = soup.find_all('section', class_='discover-vertical-event-card')
    logger.info(f"Found {len(cards)} events")

    events = []
    

    for card in cards:
        # Extract link and location info
        a_tag = card.find('a', class_='event-card-link') 
        if not a_tag:
            continue

        event_link = a_tag.get('href', '')
        # Only keep NZ events 
        if 'eventbrite.co.nz' not in event_link:
            continue   

        location = a_tag.get('data-event-location', '')
        category = a_tag.get('data-event-category', '')

        # Extract title
        title_tag = card.find('h3')
        title = title_tag.get_text(strip=True) if title_tag else 'N/A'

        # Extract venue name
        venue_tag = card.select_one('p.event-card__clamp-line--one')
        venue = venue_tag.get_text(strip=True) if venue_tag else 'N/A'

        # Extract image
        img_tag = card.find('img', class_='event-card-image')
        image_url = img_tag.get('src', 'N/A') if img_tag else 'N/A'

        # Extract price — card structures vary by section, so scan all p tags for a price pattern
        price_pattern = re.compile(r'^(Free|From \$|\$\d|NZ\$)', re.IGNORECASE)
        price = 'N/A'
        for p in card.find_all('p'):
            text = p.get_text(strip=True)
            if price_pattern.match(text):
                price = 'Free' if text == 'From $0.00' else text
                break

        events.append(
            {
                'title': title,
                'category': category,
                'image_url': image_url,
                'address': venue,
                'city': location,
                'price': price,
                'event_detail_link': event_link,
                'circle':location
            }
        )

    deduplicated = {}
    for event in events:
        key = event['event_detail_link'].split('?')[0]
        if key not in deduplicated:
            deduplicated[key] = event
        else:
            existing_price = deduplicated[key]['price']
            if existing_price == 'Check ticket price on event' and event['price'] != 'Check ticket price on event':
                deduplicated[key] = event

    return list(deduplicated.values())


def scrape_event_detail(page, url):
    """Scrape time and address from an event detail page."""
    try:
        page.goto(url)
        page.wait_for_selector('time', timeout=10000)
        html = page.content()
        soup = BeautifulSoup(html, 'lxml')
        
        # Get raw time string
        time_tag = soup.find('time')
        event_time_raw = time_tag.get_text(strip=True) if time_tag else 'N/A'

        # Get raw address string
        venue_tag = soup.find('a', {'data-testid': 'event-venue'})
        address_raw = venue_tag.get_text(strip=True) if venue_tag else 'N/A'

        return event_time_raw, address_raw

    except Exception as e:
        logger.error(f"Error scraping detail page {url}: {e}")
        return 'N/A', 'N/A'
        

def run_eventbrite_scraper():
    try:
        events = scrape_eventbrite()

        for event in events:
            logger.info(f"Title: {event['title']}")
            logger.info(f"Category:{event['category']}")
            logger.info(f"Venue: {event['address']}")
            logger.info(f"Location: {event['city']}")
            logger.info(f"Price: {event['price']}")
            logger.info(f"Time Raw: {event['event_time_raw']}")
            logger.info(f"Address Raw: {event['address_raw']}")
            logger.info(f"Duration: {event['circle']}")
            logger.info(f"Rough Location: {event['rough_location']}")
            logger.info(f"Link: {event['event_detail_link']}")
            logger.info("---")

        return events
    
    except Exception as e:
        logger.error(f"Scraper error: {e}", exc_info = True)
        return[]
    
if __name__ == "__main__":
    run_eventbrite_scraper()
    