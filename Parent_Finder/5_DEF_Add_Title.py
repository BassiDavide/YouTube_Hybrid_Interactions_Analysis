import json
import pandas as pd
import os
from pathlib import Path

def load_video_titles_from_csv(csv_folder_path):
    """Load all video titles from CSV files into a dictionary."""
    video_titles = {}
    
    # Get all CSV files in the folder
    csv_files = [f for f in os.listdir(csv_folder_path) if f.endswith('.csv')]
    
    for csv_file in csv_files:
        csv_path = os.path.join(csv_folder_path, csv_file)
        try:
            df = pd.read_csv(csv_path)
            # Create mapping from video_id to title
            for _, row in df.iterrows():
                video_titles[row['video_id']] = row['title']
            print(f"Loaded {len(df)} videos from {csv_file}")
        except Exception as e:
            print(f"Error reading {csv_file}: {e}")
    
    return video_titles

def process_comments_folder(comments_folder_path, video_titles, output_folder_path):
    """Process all JSONL files in a comments folder."""
    missing_titles = set()
    processed_files = 0
    
    # Create output folder if it doesn't exist
    os.makedirs(output_folder_path, exist_ok=True)
    
    # Get all JSONL files in the folder
    jsonl_files = [f for f in os.listdir(comments_folder_path) if f.endswith('.jsonl')]
    
    for jsonl_file in jsonl_files:
        input_path = os.path.join(comments_folder_path, jsonl_file)
        output_path = os.path.join(output_folder_path, jsonl_file)
        
        try:
            with open(input_path, 'r', encoding='utf-8') as infile, \
                 open(output_path, 'w', encoding='utf-8') as outfile:
                
                comments_processed = 0
                for line in infile:
                    try:
                        comment = json.loads(line.strip())
                        video_id = comment.get('VideoID', '')
                        
                        # Add VideoTitle field
                        if video_id in video_titles:
                            comment['VideoTitle'] = video_titles[video_id]
                        else:
                            comment['VideoTitle'] = None
                            missing_titles.add(video_id)
                        
                        # Write updated comment
                        outfile.write(json.dumps(comment, ensure_ascii=False) + '\n')
                        comments_processed += 1
                        
                    except json.JSONDecodeError as e:
                        print(f"Error parsing JSON in {jsonl_file}: {e}")
                        continue
                
                print(f"Processed {comments_processed} comments from {jsonl_file}")
                processed_files += 1
                
        except Exception as e:
            print(f"Error processing {jsonl_file}: {e}")
    
    return missing_titles, processed_files

def main():
    # Configuration - UPDATE THESE PATHS
    comments_base_path = "Path_to/Chain_Comment"
    
    csv_folder_path = "Path_to/Video"  # Assuming CSV files are in the base directory
    output_base_path = "Path_to/Chain_Comment_with_titles"
    
    print("Loading video titles from CSV files...")
    video_titles = load_video_titles_from_csv(csv_folder_path)
    print(f"Total videos loaded: {len(video_titles)}")
    
    if not video_titles:
        print("No video titles found! Check your CSV folder path.")
        return
    
    # Get all channel folders
    channel_folders = [f for f in os.listdir(comments_base_path) 
                      if os.path.isdir(os.path.join(comments_base_path, f))]
    
    print(f"Found {len(channel_folders)} channel folders")
    
    all_missing_titles = set()
    total_processed_files = 0
    
    # Process each channel folder
    for channel_folder in channel_folders:
        print(f"\nProcessing channel: {channel_folder}")
        
        comments_folder_path = os.path.join(comments_base_path, channel_folder)
        output_folder_path = os.path.join(output_base_path, channel_folder)
        
        missing_titles, processed_files = process_comments_folder(
            comments_folder_path, video_titles, output_folder_path
        )
        
        all_missing_titles.update(missing_titles)
        total_processed_files += processed_files
        
        print(f"Channel {channel_folder}: {processed_files} files processed")
    
    # Report results
    print(f"\n=== SUMMARY ===")
    print(f"Total files processed: {total_processed_files}")
    print(f"Total unique videos in titles database: {len(video_titles)}")
    print(f"Videos with missing titles: {len(all_missing_titles)}")
    
    if all_missing_titles:
        print("\nVideo IDs without titles:")
        for video_id in sorted(all_missing_titles):
            print(f"  - {video_id}")
        
        # Save missing video IDs to file
        missing_file = os.path.join(output_base_path, "missing_video_titles.txt")
        with open(missing_file, 'w') as f:
            for video_id in sorted(all_missing_titles):
                f.write(f"{video_id}\n")
        print(f"\nMissing video IDs saved to: {missing_file}")
    
    print(f"\nProcessed files saved to: {output_base_path}")

if __name__ == "__main__":
    main()
