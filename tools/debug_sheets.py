import requests
import pandas as pd
from io import BytesIO
import sys

def check_sheets(link):
    print("START CHECK", flush=True)
    if not link: return
    
    # Simple strategy
    if "1drv.ms" in link:
         link = link.split('?')[0] + "?download=1"
         
    try:
        print("Downloading...", flush=True)
        r = requests.get(link, timeout=30)
        print(f"Status: {r.status_code}, Size: {len(r.content)}", flush=True)
        
        if r.status_code == 200:
            print("Parsing Excel...", flush=True)
            xls = pd.ExcelFile(BytesIO(r.content))
            print("--- SHEET LIST START ---", flush=True)
            namelist = xls.sheet_names
            for s in namelist:
                print(f"SHEET: {s}", flush=True)
            print("--- SHEET LIST END ---", flush=True)
                
            matches = [s for s in namelist if '2026' in str(s)]
            print(f"Matches for '2026': {matches}", flush=True)
    except Exception as e:
        print(f"Error: {e}", flush=True)

if __name__ == "__main__":
    link = "https://1drv.ms/x/c/07c1e1a8c3295b87/IQDvrAVlr7kFSrpX8-QHXuOnAd7QThWBm_Q2N5J7gzjuLSk?e=s0KJKk"
    check_sheets(link)
