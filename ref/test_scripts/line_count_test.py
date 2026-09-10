import os

# This script counts the number of lines of code in the scripts in the /src directory and prints the total number of lines.

def count_lines_in_directory(directory):
    """Count code lines and comment lines in all .py files in a directory."""
    total_code_lines = 0
    total_comment_lines = 0
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                code_lines, comment_lines = count_lines_in_file(file_path)
                total_code_lines += code_lines
                total_comment_lines += comment_lines
    return total_code_lines, total_comment_lines

def count_lines_in_file(file_path):
    """Count code lines and comment lines in a single file."""
    code_lines = 0
    comment_lines = 0
    with open(file_path, 'r') as file:
        for line in file:
            stripped = line.strip()
            if not stripped:
                continue
            if line.lstrip().startswith('#'):
                comment_lines += 1
            else:
                code_lines += 1
    return code_lines, comment_lines

if __name__ == "__main__":
    src_directory = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', '..', 'src')
    )
    total_lines, total_comment_lines = count_lines_in_directory(src_directory)
    print(f"\nTotal lines of code in /src directory: {total_lines}")
    print(f"\nTotal lines of comments in /src directory: {total_comment_lines}\n")