import json
import csv
import os
from datetime import datetime
import re

# Define folder paths
input_folder = 'PS'
output_folder = 'docs'  # Changed to 'docs' for GitHub Pages
html_subfolder = os.path.join(output_folder, 'HTML')
photos_folder = 'Photos'

# Define CSV output path
csv_file = os.path.join(output_folder, 'output.csv')

# Ensure directories exist
for folder in [input_folder, output_folder, html_subfolder, photos_folder]:
    if not os.path.exists(folder):
        os.makedirs(folder)
        if folder == input_folder:
            print(f"Created '{input_folder}'. Please add 'result.json' and rerun the script.")
            exit()
        elif folder == photos_folder:
            print(f"Created '{photos_folder}'. Add group photos as needed.")
        else:
            print(f"Created '{folder}'.")

# Path to result.json
input_file = os.path.join(input_folder, 'result.json')

# Verify file existence
if not os.path.exists(input_file):
    print(f"'result.json' not found in '{input_folder}'. Please add it and rerun the script.")
    exit()

# Load JSON data
with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Access chats list
chats = data.get('chats', {}).get('list', [])
if not chats:
    print("No chats found in 'result.json'. Please verify the file content.")
    exit()

# Define CSV columns
csv_columns = [
    'date',
    'group name',
    'total messages',
    'Datedifference',
    'count of the hashtag "#FIVE"',
    'count of the hashtag "#FOUR"',
    'count of the hashtag "#Three"',
    'count of the hashtag "#SceneType"',
    'score',
    'rank',
    'total titles'
]

# Load existing CSV data for history
history_data = {}
if os.path.exists(csv_file):
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            group = row.get('group name', 'Unknown')
            try:
                rank_str = row.get('rank', '0')
                rank = int(float(rank_str))
                if group not in history_data:
                    history_data[group] = []
                history_data[group].append({
                    'date': row.get('date', ''),
                    'rank': rank
                })
            except (ValueError, TypeError) as e:
                print(f"Skipping invalid rank for group '{group}': {row}. Error: {e}")
                continue

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

# Process each chat (unchanged logic, just showing key structure)
for chat in chats:
    if chat.get('type') == 'private_supergroup':
        group_name = chat.get('name', 'Unknown Group')
        group_id = str(chat['id'])
        if group_id.startswith('-100'):
            telegram_group_id = group_id[4:]
        else:
            telegram_group_id = group_id
        messages = chat.get('messages', [])

        total_messages = sum(1 for msg in messages if msg.get('type') == 'message')
        max_messages = max(max_messages, total_messages)

        # Hashtag counting, date diff, titles, photos, etc. (unchanged, omitted for brevity)
        # Assume this part generates the same HTML content as before

        # Adjust paths for GitHub Pages
        rank_history = history_data.get(group_name, [])
        rank_history_json = json.dumps([{'date': entry['date'], 'rank': entry['rank']} for entry in rank_history])

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{group_name}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.2/dist/chart.umd.min.js"></script>
    <!-- Styles unchanged -->
</head>
<body>
    <!-- Slideshow, rank graph, and other content unchanged -->
    <script>
        // JavaScript for slideshow and Chart.js unchanged
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
            'total messages': total_messages,
            'Datedifference': date_diff if date_diff is not None else 'N/A',
            'count of the hashtag "#FIVE"': hashtag_counts.get('#FIVE', 0),
            'count of the hashtag "#FOUR"': hashtag_counts.get('#FOUR', 0),
            'count of the hashtag "#Three"': hashtag_counts.get('#Three', 0),
            'count of the hashtag "#SceneType"': scene_type_count,
            'score': 0,
            'rank': 0,
            'total titles': titles_count,
            'html_file': html_file,
            'html_content': html_content,
            'photo_rel_path': f"../{photos_folder}/{photo_file_name}" if photo_file_name else None
        })

# Calculate scores, assign ranks, and write HTML files (unchanged logic)
for entry in all_data:
    # Score calculation (unchanged)
    pass

sorted_data = sorted(all_data, key=lambda x: x['score'], reverse=True)
for i, entry in enumerate(sorted_data, 1):
    entry['rank'] = i
    html_content_with_rank = entry['html_content'].replace('RANK_PLACEHOLDER', str(i))
    with open(os.path.join(html_subfolder, entry['html_file']), 'w', encoding='utf-8') as f:
        f.write(html_content_with_rank)

# Write CSV
csv_data = [{k: (int(v) if k == 'rank' else v) for k, v in entry.items() if k in csv_columns} for entry in sorted_data]
with open(csv_file, 'w', newline='', encoding='utf-8') as f:  # Overwrite to ensure clean data
    writer = csv.DictWriter(f, fieldnames=csv_columns)
    writer.writeheader()
    writer.writerows(csv_data)

# Generate ranking HTML (adjusted paths for GitHub Pages)
table_rows = ''
for entry in sorted_data:
    photo_src = entry['photo_rel_path'] if entry['photo_rel_path'] else 'https://via.placeholder.com/300'
    html_link = f"HTML/{entry['html_file']}"
    table_rows += f"""
        <tr>
            <td>{entry['rank']}</td>
            <td><div class="flip-card"><div class="flip-card-inner"><div class="flip-card-front">
                <a href="{html_link}" target="_blank"><img src="{photo_src}" alt="{entry['group name']}" style="width:300px;height:300px;object-fit:cover;"></a>
            </div><div class="flip-card-back"><a href="{html_link}" target="_blank" style="color: white; text-decoration: none;">
                <h1>{entry['group name']}</h1></a></div></div></div></td>
            <td><a href="{html_link}" target="_blank">{entry['group name']}</a></td>
            <td>{entry['total titles']}</td>
            <td>{entry['count of the hashtag "#FIVE"']}</td>
            <td>{entry['count of the hashtag "#FOUR"']}</td>
            <td>{entry['count of the hashtag "#Three"']}</td>
            <td>{entry['count of the hashtag "#SceneType"']}</td>
            <td>{entry['score']:.2f}</td>
        </tr>
    """

ranking_html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PS Ranking - {current_date}</title>
    <!-- Styles unchanged -->
</head>
<body>
    <h1>PS Ranking - {current_date}</h1>
    <h2>Total Number of Groups: {len(sorted_data)}</h2>
    <table id="rankingTable">
        <thead><tr><th>Rank</th><th>Photo</th><th>Group Name</th><th>Total Titles</th><th>#FIVE</th><th>#FOUR</th><th>#Three</th><th>#SceneType</th><th>Score</th></tr></thead>
        <tbody id="tableBody">{table_rows}</tbody>
    </table>
    <!-- JavaScript unchanged -->
</body>
</html>
"""

ranking_html_file = os.path.join(output_folder, 'index.html')  # GitHub Pages default entry point
with open(ranking_html_file, 'w', encoding='utf-8') as f:
    f.write(ranking_html_content)

print(f"Output generated in '{output_folder}': 'index.html', 'output.csv', and HTML files in 'HTML' subfolder.")