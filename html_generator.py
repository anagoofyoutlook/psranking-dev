import json
import os
import csv
from datetime import datetime
import utils

def generate_index_html(sorted_data, output_csv_file, history_csv_file, github_raw_base, output_folder):
    ranking_html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PS Ranking - {datetime.now().strftime('%Y-%m-%d')}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f0f0f0; }}
            .container {{ max-width: 1200px; margin: auto; }}
            .tabs {{ overflow: hidden; border-bottom: 1px solid #ccc; margin-bottom: 20px; }}
            .tablink {{ background-color: #555; color: white; float: left; border: none; outline: none; cursor: pointer; padding: 14px 16px; font-size: 17px; }}
            .tablink:hover {{ background-color: #777; }}
            .tabcontent {{ display: none; padding: 6px 12px; border: 1px solid #ccc; border-top: none; }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            .grid-container {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 20px; }}
            .grid-item {{ background-color: white; border: 1px solid #ddd; padding: 10px; text-align: center; }}
            .grid-item img {{ max-width: 100%; height: auto; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>PS Ranking - {datetime.now().strftime('%Y-%m-%d')}</h1>
            <div class="tabs">
                <button class="tablink" onclick="openTab(event, 'RankingTableTab')">Ranking Table</button>
                <button class="tablink" onclick="openTab(event, 'GridViewTab')">Grid View</button>
            </div>
            <div id="RankingTableTab" class="tabcontent">
                <table>
                    <tr>
                        <th>Group Name</th>
                        <th>Rank</th>
                        <th>Last Rank</th>
                        <th>Last Rank Date</th>
                        <th>Rank Change</th>
                        <th>Last Scene (Days)</th>
                        <th>Total Titles</th>
                        <th>#FIVE</th>
                        <th>#FOUR</th>
                        <th>#Three</th>
                        <th>#SceneType</th>
                        <th>Score</th>
                    </tr>
    """
    for group in sorted_data:
        group_name = group.get('group_name', 'Unknown')
        rank_change = (
            f'<img src="{github_raw_base}/Photos/up.png" alt="Up" width="20">' if isinstance(group.get('up_down'), (int, float)) and group.get('up_down') > 0
            else f'<img src="{github_raw_base}/Photos/down.png" alt="Down" width="20">' if isinstance(group.get('up_down'), (int, float)) and group.get('up_down') < 0
            else f'<img src="{github_raw_base}/Photos/0.png" alt="No Change" width="20">'
        )
        ranking_html_content += f"""
                    <tr>
                        <td><a href="HTML/{group.get('html_file', '')}">{group_name}</a></td>
                        <td>{group.get('rank', 'N/A')}</td>
                        <td>{group.get('last_rank', 'N/A')}</td>
                        <td>{group.get('last_rank_date', 'N/A')}</td>
                        <td>{rank_change}</td>
                        <td>{group.get('Datedifference', 'N/A')}</td>
                        <td>{group.get('total titles', 'N/A')}</td>
                        <td>{group.get('count of the hashtag "#FIVE"', 0)}</td>
                        <td>{group.get('count of the hashtag "#FOUR"', 0)}</td>
                        <td>{group.get('count of the hashtag "#Three"', 0)}</td>
                        <td>{group.get('count of the hashtag "#SceneType"', 0)}</td>
                        <td>{group.get('score', 0):.2f}</td>
                    </tr>
        """
    ranking_html_content += """
                </table>
            </div>
            <div id="GridViewTab" class="tabcontent">
                <div class="grid-container">
    """
    for group in sorted_data:
        group_name = group.get('group_name', 'Unknown')
        photo_url = group.get('photo_file_name', '') if utils.is_url_accessible(group.get('photo_file_name', '')) else f"{github_raw_base}/Photos/placeholder.png"
        ranking_html_content += f"""
                    <div class="grid-item">
                        <a href="HTML/{group.get('html_file', '')}"><img src="{photo_url}" alt="{group_name}"></a>
                        <p>{group_name}<br>Rank: {group.get('rank', 'N/A')}<br>Score: {group.get('score', 0):.2f}</p>
                    </div>
        """
    ranking_html_content += """
                </div>
            </div>
            <script>
                function openTab(evt, tabName) {
                    var i, tabcontent, tablinks;
                    tabcontent = document.getElementsByClassName("tabcontent");
                    for (i = 0; i < tabcontent.length; i++) {
                        tabcontent[i].style.display = "none";
                    }
                    tablinks = document.getElementsByClassName("tablink");
                    for (i = 0; i < tablinks.length; i++) {
                        tablinks[i].className = tablinks[i].className.replace(" active", "");
                    }
                    document.getElementById(tabName).style.display = "block";
                    evt.currentTarget.className += " active";
                }
                document.getElementsByClassName("tablink")[0].click();
            </script>
        </div>
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
    # Use a single triple-quoted string with consistent indentation
    group_html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{group_name} - PS Ranking</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f0f0f0; }}
        .container {{ max-width: 1200px; margin: auto; }}
        .photo-gallery {{ display: flex; flex-wrap: wrap; gap: 10px; }}
        .photo-gallery img {{ max-width: 200px; height: auto; }}
        .hashtag-list {{ list-style-type: none; padding: 0; }}
        .hashtag-item {{ margin: 5px 0; }}
        canvas {{ margin-top: 20px; }}
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
        <h2>Photos</h2>
        <div class="photo-gallery">
            {"".join(f'<img src="{photo if utils.is_url_accessible(photo) else f"{github_raw_base}/Photos/placeholder.png"}" alt="Group Photo">' for photo in photo_paths)}
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