import json
import re
import os


def build_author_set(input_jsonl_path):
    """Build a set of all author names from a JSONL file."""
    authors = set()
    with open(input_jsonl_path, 'r', encoding='utf-8') as file:
        for line in file:
            comment = json.loads(line)
            authors.add(comment["AuthorName"])
    return authors


def process_comments_with_chain_preservation(input_jsonl_path, output_jsonl_path, deleted_jsonl_path, authors):
    """Process comments preserving conversation chains even with invalid mentions."""
    # First pass: Build comment relationships and identify invalid mentions
    comment_children = {}  # track replies to each comment
    invalid_comments = set()  # comments with invalid mentions
    all_comments = {}  # store all comments for later processing

    with open(input_jsonl_path, 'r', encoding='utf-8') as infile:
        for line in infile:
            comment = json.loads(line)
            comment_id = comment["CommentID"]
            response_to = comment["Response to"]

            # ADD THIS LINE HERE - Store comment in all_comments
            all_comments[comment_id] = comment

            # Track parent-child relationships
            if response_to:  # If this is a reply
                if response_to not in comment_children:
                    comment_children[response_to] = set()
                comment_children[response_to].add(comment_id)

            # Check for invalid mentions
            mentions = re.findall(r'@([A-Za-z0-9_.-]+)', comment["CommentText"])
            #mentions = re.findall(r'@{1,2}([A-Za-z0-9_.-]+)', comment["CommentText"])
            for mention in mentions:
                mention = mention.strip()
                if '@' + mention not in authors:
                    # CHANGE HERE: Before adding to invalid_comments, check if there's at least one valid mention
                    has_valid_mention = False
                    for other_mention in mentions:
                        other_mention = other_mention.strip()
                        if '@' + other_mention in authors:
                            has_valid_mention = True
                            break

                    # Only mark as invalid if no valid mentions were found
                    if not has_valid_mention:
                        invalid_comments.add(comment_id)
                    break

    # Second pass: Remove invalid comments only if they have no children
    comments_to_delete = set()
    for comment_id in invalid_comments:
        if comment_id not in comment_children:  # No replies to this comment
            comments_to_delete.add(comment_id)

    # Write to output files
    with open(output_jsonl_path, 'w', encoding='utf-8') as outfile, \
            open(deleted_jsonl_path, 'w', encoding='utf-8') as deletedfile:

        for comment_id, comment in all_comments.items():
            if comment_id in comments_to_delete:
                print(f"Deleting comment with invalid mentions: {comment['CommentText'][:100]}...")
                json.dump(comment, deletedfile)
                deletedfile.write('\n')
            else:
                json.dump(comment, outfile)
                outfile.write('\n')


def process_directory_with_chain_preservation(input_dir, output_dir, deleted_dir):
    """Process entire directory of JSONL files with conversation chain preservation."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    if not os.path.exists(deleted_dir):
        os.makedirs(deleted_dir)

    # Build a set of all authors from all files first
    all_authors = set()
    print("Building author set...")
    
    # Walk through all directories and subdirectories to collect authors
    for root, dirs, files in os.walk(input_dir):
        for filename in files:
            if filename.endswith('.jsonl'):
                input_path = os.path.join(root, filename)
                file_authors = build_author_set(input_path)
                all_authors.update(file_authors)
                print(f"Found {len(file_authors)} authors in {input_path}")

    print(f"Total unique authors found: {len(all_authors)}")

    # Process each file with the full author set
    for root, dirs, files in os.walk(input_dir):
        for filename in files:
            if filename.endswith('.jsonl'):
                input_path = os.path.join(root, filename)
                
                # Create corresponding subdirectory structure in both output directories
                relative_path = os.path.relpath(root, input_dir)
                if relative_path == '.':  # If files are in root input_dir
                    output_subdir = output_dir
                    deleted_subdir = deleted_dir
                else:
                    output_subdir = os.path.join(output_dir, relative_path)
                    deleted_subdir = os.path.join(deleted_dir, relative_path)
                
                # Create output subdirectories if they don't exist
                if not os.path.exists(output_subdir):
                    os.makedirs(output_subdir)
                if not os.path.exists(deleted_subdir):
                    os.makedirs(deleted_subdir)
                
                output_path = os.path.join(output_subdir, filename)
                deleted_path = os.path.join(deleted_subdir, filename)
                
                process_comments_with_chain_preservation(input_path, output_path, deleted_path, all_authors)
                print(f"Processed: {input_path} -> {output_path}")


# Example usage
input_directory = 'Path_to/Relation_Created'
output_directory = 'Path_to/Def'
deleted_directory = 'Path_to/Deleted_Check'
process_directory_with_chain_preservation(input_directory, output_directory, deleted_directory)
