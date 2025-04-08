import json
import csv
import os
from datetime import datetime
import re

# Define folder paths
input_folder = 'PS'
output_folder = 'docs'  # For GitHub Pages
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
chats = data.get('get', {}).get('list', [])
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

# Process each chat
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

        # Case-insensitive hashtag counting
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

        # Calculate date_diff before using it
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

        # Hashtag processing
        special_ratings = ['#FIVE', '#FOUR', '#THREE']
        special_scene_types = ['#FM', '#FF', '#FFM', '#FFFM', '#FFFFM', '#FMM', '#FMMM', '#FMMMM', '#FFMM', '#FFFMMM', '#ORGY']
        ratings_hashtag_list = ''
        scene_types_hashtag_list = ''
        other_hashtag_list = ''
        
        for hashtag in sorted(hashtag_counts.keys()):
            count = hashtag_counts[hashtag]
            if hashtag in special_ratings:
                ratings_hashtag_list += f'<li class="hashtag-item">{hashtag}: {count}</li>\n'
            elif hashtag in special_scene_types:
                scene_types_hashtag_list += f'<li class="hashtag-item">{hashtag}: {count}</li>\n'
            else:
                other_hashtag_list += f'<li class="hashtag-item">{hashtag}: {count}</li>\n'
        
        if not ratings_hashtag_list:
            ratings_hashtag_list = '<li>No rating hashtags (#FIVE, #FOUR, #Three) found</li>'
        if not scene_types_hashtag_list:
            scene_types_hashtag_list = '<li>No scene type hashtags found</li>'
        if not other_hashtag_list:
            other_hashtag_list = '<li>No other hashtags found</li>'

        scene_type_count = sum(hashtag_counts.get(h, 0) for h in special_scene_types)
        date_diff_text = f'{date_diff} days' if date_diff is not None else 'N/A'

        # Titles
        titles = []
        topic_created_count = 0
        for message in messages:
            if message.get('action') == 'topic_created':
                topic_created_count += 1
                title = message.get('title', '')
                message_id = message.get('id')
                date_str = message.get('date', '')
                if title.strip() and message_id and date_str:
                    try:
                        date = datetime.fromisoformat(date_str).strftime('%Y-%m-%d')
                        titles.append({'title': title, 'message_id': message_id, 'date': date})
                    except ValueError:
                        continue
        titles.sort(key=lambda x: x['title'])
        titles_count = len(titles)
        titles_table = f"""
            <p>Total Titles: {titles_count}</p>
            <table class="titles-table" id="titlesTable">
                <thead><tr><th onclick="sortTitlesTable(0)">Items</th><th onclick="sortTitlesTable(1)">Date</th></tr></thead>
                <tbody id="titlesTableBody">
        """
        for title_data in titles:
            title = title_data['title']
            message_id = title_data['message_id']
            date = title_data['date']
            link = f'https://t.me/c/{telegram_group_id}/{message_id}'
            titles_table += f'<tr><td><a href="{link}" target="_blank">{title}</a></td><td>{date}</td></tr>'
        titles_table += '</tbody></table>' if titles else f'<p>No titles found (Total: {titles_count})</p>'

        # Photos and slideshow
        photo_extensions = ['.jpg', '.jpeg', '.png', '.gif']
        photo_paths = []
        group_subfolder = os.path.join(photos_folder, group_name)
        if os.path.exists(group_subfolder):
            for file_name in os.listdir(group_subfolder):
                if file_name.lower().endswith(tuple(photo_extensions)):
                    photo_paths.append(f"../../{photos_folder}/{group_name}/{file_name}")
        if not photo_paths:
            photo_paths = ['https://via.placeholder.com/1920x800']

        slideshow_content = '<div class="container">\n'
        for i, photo_path in enumerate(photo_paths, 1):
            slideshow_content += f"""
                <div class="mySlides">
                    <div class="numbertext">{i} / {len(photo_paths)}</div>
                    <img src="{photo_path}" style="width:100%; height:100%;">
                </div>
            """
        slideshow_content += """
            <a class="prev" onclick="plusSlides(-1)">❮</a>
            <a class="next" onclick="plusSlides(1)">❯</a>
            <div class="caption-container"><p id="caption"></p></div>
            <div class="row">
        """
        for i, photo_path in enumerate(photo_paths, 1):
            slideshow_content += f"""
                <div class="column">
                    <img class="demo cursor" src="{photo_path}" style="width:100%" onclick="currentSlide({i})" alt="{group_name} Photo {i}">
                </div>
            """
        slideshow_content += '</div></div>'

        photo_file_name = None
        for ext in photo_extensions:
            photo_file = f"{group_name}{ext}"
            full_path = os.path.join(photos_folder, photo_file)
            if os.path.exists(full_path):
                photo_file_name = photo_file
                break

        rank_history = history_data.get(group_name, [])
        rank_history_json = json.dumps([{'date': entry['date'], 'rank': entry['rank']} for entry in rank_history])

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{group_name}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.2/dist/chart.umd.min.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #e6f2ff; color: #003366; text-align: center; }}
        h1 {{ color: #003366; }}
        .info {{ background-color: #cce6ff; padding: 10px; border-radius: 5px; margin-bottom: 20px; }}
        .hashtags {{ list-style-type: none; padding: 0; }}
        .hashtag-item {{ background-color: #99ccff; margin: 5px 0; padding: 5px; border-radius: 3px; display: inline-block; width: 200px; }}
        .rank-container {{ display: flex; justify-content: center; align-items: center; margin: 20px 0; gap: 20px; flex-wrap: wrap; }}
        .rank-number {{ font-size: 48px; font-weight: bold; color: #003366; display: inline-block; }}
        @keyframes countUp {{ from {{ content: "0"; }} to {{ content: attr(data-rank); }} }}
        .rank-number::before {{ content: "0"; animation: countUp 2s ease-out forwards; display: inline-block; min-width: 60px; }}
        .chart-container {{ max-width: 400px; width: 100%; }}
        canvas {{ width: 100% !important; height: auto !important; }}
        .titles-table {{ width: 80%; margin: 20px auto; border-collapse: collapse; background-color: #cce6ff; }}
        .titles-table th, .titles-table td {{ padding: 10px; border: 1px solid #99ccff; text-align: left; }}
        .titles-table th {{ background-color: #99ccff; color: #003366; cursor: pointer; }}
        .titles-table th:hover {{ background-color: #b3d9ff; }}
        a {{ color: #003366; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        .container {{ position: relative; width: 1920px; height: 800px; margin: auto; }}
        .mySlides {{ display: none; width: 100%; height: 100%; }}
        img {{ vertical-align: middle; width: 100%; height: 100%; object-fit: cover; }}
        .cursor {{ cursor: pointer; }}
        .prev, .next {{ cursor: pointer; position: absolute; top: 40%; width: auto; padding: 16px; margin-top: -50px; color: white; font-weight: bold; font-size: 20px; border-radius: 0 3px 3px 0; user-select: none; -webkit-user-select: none; }}
        .next {{ right: 0; border-radius: 3px 0 0 3px; }}
        .prev:hover, .next:hover {{ background-color: rgba(0, 0, 0, 0.8); }}
        .numbertext {{ color: #f2f2f2; font-size: 12px; padding: 8px 12px; position: absolute; top: 0; }}
        .caption-container {{ text-align: center; background-color: #222; padding: 2px 16px; color: white; }}
        .row:after {{ content: ""; display: table; clear: both; }}
        .column {{ float: left; width: {100 / len(photo_paths) if photo_paths else 100}%; }}
        .demo {{ opacity: 0.6; }}
        .active, .demo:hover {{ opacity: 1; }}
        @media only screen and (max-width: 1920px) {{ .container {{ width: 100%; height: auto; }} }}
    </style>
</head>
<body>
    {slideshow_content}
    <h1>{group_name}</h1>
    <div class="rank-container">
        <div class="chart-container"><h2>Rank History</h2><canvas id="rankChart"></canvas></div>
        <p>Rank: <span class="rank-number" data-rank="RANK_PLACEHOLDER"></span></p>
    </div>
    <div class="info"><p>Scenes: {total_messages}</p><p>Last Scene: {date_diff_text}</p></div>
    <div class="info">
        <h2>Rating Hashtag Counts (#FIVE, #FOUR, #Three)</h2><ul class="hashtags">{ratings_hashtag_list}</ul>
        <h2>Scene Type Hashtag Counts</h2><ul class="hashtags">{scene_types_hashtag_list}</ul>
        <h2>Other Hashtag Counts</h2><ul class="hashtags">{other_hashtag_list}</ul>
    </div>
    <div class="info"><h2>Titles</h2>{titles_table}</div>
    <script>
        let slideIndex = 1;
        showSlides(slideIndex);
        function plusSlides(n) {{ clearInterval(autoSlide); showSlides(slideIndex += n); autoSlide = setInterval(() => plusSlides(1), 3000); }}
        function currentSlide(n) {{ clearInterval(autoSlide); showSlides(slideIndex = n); autoSlide = setInterval(() => plusSlides(1), 3000); }}
        function showSlides(n) {{
            let i;
            let slides = document.getElementsByClassName("mySlides");
            let dots = document.getElementsByClassName("demo");
            let captionText = document.getElementById("caption");
            if (n > slides.length) {{ slideIndex = 1 }}
            if (n < 1) {{ slideIndex = slides.length }}
            for (i = 0; i < slides.length; i++) {{ slides[i].style.display = "none"; }}
            for (i = 0; i < dots.length; i++) {{ dots[i].className = dots[i].className.replace(" active", ""); }}
            slides[slideIndex-1].style.display = "block";
            dots[slideIndex-1].className += " active";
            captionText.innerHTML = dots[slideIndex-1].alt;
        }}
        let autoSlide = setInterval(() => plusSlides(1), 3000);

        document.addEventListener('DOMContentLoaded', function() {{
            const ctx = document.getElementById('rankChart').getContext('2d');
            const historyData = {rank_history_json};
            const dates = historyData.map(entry => entry.date);
            const ranks = historyData.map(entry => entry.rank);
            new Chart(ctx, {{
                type: 'line',
                data: {{ labels: dates, datasets: [{{ label: 'Rank Over Time', data: ranks, borderColor: '#003366', backgroundColor: 'rgba(0, 51, 102, 0.2)', fill: true, tension: 0.4 }}] }},
                options: {{ scales: {{ y: {{ beginAtZero: true, reverse: true, title: {{ display: true, text: 'Rank' }}, ticks: {{ stepSize: 1 }} }}, x: {{ title: {{ display: true, text: 'Date' }} }} }}, plugins: {{ legend: {{ display: true }} }} }}
            }});
            let titlesSortDirections = [0, 0];
            function sortTitlesTable(columnIndex) {{
                const tbody = document.getElementById('titlesTableBody');
                const rows = Array.from(tbody.getElementsByTagName('tr'));
                const isNumeric = [false, false];
                const direction = titlesSortDirections[columnIndex] === 1 ? -1 : 1;
                rows.sort((a, b) => {{
                    let aValue = a.cells[columnIndex].innerText;
                    let bValue = b.cells[columnIndex].innerText;
                    if (columnIndex === 1) {{ aValue = new Date(aValue); bValue = new Date(bValue); return direction * (aValue - bValue); }}
                    else {{ return direction * aValue.localeCompare(bValue); }}
                }});
                while (tbody.firstChild) {{ tbody.removeChild(tbody.firstChild); }}
                rows.forEach(row => tbody.appendChild(row));
                titlesSortDirections = titlesSortDirections.map((d, i) => (i === columnIndex ? direction : 0));
            }}
        }});
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

# Calculate scores
min_date_diff = min(date_diffs) if date_diffs else 0
max_date_diff_denom = max(date_diffs) - min_date_diff if date_diffs and max(date_diffs) > min_date_diff else 1

for entry in all_data:
    five_count = entry['count of the hashtag "#FIVE"']
    four_count = entry['count of the hashtag "#FOUR"']
    three_count = entry['count of the hashtag "#Three"']
    messages = entry['total messages']
    diff = entry['Datedifference']

    hashtag_score = (10 * five_count) + (5 * four_count) + (1 * three_count)
    messages_score = (messages / max_messages) * 10 if max_messages > 0 else 0
    date_score = 0
    if diff != 'N/A' and date_diffs:
        date_score = 10 * (1 - (diff - min_date_diff) / max_date_diff_denom) if max_date_diff_denom > 0 else 10
    entry['score'] = hashtag_score + messages_score + date_score

# Sort by score and assign ranks
sorted_data = sorted(all_data, key=lambda x: x['score'], reverse=True)
for i, entry in enumerate(sorted_data, 1):
    entry['rank'] = i
    html_content_with_rank = entry['html_content'].replace('RANK_PLACEHOLDER', str(i))
    with open(os.path.join(html_subfolder, entry['html_file']), 'w', encoding='utf-8') as f:
        f.write(html_content_with_rank)
    print(f"Group: {entry['group name']}, Rank assigned: {i}, HTML file: {entry['html_file']}")

# Write CSV
csv_data = [{k: (int(v) if k == 'rank' else v) for k, v in entry.items() if k in csv_columns} for entry in sorted_data]
with open(csv_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=csv_columns)
    writer.writeheader()
    writer.writerows(csv_data)

# Generate ranking HTML
total_groups = len(sorted_data)
table_rows = ''
for entry in sorted_data:
    group_name = entry['group name']
    photo_rel_path = entry['photo_rel_path']
    photo_src = photo_rel_path if photo_rel_path else 'https://via.placeholder.com/300'
    html_link = f"HTML/{entry['html_file']}"
    print(f"Group: {group_name}, Photo Source for Ranking: {photo_src}")

    table_rows += f"""
        <tr>
            <td>{entry['rank']}</td>
            <td>
                <div class="flip-card">
                    <div class="flip-card-inner">
                        <div class="flip-card-front">
                            <a href="{html_link}" target="_blank">
                                <img src="{photo_src}" alt="{group_name}" style="width:300px;height:300px;object-fit:cover;">
                            </a>
                        </div>
                        <div class="flip-card-back">
                            <a href="{html_link}" target="_blank" style="color: white; text-decoration: none;">
                                <h1>{group_name}</h1>
                            </a>
                        </div>
                    </div>
                </div>
            </td>
            <td><a href="{html_link}" target="_blank">{group_name}</a></td>
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
    <style>
        body {{ font-family: Arial, Helvetica, sans-serif; background-color: #e6f2ff; color: #003366; margin: 20px; text-align: center; }}
        h1 {{ color: #003366; }}
        h2 {{ color: #003366; margin-top: 10px; }}
        table {{ width: 90%; margin: 20px auto; border-collapse: collapse; background-color: #cce6ff; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1); }}
        th, td {{ padding: 15px; border: 1px solid #99ccff; text-align: center; vertical-align: middle; }}
        th {{ background-color: #99ccff; color: #003366; cursor: pointer; }}
        th:hover {{ background-color: #b3d9ff; }}
        tr:hover {{ background-color: #b3d9ff; }}
        a {{ color: #003366; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        .flip-card {{ background-color: transparent; width: 300px; height: 300px; perspective: 1000px; }}
        .flip-card-inner {{ position: relative; width: 100%; height: 100%; text-align: center; transition: transform 0.6s; transform-style: preserve-3d; box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2); }}
        .flip-card:hover .flip-card-inner {{ transform: rotateY(180deg); }}
        .flip-card-front, .flip-card-back {{ position: absolute; width: 100%; height: 100%; -webkit-backface-visibility: hidden; backface-visibility: hidden; }}
        .flip-card-front {{ background-color: #bbb; color: black; }}
        .flip-card-back {{ background-color: #2980b9; color: white; transform: rotateY(180deg); display: flex; justify-content: center; align-items: center; flex-direction: column; }}
        .flip-card-back h1 {{ margin: 0; font-size: 24px; word-wrap: break-word; padding: 10px; }}
    </style>
</head>
<body>
    <h1>PS Ranking - {current_date}</h1>
    <h2>Total Number of Groups: {total_groups}</h2>
    <table id="rankingTable">
        <thead>
            <tr>
                <th onclick="sortTable(0)">Rank</th>
                <th>Photo</th>
                <th onclick="sortTable(2)">Group Name</th>
                <th onclick="sortTable(3)">Total Titles</th>
                <th onclick="sortTable(4)">#FIVE</th>
                <th onclick="sortTable(5)">#FOUR</th>
                <th onclick="sortTable(6)">#Three</th>
                <th onclick="sortTable(7)">#SceneType</th>
                <th onclick="sortTable(8)">Score</th>
            </tr>
        </thead>
        <tbody id="tableBody">
            {table_rows}
        </tbody>
    </table>
    <script>
        let sortDirections = [0, 0, 0, 0, 0, 0, 0, 0, 0];
        function sortTable(columnIndex) {{
            const tbody = document.getElementById('tableBody');
            const rows = Array.from(tbody.getElementsByTagName('tr'));
            const isNumeric = [true, false, false, true, true, true, true, true, true][columnIndex];
            const direction = sortDirections[columnIndex] === 1 ? -1 : 1;
            rows.sort((a, b) => {{
                let aValue = a.cells[columnIndex].innerText;
                let bValue = b.cells[columnIndex].innerText;
                if (isNumeric) {{ aValue = parseFloat(aValue) || 0; bValue = parseFloat(bValue) || 0; return direction * (aValue - bValue); }}
                else {{ return direction * aValue.localeCompare(bValue); }}
            }});
            while (tbody.firstChild) {{ tbody.removeChild(tbody.firstChild); }}
            rows.forEach(row => tbody.appendChild(row));
            sortDirections = sortDirections.map((d, i) => (i === columnIndex ? direction : 0));
        }}
    </script>
</body>
</html>
"""

# Write ranking HTML file
ranking_html_file = os.path.join(output_folder, 'index.html')
with open(ranking_html_file, 'w', encoding='utf-8') as f:
    f.write(ranking_html_content)

print(f"Processed {len(chats)} chats. Output files generated in '{output_folder}': 'index.html', 'output.csv', and HTML files in 'HTML' subfolder.")