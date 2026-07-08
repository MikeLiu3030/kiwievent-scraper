# kiwiEvent-scraper

An efficient, robust, and fully automated web scraping and data persistence pipeline for New Zealand event aggregation platforms (e.g., "What's On" style websites). 

Built with Python using a modular component design, this application automatically extracts multi-tier event data (**Region ➔ City ➔ Event ➔ Dates**), cleanses raw HTML payloads, and syncs data to a remote relational MySQL database. It also includes an asynchronous backup mechanism that exports data to local JSON files appended with high-precision timestamps for disaster recovery.

## 🚀 Key Features

- **Deep Hierarchical Data Crawling**: Automatically establishes data dependency chains from Regions to Cities down to individual Events. Employs pattern recognition within loops to filter out navigational placeholders and statistical widget cards.
- **Modern Frontend Shield Bypassing**:
  - *CDN High-Res Image Unboxing*: Decouples Next.js image optimization routes (which impose `w` width and `q` quality limitations) to securely parse and reconstruct the original, uncompressed, permanently valid raw CDN source URLs.
  - *Dynamic Address Reverse Engineering*: Bypasses lazy-loaded interactive UI elements (where complete addresses load only when clicked via an image API). By predicting endpoints algorithmically using URL strings (`/api/events/{slug}/address`), the scraper cuts out heavy browser automation frameworks like Selenium or Playwright, maintaining a lightweight footprint and maximum speed.
- **Enterprise-Grade Database Normalization**:
  - *One-to-Many Structural Splitting*: Events with multiple recurring schedules or floating time slots are normalized. High-frequency date data is isolated into a child table, enabling seamless object-relational mapping (ORM) in downstream frameworks (e.g., C# EF Core navigation properties and fast LINQ `Where`/`OrderBy` range filtering).
  - *Rich Text Capture*: Retains the full semantic styling of event briefs. Instead of stripping descriptions into plain text, it captures the raw underlying HTML nodes via `.decode_contents()`, allowing complex tags (`<ul>`, `<li>`, `<p>`) to render natively on the frontend web application.
  - *Database-Level Automated Timestamps*: Leverages database-native triggers (`DEFAULT CURRENT_TIMESTAMP`) for `created_at`, resolving multi-device or distributed clock synchronization anomalies without adding overhead to the Python logic.
- **Strict Transactional & Resource Safety**: Implements Python's `@contextmanager` pattern coupled with `with` blocks to govern active database connections. Operates on an "all-or-nothing" transactional approach that instantly invokes a `rollback()` on exceptions, ensuring zero database pollution or orphan records on unexpected terminations.

## 🛠️ Prerequisites & Dependencies

- **Python Version**: Python 3.8 or higher (Virtual environment setup is highly recommended).
- **Database System**: MySQL 5.7.
- **Core Third-Party Frameworks**:
  - `requests`: Manages secure, resilient stateful HTTP sessions.
  - `beautifulsoup4`: Extracts and navigates structured DOM elements.
  - `lxml`: A highly performant, C-optimized HTML parser backend engine.
  - `mysql-connector-python`: The official, thread-safe database driver for MySQL storage engine communications.
- **Database configuture file**:  
```bash
DB_CONFIG = {
    'host': "",
    'port': ,            
    'user': "",  
    'password': "",
    'database': ""
  }
``` 
## 🐳 Local Nominatim Setup (Docker)

This project integrates with a local Docker instance of `nominatim_nz` for high-performance, offline-capable reverse geocoding and address resolution within New Zealand. 

### Prerequisites
- Docker & Docker Compose installed on your host machine.
- Sufficient RAM allocated to Docker (minimum 8GB recommended for NZ dataset).

### Installation & Startup

1. **Pull and Run the Container**  
   Execute the following command to start the Nominatim NZ service in detached mode:
  ```bash
   docker run -d \
     --name nominatim_nz \
     -p 8080:8080 \
     -v nominatim_data:/var/lib/postgresql/14/main \
     --restart unless-stopped \
     your-dockerhub-username/nominatim_nz:latest
  ```
  **Note:** Replace your-dockerhub-username/nominatim_nz:latest with your actual Docker image name/tag, and adjust the port 8080 if your host requires a different mapping.
  
2. **Verify Service Health**
  Wait for the database to fully load (this may take a few minutes depending on your hardware). Check the container logs to ensure it's ready:
  ```bash
  docker logs -f nominatim_nz
  ```
  You should see a message indicating the web server (Apache/Nginx) is running and accepting requests.
  

3. **Test the API Endpoint**
    Confirm the service is responding correctly:
  ```bash
   curl "http://localhost:8080/search.php?q=Auckland&format=json"
  ```
  
## 💻 Quick Start

### 1. Access the Project Directory
Open your terminal (PowerShell, CMD, or Terminal on Unix) and navigate to the project root directory:
```bash
cd D:\WORK\kiwisquare\kiwiEvent-scraper
# A. Create the virtual isolation sandbox
python -m venv venv
# B. Activate the environment (Windows PowerShell)
.\venv\Scripts\Activate
# For Linux / macOS systems, use:
source venv/bin/activate
# C. Set up all the libraries
pip install requirements.txt
# D. run script
python app.py
```
