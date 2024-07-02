from urllib.request import *
import os

# Get the directory of the script
script_dir = os.path.dirname(os.path.abspath(__file__))

page = "https://gamefaqs.gamespot.com/ps/916670-final-fantasy-ii/faqs/61436"

req = Request(
    page, 
    data=None, 
    headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
    }
)

html = urlopen(req).read().decode('utf-8')

# Create the 'raw' folder in the same directory as the script
raw_dir = os.path.join(script_dir, 'raw')
if not os.path.exists(raw_dir):
    os.makedirs(raw_dir)

# Write the file to the 'raw' folder
output_file = os.path.join(raw_dir, 'page01.html')
with open(output_file, 'w', encoding='utf-8') as o:
    o.write(html)

print(f"File successfully saved in {output_file}")