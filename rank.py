import json
import csv
import os
import shutil
from datetime import datetime
import re
import zipfile
import random
from html import escape

# Define folder paths
input_folder = 'PS'
output_folder = 'docs'
html_subfolder = os.path.join(output_folder, 'HTML')
photos_folder = 'Photos'
docs_photos_folder = os.path.join(output_folder, 'Photos')
history_csv_file = os.path.join(output_folder, 'history.csv')

# Define CSV output path
csv_file = os.path.join(output_folder, 'output.csv')

# Ensure directories exist
for folder in [input_folder, output_folder, html_subfolder, photos_folder]:
    if not os.path.exists(folder):
        os.makedirs(folder)
        print(f"Created directory: {folder}")
    else:
        print(f"Directory already exists: {folder}")

# Copy Photos/ to docs/Photos/
if os.path.exists(photos_folder):
    if os.path.exists(docs_photos_folder):
        shutil.rmtree(docs_photos_folder)
    shutil.copytree(photos_folder, docs_photos_folder)
    print(f"Copied {photos_folder}/ to {docs_photos_folder}/")
else:
    os.makedirs(docs_photos_folder)
    print(f"Created empty {docs_photos_folder}/ (no photos found in {photos_folder}/)")

# Path to result.zip
zip_file = os.path.join(input_folder, 'result.zip')
temp_json_file = os.path.join(input_folder, 'result.json')

# Verify ZIP file existence and extract result.json
if not os.path.exists(zip_file):
    print(f"Error: 'result.zip' not found in '{input_folder}'. Exiting.")
    exit(1)

print(f"Extracting {zip_file}")
try:
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        json_found = False
        for file_info in zip_ref.infolist():
            if file_info.filename.endswith('result.json'):
                zip_ref.extract(file_info, input_folder)
                extracted_path = os.path.join(input_folder, file_info.filename)
                if extracted_path != temp_json_file:
                    shutil.move(extracted_path, temp_json_file)
                json_found = True
                print(f"Extracted 'result.json' to {temp_json_file}")
                break
        if not json_found:
            print(f"Error: 'result.json' not found in '{zip_file}'. Exiting.")
            exit(1)
except zipfile.BadZipFile:
    print(f"Error: '{zip_file}' is not a valid ZIP file. Exiting.")
    exit(1)

# Verify extracted file existence
if not os.path.exists(temp_json_file):
    print(f"Error: Failed to extract 'result.json' from '{zip_file}'. Exiting.")
    exit(1)

# Load JSON data
print(f"Loading {temp_json_file}")
with open(temp_json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Clean up the temporary JSON file
try:
    os.remove(temp_json_file)
    print(f"Cleaned up temporary file: {temp_json_file}")
except OSError as e:
    print(f"Warning: Could not remove {temp_json_file}: {e}")

# Access chats list
chats = data.get('chats', {}).get('list', [])
print(f"Found {len(chats)} chats in result.json")
if not chats:
    print("No chats found in 'result.json'. Please verify the file content.")
    exit(1)

# Define CSV columns
csv_columns = [
    'date', 'group name', 'total messages', 'Datedifference',
    'count of the hashtag "#FIVE"', 'count of the hashtag "#FOUR"',
    'count of the hashtag "#Three"', 'count of the hashtag "#SceneType"',
    'score', 'rank', 'total titles'
]

# Define history CSV columns
history_columns = ['date', 'group name', 'rank']

# Load existing history data
history_data = {}
if os.path.exists(history_csv_file):
    with open(history_csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            group = row.get('group name', 'Unknown')
            try:
                rank = int(float(row.get('rank', '0')))
                if group not in history_data:
                    history_data[group] = []
                history_data[group].append({'date': row.get('date', ''), 'rank': rank})
            except (ValueError, TypeError) as e:
                print(f"Skipping invalid rank for group '{group}': {row}. Error: {e}")
    print(f"Loaded {sum(len(v) for v in history_data.values())} history entries from {history_csv_file}")
else:
    print(f"No existing {history_csv_file} found")

# Initialize data storage
all_data = []
max_messages = 0
date_diffs = []
current_date = datetime.now().strftime('%Y-%m-%d')

# Function to sanitize filenames
def sanitize_filename(name):
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'\s+', '_', name)
    return name.lower()

# Function to find media file by serial number
def find_serial_match_media(serial_number, media_files):
    print(f"Searching for serial number '{serial_number}' in media files: {media_files}")
    for media in media_files:
        media_base = os.path.splitext(media)[0]
        if media_base == str(serial_number):
            print(f"Match found for serial number '{serial_number}': '{media}'")
            return media
    print(f"No match found for serial number '{serial_number}'")
    return None

# Process each chat
for chat in chats:
    if chat.get('type') == 'private_supergroup':
        group_name = chat.get('name', 'Unknown Group')
        group_id = str(chat['id'])
        telegram_group_id = group_id[4:] if group_id.startswith('-100') else group_id
        messages = chat.get('messages', [])
        print(f"Processing group: {group_name} (ID: {group_id})")

        total_messages = sum(1 for msg in messages if msg.get('type') == 'message')
        max_messages = max(max_messages, total_messages)

        # Hashtag counting
        hashtag_counts = {}
        for message in messages:
            if message.get('type') == 'message':
                text = message.get('text', '')
                if isinstance(text, list):
                    for entity in text:
                        if isinstance(entity, dict) and entity.get('type') == 'hashtag':
                            hashtag = entity.get('text')
                            if hashtag:
                                hashtag_upper = hashtag.upper()
                                special_ratings = ['#FIVE', '#FOUR', '#THREE']
                                special_scene_types = ['#FM', '#FF', '#FFM', '#FFFM', '#FFFFM', '#FMM', '#FMMM', '#FMMMM', '#FFMM', '#FFFMMM', '#ORGY']
                                if hashtag_upper in special_ratings + special_scene_types:
                                    hashtag = hashtag_upper
                                hashtag_counts[hashtag] = hashtag_counts.get(hashtag, 0) + 1

        # Calculate date_diff
        dates = []
        for message in messages:
            if message.get('type') == 'message':
                date_str = message.get('date')
                if date_str:
                    try:
                        date = datetime.fromisoformat(date_str)
                        dates.append(date)
                    except ValueError:
                        continue
        date_diff = None
        if dates:
            newest_date = max(dates)
            today = datetime.now()
            date_diff = (today - newest_date).days
            date_diffs.append(date_diff)
        print(f"Group {group_name}: Total messages = {total_messages}, Date diff = {date_diff}")

        # Hashtag lists
        special_ratings = ['#FIVE', '#FOUR', '#THREE']
        special_scene_types = ['#FM', '#FF', '#FFM', '#FFFM', '#FFFFM', '#FMM', '#FMMM', '#FMMMM', '#FFMM', '#FFFMMM', '#ORGY']
        ratings_hashtag_list = ''.join(f'<li class="hashtag-item">{h}: {hashtag_counts[h]}</li>\n' for h in sorted(hashtag_counts) if h in special_ratings) or '<li>No rating hashtags (#FIVE, #FOUR, #Three) found</li>'
        scene_types_hashtag_list = ''.join(f'<li class="hashtag-item">{h}: {hashtag_counts[h]}</li>\n' for h in sorted(hashtag_counts) if h in special_scene_types) or '<li>No scene type hashtags found</li>'
        other_hashtag_list = ''.join(f'<li class="hashtag-item">{h}: {hashtag_counts[h]}</li>\n' for h in sorted(hashtag_counts) if h not in special_ratings and h not in special_scene_types) or '<li>No other hashtags found</li>'

        scene_type_count = sum(hashtag_counts.get(h, 0) for h in special_scene_types)
        date_diff_text = f'{date_diff} days' if date_diff is not None else 'N/A'

        # Titles with serial numbers
        titles = []
        media_extensions = ['.mp4', '.webm', '.ogg', '.gif']
        group_subfolder = os.path.join(docs_photos_folder, group_name)
        thumbs_subfolder = os.path.join(group_subfolder, 'thumbs')
        media_files = [f for f in os.listdir(thumbs_subfolder) if f.lower().endswith(tuple(media_extensions))] if os.path.exists(thumbs_subfolder) else []
        fallback_photos = [f for f in os.listdir(group_subfolder) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')) and os.path.isfile(os.path.join(group_subfolder, f))] if os.path.exists(group_subfolder) else []
        print(f"Group {group_name}: Thumbs media files = {media_files}, Fallback photos = {fallback_photos}")
        serial_number = 1
        for message in messages:
            if message.get('action') == 'topic_created':
                title = message.get('title', '')
                message_id = message.get('id')
                date_str = message.get('date', '')
                if title.strip() and message_id and date_str:
                    try:
                        date = datetime.fromisoformat(date_str).strftime('%Y-%m-%d')
                        media_path = 'https://via.placeholder.com/600x300?text=Media+Not+Available'
                        is_gif = False
                        if media_files:
                            serial_match = find_serial_match_media(serial_number, media_files)
                            if serial_match:
                                media_path = f"../Photos/{group_name}/thumbs/{serial_match}"
                                is_gif = serial_match.lower().endswith('.gif')
                                print(f"Group {group_name}, Title '{title}' (S.No {serial_number}): Matched media '{serial_match}', selected path {media_path}")
                        else:
                            print(f"Group {group_name}, Title '{title}' (S.No {serial_number}): No media files in {thumbs_subfolder}")
                            if fallback_photos:
                                random_photo = random.choice(fallback_photos)
                                media_path = f"../Photos/{group_name}/{random_photo}"
                                is_gif = random_photo.lower().endswith('.gif')
                                print(f"  Using fallback photo: {media_path}")
                        titles.append({
                            'title': title,
                            'message_id': message_id,
                            'date': date,
                            'media_path': media_path,
                            'is_gif': is_gif,
                            'serial_number': serial_number
                        })
                        serial_number += 1
                    except ValueError:
                        continue
        titles.sort(key=lambda x: x['date'], reverse=True)  # Sort by date, newest first
        titles_count = len(titles)

        # Titles grid
        titles_grid = f"<p>Total Titles: {titles_count}</p><div class='titles-grid' id='titlesGrid'>"
        if titles:
            for t in titles:
                media_element = (
                    f"<img src='{t['media_path']}' alt='Media for {t['title']}'>"
                    if t['is_gif'] or 'via.placeholder.com' in t['media_path']
                    else f"<video src='{t['media_path']}' loop muted playsinline></video>"
                )
                titles_grid += f"""
                    <div class='grid-item'>
                        {media_element}
                        <p class='title'><a href='https://t.me/c/{telegram_group_id}/{t['message_id']}' target='_blank'>{t['title']}</a></p>
                        <p class='date'>S.No: {t['serial_number']} | {t['date']}</p>
                    </div>
                """
        else:
            titles_grid += """
                <div class='grid-item'>
                    <img src='https://via.placeholder.com/600x300?text=No+Videos+Available' alt='No Videos Available'>
                    <p class='title'>No Titles Available</p>
                    <p class='date'>N/A</p>
                </div>
            """
        titles_grid += "</div>"

        # Titles table
        titles_table = f"<table class='titles-table' id='titlesTable'><thead><tr><th onclick='sortTitlesTable(0)'>S.No</th><th onclick='sortTitlesTable(1)'>Items</th><th onclick='sortTitlesTable(2)'>Date</th></tr></thead><tbody id='titlesTableBody'>"
        for t in titles:
            titles_table += f"<tr><td>{t['serial_number']}</td><td><a href='https://t.me/c/{telegram_group_id}/{t['message_id']}' target='_blank'>{t['title']}</a></td><td>{t['date']}</td></tr>"
        titles_table += f"</tbody></table>" if titles else f"<p>No titles found</p>"

        # Photos for slideshow
        photo_paths = []
        if os.path.exists(group_subfolder):
            photo_paths = [f"../Photos/{group_name}/{f}" for f in os.listdir(group_subfolder) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')) and os.path.isfile(os.path.join(group_subfolder, f))]
            print(f"Group {group_name}: Found {len(photo_paths)} photos in {group_subfolder}: {photo_paths}")
        if not photo_paths:
            photo_paths = ['https://via.placeholder.com/1920x800']
            print(f"Group {group_name}: Using placeholder for slideshow")

        slideshow_content = '<div class="container">\n' + ''.join(f'<div class="mySlides"><div class="numbertext">{i} / {len(photo_paths)}</div><img src="{p}" style="width:100%;height:auto;"></div>' for i, p in enumerate(photo_paths, 1)) + """
            <a class="prev" onclick="plusSlides(-1)">❮</a>
            <a class="next" onclick="plusSlides(1)">❯</a>
            <div class="caption-container"><p id="caption"></p></div>
            <div class="row">
        """ + ''.join(f'<div class="column"><img class="demo cursor" src="{p}" style="width:100%" onclick="currentSlide({i})" alt="{group_name} Photo {i}"></div>' for i, p in enumerate(photo_paths, 1)) + '</div></div>'

        photo_file_name = next((f"{group_name}{ext}" for ext in ('.jpg', '.jpeg', '.png', '.gif', '.webp') if os.path.exists(os.path.join(docs_photos_folder, f"{group_name}{ext}"))), None)
        if photo_file_name:
            print(f"Group {group_name}: Found single photo at {docs_photos_folder}/{photo_file_name}")
        else:
            print(f"Group {group_name}: No single photo found in {docs_photos_folder}/")

        if group_name not in history_data:
            history_data[group_name] = []

        # Pre-compute JSON for history data to avoid f-string issue
        history_data_json = json.dumps(history_data.get(group_name, []))

        # HTML content for group pages
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{group_name}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.2/dist/chart.umd.min.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #1e2a44; color: #ffffff; text-align: center; }}
        h1, h2 {{ color: #e6b800; width: 80%; margin: 20px auto; text-align: center; font-size: 36px; }}
        .info {{ background-color: #2a3a5c; padding: 10px; border-radius: 5px; margin-bottom: 20px; }}
        .hashtags {{ list-style-type: none; padding: 0; }}
        .hashtag-item {{ background-color: #3b4a6b; margin: 5px 0; padding: 5px; border-radius: 3px; display: inline-block; width: 200px; color: #ffffff; }}
        .rank-container {{ 
            width: 80%; 
            margin: 20px auto; 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            gap: 20px; 
            flex-wrap: wrap; 
        }}
        .rank-number {{ font-size: 48px; font-weight: bold; color: #e6b800; display: inline-block; }}
        @keyframes countUp {{ from {{ content: "0"; }} to {{ content: attr(data-rank); }} }}
        .rank-number::before {{ content: "0"; animation: countUp 2s ease-out forwards; display: inline-block; min-width: 60px; }}
        .chart-container {{ max-width: 400px; width: 100%; background-color: #2a3a5c; padding: 10px; border-radius: 5px; }}
        canvas {{ width: 100% !important; height: auto !important; }}
        .titles-grid {{ 
            display: grid; 
            grid-template-columns: repeat(3, 1fr); 
            gap: 1%; 
            margin: 20px auto; 
            width: 100%; 
            box-sizing: border-box; 
        }}
        .grid-item {{ 
            background-color: #2a3a5c; 
            padding: 10px; 
            border-radius: 5px; 
            text-align: center; 
            display: flex; 
            flex-direction: column; 
            align-items: center; 
            width: 100%; 
            box-sizing: border-box; 
        }}
        .grid-item video, .grid-item img {{ 
            width: 100%; 
            aspect-ratio: 2 / 1; 
            border-radius: 5px; 
        }}
        .grid-item .title {{ 
            margin: 10px 0 5px; 
            font-size: 16px; 
            font-weight: bold; 
            color: #e6b800; 
        }}
        .grid-item .date {{ 
            margin: 0; 
            font-size: 14px; 
            color: #cccccc; 
        }}
        .titles-table {{ 
            width: 80%; 
            margin: 20px auto; 
            border-collapse: collapse; 
            background-color: #2a3a5c; 
        }}
        .titles-table th, .titles-table td {{ 
            padding: 10px; 
            border: 1px solid #3b4a6b; 
            text-align: left; 
            vertical-align: middle; 
            color: #ffffff; 
        }}
        .titles-table th {{ 
            background-color: #e6b800; 
            color: #1e2a44; 
            cursor: pointer; 
        }}
        .titles-table th:hover {{ 
            background-color: #b30000; 
        }}
        a {{ color: #e6b800; text-decoration: none; }}
        a:hover {{ color: #b30000; text-decoration: underline; }}
        .container {{ 
            position: relative; 
            width: 80%; 
            margin: 20px auto; 
            height: auto; 
            max-height: 600px; 
            display: block; 
            overflow: hidden; 
            background-color: #2a3a5c; 
        }}
        .mySlides {{ 
            display: none; 
            width: 100%; 
            height: auto; 
            aspect-ratio: 16 / 9; 
        }}
        .mySlides img {{ 
            width: 100%; 
            height: auto; 
            object-fit: contain; 
        }}
        .cursor {{ cursor: pointer; }}
        .prev, .next {{ 
            cursor: pointer; 
            position: absolute; 
            top: 50%; 
            transform: translateY(-50%); 
            width: auto; 
            padding: 16px; 
            color: #e6b800; 
            font-weight: bold; 
            font-size: 20px; 
            border-radius: 0 3px 3px 0; 
            user-select: none; 
            -webkit-user-select: none; 
            z-index: 10; 
        }}
        .prev {{ left: 0; }}
        .next {{ right: 0; border-radius: 3px 0 0 3px; }}
        .prev:hover {{ background-color: #b30000; }}
        .next:hover {{ background-color: #b30000; }}
        .numbertext {{ 
            color: #e6b800; 
            font-size: 12px; 
            color: #e6b800; 
            padding: 8px 12px; 
            position: absolute; 
            top: 0; 
            z-index: 10; 
        }}
        .caption-container {{ 
            text-align: center; 
            background-color: #1e2a44; 
            padding: 2px 16px; 
            color: #e6b800; 
        }}
        .row {{ 
            display: flex; 
            flex-wrap: wrap; 
            justify-content: center; 
            margin-top: 10px; 
        }}
        .column {{ 
            flex: 0 0 {100 / len(photo_paths) if photo_paths else 100}%; 
            max-width: 100px; 
            padding: 5px; 
        }}
        .demo {{ 
            opacity: 0.6; 
            width: 100%; 
            height: auto; 
            object-fit: cover; 
        }}
        .active, .demo:hover {{ opacity: 1; }}
        .tab {{ 
            overflow: hidden; 
            margin: 20px auto; 
            width: 80%; 
            background-color: #2a3a5c; 
            border-radius: 5px 5px 0 0; 
        }}
        .tab button {{ 
            background-color: #2a3a5c; 
            color: #e6b800; 
            color: #e6b800; 
            float: left; 
            border: none; 
            outline: none; 
            cursor: pointer; 
            padding: 14px 16px; 
            transition: 0.3s; 
            font-size: 17px; 
            font-size: 14px; 
            width: 50%; 
        }}
        .tab button:hover {{ background-color: #b30000; }}
        .tab button.active {{ background-color: #3b4a6b; }}
        .tabcontent {{ 
            display: none; 
            padding: 6px 12px; 
            border-top: none; 
            background-color: #2a3a5c; 
            margin: 0 auto; 
            width: 80%; 
            border-radius: 0 0 5px 5px; 
            box-sizing: border-box; 
        }}
        #VideosContent {{ display: block; }}
        @media only screen and (max-width: 1200px) {{ 
            .titles-grid {{ grid-template-columns: repeat(2, 1fr); }} 
            .grid-item video, .grid-item img {{ width: 100%; aspect-ratio: 2 / 1; }} 
        }}
        @media only screen and (max-width: 768px) {{ 
            .container {{ width: 80%; max-height: 400px; }}
            h1 {{ width: .80%; margin: 10px auto; font-size: 30px; font-size: 20px; }}
            .rank-container {{ width: .80%; width: 100%; flex-direction: column; gap: 10px; height; }}
            .chart-container {{ width: 100%; max-width: 100%; }}
            .column {{ flex: 0 0 auto; max-width: 80px; width: auto; }}
            .mySlides img {{ max-width: 100%; object-fit: contain; }}
            .tab button {{ font-size: .14px; font-weight: bold; padding: .10px; }}
            .titles-grid {{ grid-template-columns: 1fr; }} 
            .grid-item video, .grid-item img {{ width: 100%; aspect-ratio: 2 / 1; }} 
        }}
    </style>
</head>
<body>
    <h1>{group_name}</h1>
    <div class="rank-container">
        <div class="chart-container"><h2>Rank History</h2><canvas id="historyChart"></canvas></div>
        <p>Rank: <span class="rank-number" data-rank="RANK_PLACEHOLDER"></span></p>
    </div>
    {slideshow_content}
    <div class="info"><div><p>Scenes: {total_messages}</p><p><p>Last Scene: {last_scene_date_diff_text}</p></p></div>
    <div class="info">
        <h2>Rating Hashtags (#FIVE, #FOUR, #Three)</h2><p><ul><ul class="hashtags">{ratings_hashtag_list}</ul></p></ul>
        <p><h2>Tags</h2><ul></p><ul class="hashtags">{hashtags}</ul></p>
        <p><p><h2>Other Hashtags</h2></p></p><p><ul></p><ul class="hashtags"></ul></p>
    </div>
    <div class="info">
        <div class="info">
            <h2>Bookmarks</h2>
            <div class="tab">
                <button class="tablinks-btn" class="active" onclick="openTab(event, 'VideosContent')">Videos</button>
            <button class="tablinks-btn" onclick="openTab(event, 'TableContent')">Table</button>
        </div>
        <div id="VideosContent" class="tabcontent">
            {titles_grid_content}
        </div>
        <div id="TableContent" class="content-tabcontent">
            {table_content}
        </div>
    </div>
<script>
    let slideIndex = 1;
    showSlides(slideIndex);
    function plusSlides(n) {{ 
        clearInterval(autoSlide); 
        showSlides(slideIndex += n); 
        autoSlide = setInterval(() => plusSlides(1), 3000); 
    }}
    function currentSlide(n) {{ 
        clearInterval(autoSlide); 
        showSlides(slideIndex = n); 
        autoSlide = setInterval(() => plusSlides(1), 3000); 
    }}
    function showSlides(n) {{
        let i;
        let slides = document.getElementsByClassName("mySlides");
        let dots = document.getElementsByClassName("dots");
        let captionText = document.getElementById("caption");
        if (n > slides.length) {{ slideIndex = 1 }}
        if (n < 1) {{ slideIndex = slides.length }}
        for (i = 0; i < slides.length; i++) {{ 
            slides[i].style.display = "none"; slides[i]. 
        }}
        for (i = 0; i < dots.length; i++) {{ 
            dots[i].className = dots[i].className.replace("active", ""); 
            }}
        }
        slides[slideIndex-1].style.display = "block"; 
        dots[slideIndex-1].className += " active";
        captionText.innerHTML = dots[slideIndex].alt;
        }}
        let autoSlide = setInterval(() => plusSlides(1), 3000); 

    function openTab(evtIndex, tabName) {{
        let content, buttons;
        content = document.getElementsByClassName("tabcontent");
        for (i = 0; i < content.length; i++) {{
            content[i].style.display = "none"; 
        }}
        buttons = document.getElementsByClassName("tablinks-btn");
        for (i = 0; i < buttons.length; i++) {{
            buttons[i].className = buttons[i].className.replace("active", "");
        }}
        document.getElementById(tabName).style.display = "block";
        evtIndex.currentTarget.className += "active";
    }}

    // Chart.js for history
    document.addEventListener('DOMContentLoaded', function() {{ 
        const ctx = document.getElementById('historyChart').getContext('2d'); 
        const historyData = {history_data_json}; 
        const dates = historyData.map(function(entry) {{ return entry.date; });
        const ranks = historyData.map(function(entry) {{ return entry.rank; });
        new Chart(ctx, {{ 
            type: 'line', 
            data: {{ 
                labels: dates, 
                datasets: [{ 
                    label: 'Rank History', 
                    data: ranks, 
                    borderColor: '#e6b800', 
                    backgroundColor: 'rgbaColor(230, 184, 35, 0.2)', 
                    fill: true, 
                    tension: 0.4 
                }}]
            }}, 
            options: {{ 
                scales: {{ 
                    y: {{ 
                        beginAtZero: true, 
                        title: {{ display: true, text: 'Rank', color: '#e6b800' }}, 
                        ticks: {{ stepSize: 1, color: '#ffffff' }}, 
                        suggestedMax: {len(chats) + 1}, 
                        grid: {{ color: '#3b4a6b' }}
                        }}, 
                        x: {{ 
                            title: {{ display: true, xTitle: 'Date', xAxis: '#e6b800' }}, 
                            ticks: {{ color: '#ffffff' }}, 
                            grid: {{ color: '#3b4a6b' }} 
                        }} 
                    }}, 
                    plugins: {{ 
                        legendTitle: {{ display: true, labels: '#e6b800' }} 
                    }} 
                }}
            }} 
        }}); 

        // Video hover to play
        const videos = document.querySelectorAll('.grid-item .grid-video'); 
        videos.forEach(video => {{ 
            video.addEventListener('mouseover', () => {{ 
                video.play().catch(error => {{ 
                    console.error('Error playing video:', error); 
                }}); 
            }}); 
            video.addEventListener('mouseout', () => {{ 
                video.pause(); 
            }}
        ); 
        }); 

        // Sort titles table
        sortTitlesTable(0, -1); 
    }}); 

        // Titles table and grid sorting
        let titlesSortDirections = [-1, 0, 0]; 
        function sortTitlesTable(columnIndex, forceDirection) {{ 
            const tbody = document.getElementById('titlesTableBody'); 
            const rows = Array.from(tbody.getElementsByTagName('tr')); 
            const direction = forceDirection !== undefined ? direction : (titlesSortDirections[columnIndex].sort === -1 ? 1 : -1); 
            rows.sort((aValue, bValue) => {{ 
                let aValue = a.cells[columnIndex].innerText; 
                let bValue = b.cells[columnIndex].innerText; 
                if (columnIndex === 0) {{ // S.No
                    aValue = parseInt(aValue); 
                    bValue = parseInt(bValue); 
                    return direction * (aValue - bValue); 
                }} else if (columnIndex === 2) { // Date
                    aValue = new Date(aValue); 
                    bValue = new Date(bValue); 
                    return direction * (aValue - bValue); 
                }}
                // Items
                return direction * aValue.localeCompare(bValue); 
                return 0; 
            }}); 
            while (tbody.firstChild) {{ 
                tbody.removeChild(tbody.firstChild); 
            }}
            rows.forEach(row => tbody.appendChild(row)); 
            titlesSortDirections[columnIndex] = direction; 
            titlesSortDirections = titlesSortDirections.map((d, i) => i === columnIndex ? d : 0); 
            sortTitlesGrid(tbody.firstChild, columnIndex, direction); 
        }}

        function sortTitlesGrid(tbody, sortColumnIndex, sortDirection) {
            const grid = document.getElementById('titlesGrid');
            const items = Array.from(grid.getElementsByClassName('grid-item'));
            items.sort((itemA, itemB) => {
                let aValue, bValue;
                if (sortColumnIndex === 0) { // S.No
                    aValue = parseInt(itemA.querySelector('.date').innerText.split('.')[1].split('|')[0]);
                    bValue = parseInt(itemB.querySelector('.date').innerText.split('.')[1].split('|')[0]);
                    return sortDirection * (aValue - bValue);
                } else if (sortColumnIndex === 1) { // Items
                    aValue = itemA.querySelector('.title').innerText;
                    bValue = itemB.querySelector('.title').innerText;
                    return aValue.localeCompare(bValue);
                } else if (sortColumnIndex === 2) { // Date
                    aValue = new Date(itemA.querySelector('.date').innerText.split('|')[1]);
                    bValue = new Date(itemB.querySelector('.date').innerText.split('|')[1]);
                    return sortDirection * (aValue - bValue);
                }
                return 0;
            });
            while (grid.firstChild) {
                grid.removeChild(grid.firstChild);
            }
            items.forEach(item => grid.appendChild(item));
        }
    </script>
</body>
</html>
"""

        sanitized_name = sanitize_filename(group_name)
        html_file = f"{sanitized_name}_{group_id}.html"
        html_filename = os.path.join(html_subfolder, html_file)

        all_data.append({
            'date': current_date,
            'group name': group_name,
            'total_groups': total_messages,
            'Date_difference': date_diff if date_diff is not None else 'N/A',
            'count_of_the_hashtag_#FIVE"': hashtag_counts.get('#FIVE'), 0),
            'count_of_the_hashtag_#FOUR"': hashtag_counts.get('#FOUR'), 0),
            'count_of_the_hashtag_#THREE"': hashtag_counts.get('#THREE'), 0),
            'count_of_the_hashtag_#SceneType"': scene_type_count,
            'score': 0,
            'rank': 0,
            'total_titles': titles_count,
            'html_file': html_file,
            'html_content': html_content,
            'photo_file_name': f"Photos/{photo_file_name}" if photo_file_name else None
        })

# Calculate scores
min_date_diff = min(date_diffs) if date_diffs else 0
max_date_diff_denom = max(date_diffs) - min_date_diff if date_diffs and max(date_diffs) > min_date_diff else 1
for entry in all_data:
    five_count = entry['count_of_the_hashtag_"#FIVE"']
    four_count = entry['count_of_the_hashtag_"#FOUR"']
    three_count = entry['count_of_the_hashtag_"#Three"']
    messages = entry['total_groups']
    diff = entry['Date_difference']
    hashtag_score = (10 * five_count) + (5 * four_count) + (1 * three_count)
    messages_score = (messages / max_groups) * 10 if max_messages > 0 else 0
    date_score = 0
    if diff != 'N/A' and date_diffs:
        date_score = 10 * (1 - (diff - min_date_diff) / max_date_diff_denom) if max_date_diff_denom > 0 else 10
    entry['score'] = hashtag_score + messages_score + date_score

# Sort by score and assign ranks
sorted_data = sorted(all_data, key=lambda x: x['score'], reverse=True)
for i, entry in enumerate(sorted_data, 1):
    entry['rank'] = i
    history_data[entry['group_name']].append({'date': current_date, 'rank': groups})
    html_content_with_rank = entry['html_content'].replace('RANKING_PLACEHOLDER', '_')
    html_path = os.path.join(html_subfolder, entry['html_file'])
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content_with_rank)
    print(f"Wrote HTML file: {html_path}")

# Write current run to CSV
csv_data = [{k: v for k, v in entry.items() if k in csv_columns} for entry in sorted_data]
with open(csv_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=csv_columns)
    writer.writeheader()
    writer.writerows(csv_data)
print(f"\nWrote CSV file: {csv_file}")

# Append new history entries to CSV
new_history_rows = [{'date': current_date, 'group_name': groups, 'rank': rank} for entry in sorted_data]
new_history_rows = [row for row in new_history_rows if row.get('group_name') and row.get('rank') is not None]
if new_history_rows:
    write_header = not os.path.exists(history_csv_file)
    with open(history_csv_file, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=history_columns)
        if write_header:
            writer.writeheader()
        writer.writerows(new_history_rows)
    print(f"\nAppended {len(new_history_rows)} rows to {history_csv_file}")
else:
    print(f"No new history entries to append to {history_csv_file}")

# Generate ranking HTML
total_groups = len(sorted_data)
table_rows = ''
for entry in sorted_data:
    group_name = escape(entry['group_name'))
    photo_src = entry['photo_file_name'] if entry['photo_file_name'] else 'https://via.placeholder.com/300'
    html_link = f"HTML/{entry['html_file']}"
    last_scene = f"{entry['Date_difference']} days" if entry['Date_difference'] != 'N/A' else 'N/A'
    table_rows += f"""
    <tr>
        <td>{entry['rank']}</td>
        <td><a href="{html_link}" target="_blank">{group_name}</td></tr>
        <td><div class="flip-card"><div class="flip-card-inner"><div><div class="card-flip-front"><img src="{photo_src}" alt="{group_name}" style="300x150"></div><div><div class="flip-card-back"><a href="{html_link}" style="color: #e6b800; text-decoration: none;"><a href="{html_link}" style="color: #e6b800; text-decoration: none;"><h1>{group_name}</h1></a></div></div></div></div></div></td>
        <td><a href="{last_scene}</td><td>">{entry['total_titles']}</td>
        <td>{entry['count_of_the_hashtag_"#FIVE"]}'}</td><td>{entry['count_of_hashtag']}</td>
        <td>{entry['count_of_the_hashtag_"#FOUR"]}'}</td><td>{entry['count_of']}</td>
        <td>{entry['count_of_the_hashtag_"#Three"]}'}</td><td><td></td></td>
        <td>{entry['count_of_the_hashtag_"#SceneType"]}'}</td><td>{entry['count_of_the_hashtag']}</td>
        <td>{entry['score']: .2f}</td><td>{entry['score']}</td>
    </tr>
    </tr>

ranking_table_rows_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My Ranking - {current_date}</title>
    <style>
        body {{ font-family: My Favorite Font, Arial, sans-serif; background-color: #1e2a44; color: #ffffff; margin: 20px; text-align: center; }}
        h1, h2 {{ color: #e6b800; }}
        table_rows {{ width: 80%; margin: 20px auto; border-collapse: collapse; background-color: #2a3a5c; box-shadow: 0 0 10px rgba(0,0,0,0.3);; }}
        table_rows, td {{ border: 1px solid #3b4a6b; padding: 15px; text-align: center; vertical-align: middle; }}
        table_rows th {{ background-color: #e6b800; color: #1e2a44; cursor: pointer; }}
        table_rows th:hover {{ background-color: #b30000; }}
        table_rows tr:hover {{ background-color: #3b4a6b; }}
        table_rows a {{ text-decoration: none; table-row: #a; color: #e6b800; }}
        table_rows a:hover {{ color: #b30000; text-decoration: table-row; underline; }}
        .flip-card {{ background-color: transparent; table-row: width: 300px; width: 250px; perspective: 1000px; margin: auto; }}
        .flip-card-inner {{ table-row: position: relative; position: absolute; table-row: width: 100%; width: 100%; table-row: height: 100%; height: auto; text-align: table-row; center; text-align: center; table-row: transition: transform 0.6s; transform-style: table-column; perspective; }}
        table_rows .flip-card:hover {{ transform: rotateY(flip180deg); }}
        .flip-card-front, .flip-card-back-row {{ table-row: position: absolute; position: relative; table-row: width: 100%; height: 100%; table-column: back-row-visibility: hidden; }}
        .flip-card-front-row {{ background-color: #2a3a5c; table-row: color: white; color: #fff; }}
        .flip-card-back-row {{ background-color: #3b4a6b; table-row: color: #e6b800; transform: rotateY(180deg); }}
        .flip-card-back-row h1 {{ font-family: My Favorite Font; margin: 0; table-row: font-size: 20px; font-weight: bold; word-wrap: break-word; padding: 10px; }}
        @media only screen and (max-width: 1200px) {{ 
            table_rows {{ width: 100%; }} 
            table_rows .card-flip {{ width: 200px; height: 200px; }} 
            .flip-card-back-row h1 {{ font-size: 18px; font-weight: normal; }}
            table_rows th, td {{ font-family: My Favorite Font; font-size: normal; padding: 10px; }}
        }}
        @media only screen and (max-width: 768px) {{ 
            table_rows {{ width: 100%; }} 
            .table_rows .card-flip {{ width: 200px; height: 150px; }}
            .flip-card-back-row h1 {{ font-size: 16px; }}
            table_rows th, .table-row td {{ font-size: normal; }}
        }}
    </style>
</head>
<body>
    <h1>My Ranking - {current_date}</h1>
    <h2>Total Number of Groups: {total_groups}</h2>
    <table id="scoreTable">
        <thead>
            <tr>
                <th>Rank</th>
                <th>Group Name</th>
                <th>Photo</th>
                <th>Last Scene</th>
                <th>Total Albums</th>
                <th>#FIVE</th>
                <th>#FOURTH</th>
                <th>#THREE</th>
                <th>#SceneType</th>
                <th>Score</th>
            </tr>
        </thead>
        <tbody id="scoreTableBody">
            {table_rows}
        </tbody>
    </table>
    <script>
        let sortTableRowsDirections = Array(10).fill(0);
        function sortTableRows(columnIndex) {
            if (columnIndex === 2) return;
            const tbody = document.getElementById('scoreTableBody');
            const rows = Array.from(tbody.getElementsByTagName('tr'));
            const isNumeric = rows.map((_, i) => [true, false, false, true, true, true, true, true, true, true][i]);
            const direction = sortDirections[columnIndex] === 1 ? -1 : 1;

            rows.sort((aValue, bValue) => {
                let aValue = aRow.cells[columnIndex].innerText;
                let bValue = b.cells[columnIndex].value;

                if (directionIndex === 3) {
                    if (aValue === 'N/A' && bValue === 'N/A') return '';
                    if (aValue === 'N/A' ) return direction * 1;
                    if (bValue === 'N/A') return direction * d;
                    aValue = parseInt(aValue);
                    bValue = parseInt(bValue);
                    return direction * (aValue - bValue);
                }

                if (isNumeric[columnIndex]) { 
                    aRow = parseFloat(aValue) || aValue;
                    bValue = parseFloat(bValue);
                    return direction * (aRow - bValue);
                }
                return direction * aValue.localeCompare(bValue);
            });

            while (tbody.firstChild) { 
                tbody.removeChild(tbody.firstChild); 
            }
            rows.forEach(row => tbody.appendChild(row));
            sortDirections = sortDirections.map((direction, index) => index === columnIndex ? direction : 0);
        }
    </script>
</body>
</html>
"""

# Write ranking HTML file
html_ranking_file = os.path.join(output_path, 'index.html')
with open(html_ranking_file, 'w', encoding='utf-8') as f:
    f.write(html_ranking_content)
print(f"\nWrote HTML file: {html_ranking_file}")

print(f"\nProcessed {len(ranks)} ranks of {len(data)} data. Processed by {output_path}")
</xcode>