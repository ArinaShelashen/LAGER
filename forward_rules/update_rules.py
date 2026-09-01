import glob

# Change "*.gml" if your rule files have a different extension
for filepath in glob.glob("*.gml"):
    with open(filepath, 'r') as file:
        lines = file.readlines()

    new_lines = []
    modified = False

    for line in lines:
        if line.strip().startswith('left ['):
            # 1. Check if we already added labelType "term" right above this
            # (Checks backwards through new_lines, ignoring blank lines)
            already_added = False
            for j in range(len(new_lines) - 1, -1, -1):
                prev_line = new_lines[j].strip()
                if not prev_line:
                    continue
                if prev_line == 'labelType "term"':
                    already_added = True
                break

            # 2. If it's not there, insert it with matching indentation
            if not already_added:
                indent = line[:len(line) - len(line.lstrip())]
                new_lines.append(f'{indent}labelType "term"\n')
                modified = True

        # 3. Always append the current line
        new_lines.append(line)

    # Overwrite the file only if changes were made
    if modified:
        with open(filepath, 'w') as file:
            file.writelines(new_lines)
        print(f"Updated: {filepath}")
    else:
        print(f"Skipping: {filepath} (already updated or no rules found)")