from utils.prosync import extract_prosync_content
from utils.oberon import extract_oberon_content, format_file_name
from pathlib import Path
from docxtpl import DocxTemplate
from datetime import datetime
from io import BytesIO

current_path = Path(__file__)
ROOT = current_path.parent.parent
REPORT_TEMPLATE_PATH = ROOT / 'assets/report/template_relatorio.docx'

def process_input_content(
    prosync_file: Path,
    oberon_files: list[Path],
    prosync_threshold: float,
    oberon_threshold: float
):
    summary_results = {
        'prosync': {},
        'oberon': {}
    }
    
    summary_results['prosync'] = extract_prosync_content(prosync_file)
    
    for oberon_file in oberon_files:
        formated_file_name = format_file_name(oberon_file.name)
        summary_results['oberon'][formated_file_name] = extract_oberon_content(oberon_file)

    return summary_results

def oberon_table_content(oberon_obj:dict):
    table_obj = {
        'content': [],
    }

    for test_name, test_value in oberon_obj.items():
        for value_name, value in test_value.items():
            table_obj['content'].append([
                test_name,
                value_name,
                value
            ])

    return table_obj

def prosync_table_content(prosync_obj:dict):
    table_obj = {
        'content': [],
    }

    for test_name, test_value in prosync_obj.items():
        table_obj['content'].append([
            test_name,
            test_value
        ])

    return table_obj


def generate_report(
    table_prosync_obj,
    table_oberon_obj,
    name):
    if not REPORT_TEMPLATE_PATH.exists():
        print(f'Template not found at {REPORT_TEMPLATE_PATH}')
        return

    context = {
        'date': datetime.now().strftime('%d/%m/%Y'),
        'table_prosync': table_prosync_obj,
        'table_oberon': table_oberon_obj,
        'name': name
    }

    doc = DocxTemplate(REPORT_TEMPLATE_PATH)
    doc.render(context)
    
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    
    return buffer
