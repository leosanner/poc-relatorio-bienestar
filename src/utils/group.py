"""Group processing utilities (F-03).

Pure-Python comparison/partition logic and content-dict builders for shared and
individual documents. Dependency-free (only ``re``, ``dataclasses``,
``datetime``) so it can be reused by every existing generator without pulling in
heavy dependencies.
"""

import re
from dataclasses import dataclass
from datetime import datetime

DEFAULT_COMPARE_CATEGORIES = ("microorganisms", "toxins")

# Which content-dict keys feed each comparison category. Keep this as the single
# extensibility point so more categories can be added later (INV-07).
CATEGORY_CONTENT_KEYS = {
    "microorganisms": ("table_prosync", "table_microorganism"),
    "toxins": ("table_toxins",),
}


def normalize_name(value) -> str:
    """Lowercase + collapse internal whitespace + strip."""
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


@dataclass
class GroupPartition:
    common_elements: dict          # category -> representative rows common to ALL patients
    per_patient_unique: list       # one dict per patient: category -> that patient's unique rows


def extract_category_elements(patient_content: dict, category: str) -> list:
    """Gather rows from ``CATEGORY_CONTENT_KEYS[category]`` (in key order),
    deduped by ``normalize_name(row["nome"])`` with first occurrence winning
    (RN-04 representative). Rows with empty/missing ``nome`` are skipped.

    A ``None`` patient (e.g. one that failed processing) is treated as empty so a
    single failed patient never aborts the whole group partition (RF-12).
    """
    patient_content = patient_content or {}
    rows = []
    seen = set()
    for key in CATEGORY_CONTENT_KEYS.get(category, ()):
        for row in patient_content.get(key) or []:
            name = normalize_name(row.get("nome"))
            if not name or name in seen:
                continue
            seen.add(name)
            rows.append(row)
    return rows


def partition_group_elements(
    patients_content: list, compare_categories=DEFAULT_COMPARE_CATEGORIES
) -> GroupPartition:
    """Partition each category's elements into a common set (present in ALL
    patients, RN-03/INV-04) and per-patient unique remainders.

    The common representative row is taken from the FIRST patient (in list order)
    that contains that element (RN-04). Name ordering follows the order in which
    names first appear across patients for determinism.
    """
    patients_content = list(patients_content or [])
    num_patients = len(patients_content)

    # Per-category extracted rows for each patient.
    extracted = [
        {cat: extract_category_elements(pc, cat) for cat in compare_categories}
        for pc in patients_content
    ]

    common_elements = {cat: [] for cat in compare_categories}
    common_names = {cat: set() for cat in compare_categories}

    for cat in compare_categories:
        # Track, per normalized name, the count of patients that have it and the
        # representative row (first patient that has it). Preserve first-seen order.
        counts = {}
        representatives = {}
        order = []
        for patient_rows in extracted:
            for row in patient_rows[cat]:
                name = normalize_name(row.get("nome"))
                if name not in counts:
                    counts[name] = 0
                    representatives[name] = row
                    order.append(name)
                counts[name] += 1

        if num_patients == 0:
            continue

        for name in order:
            if counts[name] == num_patients:
                common_elements[cat].append(representatives[name])
                common_names[cat].add(name)

    per_patient_unique = []
    for patient_rows in extracted:
        unique = {}
        for cat in compare_categories:
            unique[cat] = [
                row
                for row in patient_rows[cat]
                if normalize_name(row.get("nome")) not in common_names[cat]
            ]
        per_patient_unique.append(unique)

    return GroupPartition(
        common_elements=common_elements,
        per_patient_unique=per_patient_unique,
    )


def format_shared_name(patient_names: list) -> str:
    """Format the shared-document name label (RN-09)."""
    names = [str(n).strip() for n in (patient_names or []) if str(n).strip()]
    return "Compartilhado: " + ", ".join(names)


def build_shared_content(common_elements: dict, patient_names: list) -> dict:
    """Content dict for shared protocolo/orcamento/controle. No extra sessions
    (RN-08). Missing categories are tolerated via ``.get``.
    """
    common_elements = common_elements or {}
    return {
        "name": format_shared_name(patient_names),
        "table_prosync": [],
        "table_microorganism": list(common_elements.get("microorganisms", [])),
        "table_toxins": list(common_elements.get("toxins", [])),
        "extra_sessions": [],
        "extra_session_prices": {},
    }


def build_individual_content(
    unique_elements: dict,
    extra_sessions: list,
    patient_name: str,
    extra_session_prices: dict = None,
) -> dict:
    """Per-patient treatment content (RN-06). ``unique_elements`` is one entry of
    ``GroupPartition.per_patient_unique``.
    """
    unique_elements = unique_elements or {}
    return {
        "name": patient_name,
        "table_prosync": [],
        "table_microorganism": list(unique_elements.get("microorganisms", [])),
        "table_toxins": list(unique_elements.get("toxins", [])),
        "extra_sessions": extra_sessions or [],
        "extra_session_prices": extra_session_prices or {},
    }


def build_individual_report_content(
    unique_micro: list,
    unique_toxins: list,
    other_categories: dict,
    patient_name: str,
) -> dict:
    """Per-patient relatorio content (RN-07): unique micro + unique toxins + ALL
    uncompared categories (crystals/food/emotions/patologies).
    """
    content = dict(other_categories or {})
    content.update(
        {
            "name": patient_name,
            "table_prosync": [],
            "table_microorganism": list(unique_micro or []),
            "table_toxins": list(unique_toxins or []),
            "date": datetime.now().strftime("%d/%m/%Y"),
        }
    )
    return content
