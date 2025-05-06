import csv
import re

input_file = 'input_abnormal.txt'
output_file = 'output_abnormal.csv'

# Read the full content
with open(input_file, 'r') as f:
    lines = f.readlines()

# Group lines into blocks using the DEBUG line as the start
blocks = []
current_block = []
for line in lines:
    if 'DEBUG -' in line:
        if current_block:
            blocks.append(current_block)
        current_block = [line.strip()]
    else:
        current_block.append(line.strip())
if current_block:
    blocks.append(current_block)

# Define headers
headers = [
    'Timestamp',
    # 'Capsule Index',
    'Length',
    # 'Length Range Low', 'Length Range High', 'Length Normal',
    'Width',
    'Area',
    # 'Area Range Low', 'Area Range High', 'Area Normal',
    'Contour Similarity Overall', 'Contour Similarity Head', 'Contour Similarity Tail',
    # 'Similarity Overall', 'Similarity Head', 'Similarity Tail',
    'Local Defect Length',
    'Partial Defect Detected'
]

# Parser for each block
def parse_block(block):
    ts_match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - DEBUG - (\d+) of \d+ capsules:', block[0])
    timestamp = ts_match.group(1)
    capsule_index = ts_match.group(2)

    length_match = re.search(r'Length:\s*([\d.]+).*?\(([\d.]+),\s*([\d.]+)\)', block[1])
    width_match = re.search(r'Width:\s*([\d.]+)', block[1])
    length_normal = block[2].split(":")[1].strip()

    area_match = re.search(r'Area:\s*([\d.]+).*?\(([\d.]+),\s*([\d.]+)\)', block[3])
    area_normal = block[4].split(":")[1].strip()

    contour_similarities = re.findall(r'[\d.]+', block[5])
    similarities = [val.strip() for val in block[6].split(":")[1].split(",")]

    local_defect_match = re.search(r'Local Defect Length:\s*([\d.]+)', block[7])
    local_defect_length = local_defect_match.group(1) if local_defect_match else ''

    partial_defect = block[8].split(":")[1].strip()

    return [
        timestamp,
        # capsule_index,
        length_match.group(1),
        # length_match.group(2), length_match.group(3), length_normal,
        width_match.group(1),
        area_match.group(1),
        # area_match.group(2), area_match.group(3), area_normal,
        *contour_similarities,
        # *similarities,
        local_defect_length,
        partial_defect
    ]

# Parse all blocks
rows = [parse_block(block) for block in blocks]

# Write CSV
with open(output_file, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(headers)
    writer.writerows(rows)

print(f"Parsed {len(rows)} blocks and saved to '{output_file}'")
