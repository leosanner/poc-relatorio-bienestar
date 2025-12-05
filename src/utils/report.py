from utils.prosync import extract_prosync_content
from utils.oberon import extract_oberon_content, format_file_name, important_microrganisms
from pathlib import Path
from docxtpl import DocxTemplate, RichText
from datetime import datetime
from io import BytesIO
from utils.find_most_related_term import find_related_term

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


def oberon_table_content(oberon_obj: dict, thershold_ranges: dict):
    table_obj = {
        "content": [],
    }

    for test_name, test_value in oberon_obj.items():

        t_range = thershold_ranges.get(test_name, [0.0, 1.0])
        t_range = [float(x) for x in t_range]

        for value_name, value in test_value.items():

            if inside_interval(float(value), t_range):
                table_obj["content"].append(
                    [test_name.title(), value_name.title(), value]
                )

    return table_obj


def prosync_table_content(prosync_obj: list[dict], gen_report=False):
    docx_obj_template = {
            'nome': '',
            'tipo': '',
            'sintomas':'',
            'D': ''
    }
    
    table_obj = {"test": [], "value": []}
    formatted_docx = []
    control = prosync_obj[0].get("D")

    if gen_report:
        prosync_obj.pop(0)

    for data in prosync_obj:
        d = data.get("D")
        table_obj["test"].append(data.get("nome").title())
        table_obj["value"].append(f"{d}/{control}")

        docx_obj = docx_obj_template.copy()
        docx_obj['nome'] = data.get('nome').title()
        docx_obj['tipo'] =  data.get('tipo').title()
        docx_obj['sintomas'] = data.get('sintomas')
        docx_obj['D'] = f"{d}/{control}"

        formatted_docx.append(docx_obj)

    return table_obj, formatted_docx


def generate_report(prosync_data, oberon_data, oberon_thresholds, patient_name):

    if not REPORT_TEMPLATE_PATH.exists():
        print(f"Template not found at {REPORT_TEMPLATE_PATH}")
        return

    context = {
        "date": datetime.now().strftime("%d/%m/%Y"),
        "name": patient_name,
        "table_prosync": [], 
        "table_toxins": [],
        "table_microorganism": [],
        "table_crystals": [],
        "table_food": {},
        "table_emotions": {},
    }

    if prosync_data:
        context["table_prosync"] = prosync_data

    # Process Oberon
    for category, data in oberon_data.items():
        threshold = oberon_thresholds.get(category, [0.0, 1.0])
        min_d, max_d = float(threshold[0]), float(threshold[1])

        if category == "toxinas":
            # List of dicts
            filtered = []
            if isinstance(data, list):
                for item in data:
                    d_val = float(item.get("D", -1))
                    if min_d <= d_val <= max_d:
                        filtered.append(item)
            context["table_toxins"] = filtered

        elif category == "microrganismos":
            # List of dicts
            filtered = []
            if isinstance(data, list):
                for item in data:
                    d_val = float(item.get("D", -1))
                    if 0.35 <= d_val <= 0.45:
                        item["D"] = RichText(str(d_val), color="#FFA500")

                    if find_related_term(
                        item.get('nome'), important_microrganisms
                    ):
                        filtered.append(item)
                        continue

                    if min_d <= d_val <= max_d:
                        filtered.append(item)
            context["table_microorganism"] = filtered

        elif category == "cristais":
            # List of dicts
            filtered = []
            if isinstance(data, list):
                for item in data:
                    d_val = float(item.get("D", -1))
                    if min_d <= d_val <= max_d:
                        filtered.append(item)
            context["table_crystals"] = filtered

        elif category == "alimentos":
            # Dict {Name: Value}
            filtered = {}
            if isinstance(data, dict):
                for k, v in data.items():
                    try:
                        d_val = float(v)
                        if min_d <= d_val <= max_d:
                            filtered[k] = v
                    except ValueError:
                        pass
            context["table_food"] = filtered

        elif category == "emocoes":
            # Dict {Name: Value}
            filtered = {}
            if isinstance(data, dict):
                for k, v in data.items():
                    try:
                        d_val = float(v)
                        if min_d <= d_val <= max_d:
                            filtered[k] = v
                    except ValueError:
                        pass
            context["table_emotions"] = filtered

    doc = DocxTemplate(REPORT_TEMPLATE_PATH)
    doc.render(context)

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    return buffer
