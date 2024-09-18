import pandas as pd
import os
import json
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
import re

# Load the uploaded CSV file
file_path = 'Input path to CSV file with selected URLS'
urls_df = pd.read_csv(file_path)

# Initialize YouTube API client
api_key = 'Input YouTube API Key'
youtube = build('youtube', 'v3', developerKey=api_key)

# Define the output path 
output_path = 'Output Directory + File_Name'
os.makedirs(output_path, exist_ok=True)

def extract_video_id(url):
    video_id = None
    patterns = [
        r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})',
        r'(?:https?:\/\/)?(?:www\.)?youtube.com\/shorts\/([a-zA-Z0-9_-]{11})'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            video_id = match.group(1)
            break
    return video_id

def fetch_replies(youtube, json_file, parent_id, thread_id, video_id):
    page_token = None
    while True:
        replies_response = youtube.comments().list(
            part='snippet',
            parentId=parent_id,
            maxResults=100,
            pageToken=page_token,
            textFormat='plainText'
        ).execute()

        for reply in replies_response.get('items', []):
            json_file.write(json.dumps({
                'CommentID': reply['id'],
                'ThreadID': thread_id,
                'VideoID': video_id,
                'ParentCommentID': parent_id,
                'CommentText': reply['snippet']['textDisplay'],
                'AuthorName': reply['snippet']['authorDisplayName'],
                'NumberOfLikes': reply['snippet']['likeCount'],
                'IsReply': 'True',
                'Timestamp': reply['snippet']['publishedAt']
            }) + '\n')

        page_token = replies_response.get('nextPageToken')
        if not page_token:
            break

for index, row in urls_df.iterrows():
    video_url = row['url']
    video_id = extract_video_id(video_url)
    if not video_id:
        print(f"Failed to extract video ID from URL: {video_url}")
        continue

    comments_file_path = os.path.join(output_path, f'comments_{video_id}.jsonl')
    transcript_file_path = os.path.join(output_path, f'transcripts_{video_id}.jsonl')

    with open(comments_file_path, 'w', encoding='utf-8') as comments_file, \
         open(transcript_file_path, 'w', encoding='utf-8') as transcript_file:

        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
            for segment in transcript:
                transcript_file.write(json.dumps({
                    'VideoID': video_id,
                    'Timestamp': segment['start'],
                    'Transcript': segment['text']
                }) + '\n')
            print(f"Transcript for video {video_id} downloaded successfully.")
        except Exception as e:
            print(f"Failed to download transcript for video {video_id}: {e}")

        page_token = None
        while True:
            top_level_comments_response = youtube.commentThreads().list(
                part='snippet',
                videoId=video_id,
                maxResults=100,
                pageToken=page_token,
                order='relevance',
                textFormat='plainText'
            ).execute()

            for item in top_level_comments_response['items']:
                thread_id = item['id']
                top_level_comment = item['snippet']['topLevelComment']
                comment_id = top_level_comment['id']
                comments_file.write(json.dumps({
                    'CommentID': comment_id,
                    'ThreadID': thread_id,
                    'VideoID': video_id,
                    'ParentCommentID': '',
                    'CommentText': top_level_comment['snippet']['textDisplay'],
                    'AuthorName': top_level_comment['snippet']['authorDisplayName'],
                    'NumberOfLikes': top_level_comment['snippet']['likeCount'],
                    'IsReply': 'False',
                    'Timestamp': top_level_comment['snippet']['publishedAt']
                }) + '\n')
                fetch_replies(youtube, comments_file, comment_id, thread_id, video_id)

            page_token = top_level_comments_response.get('nextPageToken')
            if not page_token:
                break

print("Data collection complete.")
