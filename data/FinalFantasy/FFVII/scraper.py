import os
import time
from urllib.request import urlopen
from urllib.error import URLError

# Get the directory of the script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Base URL for scraping
base_url = "http://www.yinza.com/Fandom/Script/"

# Create 'raw' folder if it doesn't exist
raw_dir = os.path.join(script_dir, 'raw')
os.makedirs(raw_dir, exist_ok=True)

# Number of pages to scrape
total_pages = 48

for page_num in range(1, total_pages + 1):
    url = f"{base_url}{page_num:02d}.html"
    file_name = os.path.join(raw_dir, f"page_{page_num:02d}.html")
    
    if not os.path.exists(file_name):
        try:
            # Fetch and decode the HTML content
            with urlopen(url) as response:
                html = response.read().decode('utf-8')
            
            # Write the content to a file in the 'raw' folder
            with open(file_name, 'w', encoding='utf-8') as f:
                f.write(html)
            
            print(f"Successfully saved page {page_num} to {file_name}")
            
            # Pause to avoid overwhelming the server
            time.sleep(2)
        
        except URLError as e:
            print(f"Error fetching page {page_num}: {e}")
        except IOError as e:
            print(f"Error writing file for page {page_num}: {e}")
        except Exception as e:
            print(f"Unexpected error on page {page_num}: {e}")

print("Scraping completed.")