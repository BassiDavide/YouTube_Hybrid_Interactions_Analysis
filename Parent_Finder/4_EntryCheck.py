import json
import os

def analyze_comments_from_jsonl(file_path):
    # Initialize counters and lists
    analyzed_count = 0
    correct_count = 0
    problematic_count = 0
    problematic_comments = []  # List to store details of problematic comments

    # Read the JSONL file
    with open(file_path, 'r') as file:
        for line in file:
            comment = json.loads(line)
            # Increment analyzed count
            analyzed_count += 1
            # Check if the comment is at least Level 2 and contains a mention in the required format
            if comment['Level'] == 1 and '@@' in comment['CommentText']:
                problematic_count += 1
                # Store problematic comment details if the count is less than 50
                if len(problematic_comments) < 50:
                    problematic_comments.append({
                        'CommentText': comment['CommentText'],
                        'Level': comment['Level'],
                        'CommentID': comment['CommentID']
                    })
            else:
                correct_count += 1

    # Return counts and the list of problematic comments
    return analyzed_count, correct_count, problematic_count, problematic_comments

def analyze_directory(input_dir):
    """Analyze all JSONL files in directory and subdirectories"""
    total_analyzed = 0
    total_correct = 0
    total_problematic = 0
    all_problematic_details = []
    
    print(f"Analyzing files in: {input_dir}")
    print("-" * 60)
    
    # Walk through all directories and subdirectories
    for root, dirs, files in os.walk(input_dir):
        for filename in files:
            if filename.endswith('.jsonl'):
                file_path = os.path.join(root, filename)
                
                # Get relative path for cleaner output
                relative_path = os.path.relpath(file_path, input_dir)
                
                analyzed, correct, problematic, problematic_details = analyze_comments_from_jsonl(file_path)
                
                # Add to totals
                total_analyzed += analyzed
                total_correct += correct
                total_problematic += problematic
                
                # Add problematic details (limit total to reasonable number)
                if len(all_problematic_details) < 200:
                    for detail in problematic_details:
                        if len(all_problematic_details) < 200:
                            detail['File'] = relative_path  # Add file info
                            all_problematic_details.append(detail)
                
                print(f"File: {relative_path}")
                print(f"  Analyzed: {analyzed}, Correct: {correct}, Problematic: {problematic}")
                
                # Show some problematic examples for this file
                if problematic_details and len(problematic_details) <= 5:
                    print("  Problematic examples:")
                    for comment in problematic_details:
                        print(f"    ID: {comment['CommentID']}, Level: {comment['Level']}")
                        print(f"    Text: {comment['CommentText'][:100]}...")
                elif problematic_details:
                    print(f"  (Showing first 3 of {len(problematic_details)} problematic examples)")
                    for comment in problematic_details[:3]:
                        print(f"    ID: {comment['CommentID']}, Level: {comment['Level']}")
                        print(f"    Text: {comment['CommentText'][:100]}...")
                print()
    
    # Print summary
    print("=" * 60)
    print("SUMMARY:")
    print(f"Total Analyzed: {total_analyzed}")
    print(f"Total Correct: {total_correct}")
    print(f"Total Problematic: {total_problematic}")
    if total_analyzed > 0:
        print(f"Problematic Percentage: {(total_problematic/total_analyzed)*100:.2f}%")
    
    print(f"\nShowing up to {len(all_problematic_details)} problematic examples across all files:")
    print("-" * 60)
    for i, comment in enumerate(all_problematic_details[:50], 1):  # Show max 50
        print(f"{i}. File: {comment['File']}")
        print(f"   ID: {comment['CommentID']}, Level: {comment['Level']}")
        print(f"   Text: {comment['CommentText'][:150]}...")
        print()

# Example usage - analyze entire directory
input_directory = 'Path_to/Def'
analyze_directory(input_directory)
