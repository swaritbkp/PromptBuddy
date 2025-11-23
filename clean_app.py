import os

# Read the file
with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Keep lines up to 716 (0-indexed, so 716 lines total)
clean_lines = lines[:716]

# Write back
with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(clean_lines)
    f.write('\n')

print("File cleaned successfully")
