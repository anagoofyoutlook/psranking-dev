import json
import os
import shutil
import zipfile
from datetime import datetime
from html import escape
import data_processing
import html_generator
import utils

# Define folder paths
input_folder = 'PS'
output_folder = 'docs'
html_subfolder = os.path.join(output_folder, 'HTML')
photos_folder = 'Photos'
history_csv_file = os.path.join(output_folder, 'history.csv')
csv_file = os.path.join(output_folder, 'output.csv')

# GitHub raw content base URL
github_raw_base = 'https://raw.githubusercontent.com/anagoofyoutlook/psranking-dev/main'

def setup_directories():
    for folder in [input_folder, output_folder, html_subfolder, photos_folder]:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"Created directory: {folder}")
        else:
            print(f"Directory already exists: {folder}")

def extract_json():
    zip_file = os.path.join(input_folder, 'result.zip')
    temp_json_file = os.path.join(input_folder, 'result.json')
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
    if not os.path.exists(temp_json_file):
        print(f"Error: Failed to extract 'result.json' from '{zip_file}'. Exiting.")
        exit(1)
    return temp_json_file

def main():
    setup_directories()
    temp_json_file = extract_json()
    print(f"Loading {temp_json_file}")
    with open(temp_json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    try:
        os.remove(temp_json_file)
        print(f"Removed temporary file: {temp_json_file}")
    except OSError as e:
        print(f"Warning: Could not remove {temp_json_file}: {e}")

    chats = data.get('chats', {}).get('list', [])
    print(f"Found {len(chats)} chats in result.json")
    if not chats:
        print("No chats found in 'result.json'. Exiting.")
        exit(1)

    all_data, max_messages, date_diffs = data_processing.process_chats(chats, history_csv_file, csv_file, photos_folder, github_raw_base)
    data_processing.calculate_scores_and_ranks(all_data, max_messages, date_diffs, history_csv_file, html_subfolder)
    html_generator.generate_index_html(all_data, csv_file, history_csv_file, github_raw_base, output_folder)

if __name__ == "__main__":
    main()