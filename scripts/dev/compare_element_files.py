# compare two json list files by filtering out uuids and comparing the rest of the content
import re
import sys

uuid_pattern = r'[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}'


def read_file(file_path):
    with open(file_path, 'r') as file:
        lines = []
        for line in file.readlines():
            line = re.sub(uuid_pattern, '', line)
            lines.append(line)
    return lines


def diff_files_ignore_uuid(file1, file2):
    lines1 = read_file(file1)
    lines2 = read_file(file2)
    return lines1 == lines2


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python compare_element_files.py file1 file2')
        sys.exit(1)

    file1 = sys.argv[1]
    file2 = sys.argv[2]

    if diff_files_ignore_uuid(file1, file2):
        print('Files are equal')
        rv = 0
    else:
        print('Files are different')
        rv = 1
sys.exit(rv)
