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
        minimal_html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>PS Ranking - {datetime.now().strftime('%Y-%m-%d')}</title>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #1e2a44; color: #ffffff; margin: 20px; text-align: center; }}
                h1 {{ color: #e6b800; }}
            </style>
        </head>
        <body>
            <h1>PS Ranking - {datetime.now().strftime('%Y-%m-%d')}</h1>
            <p>Error: result.zip not found in PS folder.</p>
        </body>
        </html>
        """
        index_path = os.path.join(output_folder, 'index.html')
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(minimal_html)
        print(f"Wrote minimal HTML file: {index_path}")
        return

    # Log zip file contents
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_contents = zip_ref.namelist()
            print(f"Contents of {zip_path}: {zip_contents}")
            if 'result.json' not in zip_contents:
                print("Error: result.json not found in result.zip")
                minimal_html = f"""
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>PS Ranking - {datetime.now().strftime('%Y-%m-%d')}</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; background-color: #1e2a44; color: #ffffff; margin: 20px; text-align: center; }}
                        h1 {{ color: #e6b800; }}
                    </style>
                </head>
                <body>
                    <h1>PS Ranking - {datetime.now().strftime('%Y-%m-%d')}</h1>
                    <p>Error: result.json not found in result.zip.</p>
                </body>
                </html>
                """
                index_path = os.path.join(output_folder, 'index.html')
                with open(index_path, 'w', encoding='utf-8') as f:
                    f.write(minimal_html)
                print(f"Wrote minimal HTML file: {index_path}")
                return
    except zipfile.BadZipFile as e:
        print(f"Error: Failed to read {zip_path}: {e}")
        minimal_html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>PS Ranking - {datetime.now().strftime('%Y-%m-%d')}</title>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #1e2a44; color: #ffffff; margin: 20px; text-align: center; }}
                h1 {{ color: #e6b800; }}
            </style>
        </head>
        <body>
            <h1>PS Ranking - {datetime.now().strftime('%Y-%m-%d')}</h1>
            <p>Error: Failed to read result.zip: {e}</p>
        </body>
        </html>
        """
        index_path = os.path.join(output_folder, 'index.html')
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(minimal_html)
        print(f"Wrote minimal HTML file: {index_path}")
        return

    all_data = data_processing.load_data(zip_path)
    print(f"Loaded {len(all_data)} groups from result.zip")
    if not all_data:
        print("No data loaded, generating minimal index.html")
        minimal_html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>PS Ranking - {datetime.now().strftime('%Y-%m-%d')}</title>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #1e2a44; color: #ffffff; margin: 20px; text-align: center; }}
                h1 {{ color: #e6b800; }}
            </style>
        </head>
        <body>
            <h1>PS Ranking - {datetime.now().strftime('%Y-%m-%d')}</h1>
            <p>No groups found in result.json. Please verify the data format.</p>
        </body>
        </html>
        """
        index_path = os.path.join(output_folder, 'index.html')
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(minimal_html)
        print(f"Wrote minimal HTML file: {index_path}")
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

    # Added debugging
    print("Sorted data contents:")
    for group in sorted_data:
        print(f"Group: {group.get('group_name', 'Unknown')}, Keys: {list(group.keys())}, up_down: {group.get('up_down', 'N/A')}, Titles: {len(group.get('titles', []))}")

    html_generator.generate_index_html(sorted_data, output_csv_file, history_csv_file, github_raw_base, output_folder)
    print("Generated index.html and group HTML files")
    print(f"Listing files in {output_folder}:")
    os.system(f"ls -R {output_folder}")

if __name__ == '__main__':
    main()