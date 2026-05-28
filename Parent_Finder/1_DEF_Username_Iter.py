import json
import os

# Specify your directories
input_dir = 'Folder_with_jsonl_files'
output_dir = 'Path_to/Username_Fix'


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
            # Find the next @@ occurrence
            start_idx = text.find("@@", search_idx)
            end_idx = start_idx + 2

            # Extend until we hit a non-username character
            while end_idx < len(text) and (text[end_idx].isalnum() or text[end_idx] in {'_', '-', '.'}):
                end_idx += 1

            # Get the potential username text
            potential_username = text[start_idx + 2:end_idx]

            # Try to find the longest valid username
            valid_username_found = False
            for i in range(len(potential_username), 0, -1):
                test_username = "@" + potential_username[:i]
                if test_username in author_set:
                    # Reconstruct the text with proper formatting:
                    # 1. Everything before @@
                    # 2. The valid @username
                    # 3. A space
                    # 4. Any remaining characters from the invalid part
                    # 5. The rest of the text
                    text = (text[:start_idx] +  # Keep text before @@
                            test_username +  # Add valid username
                            " " +  # Add space after username
                            text[start_idx + 2 + i:end_idx] +  # Add any remaining characters
                            text[end_idx:])  # Add rest of text
                    search_idx = start_idx + len(test_username) + 2
                    valid_username_found = True
                    break

            if not valid_username_found:
                # Just convert @@ to @ (simplest solution)
                text = text[:start_idx] + text[start_idx + 1:]  # Remove one @ symbol
                search_idx = start_idx + 1  # Move past the remaining @

        comment["CommentText"] = text

    return comments


def process_files(input_dir, output_dir):
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Walk through all directories and subdirectories
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.endswith('.jsonl'):
                input_path = os.path.join(root, file)
                
                # Create corresponding subdirectory structure in output
                relative_path = os.path.relpath(root, input_dir)
                if relative_path == '.':  # If files are in root input_dir
                    output_subdir = output_dir
                else:
                    output_subdir = os.path.join(output_dir, relative_path)
                
                # Create output subdirectory if it doesn't exist
                if not os.path.exists(output_subdir):
                    os.makedirs(output_subdir)
                
                output_path = os.path.join(output_subdir, 'Pre' + file)

                # Load and process the file
                comments = load_comments(input_path)
                author_set = extract_authors(comments)
                fixed_comments = fix_usernames(comments, author_set)
                save_comments(fixed_comments, output_path)
                print(f'Processed: {input_path} -> {output_path}')


# Run the function for processing all files
process_files(input_dir, output_dir)
