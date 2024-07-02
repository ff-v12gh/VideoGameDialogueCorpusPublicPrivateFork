from urllib.request import *
import os

page = "https://gamefaqs.gamespot.com/ps/916670-final-fantasy-ii/faqs/61436"

req = Request(
    page, 
    data=None, 
    headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
    }
)

html = urlopen(req).read().decode('utf-8')

# Create the 'raw' folder if it doesn't exist
if not os.path.exists('raw'):
    os.makedirs('raw')

# Write the file to the 'raw' folder
with open("raw/page01.html", 'w', encoding='utf-8') as o:
    o.write(html)

print("File successfully saved in raw/page01.html.")