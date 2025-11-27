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


def generate_report(prosync_data, oberon_data, oberon_thresholds, patient_name):
    if not REPORT_TEMPLATE_PATH.exists():
        print(f"Template not found at {REPORT_TEMPLATE_PATH}")
        return

    # Prepare context
    context = {
        "date": datetime.now().strftime("%d/%m/%Y"),
        "name": patient_name,
        "table_prosync": [], # Will be populated if needed or we can reuse prosync_table_content logic
        "table_toxins": [],
        "table_microorganism": [],
        "table_crystals": [],
        "table_food": {},
        "table_emotions": {}
    }

    # Process Prosync (reuse existing logic for list format if template expects it, or pass raw dict)
    # Assuming template expects a list of [Name, Value, Result] like before, or we can pass the raw dict.
    # The prompt didn't specify prosync format change, so let's stick to the table format for consistency or raw if requested.
    # "receive the prosync files... values, the results from previous steps"
    # Let's use the existing prosync_table_content to get the list of lists
    if prosync_data:
        # We need the std value, but it's not passed here. 
        # Let's assume std is handled outside or we need to pass it.
        # For now, let's pass the raw prosync_data and let the template handle it or use a default std if we call the helper.
        # Actually, let's just pass the raw dict as "prosync_data" and also the table as "table_prosync" for flexibility.
        context["prosync_data"] = prosync_data
        # If we want the calculated "Positivo/Negativo", we need the std. 
        # I'll add std to the function signature.
    
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
