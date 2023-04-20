import pandas as pd
import requests
import logging
import os
from time import sleep

from_date: str = "2023-01-31"
to_date: str = "2023-03-31"

file_patterns = {
    "mcwb": (
        "https://niftyindices.com/Market_Capitalisation_Weightage_Beta_for_NIFTY_50_And_NIFTY_Next_50/mcwb_{date}.zip",
        lambda x: {"date": x.strftime("%b%y").lower()
                   },
    ),
}

key: str = "mcwb"  # Should be one of the available keys
output_directory: str = "."
__niftyindices_headers = {
    'Connection': 'keep-alive',
    'sec-ch-ua': '" Not;A Brand";v="99", "Google Chrome";v="91", "Chromium";v="91"',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'DNT': '1',
    'X-Requested-With': 'XMLHttpRequest',
    'sec-ch-ua-mobile': '?0',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36',
    'Content-Type': 'application/json; charset=UTF-8',
    'Origin': 'https://niftyindices.com',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Dest': 'empty',
    'Referer': 'https://niftyindices.com/reports/historical-data',
    'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8'
}


def download_and_save_file(url: str, filename: str) -> bool:
    """
    Download the file from the given url and save it in the given filename
    url
        valid url to download
    filename
        filename as str, can include entire path
    returns True if the file is downloaded and saved else returns False
    """
    try:
        req = requests.get(url, headers=__niftyindices_headers, timeout=15)
        if req.status_code == 200:
            with open(filename, "wb") as f:
                f.write(req.content)
            return True
        else:
            return False
    except Exception as e:
        logging.error(e)
        return False


dates = pd.bdate_range(start=from_date, end=to_date)
pat, func = file_patterns[key]
missed_dates = []
skipped = 0
downloaded = 0
for dt in dates:
    url = pat.format(**func(dt))
    name = url.split("/")[-1]
    filename = os.path.join(output_directory, name)
    if os.path.exists(filename):
        logging.info(f"File already exists for date {dt}")
        skipped += 1
    else:
        status = download_and_save_file(url, filename)
        sleep(1)
        if status:
            downloaded += 1
        else:
            missed_dates.append(dt)

print(f"Total number of dates = {len(dates)}")
print(f"Number of missed dates = {len(missed_dates)}")
print(f"Number of skipped dates = {skipped}")
print(f"Number of downloaded dates = {downloaded}")
