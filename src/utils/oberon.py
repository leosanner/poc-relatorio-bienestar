from pathlib import Path
import os

current_path = Path(__file__)
ROOT = current_path.parent.parent
OBERON_DATA_PATH = ROOT / 'assets/oberon'
FILE_NAME = 'example.txt'


def load_txt(path, encoding = 'utf-8'):
    if hasattr(path, 'read'):
        content = path.read()
        if isinstance(content, bytes):
            return content.decode(encoding)
        return content

    with open(path, 'r', encoding=encoding) as file:
        return file.read()


def format_file_name(file_name):
    file_name = file_name.replace('.txt', '')
    file_name = file_name.split('-')[1]
    return file_name.lower().strip()

def extract_row_content(row:str, term="D="):
    idx = row.find(term)

    if idx == -1:
        return row

    return (
        row[:idx], term, row[idx + len(term):len(row) -1]
    )

def extract_oberon_content(file_path, enc='utf-8'):
    txt = load_txt(file_path, enc)
    content = []

    for row in txt.splitlines():
        for token in row.split():
            if "D=" in token:
                content.append(
                    extract_row_content(row.strip())
                )

    content = {
        line[0]: line[2]
        for line in content
    }

    return content


if __name__ == "__main__":
    print(
        extract_oberon_content(OBERON_DATA_PATH / FILE_NAME,)
    )