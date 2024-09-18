import csv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import time
import isodate

# Initialize the YouTube API client
youtube = build('youtube', 'v3', developerKey='Input YouTube API Key')

def youtube_search(queries, min_views=1, min_comments=1, max_results=1000, published_after="Start Time", published_before="End Time"):
    videos = []
    total_videos_processed = 0

    for query in queries:
        next_page_token = None

        while len(videos) < max_results:
            try:
                search_response = youtube.search().list(
                    q=query,
                    part='id,snippet',
                    maxResults=50,  # Max results per request, it can be modified
                    type='video',
                    relevanceLanguage='en',  # Set relevance language to English, it can be modified
                    regionCode='US',  # Set region code to US, it can be modified
                    publishedAfter=published_after,
                    publishedBefore=published_before,
                    pageToken=next_page_token
                ).execute()

                video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]

                if video_ids:
                    video_response = youtube.videos().list(
                        part='snippet,statistics,contentDetails',
                        id=','.join(video_ids)
                    ).execute()

                    for video in video_response.get('items', []):
                        duration = video['contentDetails']['duration']
                        view_count = int(video['statistics'].get('viewCount', 0))
                        comment_count = int(video['statistics'].get('commentCount', 0))

                        video_info = {
                            'title': video['snippet']['title'],
                            'url': f"https://www.youtube.com/watch?v={video['id']}",
                            'views': view_count,
                            'comments': comment_count,
                            'duration': duration
                        }
                        videos.append(video_info)

                    total_videos_processed += len(video_response.get('items', []))

                next_page_token = search_response.get('nextPageToken')
                if not next_page_token:
                    break

            except HttpError as e:
                error = e.resp.status
                if error == 403:
                    print("Quota exceeded. Waiting for quota reset...")
                    time.sleep(3600)  # Wait for an hour before retrying
                else:
                    print(f"An HTTP error {error} occurred:\n{e}")
                    break

            if len(videos) >= max_results:
                break

    return videos[:max_results], total_videos_processed

def filter_videos(videos, min_views=1, min_comments=300, max_duration='PT15M'): #Defines max lenght for video, it can be modified
    filtered_videos = []
    max_duration_seconds = isodate.parse_duration(max_duration).total_seconds()
    for video in videos:
        duration = isodate.parse_duration(video['duration']).total_seconds()
        view_count = video['views']
        comment_count = video['comments']

        # Debugging prints
        print(f"Checking video: {video['title']}")
        print(f"Duration (seconds): {duration}, Views: {view_count}, Comments: {comment_count}")

        if view_count >= min_views and comment_count >= min_comments and duration <= max_duration_seconds:
            filtered_videos.append(video)
        else:
            print(f"Excluded video: {video['title']}")
    return filtered_videos

def remove_duplicates(videos):
    seen_urls = set()
    unique_videos = []
    for video in videos:
        if video['url'] not in seen_urls:
            unique_videos.append(video)
            seen_urls.add(video['url'])
    return unique_videos

def save_to_csv(videos, filename):
    keys = ['title', 'url', 'views', 'comments', 'duration']
    with open(filename, 'w', newline='', encoding='utf-8') as output_file:
        dict_writer = csv.DictWriter(output_file, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(videos)

# Example usage
queries = [
    'immigration crisis',
    'refugees asylum seeker',
    'border control',
    'migrants acceptance hospitality',
]

# Retrieve all videos
all_videos, total_videos_processed = youtube_search(queries, max_results=1000)

# Save unfiltered videos to a CSV file
save_to_csv(all_videos, "Output Directory_all the gathered videos")

# Remove duplicates from the list of all videos
unique_videos = remove_duplicates(all_videos)

# Apply filtering criteria
filtered_videos = filter_videos(unique_videos, min_views=1, min_comments=300, max_duration='PT15M') #Additional filter applied on the csv file for max lenght for video, it can be modified

# Save filtered videos to a CSV file
save_to_csv(filtered_videos, "Output Directory_filtered videos by leght")

print(f"Total videos processed: {total_videos_processed}")
print(f"Total unique videos: {len(unique_videos)}")
print(f"Total filtered videos: {len(filtered_videos)}")

for video in filtered_videos:
    print(f"{video['title']} - {video['url']} (Views: {video['views']}, Comments: {video['comments']}, Duration: {video['duration']})")
