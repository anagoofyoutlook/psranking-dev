import csv
import json
from datetime import datetime
import random
from html import escape
import math
import os
import utils

def process_chats(chats, history_csv_file, csv_file, photos_folder, github_raw_base):
    csv_columns = [
        'date', 'group name', 'rank', 'last rank', 'up down', 'total messages', 'Datedifference',
        'count of the hashtag "#FIVE"', 'count of the hashtag "#FOUR"', 'count of the hashtag "#Three"',
        'count of the hashtag "#SceneType"', 'score', 'total titles'
    ]
    history_columns = ['date', 'group name', 'rank']
    current_date = datetime.now().strftime('%Y-%m-%d')

    # Load existing history data
    history_data = {}
    if os.path.exists(history_csv_file):
        with open(history_csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                group = row.get('group name', 'Unknown')
                date = row.get('date', '')
                try:
                    rank = int(row.get('rank', '0'))
                    if group not in history_data:
                        history_data[group] = {}
                    if date != current_date:
                        if date not in history_data[group] or rank < history_data[group][date]['rank']:
                            history_data[group][date] = {'date': date, 'rank': rank}
                except (ValueError, TypeError) as e:
                    print(f"Skipping invalid rank for group '{group}' on date '{date}': {row}. Error: {e}")
        for group in history_data:
            history_data[group] = list(history_data[group].values())
            history_data[group].sort(key=lambda x: x['date'])
        print(f"Loaded {sum(len(v) for v in history_data.values())} history entries from {history_csv_file}")
    else:
        print(f"No existing {history_csv_file} found")

    all_data = []
    max_messages = 0
    date_diffs = []

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
            group_subfolder = os.path.join(photos_folder, group_name)
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
                            media_path = 'https://via.placeholder.com/600x300'
                            is_gif = False
                            if media_files:
                                serial_match = utils.find_serial_match_media(serial_number, media_files, group_name, github_raw_base)
                                if serial_match:
                                    media_path = f"{github_raw_base}/Photos/{group_name}/thumbs/{serial_match}"
                                    is_gif = serial_match.lower().endswith('.gif')
                                    print(f"Group {group_name}, Title '{title}' (S.No {serial_number}): Matched media '{serial_match}', selected path {media_path}")
                            else:
                                print(f"Group {group_name}, Title '{title}' (S.No {serial_number}): No media files in {thumbs_subfolder}")
                                if fallback_photos:
                                    random_photo = random.choice(fallback_photos)
                                    media_path = f"{github_raw_base}/Photos/{group_name}/{random_photo}"
                                    is_gif = random_photo.lower().endswith('.gif')
                                    print(f"  Using fallback photo: {media_path}")
                                    if not utils.is_url_accessible(media_path):
                                        print(f"  Fallback photo inaccessible: {media_path}")
                                        media_path = 'https://via.placeholder.com/600x300'
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
            titles.sort(key=lambda x: x['date'], reverse=True)
            titles_count = len(titles)

            # Photos for slideshow
            photo_paths = []
            if os.path.exists(group_subfolder):
                photo_paths = [f"{github_raw_base}/Photos/{group_name}/{f}" for f in os.listdir(group_subfolder) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')) and os.path.isfile(os.path.join(group_subfolder, f))]
                photo_paths = [p for p in photo_paths if utils.is_url_accessible(p)]
                print(f"Group {group_name}: Found {len(photo_paths)} accessible photos in {group_subfolder}: {photo_paths}")
            if not photo_paths:
                photo_paths = ['https://via.placeholder.com/1920x800']
                print(f"Group {group_name}: Using placeholder for slideshow")

            slideshow_content = '<div class="container">\n' + ''.join(f'<div class="mySlides"><div class="numbertext">{i} / {len(photo_paths)}</div><img src="{p}" style="width:100%;height:auto;"></div>' for i, p in enumerate(photo_paths, 1)) + """
                <a class="prev" onclick="plusSlides(-1)">❮</a>
                <a class="next" onclick="plusSlides(1)">❯</a>
                <div class="caption-container"><p id="caption"></p></div>
                <div class="row">
            """ + ''.join(f'<div class="column"><img class="demo cursor" src="{p}" style="width:100%" onclick="currentSlide({i})" alt="{group_name} Photo {i}"></div>' for i, p in enumerate(photo_paths, 1)) + '</div></div>'

            # Single photo for group
            photo_file_name = None
            if os.path.exists(photos_folder):
                group_name_lower = group_name.lower()
                for ext in ('.jpg', '.jpeg', '.png', '.gif', '.webp'):
                    candidate = f"{group_name}{ext}"
                    candidate_lower = f"{group_name_lower}{ext}"
                    if os.path.exists(os.path.join(photos_folder, candidate)):
                        photo_file_name = candidate
                        photo_url = f"{github_raw_base}/Photos/{candidate}"
                        print(f"Group {group_name}: Found exact match photo '{candidate}' at {photo_url}")
                        break
                    elif os.path.exists(os.path.join(photos_folder, candidate_lower)):
                        photo_file_name = candidate_lower
                        photo_url = f"{github_raw_base}/Photos/{candidate_lower}"
                        print(f"Group {group_name}: Found case-insensitive match photo '{candidate_lower}' at {photo_url}")
                        break
                if not photo_file_name:
                    print(f"Group {group_name}: No photo named '{group_name}.{{jpg,jpeg,png,gif,webp}}' or case-insensitive match found in {photos_folder}, using placeholder")
            else:
                print(f"Group {group_name}: No Photos folder {photos_folder}, using placeholder")

            if group_name not in history_data:
                history_data[group_name] = []

            # Find last rank and its date
            last_rank = 'N/A'
            last_rank_date = 'N/A'
            if group_name in history_data and history_data[group_name]:
                sorted_history = sorted(history_data[group_name], key=lambda x: x['date'], reverse=True)
                last_rank = sorted_history[0]['rank']
                last_rank_date = sorted_history[0]['date']

            all_data.append({
                'date': current_date,
                'group name': group_name,
                'total messages': total_messages,
                'Datedifference': date_diff if date_diff is not None else 'N/A',
                'count of the hashtag "#FIVE"': hashtag_counts.get('#FIVE', 0),
                'count of the hashtag "#FOUR"': hashtag_counts.get('#FOUR', 0),
                'count of the hashtag "#Three"': hashtag_counts.get('#THREE', 0),
                'count of the hashtag "#SceneType"': scene_type_count,
                'score': 0,
                'rank': 0,
                'last rank': last_rank,
                'last rank date': last_rank_date,
                'up down': 'N/A',
                'total titles': titles_count,
                'html_file': f"{utils.sanitize_filename(group_name)}_{group_id}.html",
                'photo_file_name': f"{github_raw_base}/Photos/{photo_file_name}" if photo_file_name else 'https://via.placeholder.com/300',
                'slideshow_content': slideshow_content,
                'ratings_hashtag_list': ratings_hashtag_list,
                'scene_types_hashtag_list': scene_types_hashtag_list,
                'other_hashtag_list': other_hashtag_list,
                'titles_count': titles_count,
                'telegram_group_id': telegram_group_id
            })

    return all_data, max_messages, date_diffs

def calculate_scores_and_ranks(all_data, max_messages, date_diffs, history_csv_file, html_subfolder):
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

    sorted_data = sorted(all_data, key=lambda x: x['score'], reverse=True)
    history_data = {}
    for i, entry in enumerate(sorted_data, 1):
        entry['rank'] = i
        if entry['last rank'] != 'N/A':
            entry['up down'] = int(entry['last rank']) - i
        group_name = entry['group name']
        if group_name not in history_data:
            history_data[group_name] = []
        history_data[group_name].append({'date': entry['date'], 'rank': i})

    # Write current run to output.csv
    csv_columns = [
        'date', 'group name', 'rank', 'last rank', 'up down', 'total messages', 'Datedifference',
        'count of the hashtag "#FIVE"', 'count of the hashtag "#FOUR"', 'count of the hashtag "#Three"',
        'count of the hashtag "#SceneType"', 'score', 'total titles'
    ]
    csv_data = [{k: v for k, v in entry.items() if k in csv_columns} for entry in sorted_data]
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=csv_columns)
        writer.writeheader()
        writer.writerows(csv_data)
    print(f"\nWrote CSV file: {csv_file}")

    # Append new history entries to history.csv
    history_columns = ['date', 'group name', 'rank']
    new_history_rows = [{'date': entry['date'], 'group name': entry['group name'], 'rank': entry['rank']} for entry in sorted_data]
    new_history_rows = [row for row in new_history_rows if row.get('group name') and row.get('rank') is not None]
    if new_history_rows:
        write_header = not os.path.exists(history_csv_file)
        with open(history_csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=history_columns)
            if write_header:
                writer.writeheader()
            writer.writerows(new_history_rows)
        print(f"\nAppended {len(new_history_rows)} rows to {history_csv_file}")
    else:
        print(f"No new history entries to append to {history_csv_file}")

    return sorted_data, history_data