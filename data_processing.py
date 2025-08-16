import json
import os
import math
import csv
import zipfile  # Added import
from datetime import datetime, timedelta
import random
import re
import utils  # Ensure utils is imported for sanitize_filename

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
        for chat in chats:
            if chat.get('type') == 'private_supergroup':
                group_data = {
                    'id': chat.get('id'),
                    'name': chat.get('name', 'Unknown'),
                    'messages': []
                }
                for msg in chat.get('messages', []):
                    if msg.get('type') == 'message':
                        text = msg.get('text', '')
                        if isinstance(text, list):
                            text = ''.join(str(t) for t in text)
                        group_data['messages'].append({
                            'id': msg.get('id'),
                            'date': msg.get('date'),
                            'text': text,
                            'media': msg.get('file'),
                            'is_gif': msg.get('media_type') == 'animation'
                        })
                    elif msg.get('action') == 'topic_created':
                        group_data['messages'].append({
                            'id': msg.get('id'),
                            'date': msg.get('date'),
                            'title': msg.get('title', 'No Title'),
                            'is_topic': True
                        })
                all_data.append(group_data)
    except Exception as e:
        print(f"Error loading data: {e}")
        return all_data
    return all_data

def process_group_data(group, current_date, github_raw_base):
    messages = group.get('messages', [])
    total_messages = len(messages)
    date_diffs = []
    titles = []
    ratings_hashtags = {'#FIVE': 0, '#FOUR': 0, '#Three': 0}
    scene_types_hashtags = {'#SceneType': 0}
    other_hashtags = {}
    photo_paths = []
    telegram_group_id = str(group['id']).replace('-100', '')

    for msg in messages:
        date_diff = get_date_difference(msg['date'], current_date)
        if date_diff is not None:
            date_diffs.append(date_diff)
        if msg.get('is_topic'):
            media_path = f"{github_raw_base}/Photos/placeholder.png"
            if msg.get('media'):
                media_path = f"{github_raw_base}/Photos/{msg['media']}" if not msg.get('is_gif') else f"{github_raw_base}/Photos/{msg['media']}"
            titles.append({
                'message_id': msg['id'],
                'title': msg['title'],
                'date': msg['date'].split('T')[0],
                'media_path': media_path,
                'is_gif': msg.get('is_gif', False),
                'serial_number': len(titles) + 1
            })
        hashtags = extract_hashtags(msg['text'])
        for hashtag in hashtags:
            if hashtag in ratings_hashtags:
                ratings_hashtags[hashtag] += 1
            elif hashtag == '#SceneType':
                scene_types_hashtags[hashtag] += 1
            else:
                other_hashtags[hashtag] = other_hashtags.get(hashtag, 0) + 1
        if msg.get('media') and not msg.get('is_topic'):
            photo_path = f"{github_raw_base}/Photos/{msg['media']}"
            if photo_path not in photo_paths:
                photo_paths.append(photo_path)

    return {
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

def calculate_scores_and_ranks(all_data, max_messages, date_diffs, history_csv_file, html_subfolder, csv_file):
    current_date = datetime.now()
    groups_data = []
    for group in all_data:
        group_info = process_group_data(group, current_date, github_raw_base="https://raw.githubusercontent.com/anagoofyoutlook/psranking-dev/main")
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

    history_data = {}
    if os.path.exists(history_csv_file):
        with open(history_csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                group_name = row['group name']
                history_data[group_name] = history_data.get(group_name, [])
                history_data[group_name].append({
                    'date': row['date'],
                    'rank': int(row['rank'])
                })

    for group in sorted_data:
        group_name = group['group_name']
        group['last_rank'] = 'N/A'
        group['last_rank_date'] = 'N/A'
        group['up_down'] = 'N/A'
        if group_name in history_data and history_data[group_name]:
            last_entry = history_data[group_name][-1]
            group['last_rank'] = last_entry['rank']
            group['last_rank_date'] = last_entry['date']
            group['up_down'] = last_entry['rank'] - group['rank']

    with open(history_csv_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if os.path.getsize(history_csv_file) == 0:
            writer.writerow(['group name', 'date', 'rank'])
        for group in sorted_data:
            writer.writerow([group['group_name'], current_date.strftime('%Y-%m-%d'), group['rank']])

    output_data = []
    for group in sorted_data:
        photo_file_name = group['photo_paths'][0] if group['photo_paths'] else f"{github_raw_base}/Photos/placeholder.png"
        html_file = f"{utils.sanitize_filename(group['group_name'])}_{group['group_id']}.html"
        last_scene_days = min(group['date_diffs']) if group['date_diffs'] else 'N/A'
        output_data.append({
            'group name': group['group_name'],
            'rank': group['rank'],
            'last rank': group['last_rank'],
            'last rank date': group['last_rank_date'],
            'up down': group['up_down'],
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
            github_raw_base="https://raw.githubusercontent.com/anagoofyoutlook/psranking-dev/main",
            html_subfolder=html_subfolder
        )

    return output_data