import json
import os

# Specify your directories
input_dir = 'Input_Dir'
output_dir = 'Output_Dir'


def load_comments(file_path):
    comments = []
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            comments.append(json.loads(line))
    return comments


def save_comments(comments, file_path):
    with open(file_path, 'w', encoding='utf-8') as file:
        for comment in comments:
            file.write(json.dumps(comment) + '\n')


def extract_authors(comments):
    return {comment["AuthorName"] for comment in comments}


def fix_usernames(comments, author_set):
    for comment in comments:
        text = comment["CommentText"]
        search_idx = 0
        while "@@" in text[search_idx:]:
            start_idx = text.find("@@", search_idx)
            end_idx = start_idx + 2
            while end_idx < len(text) and (text[end_idx].isalnum() or text[end_idx] in {'_', '-'}):
                end_idx += 1

            full_username = text[start_idx + 2:end_idx]
            username = "@" + full_username

            valid_username_found = False
            for i in range(len(username), 0, -1):
                if username[:i] in author_set:
                    valid_username = username[:i]
                    remaining_text = text[start_idx + 1 + i:end_idx] + text[end_idx:]
                    text = text[:start_idx + 1] + valid_username + " " + remaining_text
                    search_idx = start_idx + len(valid_username) + 2
                    valid_username_found = True
                    break

            if not valid_username_found:
                search_idx = end_idx

        comment["CommentText"] = text

    return comments


def process_files(input_dir, output_dir):
    for file in os.listdir(input_dir):
        if file.endswith('.jsonl'):
            input_path = os.path.join(input_dir, file)
            output_path = os.path.join(output_dir, 'Pre' + file)

            comments = load_comments(input_path)
            author_set = extract_authors(comments)
            fixed_comments = fix_usernames(comments, author_set)
            save_comments(fixed_comments, output_path)
            print(f'Processed file saved to: {output_path}')


# Run the function for processing all files
process_files(input_dir, output_dir)
