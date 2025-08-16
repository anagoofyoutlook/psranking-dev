import os
import math
from html import escape
import utils

def generate_group_html(group_name, group_id, titles, history_data, photo_paths, ratings_hashtag_list, scene_types_hashtag_list, other_hashtag_list, titles_count, date_diff_text, total_messages, telegram_group_id, github_raw_base, html_subfolder):
    titles_grid = f"<p>Total Titles: {titles_count}</p><div class='titles-grid' id='titlesGrid'>"
    for t in titles:
        media_element = (
            f"<img src='{t['media_path']}' alt='Media for {t['title']}' style='width:100%;height:300px;object-fit:cover;border-radius:5px;'>"
            if t['is_gif'] or t['media_path'] == 'https://via.placeholder.com/600x300'
            else f"<video src='{t['media_path']}' style='width:100%;height:300px;object-fit:cover;border-radius:5px;' loop muted playsinline></video>"
        )
        titles_grid += f"""
            <div class='grid-item'>
                {media_element}
                <p class='title'><a href='https://t.me/c/{telegram_group_id}/{t['message_id']}' target='_blank'>{t['title']}</a></p>
                <p class='date'>S.No: {t['serial_number']} | {t['date']}</p>
            </div>
        """
    titles_grid += f"</div>" if titles else f"<p>No titles found (Total: {titles_count})</p>"

    titles_table = f"<table class='titles-table' id='titlesTable'><thead><tr><th onclick='sortTitlesTable(0)'>S.No</th><th onclick='sortTitlesTable(1)'>Items</th><th onclick='sortTitlesTable(2)'>Date</th></tr></thead><tbody id='titlesTableBody'>"
    for t in titles:
        titles_table += f"<tr><td>{t['serial_number']}</td><td><a href='https://t.me/c/{telegram_group_id}/{t['message_id']}' target='_blank'>{t['title']}</a></td><td>{t['date']}</td></tr>"
    titles_table += f"</tbody></table>" if titles else f"<p>No titles found</p>"

    slideshow_content = '<div class="container">\n' + ''.join(f'<div class="mySlides"><div class="numbertext">{i} / {len(photo_paths)}</div><img src="{p}" style="width:100%;height:auto;"></div>' for i, p in enumerate(photo_paths, 1)) + """
        <a class="prev" onclick="plusSlides(-1)">❮</a>
        <a class="next" onclick="plusSlides(1)">❯</a>
        <div class="caption-container"><p id="caption"></p></div>
        <div class="row">
    """ + ''.join(f'<div class="column"><img class="demo cursor" src="{p}" style="width:100%" onclick="currentSlide({i})" alt="{group_name} Photo {i}"></div>' for i, p in enumerate(photo_paths, 1)) + '</div></div>'

    history_data_json = json.dumps(history_data.get(group_name, []))
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{group_name}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.2/dist/chart.umd.min.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #1e2a44; color: #ffffff; text-align: center; }}
        h1, h2 {{ color: #e6b800; width: 90%; margin: 20px auto; text-align: center; font-size: 36px; }}
        .info {{ background-color: #2a3a5c; padding: 10px; border-radius: 5px; margin-bottom: 20px; width: 90%; margin-left: auto; margin-right: auto; }}
        .hashtags {{ list-style-type: none; padding: 0; }}
        .hashtag-item {{ background-color: #3b4a6b; margin: 5px 0; padding: 5px; border-radius: 3px; display: inline-block; width: 200px; color: #ffffff; }}
        .rank-container {{ 
            width: 90%; 
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
            gap: 20px; 
            margin: 20px 0; 
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
            height: 300px; 
            border-radius: 5px; 
            object-fit: cover; 
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
            width: 100%; 
            margin: 20px 0; 
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
            width: 90%; 
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
            aspect-ratio: 16/9; 
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
        .prev:hover, .next:hover {{ background-color: #b30000; }}
        .numbertext {{ 
            color: #e6b800; 
            font-size: 12px; 
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
            width: 90%; 
            background-color: #2a3a5c; 
            border-radius: 5px 5px 0 0; 
        }}
        .tab button {{ 
            background-color: #2a3a5c; 
            color: #e6b800; 
            float: left; 
            border: none; 
            outline: none; 
            cursor: pointer; 
            padding: 14px 16px; 
            transition: 0.3s; 
            font-size: 17px; 
            width: 50%; 
        }}
        .tab button:hover {{ background-color: #b30000; }}
        .tab button.active {{ background-color: #e6b800; color: #1e2a44; }}
        .tabcontent {{ 
            display: none; 
            padding: 6px 12px; 
            border-top: none; 
            background-color: #2a3a5c; 
            margin: 0 auto; 
            width: 90%; 
            border-radius: 0 0 5px 5px; 
        }}
        #Videos {{ display: block; }}
        @media only screen and (max-width: 1200px) {{ 
            .titles-grid {{ grid-template-columns: repeat(3, 1fr); }} 
            .grid-item video, .grid-item img {{ height: 200px; }}
            h1, .info, .container, .tab, .tabcontent {{ width: 90%; }}
            .rank-container {{ width: 90%; }}
        }}
        @media only screen and (max-width: 768px) {{ 
            .titles-grid {{ grid-template-columns: repeat(3, 1fr); }} 
            .grid-item video, .grid-item img {{ height: 150px; }}
            .container {{ width: 90%; max-height: 400px; }} 
            h1 {{ margin: 10px auto; font-size: 30px; }}
            .info, .tab, .tabcontent, .rank-container {{ width: 90%; }}
            .rank-container {{ flex-direction: column; gap: 10px; }} 
            .chart-container {{ max-width: 100%; }} 
            .column {{ flex: 0 0 80px; max-width: 80px; }} 
            .mySlides img {{ object-fit: contain; }} 
            .tab button {{ font-size: 14px; padding: 10px; }}
        }}
    </style>
</head>
<body>
    <h1>{group_name}</h1>
    <div class="rank-container">
        <div class="chart-container"><h2>Rank History</h2><canvas id="rankChart"></canvas></div>
        <p>Rank: <span class="rank-number" data-rank="RANK_PLACEHOLDER"></span></p>
    </div>
    {slideshow_content}
    <div class="info"><p>Scenes: {total_messages}</p><p>Last Scene: {date_diff_text}</p></div>
    <div class="info">
        <h2>Rating Hashtag Counts (#FIVE, #FOUR, #Three)</h2><ul class="hashtags">{ratings_hashtag_list}</ul>
        <h2>Scene Type Hashtag Counts</h2><ul class="hashtags">{scene_types_hashtag_list}</ul>
        <h2>Other Hashtag Counts</h2><ul class="hashtags">{other_hashtag_list}</ul>
    </div>
    <div class="info">
        <h2>Titles</h2>
        <div class="tab">
            <button class="tablinks active" onclick="openTab(event, 'Videos')">Videos</button>
            <button class="tablinks" onclick="openTab(event, 'Table')">Table</button>
        </div>
        <div id="Videos" class="tabcontent">
            {titles_grid}
        </div>
        <div id="Table" class="tabcontent">
            {titles_table}
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
            let dots = document.getElementsByClassName("demo");
            let captionText = document.getElementById("caption");
            if (n > slides.length) {{ slideIndex = 1 }}
            if (n < 1) {{ slideIndex = slides.length }}
            for (i = 0; i < slides.length; i++) {{ 
                slides[i].style.display = "none"; 
            }}
            for (i = 0; i < dots.length; i++) {{ 
                dots[i].className = dots[i].className.replace(" active", ""); 
            }}
            slides[slideIndex-1].style.display = "block";
            dots[slideIndex-1].className += " active";
            captionText.innerHTML = dots[slideIndex-1].alt;
        }}
        let autoSlide = setInterval(() => plusSlides(1), 3000);

        function openTab(evt, tabName) {{
            let i, tabcontent, tablinks;
            tabcontent = document.getElementsByClassName("tabcontent");
            for (i = 0; i < tabcontent.length; i++) {{
                tabcontent[i].style.display = "none";
            }}
            tablinks = document.getElementsByClassName("tablinks");
            for (i = 0; i < tablinks.length; i++) {{
                tablinks[i].className = tablinks[i].className.replace(" active", "");
            }}
            document.getElementById(tabName).style.display = "block";
            evt.currentTarget.className += " active";
        }}

        document.addEventListener('DOMContentLoaded', function() {{
            const ctx = document.getElementById('rankChart').getContext('2d');
            const historyData = {history_data_json};
            const dates = historyData.map(entry => entry.date);
            const ranks = historyData.map(entry => entry.rank);
            new Chart(ctx, {{
                type: 'line',
                data: {{ 
                    labels: dates, 
                    datasets: [{{
                        label: 'Rank Over Time', 
                        data: ranks, 
                        borderColor: '#e6b800', 
                        backgroundColor: 'rgba(230, 184, 0, 0.2)', 
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
                            suggestedMax: {len(titles)},
                            grid: {{ color: '#3b4a6b' }}
                        }}, 
                        x: {{ 
                            title: {{ display: true, text: 'Date', color: '#e6b800' }}, 
                            ticks: {{ color: '#ffffff' }}, 
                            grid: {{ color: '#3b4a6b' }}
                        }} 
                    }}, 
                    plugins: {{ 
                        legend: {{ display: true, labels: {{ color: '#e6b800' }} }} 
                    }} 
                }}
            }});

            const videos = document.querySelectorAll('.grid-item video');
            videos.forEach(video => {{
                video.addEventListener('mouseover', () => {{
                    video.play().catch(error => {{
                        console.error('Error playing video:', error);
                    }});
                }});
                video.addEventListener('mouseout', () => {{
                    video.pause();
                }});
            }});

            sortTitlesTable(0, -1);
        }});

        let titlesSortDirections = [-1, 0, 0];
        function sortTitlesTable(columnIndex, forceDirection) {{
            const tbody = document.getElementById('titlesTableBody');
            const rows = Array.from(tbody.getElementsByTagName('tr'));
            const direction = forceDirection !== undefined ? forceDirection : (titlesSortDirections[columnIndex] === 1 ? -1 : 1);
            rows.sort((a, b) => {{
                let aValue = a.cells[columnIndex].innerText;
                let bValue = b.cells[columnIndex].innerText;
                if (columnIndex === 0) {{ 
                    aValue = parseInt(aValue);
                    bValue = parseInt(bValue);
                    return direction * (aValue - bValue);
                }} else if (columnIndex === 2) {{ 
                    aValue = new Date(aValue);
                    bValue = new Date(bValue);
                    return direction * (aValue - bValue);
                }} else if (columnIndex === 1) {{ 
                    return direction * aValue.localeCompare(bValue);
                }}
                return 0;
            }});
            while (tbody.firstChild) {{ 
                tbody.removeChild(tbody.firstChild); 
            }}
            rows.forEach(row => tbody.appendChild(row));
            titlesSortDirections[columnIndex] = direction;
            titlesSortDirections = titlesSortDirections.map((d, i) => i === columnIndex ? d : 0);
            sortTitlesGrid(columnIndex, direction);
        }}

        function sortTitlesGrid(columnIndex, direction) {{
            const grid = document.getElementById('titlesGrid');
            const items = Array.from(grid.getElementsByClassName('grid-item'));
            items.sort((a, b) => {{
                let aValue, bValue;
                if (columnIndex === 0) {{ 
                    aValue = parseInt(a.querySelector('.date').innerText.split('S.No: ')[1].split(' | ')[0]);
                    bValue = parseInt(b.querySelector('.date').innerText.split('S.No: ')[1].split(' | ')[0]);
                    return direction * (aValue - bValue);
                }} else if (columnIndex === 1) {{ 
                    aValue = a.querySelector('.title').innerText;
                    bValue = b.querySelector('.title').innerText;
                    return direction * aValue.localeCompare(bValue);
                }} else if (columnIndex === 2) {{ 
                    aValue = new Date(a.querySelector('.date').innerText.split(' | ')[1]);
                    bValue = new Date(b.querySelector('.date').innerText.split(' | ')[1]);
                    return direction * (aValue - bValue);
                }}
                return 0;
            }});
            while (grid.firstChild) {{ 
                grid.removeChild(grid.firstChild); 
            }}
            items.forEach(item => grid.appendChild(item));
        }}
    </script>
</body>
</html>
"""
    html_path = os.path.join(html_subfolder, f"{utils.sanitize_filename(group_name)}_{group_id}.html")
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"Wrote HTML file: {html_path}")
    return html_content

def generate_index_html(sorted_data, csv_file, history_csv_file, github_raw_base, output_folder):
    current_date = datetime.now().strftime('%Y-%m-%d')
    items_per_page = 50
    total_pages = math.ceil(len(sorted_data) / items_per_page)
    table_rows = ''
    grid_items = ''
    for i, entry in enumerate(sorted_data):
        group_name = escape(entry['group name'])
        photo_src = entry['photo_file_name']
        html_link = f"HTML/{entry['html_file']}"
        last_scene = f"{entry['Datedifference']} days" if entry['Datedifference'] != 'N/A' else 'N/A'
        last_rank = entry['last rank']
        last_rank_date = entry['last rank date']
        last_rank_display = f"{last_rank} ({last_rank_date})" if last_rank != 'N/A' else 'N/A'
        up_down = entry['up down']
        up_down_img = 'https://via.placeholder.com/20'
        if up_down != 'N/A':
            if up_down > 0:
                up_url = f"{github_raw_base}/Photos/up.png"
                up_down_img = up_url if utils.is_url_accessible(up_url) else up_down_img
            elif up_down < 0:
                down_url = f"{github_raw_base}/Photos/down.png"
                up_down_img = down_url if utils.is_url_accessible(down_url) else up_down_img
            else:
                zero_url = f"{github_raw_base}/Photos/0.png"
                up_down_img = zero_url if utils.is_url_accessible(zero_url) else up_down_img
        page_number = (i // items_per_page) + 1
        print(f"Ranking Table/Grid: Group {group_name}, Photo: {photo_src}, Up Down image: {up_down_img}, Page: {page_number}")
        table_rows += f"""
        <tr data-page="{page_number}">
            <td>{entry['rank']}</td>
            <td>{last_rank_display}</td>
            <td>{up_down} <img src="{up_down_img}" alt="Up Down" class="up-down-img"></td>
            <td><a href="{html_link}" target="_blank">{group_name}</a></td>
            <td><div class="flip-card"><div class="flip-card-inner"><div class="flip-card-front"><img src="{photo_src}" alt="{group_name}" style="width:300px;height:300px;object-fit:cover;"></div><div class="flip-card-back"><a href="{html_link}" target="_blank" style="color: #e6b800; text-decoration: none;"><h1>{group_name}</h1></a></div></div></div></td>
            <td>{last_scene}</td>
            <td>{entry['total titles']}</td>
            <td>{entry['count of the hashtag "#FIVE"']}</td>
            <td>{entry['count of the hashtag "#FOUR"']}</td>
            <td>{entry['count of the hashtag "#Three"']}</td>
            <td>{entry['count of the hashtag "#SceneType"']}</td>
            <td>{entry['score']:.2f}</td>
        </tr>
        """
        grid_items += f"""
        <div class="grid-item" data-page="{page_number}">
            <div class="flip-card"><div class="flip-card-inner"><div class="flip-card-front"><img src="{photo_src}" alt="{group_name}" style="width:100%;height:300px;object-fit:cover;"></div><div class="flip-card-back"><a href="{html_link}" target="_blank" style="color: #e6b800; text-decoration: none;"><h1>{group_name}</h1></a></div></div></div>
            <p><strong>Rank:</strong> <span class="data-field" data-column="0">{entry['rank']}</span></p>
            <p><strong>Last Rank:</strong> <span class="data-field" data-column="1">{last_rank_display}</span></p>
            <p><strong>Up Down:</strong> <span class="data-field" data-column="2">{up_down} <img src="{up_down_img}" alt="Up Down" class="up-down-img"></span></p>
            <p><strong>Group Name:</strong> <span class="data-field" data-column="3"><a href="{html_link}" target="_blank">{group_name}</a></span></p>
            <p><strong>Last Scene:</strong> <span class="data-field" data-column="5">{last_scene}</span></p>
            <p><strong>Total Titles:</strong> <span class="data-field" data-column="6">{entry['total titles']}</span></p>
            <p><strong>#FIVE:</strong> <span class="data-field" data-column="7">{entry['count of the hashtag "#FIVE"']}</span></p>
            <p><strong>#FOUR:</strong> <span class="data-field" data-column="8">{entry['count of the hashtag "#FOUR"']}</span></p>
            <p><strong>#Three:</strong> <span class="data-field" data-column="9">{entry['count of the hashtag "#Three"']}</span></p>
            <p><strong>Thumbnails:</strong> <span class="data-field" data-column="10">{entry['count of the hashtag "#SceneType"']}</span></p>
            <p><strong>Score:</strong> <span class="data-field" data-column="11">{entry['score']:.2f}</span></p>
        </div>
        """

    # Generate top movers
    up_groups = [entry for entry in sorted_data if entry['up down'] != 'N/A' and entry['up down'] > 0]
    down_groups = [entry for entry in sorted_data if entry['up down'] != 'N/A' and entry['up down'] < 0]
    unchanged_groups = [entry for entry in sorted_data if entry['up down'] == 0]
    up_groups = sorted(up_groups, key=lambda x: (x['up down'], -x['rank']), reverse=True)[:5]
    down_groups = sorted(down_groups, key=lambda x: (x['up down'], -x['rank']), reverse=True)[:5]
    unchanged_groups = sorted(unchanged_groups, key=lambda x: x['rank'])[:5]

    top_movers_rows = ''
    if up_groups or down_groups or unchanged_groups:
        for group_list, title in [(up_groups, 'Top 5 Up'), (down_groups, 'Top 5 Down'), (unchanged_groups, 'Top 5 Unchanged')]:
            if group_list:
                top_movers_rows += f'<tr><th style="background-color: #b30000;">{title}</th></tr><tr>'
                for entry in group_list:
                    group_name = escape(entry['group name'])
                    photo_src = entry['photo_file_name']
                    html_link = f"HTML/{entry['html_file']}"
                    last_rank = entry['last rank']
                    last_rank_date = entry['last rank date']
                    last_rank_display = f"{last_rank} ({last_rank_date})" if last_rank != 'N/A' else 'N/A'
                    up_down = entry['up down']
                    up_down_img = 'https://via.placeholder.com/20'
                    if up_down > 0:
                        up_url = f"{github_raw_base}/Photos/up.png"
                        up_down_img = up_url if utils.is_url_accessible(up_url) else up_down_img
                    elif up_down < 0:
                        down_url = f"{github_raw_base}/Photos/down.png"
                        up_down_img = down_url if utils.is_url_accessible(down_url) else up_down_img
                    else:
                        zero_url = f"{github_raw_base}/Photos/0.png"
                        up_down_img = zero_url if utils.is_url_accessible(zero_url) else up_down_img
                    print(f"Top Movers: Group {group_name}, Up Down image: {up_down_img}")
                    top_movers_rows += f"""
                        <td>
                            <div class="mover-info">
                                <p><strong>Name:</strong> <a href="{html_link}" target="_blank">{group_name}</a></p>
                                <div class="flip-card"><div class="flip-card-inner"><div class="flip-card-front"><img src="{photo_src}" alt="{group_name}" style="width:300px;height:300px;object-fit:cover;"></div><div class="flip-card-back"><a href="{html_link}" target="_blank" style="color: #e6b800; text-decoration: none;"><h1>{group_name}</h1></a></div></div></div>
                                <p><strong>Rank:</strong> {entry['rank']}</p>
                                <p><strong>Last Rank:</strong> {last_rank_display}</p>
                                <p><strong>Up Down:</strong> {up_down} <img src="{up_down_img}" alt="Up Down" class="up-down-img"></p>
                            </div>
                        </td>
                    """
                top_movers_rows += '</tr>'
    else:
        top_movers_rows = '<tr><td>No significant rank changes</td></tr>'

    total_groups = len(sorted_data)
    ranking_html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PS Ranking - {current_date}</title>
    <style>
        body {{ font-family: Arial, sans-serif; background-color: #1e2a44; color: #ffffff; margin: 20px; text-align: center; }}
        h1, h2 {{ color: #e6b800; }}
        table {{ width: 80%; margin: 20px auto; border-collapse: collapse; background-color: #2a3a5c; box-shadow: 0 0 10px rgba(0, 0, 0, 0.3); }}
        th, td {{ border: 1px solid #3b4a6b; text-align: center; vertical-align: middle; padding: 15px; color: #ffffff; }}
        th {{ background-color: #e6b800; color: #1e2a44; cursor: pointer; }}
        th:hover {{ background-color: #b30000; }}
        tr:hover {{ background-color: #3b4a6b; }}
        #rankingTable thead tr {{ display: table-row !important; }}
        #rankingTable tbody tr {{ display: none; }}
        #rankingTable tbody tr[data-page="1"] {{ display: table-row; }}
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
        .pagination {{ margin: 20px auto; text-align: center; }}
        .pagination button {{ 
            background-color: #2a3a5c; 
            color: #e6b800; 
            border: 1px solid #3b4a6b; 
            padding: 10px 15px; 
            margin: 0 5px; 
            cursor: pointer; 
            border-radius: 5px; 
            font-size: 16px; 
        }}
        .pagination button:hover {{ background-color: #b30000; }}
        .pagination button.active {{ background-color: #e6b800; color: #1e2a44; }}
        .pagination button:disabled {{ opacity: 0.5; cursor: not-allowed; }}
        #backToTop {{
            display: none;
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 1000;
            background-color: #e6b800;
            color: #1e2a44;
            border: none;
            padding: 10px 15px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }}
        #backToTop:hover {{
            background-color: #b30000;
        }}
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
            float: left; 
            border: none; 
            outline: none; 
            cursor: pointer; 
            padding: 14px 16px; 
            transition: 0.3s; 
            font-size: 17px; 
            width: 33.33%; 
        }}
        .tab button:hover {{ background-color: #b30000; }}
        .tab button.active {{ background-color: #e6b800; color: #1e2a44; }}
        .tabcontent {{ 
            display: none; 
            padding: 6px 12px; 
            border-top: none; 
            background-color: #2a3a5c; 
            margin: 0 auto; 
            width: 80%; 
            border-radius: 0 0 5px 5px; 
        }}
        #RankingTableTab {{ display: block; }}
        .ranking-grid {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); 
            gap: 20px; 
            margin: 20px 0; 
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
        .grid-item p {{ margin: 5px 0; font-size: 14px; }}
        .grid-item .flip-card {{ width: 100%; height: 300px; }}
        .grid-header {{ 
            display: flex; 
            flex-wrap: wrap; 
            gap: 10px; 
            justify-content: center; 
            margin-bottom: 20px; 
        }}
        .grid-header span {{ 
            background-color: #e6b800; 
            color: #1e2a44; 
            padding: 10px 15px; 
            border-radius: 5px; 
            cursor: pointer; 
            font-size: 14px; 
            text-align: center; 
            min-width: 80px; 
        }}
        .grid-header span:hover {{ background-color: #b30000; }}
        .grid-item img {{ width: 100%; height: 300px; object-fit: cover; border-radius: 5px; }}
        @keyframes countUp {{ from {{ content: "0"; }} to {{ content: attr(data-rank); }} }}
        @media only screen and (max-width: 1200px) {{ 
            table {{ width: 90%; }} 
            .flip-card {{ width: 200px; height: 200px; }} 
            .flip-card-back h1 {{ font-size: 18px; }}
            th, td {{ font-size: 14px; padding: 10px; }}
            .mover-info {{ width: 220px; }}
            .mover-info p {{ font-size: 14px; }}
            #topMoversTable td {{ min-width: 240px; }}
            .tab, .tabcontent {{ width: 90%; }}
            .pagination button {{ padding: 8px 12px; font-size: 14px; }}
            #backToTop {{ padding: 8px 12px; font-size: 14px; }}
            .ranking-grid {{ grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); }}
            .grid-item .flip-card {{ height: 200px; }}
            .grid-item img {{ height: 200px; }}
            .grid-header span {{ font-size: 12px; padding: 8px 10px; min-width: 60px; }}
        }}
        @media only screen and (max-width: 768px) {{ 
            table {{ width: 95%; }} 
            .flip-card {{ width: 150px; height: 150px; }} 
            .flip-card-back h1 {{ font-size: 16px; }}
            th, td {{ font-size: 12px; padding: 8px; }}
            .mover-info {{ width: 170px; }}
            .mover-info p {{ font-size: 12px; }}
            #topMoversTable td {{ min-width: 190px; }}
            #topMoversTable {{ display: block; overflow-x: auto; white-space: nowrap; }}
            #rankingTable {{ display: block; overflow-x: auto; white-space: nowrap; }}
            .tab, .tabcontent {{ width: 95%; }}
            .tab button {{ font-size: 14px; padding: 10px; width: 33.33%; }}
            .pagination button {{ padding: 6px 10px; font-size: 12px; }}
            #backToTop {{ padding: 6px 10px; font-size: 12px; }}
            .ranking-grid {{ grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); }}
            .grid-item .flip-card {{ height: 150px; }}
            .grid-item img {{ height: 150px; }}
            .grid-header span {{ font-size: 10px; padding: 6px 8px; min-width: 50px; }}
        }}
    </style>
</head>
<body>
    <h1>PS Ranking - {current_date}</h1>
    <div class="tab">
        <button class="tablinks" onclick="openTab(event, 'TopMoversTab')">Top Movers</button>
        <button class="tablinks active" onclick="openTab(event, 'RankingTableTab')">Ranking Table</button>
        <button class="tablinks" onclick="openTab(event, 'GridViewTab')">Grid View</button>
    </div>
    <div id="TopMoversTab" class="tabcontent">
        <h2>Top Movers</h2>
        <table id="topMoversTable">
            <tbody>
                {top_movers_rows}
            </tbody>
        </table>
    </div>
    <div id="RankingTableTab" class="tabcontent">
        <h2>Total Number of Groups: {total_groups}</h2>
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
                    <th onclick="sortTable(10)">Thumbnails</th>
                    <th onclick="sortTable(11)">Score</th>
                </tr>
            </thead>
            <tbody id="tableBody">
                {table_rows}
            </tbody>
        </table>
        <div class="pagination" id="pagination">
            <button onclick="changePage(-1, 'rankingTable')" id="prevPage" disabled>Previous</button>
            <span id="pageButtons"></span>
            <button onclick="changePage(1, 'rankingTable')" id="nextPage">Next</button>
        </div>
    </div>
    <div id="GridViewTab" class="tabcontent">
        <h2>Total Number of Groups: {total_groups}</h2>
        <div class="grid-header">
            <span onclick="sortGrid(0)">Rank</span>
            <span onclick="sortGrid(1)">Last Rank</span>
            <span onclick="sortGrid(2)">Up Down</span>
            <span onclick="sortGrid(3)">Group Name</span>
            <span style="cursor: default;">Photo</span>
            <span onclick="sortGrid(5)">Last Scene</span>
            <span onclick="sortGrid(6)">Total Titles</span>
            <span onclick="sortGrid(7)">#FIVE</span>
            <span onclick="sortGrid(8)">#FOUR</span>
            <span onclick="sortGrid(9)">#Three</span>
            <span onclick="sortGrid(10)">Thumbnails</span>
            <span onclick="sortGrid(11)">Score</span>
        </div>
        <div class="ranking-grid" id="rankingGrid">
            {grid_items}
        </div>
        <div class="pagination" id="gridPagination">
            <button onclick="changePage(-1, 'rankingGrid')" id="gridPrevPage" disabled>Previous</button>
            <span id="gridPageButtons"></span>
            <button onclick="changePage(1, 'rankingGrid')" id="gridNextPage">Next</button>
        </div>
    </div>
    <button id="backToTop" title="Back to Top">↑ Top</button>
    <script>
        let sortDirections = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
        let currentTablePage = 1;
        let currentGridPage = 1;
        const itemsPerPage = 50;
        const totalPages = {total_pages};

        function openTab(evt, tabName) {{
            let i, tabcontent, tablinks;
            tabcontent = document.getElementsByClassName("tabcontent");
            for (i = 0; i < tabcontent.length; i++) {{
                tabcontent[i].style.display = "none";
            }}
            tablinks = document.getElementsByClassName("tablinks");
            for (i = 0; i < tablinks.length; i++) {{
                tablinks[i].className = tablinks[i].className.replace(" active", "");
            }}
            document.getElementById(tabName).style.display = "block";
            evt.currentTarget.className += " active";
            if (tabName === 'RankingTableTab') {{
                updatePagination('rankingTable', currentTablePage);
            }} else if (tabName === 'GridViewTab') {{
                updatePagination('rankingGrid', currentGridPage);
            }}
        }}

        function updatePagination(containerId, page) {{
            const isTable = containerId === 'rankingTable';
            const currentPage = isTable ? (currentTablePage = page) : (currentGridPage = page);
            const items = isTable 
                ? document.querySelectorAll('#tableBody tr')
                : document.querySelectorAll('#rankingGrid .grid-item');
            items.forEach(item => {{
                item.style.display = 'none';
                if (parseInt(item.getAttribute('data-page')) === currentPage) {{
                    item.style.display = isTable ? 'table-row' : 'flex';
                }}
            }});
            const prevButton = document.getElementById(isTable ? 'prevPage' : 'gridPrevPage');
            const nextButton = document.getElementById(isTable ? 'nextPage' : 'gridNextPage');
            const pageButtons = document.getElementById(isTable ? 'pageButtons' : 'gridPageButtons');
            prevButton.disabled = currentPage === 1;
            nextButton.disabled = currentPage === totalPages;
            pageButtons.innerHTML = '';
            for (let i = 1; i <= totalPages; i++) {{
                const button = document.createElement('button');
                button.textContent = i;
                button.className = i === currentPage ? 'active' : '';
                button.onclick = () => {{
                    if (isTable) {{
                        currentTablePage = i;
                        updatePagination('rankingTable', i);
                    }} else {{
                        currentGridPage = i;
                        updatePagination('rankingGrid', i);
                    }}
                }};
                pageButtons.appendChild(button);
            }}
        }}

        function changePage(delta, containerId) {{
            const isTable = containerId === 'rankingTable';
            let currentPage = isTable ? currentTablePage : currentGridPage;
            currentPage += delta;
            if (currentPage < 1) currentPage = 1;
            if (currentPage > totalPages) currentPage = totalPages;
            if (isTable) {{
                currentTablePage = currentPage;
            }} else {{
                currentGridPage = currentPage;
            }}
            updatePagination(containerId, currentPage);
        }}

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
            sortGrid(columnIndex);
        }}

        function sortGrid(columnIndex) {{
            const grid = document.getElementById('rankingGrid');
            const items = Array.from(grid.getElementsByClassName('grid-item'));
            const isNumeric = [true, true, true, false, false, true, true, true, true, true, true, true];
            const direction = sortDirections[columnIndex] === 1 ? -1 : 1;
            items.sort((a, b) => {{
                let aValue = a.querySelector(`.data-field[data-column="${{columnIndex}}"]`).textContent;
                let bValue = b.querySelector(`.data-field[data-column="${{columnIndex}}"]`).textContent;
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
            while (grid.firstChild) {{ 
                grid.removeChild(grid.firstChild); 
            }}
            items.forEach(item => grid.appendChild(item));
            sortDirections[columnIndex] = direction;
            sortDirections = sortDirections.map((d, i) => i === columnIndex ? d : 0);
            sortTable(columnIndex);
        }}

        document.addEventListener('DOMContentLoaded', () => {{
            updatePagination('rankingTable', currentTablePage);
            const backToTop = document.getElementById('backToTop');
            window.onscroll = () => {{
                backToTop.style.display = window.scrollY > 200 ? 'block' : 'none';
            }};
            backToTop.onclick = () => {{
                window.scrollTo({{ top: 0, behavior: 'smooth' }});
            }};
        }});
    </script>
</body>
</html>
"""
    html_path = os.path.join(output_folder, 'index.html')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(ranking_html_content)
    print(f"Wrote HTML file: {html_path}")
    return ranking_html_content