import json
import os

def process_jsonl_file(input_path, output_path):
    """Process a single JSONL file to add ConText field."""
    
    # First pass: load all comments into a dictionary for lookup
    comments_dict = {}
    
    print(f"Loading comments from {os.path.basename(input_path)}...")
    
    with open(input_path, 'r', encoding='utf-8') as file:
        for line in file:
            try:
                comment = json.loads(line.strip())
                comment_id = comment.get('CommentID', '')
                if comment_id:
                    comments_dict[comment_id] = comment
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON: {e}")
                continue
    
    print(f"Loaded {len(comments_dict)} comments")
    
    # Second pass: add ConText field and write to output
    with open(input_path, 'r', encoding='utf-8') as infile, \
         open(output_path, 'w', encoding='utf-8') as outfile:
        
        processed_count = 0
        context_added_count = 0
        missing_parent_count = 0
        missing_parents = []
        
        for line in infile:
            try:
                comment = json.loads(line.strip())
                
                # Get the parent comment ID
                parent_id = comment.get('Response to')
                
                # Add ConText field
                if parent_id and parent_id != "null":  # Check for non-null parent
                    if parent_id in comments_dict:
                        parent_comment = comments_dict[parent_id]
                        comment['ConText'] = parent_comment.get('CommentText', '')
                        context_added_count += 1
                    else:
                        # Parent comment not found
                        comment['ConText'] = ''
                        missing_parent_count += 1
                        missing_parents.append({
                            'CommentID': comment.get('CommentID', ''),
                            'MissingParentID': parent_id,
                            'AuthorName': comment.get('AuthorName', ''),
                            'Timestamp': comment.get('Timestamp', '')
                        })
                else:
                    comment['ConText'] = ''
                
                # Write updated comment
                outfile.write(json.dumps(comment, ensure_ascii=False) + '\n')
                processed_count += 1
                
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON: {e}")
                continue
    
    if missing_parent_count > 0:
        print(f"WARNING: {missing_parent_count} comments had missing parent comments")
    
    print(f"Processed {processed_count} comments, added context to {context_added_count} replies")
    return processed_count, context_added_count, missing_parent_count, missing_parents

def process_all_folders(base_path, output_base_path):
    """Process all JSONL files in all channel folders."""
    
    total_files = 0
    total_comments = 0
    total_context_added = 0
    total_missing_parents = 0
    all_missing_parents = []
    
    # Get all channel folders
    channel_folders = [f for f in os.listdir(base_path) 
                      if os.path.isdir(os.path.join(base_path, f))]
    
    print(f"Found {len(channel_folders)} channel folders")
    
    for channel_folder in channel_folders:
        print(f"\nProcessing channel: {channel_folder}")
        
        input_folder = os.path.join(base_path, channel_folder)
        output_folder = os.path.join(output_base_path, channel_folder)
        
        # Create output folder if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)
        
        # Get all JSONL files in the channel folder
        jsonl_files = [f for f in os.listdir(input_folder) if f.endswith('.jsonl')]
        
        for jsonl_file in jsonl_files:
            input_path = os.path.join(input_folder, jsonl_file)
            output_path = os.path.join(output_folder, jsonl_file)
            
            try:
                comments_count, context_count, missing_count, missing_list = process_jsonl_file(input_path, output_path)
                total_files += 1
                total_comments += comments_count
                total_context_added += context_count
                total_missing_parents += missing_count
                
                # Add file info to missing parents
                for missing in missing_list:
                    missing['FileName'] = jsonl_file
                    missing['Channel'] = channel_folder
                all_missing_parents.extend(missing_list)
                
            except Exception as e:
                print(f"Error processing {jsonl_file}: {e}")
    
    return total_files, total_comments, total_context_added, total_missing_parents, all_missing_parents

def main():
    # Configuration - UPDATE THESE PATHS
    input_base_path = "/mnt/beegfs/home/davide.bassi/YT_continuous_scraper/Chain_Comment_with_titles"
    output_base_path = "/mnt/beegfs/home/davide.bassi/YT_continuous_scraper/Chain_Comment_with_context"
    
    print("Starting to add ConText field to YouTube comments...")
    
    total_files, total_comments, total_context_added, total_missing_parents, all_missing_parents = process_all_folders(
        input_base_path, output_base_path
    )
    
    print(f"\n=== SUMMARY ===")
    print(f"Total files processed: {total_files}")
    print(f"Total comments processed: {total_comments}")
    print(f"Total replies with context added: {total_context_added}")
    print(f"Total replies with missing parent comments: {total_missing_parents}")
    
    if total_missing_parents > 0:
        print(f"\nWARNING: {total_missing_parents} comments referenced parent comments that could not be found!")
        
        # Save missing parents info to file
        missing_file = os.path.join(output_base_path, "missing_parent_comments.jsonl")
        with open(missing_file, 'w', encoding='utf-8') as f:
            for missing in all_missing_parents:
                f.write(json.dumps(missing, ensure_ascii=False) + '\n')
        
        print(f"Details of missing parent comments saved to: {missing_file}")
        
        # Show first few examples
        print("\nFirst 5 examples of missing parent comments:")
        for i, missing in enumerate(all_missing_parents[:5]):
            print(f"  {i+1}. Comment {missing['CommentID']} by {missing['AuthorName']} ")
            print(f"      Looking for parent: {missing['MissingParentID']}")
            print(f"      File: {missing['Channel']}/{missing['FileName']}")
    
    print(f"\nOutput saved to: {output_base_path}")

if __name__ == "__main__":
    main()