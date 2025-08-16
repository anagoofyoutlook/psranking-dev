import re
import requests
import os

def sanitize_filename(name):
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'\s+', '_', name)
    return name.lower()

def is_url_accessible(url):
    try:
        response = requests.head(url, timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False

def find_serial_match_media(serial_number, media_files, group_name, github_raw_base):
    print(f"Searching for serial number '{serial_number}' in media files: {media_files}")
    for media in media_files:
        media_base = os.path.splitext(media)[0]
        if media_base == str(serial_number):
            media_url = f"{github_raw_base}/Photos/{group_name}/thumbs/{media}"
            if is_url_accessible(media_url):
                print(f"Match found for serial number '{serial_number}': '{media}' at {media_url}")
                return media
            else:
                print(f"Media '{media}' at {media_url} is inaccessible")
    print(f"No accessible match found for serial number '{serial_number}'")
    return None