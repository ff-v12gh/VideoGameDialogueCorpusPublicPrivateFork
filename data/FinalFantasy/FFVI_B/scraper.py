import os
from urllib.request import urlopen
from urllib.error import URLError

# Get the directory of the script
script_dir = os.path.dirname(os.path.abspath(__file__))

# URL of the page to scrape
page = "https://finalfantasy.fandom.com/wiki/Final_Fantasy_VI_SNES_script"

try:
    # Fetch and decode the HTML content
    html = urlopen(page).read().decode('utf-8')

    # Create 'raw' folder if it doesn't exist
    raw_dir = os.path.join(script_dir, 'raw')
    os.makedirs(raw_dir, exist_ok=True)

    # Write the content to a file in the 'raw' folder
    output_file = os.path.join(raw_dir, 'page01.html')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"File successfully saved in {output_file}")

except URLError as e:
    print(f"An error occurred while fetching the URL: {e}")
except IOError as e:
    print(f"An error occurred while writing the file: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")