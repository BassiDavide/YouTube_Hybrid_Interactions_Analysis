import json
import re
import os

# Function to process JSONL file and append extra data
def process_jsonl_comments(input_jsonl_path, output_jsonl_path):
    with open(input_jsonl_path, 'r', encoding='utf-8') as infile, open(output_jsonl_path, 'w', encoding='utf-8') as outfile:

        last_comment_by_author = {}
        levels = {}

        for line in infile:
            comment = json.loads(line)

            author = comment["AuthorName"]
            comment_id = comment["CommentID"]
            parent_id = comment["ParentCommentID"]
            is_reply = comment["IsReply"] == "True"
            comment_text = comment["CommentText"]



            last_comment_by_author[author] = comment_id

            comment['Response to'] = None
            comment['Level'] = 0

            if is_reply:

                comment['Response to'] = parent_id

                parent_level = levels.get(parent_id, 0)
                response_level = parent_level + 1

                mentions = re.findall(r'@([A-Za-z0-9_.-]+)', comment_text)
                if mentions:
                    # Instead of always using the last mention, find the first valid one
                    referenced_id = None
                    for potential_mention in mentions:
                        potential_username = '@' + potential_mention
                        if potential_username in last_comment_by_author:
                            # We found a valid mention, use it and stop looking
                            referenced_id = last_comment_by_author.get(potential_username, None)
                            if referenced_id and referenced_id in levels:
                                comment['Response to'] = referenced_id
                                response_level = levels[referenced_id] + 1
                                break

                comment['Level'] = response_level

            levels[comment_id] = comment['Level']
            json.dump(comment, outfile)
            outfile.write('\n')

def process_directory(input_dir, output_dir):
    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Walk through all directories and subdirectories
    for root, dirs, files in os.walk(input_dir):
        for filename in files:
            if filename.endswith('.jsonl'):
                input_path = os.path.join(root, filename)
                
                # Create corresponding subdirectory structure in output
                relative_path = os.path.relpath(root, input_dir)
                if relative_path == '.':  # If files are in root input_dir
                    output_subdir = output_dir
                else:
                    output_subdir = os.path.join(output_dir, relative_path)
                
                # Create output subdirectory if it doesn't exist
                if not os.path.exists(output_subdir):
                    os.makedirs(output_subdir)
                
                output_path = os.path.join(output_subdir, filename)
                
                process_jsonl_comments(input_path, output_path)
                print(f"Processed: {input_path} -> {output_path}")

# Example usage
input_directory = '/mnt/beegfs/home/davide.bassi/YT_continuous_scraper/Conversation_Builder/Intermediate/Username_Fix'
output_directory = '/mnt/beegfs/home/davide.bassi/YT_continuous_scraper/Conversation_Builder/Intermediate/Relation_Created'
process_directory(input_directory, output_directory)