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
    os.makedirs(folder, exist_ok=True)

# Copy Photos/ to docs/Photos/
if os.path.exists(photos_folder):
    if os.path.exists(docs_photos_folder):
        shutil.rmtree(docs_photos_folder)
    shutil.copytree(photos_folder, docs_photos_folder)

# Extract result.json from ZIP
zip_file = os.path.join(input_folder, 'result.zip')
temp_json_file = os.path.join(input_folder, 'result.json')

if not os.path.exists(zip_file):
    exit(1)

with zipfile.ZipFile(zip_file, 'r') as zip_ref:
    for file_info in zip_ref.infolist():
        if file_info.filename.endswith('result.json'):
            zip_ref.extract(file_info, input_folder)
            extracted_path = os.path.join(input_folder, file_info.filename)
            if extracted_path != temp_json_file:
                shutil.move(extracted_path, temp_json_file)
            break

# Load JSON data
with open(temp_json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)
os.remove(temp_json_file)

chats = data.get('chats', {}).get('list', [])

# Load and deduplicate history
history_data = {}
current_date = datetime.now().strftime('%Y-%m-%d')
if os.path.exists(history_csv_file):
    with open(history_csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            group = row.get('group name', 'Unknown')
            date = row.get('date', '')
            try:
                rank = int(float(row.get('rank', '0')))
                if group not in history_data:
                    history_data[group] = {}
                if date != current_date:
                    if date not in history_data[group] or rank < history_data[group][date]:
                        history_data[group][date] = rank
            except Exception:
                continue
# Convert dicts to list
for group in history_data:
    history_data[group] = [
        {'date': date, 'rank': rank}
        for date, rank in sorted(history_data[group].items())
    ]

# Further processing logic continues here...
# Keep rest of the script unchanged or insert your logic where appropriate
