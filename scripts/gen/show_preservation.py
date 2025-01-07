# one time use script that is safe to ignore
# consumed the output of check_similarity_preservation.py
# and restructured it into a tabular format

from collections import defaultdict

# Reprocess the uploaded text file to create a structured tabular format

file_path = 'linear_results_preservation.txt'

# Parsing the file to structure data into a DataFrame

cols = []
rows = []
scores = defaultdict(dict)

with open(file_path, 'r') as file:
    lines = file.readlines()


def get_key(line):
    file_name = line.split(":")[1].strip()
    parts = file_name.split("_")
    dim = parts[2]
    stype = parts[3] if len(parts) == 5 else 'float32'
    # print(dim, stype, line)
    return dim, stype


current_original_file = None
for line in lines:
    line = line.strip()
    if line.startswith("Original File:"):
        col = get_key(line)
        if col not in cols:
            cols.append(col)
    elif line.startswith("Transformed File:"):
        row = get_key(line)
        if row not in rows:
            rows.append(row)
    elif line.startswith("Preservation Score:"):
        preservation_score = float(line.split(":")[1].strip())
        scores[col][row] = preservation_score

first_order = ['float32', 'float16', 'int8', 'uint8']
second_order = ['768', '512', '256', '128']

cols.sort(key=lambda x: (second_order.index(x[0]), first_order.index(x[1])))
rows.sort(key=lambda x: (second_order.index(x[0]), first_order.index(x[1])))

records = []
record = [f'"{p}"' for p in cols]
record.insert(0, '')
records.append(record)

for row in rows:
    record = list()
    record.append(f'"{row}"')
    print(f"R: {row}")
    for col in cols:
        print(f"\tL: {col}", end=' ->')
        value = scores[col].get(row, '')
        print(value)
        record.append(value)
    records.append(record)

print("\n".join("\t".join(str(x) for x in record) for record in records))
