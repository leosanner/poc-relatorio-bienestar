from utils.prosync import extract_prosync_content
from utils.oberon import extract_oberon_content, format_file_name
from pathlib import Path
from docxtpl import DocxTemplate
from datetime import datetime
from io import BytesIO

current_path = Path(__file__)
ROOT = current_path.parent.parent
REPORT_TEMPLATE_PATH = ROOT / "assets/report/template_relatorio.docx"


def inside_interval(val, interval):
    if val < interval[0] or val > interval[1]:
        return False

    return True


def process_input_content(
    prosync_file: Path,
    oberon_files: list[Path],
):
    summary_results = {"prosync": {}, "oberon": {}}

    summary_results["prosync"] = extract_prosync_content(prosync_file)

    for oberon_file in oberon_files:
        formated_file_name = format_file_name(oberon_file.name)
        summary_results["oberon"][formated_file_name] = extract_oberon_content(
            oberon_file
        )

    return summary_results


def oberon_table_content(oberon_obj: dict, thershold_range: list):
    table_obj = {
        "content": [],
    }

    thershold_range = [float(x) for x in thershold_range] 

    for test_name, test_value in oberon_obj.items():
        for value_name, value in test_value.items():

            if inside_interval(float(value), thershold_range):
                table_obj["content"].append([test_name.title(), value_name.title(), value])

    return table_obj


def prosync_table_content(prosync_obj: dict, std: float = 0.1):
    table_obj = {
        "content": [],
    }

    control = prosync_obj.get("controle")
    var = control * std
    range_control = [control - var, control + var]

    for test_name, test_value in prosync_obj.items():
        r = "Negativo" if inside_interval(test_value, range_control) else "Positivo"

        table_obj["content"].append([test_name, test_value, r])

    return table_obj


def generate_report(table_prosync_obj, table_oberon_obj, name):
    if not REPORT_TEMPLATE_PATH.exists():
        print(f"Template not found at {REPORT_TEMPLATE_PATH}")
        return

    context = {
        "date": datetime.now().strftime("%d/%m/%Y"),
        "table_prosync": table_prosync_obj,
        "table_oberon": table_oberon_obj,
        "name": name,
    }

    doc = DocxTemplate(REPORT_TEMPLATE_PATH)
    doc.render(context)

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    return buffer
