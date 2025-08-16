import os
import shutil
import zipfile
import data_processing
import html_generator
import utils
from datetime import datetime

def main():
    output_folder = 'docs'
    html_subfolder = os.path.join(output_folder, 'HTML')
    output_csv_file = os.path.join(output_folder, 'output.csv')
    history_csv_file = os.path.join(output_folder, 'history.csv')
    zip_path = os.path.join('PS', 'result.zip')
    github_raw_base = 'https://raw.githubusercontent.com/anagoofyoutlook/psranking-dev/main'

    if os.path.exists(output_folder):
        shutil.rmtree(output_folder)
    os.makedirs(html_subfolder, exist_ok=True)

    print(f"Checking for result.zip at: {zip_path}")
    if not os.path.exists(zip_path):
        print(f"Error: {zip_path} not found")
        return

    all_data = data_processing.load_data(zip_path)
    print(f"Loaded {len(all_data)} groups from result.zip")
    if not all_data:
        print("No data loaded, exiting.")
        return

    max_messages = max(len(group['messages']) for group in all_data) if all_data else 1
    date_diffs = {group['id']: [] for group in all_data}
    for group in all_data:
        for msg in group['messages']:
            date_diff = data_processing.get_date_difference(msg['date'], datetime.now())
            if date_diff is not None:
                date_diffs[group['id']].append(date_diff)

    sorted_data = data_processing.calculate_scores_and_ranks(all_data, max_messages, date_diffs, history_csv_file, html_subfolder, output_csv_file, github_raw_base)
    print(f"Generated {len(sorted_data)} group rankings")
    html_generator.generate_index_html(sorted_data, output_csv_file, history_csv_file, github_raw_base, output_folder)
    print("Generated index.html and group HTML files")
    print(f"Listing files in {output_folder}:")
    os.system(f"ls -R {output_folder}")

if __name__ == '__main__':
    main()