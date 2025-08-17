import json
import os
import math
import csv
import zipfile
import html_generator
from datetime import datetime, timedelta
import random
import re
import utils

def extract_hashtags(text):
    return re.findall(r'#\w+', text)

def get_date_difference(date_str, current_date):
    try:
        message_date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S')
        return (current_date - message_date).days
    except ValueError:
        return None

def load_data(zip_path):
    all_data = []
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall('PS')
        json_path = os.path.join('PS', 'result.json')
        if not os.path.exists(json_path):
            print(f"Error: {json_path} not found after extraction")
            return all_data
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        chats = data.get('chats', {}).get('list', [])
        if not chats:
            print("Error: No chats found in result.json")
            return all_data
        for chat in chats:
            if chat.get('type') == 'private_supergroup':
                group_data = {
                    'id': chat.get('id', 0),  # Ensure id is set
                    'name': chat.get('name', 'Unknown'),  # Ensure name is set
                    'messages': []
                }
                print(f"Loaded group: {group_data['name']} (ID: {group_data['id']})")
                for msg in chat.get('messages', []):
                    if msg.get('type') == 'message':
                        text = msg.get('text', '')
                        if isinstance(text, list):
                            text = ''.join(str(t.get('text', '')) for t in text)
                        group_data['messages'].append({
                            'id': msg.get('id'),
                            'date': msg.get('date'),
                            'text': text,
                            'media': msg.get('file'),
                            'thumbnail': msg.get('thumbnail'),
                            'is_gif': msg.get('media_type') == 'animation',
                            'action': msg.get('action'),
                            'reply_to_message_id': msg.get('reply_to_message_id')
                        })
                    elif msg.get('action') == 'topic_created':
                        group_data['messages'].append({
                            'id': msg.get('id'),
                            'date': msg.get('date'),
                            'title': msg.get('title', 'No Title'),
                            'media': msg.get('file'),
                            'thumbnail': msg.get('thumbnail'),
                            'is_gif': msg.get('media_type') == 'animation',
                            'is_topic': True,
                            'reply_to_message_id': msg.get('reply_to_message_id')
                        })
                all_data.append(group_data)
    except Exception as e:
        print(f"Error loading data: {e}")
        return all_data
    return all_data

def process_group_data(group, current_date, github_raw_base):
    if not group.get('name'):
        print(f"Warning: Group missing name, setting to 'Unknown': {group}")
        group['name'] = 'Unknown'
    messages = group.get('messages', [])
    total_messages = len(messages)
    date_diffs = []
    titles = []
    ratings_hashtags = {'#FIVE': 0, '#FOUR': 0, '#Three': 0}
    scene_types_hashtags = {'#SceneType': 0}
    other_hashtags = {}
    photo_paths = []
    telegram_group_id = str(group['id']).replace('-100', '')
    group_name = group['name']
    media_files = [msg.get('media') or msg.get('thumbnail') for msg in messages if (msg.get('media') or msg.get('thumbnail')) and not msg.get('is_gif')]

    # Map topic messages to their replies
    topic_replies = {}
    for msg in messages:
        if msg.get('reply_to_message_id') and any(t['id'] == msg['reply_to_message_id'] for t in messages if t.get('is_topic')):
            topic_replies[msg['reply_to_message_id']] = msg

    for msg in messages:
        date_diff = get_date_difference(msg['date'], current_date)
        if date_diff is not None:
            date_diffs.append(date_diff)
        if msg.get('is_topic'):
            serial_number = len(titles) + 1
            media = msg.get('media')
            thumbnail = msg.get('thumbnail')
            # Check for reply message with media/thumbnail
            reply_msg = topic_replies.get(msg['id'])
            if reply_msg:
                media = media or reply_msg.get('media')
                thumbnail = thumbnail or reply_msg.get('thumbnail')
                print(f"Found reply for topic {msg.get('title', 'No Title')}: Media={media}, Thumbnail={thumbnail}")
            # Prefer thumbnail over media
            if thumbnail:
                media_path = f"{github_raw_base}/Photos/{group_name}/thumbs/{thumbnail}"
            elif media:
                # Convert video file to jpg for thumbnail
                media_base = os.path.splitext(media)[0]
                media_path = f"{github_raw_base}/Photos/{group_name}/thumbs/{media_base}.jpg"
            else:
                media_path = f"{github_raw_base}/Photos/{group_name}.jpg"
            accessible = utils.is_url_accessible(media_path)
            print(f"Title for {group_name}: {msg.get('title', 'No Title')}, Serial: {serial_number}, Media: {media_path}, Accessible: {accessible}")
            media_path = media_path if accessible else f"{github_raw_base}/Photos/placeholder.png"
            titles.append({
                'message_id': msg['id'],
                'title': msg.get('title', 'No Title'),
                'date': msg['date'].split('T')[0],
                'media_path': media_path,
                'is_gif': msg.get('is_gif', False),
                'serial_number': serial_number
            })
        text = msg.get('text', '')
        hashtags = extract_hashtags(text)
        for hashtag in hashtags:
            if hashtag in ratings_hashtags:
                ratings_hashtags[hashtag] += 1
            elif hashtag == '#SceneType':
                scene_types_hashtags[hashtag] += 1
            else:
                other_hashtags[hashtag] = other_hashtags.get(hashtag, 0) + 1
        if (msg.get('media') or msg.get('thumbnail')) and not msg.get('is_topic') and not msg.get('is_gif'):
            photo_path = f"{github_raw_base}/Photos/{msg.get('thumbnail') or msg.get('media')}"
            if photo_path not in photo_paths:
                photo_paths.append(photo_path)

    group_info = {
        'group_id': group['id'],
        'group_name': group['name'],
        'total_messages': total_messages,
        'date_diffs': date_diffs,
        'titles': titles,
        'ratings_hashtags': ratings_hashtags,
        'scene_types_hashtags': scene_types_hashtags,
        'other_hashtags': other_hashtags,
        'photo_paths': photo_paths,
        'telegram_group_id': telegram_group_id
    }
    print(f"Processed group: {group_info['group_name']} (ID: {group_info['group_id']}), Titles: {len(titles)}, Photos: {len(photo_paths)}")
    return group_info

def calculate_scores_and_ranks(all_data, max_messages, date_diffs, history_csv_file, html_subfolder, csv_file, github_raw_base):
    current_date = datetime.now()
    groups_data = []
    for group in all_data:
        group_info = process_group_data(group, current_date, github_raw_base)
        group_info['max_messages'] = max_messages
        group_info['date_diffs'] = date_diffs.get(group['id'], [])
        groups_data.append(group_info)

    for group in groups_data:
        total_messages = group['total_messages']
        message_score = (total_messages / group['max_messages']) * 50 if group['max_messages'] > 0 else 0
        ratings_score = sum(group['ratings_hashtags'].values()) * 10
        date_diff_score = sum(group['date_diffs']) / len(group['date_diffs']) if group['date_diffs'] else 0
        date_diff_score = 50 * math.exp(-date_diff_score / 30) if date_diff_score > 0 else 0
        group['score'] = message_score + ratings_score + date_diff_score

    sorted_data = sorted(groups_data, key=lambda x: x['score'], reverse=True)
    for i, group in enumerate(sorted_data, 1):
        group['rank'] = i
        if 'group_name' not in group:
            print(f"Error: group_name missing in sorted_data: {group}")
            group['group_name'] = 'Unknown'

    history_data = {}
    if os.path.exists(history_csv_file):
        try:
            with open(history_csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    group_name = row.get('group name', 'Unknown')
                    history_data[group_name] = history_data.get(group_name, [])
                    try:
                        history_data[group_name].append({
                            'date': row['date'],
                            'rank': int(row['rank'])
                        })
                    except (ValueError, KeyError) as e:
                        print(f"Error processing history row for {group_name}: {e}")
                        continue
            print(f"History data loaded: {history_data}")
        except Exception as e:
            print(f"Error reading history_csv_file: {e}")

    for group in sorted_data:
        group_name = group['group_name']
        group['last_rank'] = 'N/A'
        group['last_rank_date'] = 'N/A'
        group['up_down'] = 'N/A'
        if group_name in history_data and history_data[group_name]:
            try:
                last_entry = history_data[group_name][-1]
                last_rank = last_entry.get('rank')
                if not isinstance(last_rank, int):
                    print(f"Invalid last_rank for {group_name}: {last_rank}")
                    last_rank = 'N/A'
                group['last_rank'] = last_rank
                group['last_rank_date'] = last_entry.get('date', 'N/A')
                if isinstance(last_rank, int) and isinstance(group['rank'], int):
                    group['up_down'] = last_rank - group['rank']
                    print(f"Set up_down for {group_name}: {group['up_down']}")
                else:
                    group['up_down'] = 'N/A'
                    print(f"Set up_down to 'N/A' for {group_name} due to invalid ranks")
            except Exception as e:
                print(f"Error setting history for {group_name}: {e}")
                group['last_rank'] = 'N/A'
                group['up_down'] = 'N/A'

    with open(history_csv_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if os.path.getsize(history_csv_file) == 0:
            writer.writerow(['group name', 'date', 'rank'])
        for group in sorted_data:
            writer.writerow([group['group_name'], current_date.strftime('%Y-%m-%d'), group['rank']])

    output_data = []
    for group in sorted_data:
        # Use raw group name for main page photo
        group_photo = f"{github_raw_base}/Photos/{group['group_name']}.jpg"
        photo_file_name = group_photo if utils.is_url_accessible(group_photo) else f"{github_raw_base}/Photos/placeholder.png"
        print(f"Main page - Group: {group['group_name']}, photo_file_name: {photo_file_name}, Accessible: {utils.is_url_accessible(photo_file_name)}")
        html_file = f"{utils.sanitize_filename(group['group_name'])}_{group['group_id']}.html"
        last_scene_days = min(group['date_diffs']) if group['date_diffs'] else 'N/A'
        output_data.append({
            'group name': group['group_name'],
            'rank': group['rank'],
            'last rank': group.get('last_rank', 'N/A'),
            'last rank date': group.get('last_rank_date', 'N/A'),
            'up down': group.get('up_down', 'N/A'),
            'photo_file_name': photo_file_name,
            'html_file': html_file,
            'Datedifference': last_scene_days,
            'total titles': len(group['titles']),
            'count of the hashtag "#FIVE"': group['ratings_hashtags']['#FIVE'],
            'count of the hashtag "#FOUR"': group['ratings_hashtags']['#FOUR'],
            'count of the hashtag "#Three"': group['ratings_hashtags']['#Three'],
            'count of the hashtag "#SceneType"': group['scene_types_hashtags']['#SceneType'],
            'score': group['score']
        })

    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'group name', 'rank', 'last rank', 'last rank date', 'up down',
            'photo_file_name', 'html_file', 'Datedifference', 'total titles',
            'count of the hashtag "#FIVE"', 'count of the hashtag "#FOUR"',
            'count of the hashtag "#Three"', 'count of the hashtag "#SceneType"', 'score'
        ])
        writer.writeheader()
        writer.writerows(output_data)

    for group in sorted_data:
        ratings_hashtag_list = ''.join(f'<li class="hashtag-item">{k}: {v}</li>' for k, v in group['ratings_hashtags'].items() if v > 0)
        scene_types_hashtag_list = ''.join(f'<li class="hashtag-item">{k}: {v}</li>' for k, v in group['scene_types_hashtags'].items() if v > 0)
        other_hashtag_list = ''.join(f'<li class="hashtag-item">{k}: {v}</li>' for k, v in group['other_hashtags'].items() if v > 0)
        html_generator.generate_group_html(
            group['group_name'], group['group_id'], group['titles'],
            history_data, group['photo_paths'], ratings_hashtag_list,
            scene_types_hashtag_list, other_hashtag_list, len(group['titles']),
            f"{min(group['date_diffs'])} days" if group['date_diffs'] else 'N/A',
            group['total_messages'], group['telegram_group_id'],
            github_raw_base=github_raw_base,
            html_subfolder=html_subfolder
        )

    print(f"Returning {len(sorted_data)} groups in sorted_data")
    return output_data