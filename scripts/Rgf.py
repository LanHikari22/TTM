#!/usr/bin/env python3

# TODO: need to get line and ripgrep, pipe it to this, make a vim function nthat handles all that
# nnoremap <C-Y> :Rgf <c-r><c-w><cr>

import sys
import os
import re
import json

def extract_line_number(file_path, regex_pattern):
    """Extract line number from a file based on the regex pattern."""
    try:
        # Escape special characters in regex_pattern for literal match
        escaped_pattern = re.escape(regex_pattern)
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for idx, line in enumerate(f, 1):
                if re.match(escaped_pattern, line):
                    return idx
    except Exception as e:
        pass
    return None

def parse_tags(tags_file):
    """Parse the tags and store the essential information."""
    all_tags = []
    with open(tags_file, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) < 3:
                continue
            func_name, path, pattern = parts[:3]
            regex = pattern.strip("/^$").replace("\\/", "/")
            lineno = extract_line_number(path, regex)
            if lineno is not None:
                tag_entry = {
                    "function": func_name,
                    "path": path,
                    "regex": regex,
                    "lineno": lineno
                }
                all_tags.append(tag_entry)
    all_tags.sort(key=lambda x: (x['path'], x['lineno']))
    return all_tags

def find_function(all_tags, file_path, line_number):
    """Find the nearest function for a given file and line number."""
    tags_for_file = [tag for tag in all_tags if tag['path'] == file_path]
    last_func = None
    for tag in tags_for_file:
        if tag['lineno'] <= line_number:
            last_func = tag['function']
        else:
            break
    return last_func

def main():
    tags_file = os.path.join(os.getcwd(), "tags")
    all_tags = parse_tags(tags_file)

    # Save as JSON for later use
    with open("tags.json", "w") as f:
        json.dump(all_tags, f, indent=4)

    for line in sys.stdin:
        # Strip ANSI codes for processing
        stripped_line = re.sub(r'\x1b[^m]*m', '', line)
        
        # Extract path, line number, and column number from the stripped line
        path, lineno_str, colno_str, _ = stripped_line.split(":", 3)
        
        lineno = int(lineno_str)
        func = find_function(all_tags, path, lineno) or 'UNKNOWN'

        # Don't annotate header files, just print them
        if path.endswith('.h'):
            print(line.strip())
            continue
        
        # Split the original line and construct the output
        parts = line.split(':', 3)
        print(f"{parts[0]}:{parts[1]}:{parts[2]}:  {func}(): {parts[3].strip()}")

if __name__ == "__main__":
    main()
