import requests
from io import BytesIO
import base64
import time

def convert_onedrive_link(share_link, cache_bust=False):
    """Convert OneDrive share link ke direct download link"""
    if not share_link or not isinstance(share_link, str) or share_link.strip() == "":
        return None
    
    share_link = share_link.strip()
    
    # STRATEGY 1: Simple 'download=1' param replacement
    if "1drv.ms" in share_link or "onedrive.live.com" in share_link:
        try:
            base_link = share_link.split('?')[0]
            final_link = f"{base_link}?download=1"
            if cache_bust:
                final_link += f"&t={int(time.time())}"
            return final_link
        except:
            pass

    # STRATEGY 2: Legacy API (u! encoding)
    try:
        encoded = base64.b64encode(share_link.encode()).decode()
        encoded = encoded.rstrip('=').replace('/', '_').replace('+', '-')
        final_link = f"https://api.onedrive.com/v1.0/shares/u!{encoded}/root/content"
        if cache_bust:
             final_link += f"?t={int(time.time())}"
        return final_link
    except Exception:
        return None

def download_from_onedrive(share_link, timeout=60, cache_bust=False):
    """Download file from OneDrive"""
    direct_url = convert_onedrive_link(share_link, cache_bust=cache_bust)
    
    if not direct_url:
        print(f"Invalid OneDrive link provided.")
        return None
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(direct_url, headers=headers, timeout=timeout)
        response.raise_for_status()
        print(f"Download success. Size: {len(response.content)/1024:.2f} KB")
        return BytesIO(response.content)
    except Exception as e:
        print(f"Download error: {e}")
        if cache_bust:
             raise e
        return None
