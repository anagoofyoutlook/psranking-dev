import json
import os
import csv
from datetime import datetime
import utils

def generate_index_html(sorted_data, output_csv_file, history_csv_file, github_raw_base, output_folder):
    # Sort for top movers (top risers)
    top_movers = sorted(
        [g for g in sorted_data if g.get('up_down') != 'N/A' and isinstance(g.get('up_down'), (int, float)) and g.get('up_down') > 0],
        key=lambda x: x.get('up_down', 0), reverse=True
    )[:5]

    # Generate top movers rows
    top_movers_rows = ''
    for group in top_movers:
        group_name = group.get('group_name', 'Unknown')
        rank = group.get('rank', 'N/A')
        up_down = group.get('up_down', 'N/A')
        photo_url = group.get('photo_file_name', '') if utils.is_url_accessible(group.get('photo_file_name', '')) else f"{github_raw_base}/Photos/placeholder.png"
        html_link = f"HTML/{group.get('html_file', '')}"
        up_down_str = f'<p style="color: green;">+{up_down} Up</p>' if isinstance(up_down, (int, float)) and up_down > 0 else '<p>N/A</p>'
        top_movers_rows += f'''
            <tr>
                <td>
                    <div class="mover-info">
                        <p>Rank: {rank}</p>
                        <p>{group_name}</p>
                        <img src="{photo_url}" alt="{group_name}" style="width:200px;height:200px;object-fit:cover;">
                        {up_down_str}
                    </div>
                </td>
            </tr>
        '''

    # Generate main table rows
    table_rows = ''
    for group in sorted_data:
        group_name = group.get('group_name', 'Unknown')
        photo_url = group.get('photo_file_name', '') if utils.is_url_accessible(group.get('photo_file_name', '')) else f"{github_raw_base}/Photos/placeholder.png"
        html_link = f"HTML/{group.get('html_file', '')}"
        flip_card = f'''
            <div class="flip-card">
                <div class="flip-card-inner">
                    <div class="flip-card-front">
                        <img src="{photo_url}" alt="{group_name}" style="width:300px;height:300px;object-fit:cover;">
                    </div>
                    <div class="flip-card-back">
                        <a href="{html_link}" target="_blank" style="color: #e6b800; text-decoration: none;"><h1>{group_name}</h1></a>
                    </div>
                </div>
            </div>
        '''
        up_down = group.get('up_down', 'N/A')
        if up_down != 'N/A' and isinstance(up_down, (int, float)):
            color = "green" if up_down > 0 else "red"
            direction = "Up" if up_down > 0 else "Down"
            up_down_str = f'<span style="color: {color};">{up_down} {direction}</span>'
        else:
            up_down_str = 'N/A'
        last_scene = group.get('Datedifference', 'N/A')
        table_rows += f'''
            <tr>
                <td>{group.get('rank', 'N/A')}</td>
                <td>{group.get('last_rank', 'N/A')}</td>
                <td>{up_down_str}</td>
                <td><a href="{html_link}" target="_blank">{group_name}</a></td>
                <td>{flip_card}</td>
                <td>{last_scene}</td>
                <td>{group.get('total titles', 'N/A')}</td>
                <td>{group.get('count of the hashtag "#FIVE"', 0)}</td>
                <td>{group.get('count of the hashtag "#FOUR"', 0)}</td>
                <td>{group.get('count of the hashtag "#Three"', 0)}</td>
                <td>{group.get('count of the hashtag "#SceneType"', 0)}</td>
                <td>{group.get('score', 0):.2f}</td>
            </tr>
        '''

    # HTML content with CSS from rank.py
    ranking_html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PS Ranking - {datetime.now().strftime('%Y-%m-%d')}</title>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #1e2a44; color: #ffffff; margin: 20px; text-align: center; }}
            h1, h2 {{ color: #e6b800; }}
            table {{ width: 80%; margin: 20px auto; border-collapse: collapse; background-color: #2a3a5c; box-shadow: 0 0 10px rgba(0, 0, 0, 0.3); }}
            th, td {{ border: 1px solid #3b4a6b; text-align: center; vertical-align: middle; padding: 15px; color: #ffffff; }}
            th {{ background-color: #e6b800; color: #1e2a44; cursor: pointer; }}
            th:hover {{ background-color: #b30000; }}
            tr:hover {{ background-color: #3b4a6b; }}
            .up-down-img {{ width: 20px; height: 20px; vertical-align: middle; }}
            a {{ text-decoration: none; color: #e6b800; }}
            a:hover {{ color: #b30000; text-decoration: underline; }}
            .flip-card {{ background-color: transparent; width: 300px; height: 300px; perspective: 1000px; margin: 10px auto; }}
            .flip-card-inner {{ position: relative; width: 100%; height: 100%; text-align: center; transition: transform 0.6s; transform-style: preserve-3d; box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2); }}
            .flip-card:hover .flip-card-inner {{ transform: rotateY(180deg); }}
            .flip-card-front, .flip-card-back {{ position: absolute; width: 100%; height: 100%; backface-visibility: hidden; border-radius: 5px; }}
            .flip-card-front {{ background-color: #2a3a5c; color: #ffffff; }}
            .flip-card-back {{ background-color: #3b4a6b; color: #e6b800; transform: rotateY(180deg); display: flex; justify-content: center; align-items: center; flex-direction: column; }}
            .flip-card-back h1 {{ margin: 0; font-size: 24px; word-wrap: break-word; padding: 10px; }}
            .mover-info {{ display: flex; flex-direction: column; align-items: center; gap: 10px; width: 320px; }}
            .mover-info p {{ margin: 5px 0; font-size: 16px; }}
            #topMoversTable td {{ min-width: 340px; }}
            @keyframes countUp {{ from {{ content: "0"; }} to {{ content: attr(data-rank); }} }}
            @media only screen and (max-width: 1200px) {{ 
                table {{ width: 90%; }} 
                .flip-card {{ width: 200px; height: 200px; }} 
                .flip-card-back h1 {{ font-size: 18px; }}
                th, td {{ font-size: 14px; padding: 10px; }}
                .mover-info {{ width: 220px; }}
                .mover-info p {{ font-size: 14px; }}
                #topMoversTable td {{ min-width: 240px; }}
            }}
            @media only screen and (max-width: 768px) {{ 
                table {{ width: 95%; }} 
                .flip-card {{ width: 150px; height: 150px; }} 
                .flip-card-back h1 {{ font-size: 16px; }}
                th, td {{ font-size: 12px; padding: 8px; }}
                .mover-info {{ width: 170px; }}
                .mover-info p {{ font-size: 12px; }}
                #topMoversTable {{ display: block; overflow-x: auto; white-space: nowrap; }}
            }}
        </style>
    </head>
    <body>
        <h1>PS Ranking - {datetime.now().strftime('%Y-%m-%d')}</h1>
        <h2>Top Movers</h2>
        <table id="topMoversTable">
            <tbody>
                {top_movers_rows}
            </tbody>
        </table>
        <h2>Total Number of Groups: {len(sorted_data)}</h2>
        <table id="rankingTable">
            <thead>
                <tr>
                    <th onclick="sortTable(0)">Rank</th>
                    <th onclick="sortTable(1)">Last Rank</th>
                    <th onclick="sortTable(2)">Up Down</th>
                    <th onclick="sortTable(3)">Group Name</th>
                    <th>Photo</th>
                    <th onclick="sortTable(5)">Last Scene</th>
                    <th onclick="sortTable(6)">Total Titles</th>
                    <th onclick="sortTable(7)">#FIVE</th>
                    <th onclick="sortTable(8)">#FOUR</th>
                    <th onclick="sortTable(9)">#Three</th>
                    <th onclick="sortTable(10)">#SceneType</th>
                    <th onclick="sortTable(11)">Score</th>
                </tr>
            </thead>
            <tbody id="tableBody">
                {table_rows}
            </tbody>
        </table>
        <script>
            let sortDirections = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
            function sortTable(columnIndex) {{
                if (columnIndex === 4) return;
                const tbody = document.getElementById('tableBody');
                const rows = Array.from(tbody.getElementsByTagName('tr'));
                const isNumeric = [true, true, true, false, false, true, true, true, true, true, true, true];
                const direction = sortDirections[columnIndex] === 1 ? -1 : 1;
                rows.sort((a, b) => {{
                    let aValue = a.cells[columnIndex].textContent;
                    let bValue = b.cells[columnIndex].textContent;
                    if (columnIndex === 1) {{ 
                        if (aValue === 'N/A' && bValue === 'N/A') return 0;
                        if (aValue === 'N/A') return direction * 1;
                        if (bValue === 'N/A') return direction * -1;
                        aValue = parseFloat(aValue.split(' ')[0]);
                        bValue = parseFloat(bValue.split(' ')[0]);
                        return direction * (aValue - bValue);
                    }} else if (columnIndex === 2) {{ 
                        if (aValue === 'N/A' && bValue === 'N/A') return 0;
                        if (aValue === 'N/A') return direction * 1;
                        if (bValue === 'N/A') return direction * -1;
                        aValue = parseFloat(aValue.split(' ')[0]);
                        bValue = parseFloat(bValue.split(' ')[0]);
                        return direction * (aValue - bValue);
                    }} else if (columnIndex === 5) {{ 
                        if (aValue === 'N/A' && bValue === 'N/A') return 0;
                        if (aValue === 'N/A') return direction * 1;
                        if (bValue === 'N/A') return direction * -1;
                        aValue = parseInt(aValue);
                        bValue = parseInt(bValue);
                        return direction * (aValue - bValue);
                    }}
                    if (isNumeric[columnIndex]) {{ 
                        aValue = parseFloat(aValue) || aValue; 
                        bValue = parseFloat(bValue) || bValue; 
                        return direction * (aValue - bValue); 
                    }}
                    return direction * aValue.localeCompare(bValue);
                }});
                while (tbody.firstChild) {{ 
                    tbody.removeChild(tbody.firstChild); 
                }}
                rows.forEach(row => tbody.appendChild(row));
                sortDirections[columnIndex] = direction;
                sortDirections = sortDirections.map((d, i) => i === columnIndex ? d : 0);
            }}
        </script>
    </body>
    </html>
    """
    index_path = os.path.join(output_folder, 'index.html')
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(ranking_html_content)
    print(f"Wrote HTML file: {index_path}")

def generate_group_html(group_name, group_id, titles, history_data, photo_paths, ratings_hashtag_list, scene_types_hashtag_list, other_hashtag_list, total_titles, last_scene_days, total_messages, telegram_group_id, github_raw_base, html_subfolder):
    group_name = group_name or 'Unknown'  # Ensure group_name is not None
    history_data_json = json.dumps(history_data.get(group_name, []))
    
    # Generate title cards with flip effect, falling back to photo_paths if titles is empty
    title_cards = ''
    if titles:
        print(f"Generating title cards for group {group_name}: {len(titles)} titles found")
        for title in titles:
            title_text = title.get('title', 'No Title')
            media_path = title.get('media_path', f"{github_raw_base}/Photos/placeholder.png")
            accessible = utils.is_url_accessible(media_path)
            print(f"Title: {title_text}, Media: {media_path}, Accessible: {accessible}")
            media_path = media_path if accessible else f"{github_raw_base}/Photos/placeholder.png"
            title_cards += f'''
                <div class="flip-card">
                    <div class="flip-card-inner">
                        <div class="flip-card-front">
                            <img src="{media_path}" alt="{title_text}" style="width:300px;height:300px;object-fit:cover;">
                        </div>
                        <div class="flip-card-back">
                            <h3 style="color: #e6b800; margin: 0; font-size: 20px; word-wrap: break-word; padding: 10px;">{title_text}</h3>
                            <p style="color: #ffffff; font-size: 14px;">Date: {title.get('date', 'N/A')}</p>
                        </div>
                    </div>
                </div>
            '''
    else:
        print(f"No titles found for group {group_name}, falling back to photo_paths: {len(photo_paths)} photos")
        for photo in photo_paths:
            photo_path = photo if utils.is_url_accessible(photo) else f"{github_raw_base}/Photos/placeholder.png"
            print(f"Photo: {photo_path}, Accessible: {utils.is_url_accessible(photo_path)}")
            title_cards += f'''
                <div class="flip-card">
                    <div class="flip-card-inner">
                        <div class="flip-card-front">
                            <img src="{photo_path}" alt="Group Photo" style="width:300px;height:300px;object-fit:cover;">
                        </div>
                        <div class="flip-card-back">
                            <h3 style="color: #e6b800; margin: 0; font-size: 20px; word-wrap: break-word; padding: 10px;">Group Photo</h3>
                        </div>
                    </div>
                </div>
            '''

    # Use the same CSS as rank.py
    group_html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{group_name} - PS Ranking</title>
    <style>
        body {{ font-family: Arial, sans-serif; background-color: #1e2a44; color: #ffffff; margin: 20px; text-align: center; }}
        h1, h2, h3 {{ color: #e6b800; }}
        .container {{ max-width: 1200px; margin: auto; }}
        .photo-gallery {{ display: flex; flex-wrap: wrap; gap: 20px; justify-content: center; }}
        .hashtag-list {{ list-style-type: none; padding: 0; text-align: left; max-width: 600px; margin: 20px auto; }}
        .hashtag-item {{ margin: 5px 0; font-size: 16px; }}
        canvas {{ margin-top: 20px; max-width: 100%; }}
        a {{ text-decoration: none; color: #e6b800; }}
        a:hover {{ color: #b30000; text-decoration: underline; }}
        .flip-card {{ background-color: transparent; width: 300px; height: 300px; perspective: 1000px; margin: 10px; }}
        .flip-card-inner {{ position: relative; width: 100%; height: 100%; text-align: center; transition: transform 0.6s; transform-style: preserve-3d; box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2); }}
        .flip-card:hover .flip-card-inner {{ transform: rotateY(180deg); }}
        .flip-card-front, .flip-card-back {{ position: absolute; width: 100%; height: 100%; backface-visibility: hidden; border-radius: 5px; }}
        .flip-card-front {{ background-color: #2a3a5c; color: #ffffff; }}
        .flip-card-back {{ background-color: #3b4a6b; color: #e6b800; transform: rotateY(180deg); display: flex; justify-content: center; align-items: center; flex-direction: column; }}
        .flip-card-back h3 {{ margin: 0; font-size: 20px; word-wrap: break-word; padding: 10px; }}
        .flip-card-back p {{ margin: 5px 0; font-size: 14px; color: #ffffff; }}
        @media only screen and (max-width: 1200px) {{ 
            .flip-card {{ width: 200px; height: 200px; }} 
            .flip-card-back h3 {{ font-size: 16px; }}
            .flip-card-back p {{ font-size: 12px; }}
        }}
        @media only screen and (max-width: 768px) {{ 
            .flip-card {{ width: 150px; height: 150px; }} 
            .flip-card-back h3 {{ font-size: 14px; }}
            .flip-card-back p {{ font-size: 10px; }}
        }}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="container">
        <h1>{group_name}</h1>
        <p><a href="https://t.me/{telegram_group_id}" target="_blank">Join Telegram Group</a></p>
        <p>Total Titles: {total_titles}</p>
        <p>Last Scene: {last_scene_days}</p>
        <p>Total Messages: {total_messages}</p>
        <h2>{'Titles' if titles else 'Photos'}</h2>
        <div class="photo-gallery">
            {title_cards if title_cards else '<p>No titles or photos available.</p>'}
        </div>
        <h2>Hashtags</h2>
        <ul class="hashtag-list">
            {ratings_hashtag_list}
            {scene_types_hashtag_list}
            {other_hashtag_list}
        </ul>
        <h2>Rank History</h2>
        <canvas id="rankHistoryChart"></canvas>
        <script>
            const historyData = {history_data_json};
            const ctx = document.getElementById('rankHistoryChart').getContext('2d');
            new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: historyData.map(data => data.date),
                    datasets: [{{
                        label: 'Rank',
                        data: historyData.map(data => data.rank),
                        borderColor: '#007bff',
                        fill: false
                    }}]
                }},
                options: {{
                    scales: {{
                        y: {{
                            reverse: true,
                            beginAtZero: false
                        }}
                    }}
                }}
            }});
        </script>
    </div>
</body>
</html>
"""
    html_file = f"{utils.sanitize_filename(group_name)}_{group_id}.html"
    html_path = os.path.join(html_subfolder, html_file)
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(group_html_content)
    print(f"Wrote HTML file: {html_path}")