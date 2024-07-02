import os
from urllib.request import urlopen

# URL of the page to be scraped
url = "https://archive.rpgamer.com/games/ff/ff1/info/ff1_script.txt"

# Determine the path of the script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Define the path for the raw folder relative to the script
output_dir = os.path.join(script_dir, "raw")

# Create the raw folder if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

# Define the output filename
output_file = "page01.txt"

try:
    # Open the URL and read the content
    with urlopen(url) as response:
        html = response.read().decode("utf-8", "backslashreplace")
    
    # Write the content to the file in the raw folder
    output_path = os.path.join(output_dir, output_file)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"File successfully downloaded and saved in {output_path}.")

except Exception as e:
    print(f"An error occurred: {e}")