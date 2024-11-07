import json
import re
import os


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

                mentions = re.findall(r'@(\w+)', comment_text)
                if mentions:
                    last_mention = '@' + mentions[-1]
                    referenced_id = last_comment_by_author.get(last_mention, None)
                    if referenced_id and referenced_id in levels:
                        comment['Response to'] = referenced_id
                        response_level = levels[referenced_id] + 1

                comment['Level'] = response_level

            levels[comment_id] = comment['Level']
            json.dump(comment, outfile)
            outfile.write('\n')

def process_directory(input_dir, output_dir):
    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)


    for filename in os.listdir(input_dir):
        if filename.endswith('.jsonl'):
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, filename)
            process_jsonl_comments(input_path, output_path)
            print(f"Processed {filename}")

# Example usage
input_directory = 'Input_Dir'
output_directory = 'Output_Dir'
process_directory(input_directory, output_directory)
