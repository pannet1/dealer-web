import pandas as pd
import requests
import logging
import os

file_patterns = {
    "bhav": (
        "https://archives.nseindia.com/content/historical/EQUITIES/{year}/{month}/cm{date}bhav.csv.zip",
        lambda x: {
            "year": x.year,
            "month": x.strftime("%b").upper(),
            "date": x.strftime("%d%b%Y").upper(),
        },
    ),
    "hist_data": (
        "https://www.nseindia.com/api/historical/cm/equity?symbol={symbol}",
        lambda x: {"symbol": x.upper()},
    ),
    "bhavcopy": (
        "https://nseindia.com/ArchieveSearch?h_filetype=eqbhav&date={date}&section=EQ",
        lambda x: {"date": x.strftime("%d-%m-%Y")},
    ),
}

key: str = "bhav"  # Should be one of the available keys
from_date: str = "2022-03-31"
to_date: str = "2022-03-31"
output_directory: str = "."


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
        req = requests.get(url, timeout=3)
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
for dt in dates:
    url = pat.format(**func(dt))
    name = url.split("/")[-1]
    filename = os.path.join(output_directory, name)
    if download_and_save_file(url, filename):
        pass
    else:
        logging.warning(f"File not found for date {dt}")
        missed_dates.append(dt)
