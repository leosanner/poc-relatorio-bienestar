# F-03 - Processamento em Grupo (2-3 Pacientes)

## Scope

**In scope:**
- Add a new `Processamento em Grupo` tab alongside the existing `Processamento` and `Dados do Sistema` tabs, without changing the single-patient tab.
- Let staff input 2 or 3 patients in one flow, each with the same fields as the single-patient tab (nome, Prosync, 6 Oberon TXT + thresholds, `prosync_std`, sessoes extras, selectable tables).
- Compare the patients' selected treatment elements (microrganismos + metais/toxinas) to find what is common to ALL patients.
- Generate shared `protocolo`, `orcamento`, and `controle` for the common treatment elements (once for the group).
- Generate per-patient `protocolo`, `orcamento`, and `controle` for each patient's unique treatment elements + that patient's extra sessions.
- Generate a per-patient `relatorio` containing the patient's unique micro/toxinas plus all of their crystals/food/emotions/patologies.
- Reuse the existing generators (`report`, `protocol`, `budget`, `control`) by feeding them different content dicts.
- Build the comparison/partition logic so the compared category list is extensible for the future.

**Out of scope:**
- Anamnesis lookup in the group tab (deferred to a later version).
- A shared `relatorio` document for the group.
- Comparison of crystals/food/emotions/patologies categories (only micro + toxins are compared in this version).
- Subgroup logic (elements common to only 2 of 3 patients are NOT treated as shared; only all-patients-common counts).
- Mixing clinics within a group; one clinic applies to the whole group.
- Persisting group attendances, exposing a ZIP download, or any administrative screen.

## Context & Motivation

The client wants to run treatment protocols for 2-3 patients at once, producing unified documents for what the patients have in common and individualized documents for the rest. Today `src/app.py` only processes one patient per run and emits four DOCX (`protocolo`, `orcamento`, `controle`, `relatorio`), all derived from a single `protocol_content` dict.

Because `protocolo`, `orcamento`, and `controle` all derive from the same content dict (`table_prosync`, `table_microorganism`, `table_toxins`, `extra_sessions`, `name`, ...), the feature can be implemented by partitioning the selected treatment elements into a "common" set and per-patient "unique" sets, then building separate content dicts and reusing every existing generator unchanged.

## Business Rules

- RN-01: A group has exactly 2 or 3 patients, all from the same clinic. The clinic is chosen once for the group.
- RN-02: Comparison runs only over microrganismos (Prosync + Oberon unified) and metais/toxinas, using each patient's manually selected rows.
- RN-03: An element is "common" only when present in ALL patients of the group, matched by normalized name (lowercase + collapsed whitespace), regardless of Prosync/Oberon origin.
- RN-04: The representative row used in shared documents is taken from the first patient that has the element (type/frequency are identical because it is the same element).
- RN-05: Common micro/toxins generate shared `protocolo`, `orcamento`, and `controle` (one set for the group).
- RN-06: Each patient's remaining (unique) micro/toxins plus that patient's extra sessions generate per-patient `protocolo`, `orcamento`, and `controle`.
- RN-07: The per-patient `relatorio` contains the patient's unique micro + unique toxins + ALL of their crystals/food/emotions/patologias (the uncompared categories are always shown because "unique" is undefined for them in this version).
- RN-08: Extra sessions are selected per patient and only appear in that patient's individual documents; shared documents have no extra sessions.
- RN-09: Shared documents set the `name` field to a list of the group's patient names (e.g. `Compartilhado: Ana, Bruno, Carla`). No template changes are required.
- RN-10: A configurable global multiplier (default `1.0`) is applied to the unit price of shared sessions, reflected in the shared orcamento rows and total and in the shared protocolo `total_pix`/`total_card`.
- RN-11: Session line numbering, the "Sessao intermediaria" cadence (every 9 sessions), and control week numbering (starting at 10) are computed independently per document, from scratch.
- RN-12: Empty documents are not generated. If there is no common set, the three shared documents are skipped with a notice. If a patient has no unique treatment elements (and no extra sessions), that patient's individual treatment documents are skipped.
- RN-13: Generated files are presented in sections (`Compartilhado` + one per patient) using the existing data-uri download links.

## Functional Requirements

- [ ] RF-01: A third tab `Processamento em Grupo` is added; the existing single-patient tab is unchanged.
- [ ] RF-02: The group tab shows, at the top, a single clinic selector and a patient count selector (2 or 3).
- [ ] RF-03: One sub-tab (`st.tabs`) per patient renders the full single-patient form: nome, Prosync upload, 6 Oberon uploads with min/max D, `prosync_std`, extra sessions, and the selectable tables.
- [ ] RF-04: All widget and `st.session_state` keys in the group tab are namespaced by patient index to avoid collisions across sub-tabs.
- [ ] RF-05: A single `Gerar documentos do grupo` button triggers processing for all patients and the comparison.
- [ ] RF-06: Each patient is processed exactly as in the single-patient flow to produce its `protocol_and_report_content` from selected rows.
- [ ] RF-07: The app partitions the selected micro/toxins into a common set (present in all patients) and per-patient unique sets, matched by normalized name.
- [ ] RF-08: When a common set exists, the app generates shared `protocolo`, `orcamento`, and `controle` from a content dict containing only the common elements, with the group name and the shared-session multiplier.
- [ ] RF-09: For each patient, the app generates `protocolo`, `orcamento`, and `controle` from that patient's unique elements + extra sessions, skipping any that would be empty.
- [ ] RF-10: For each patient, the app generates a `relatorio` containing unique micro + unique toxins + all crystals/food/emotions/patologias.
- [ ] RF-11: The UI shows results in a `Compartilhado` section plus one section per patient, each with the existing download links; missing documents show a clear notice instead of a broken link.
- [ ] RF-12: Per-patient processing errors are surfaced per patient and do not abort the rest of the group.

## System Flow

1. `src/app.py` renders the `Processamento em Grupo` tab with a top-level clinic selector and a patient count selector (2 or 3).
2. `src/app.py` renders one `st.tabs` sub-tab per patient, each containing the single-patient input form with patient-index-namespaced keys.
3. Staff fill each patient's inputs and make manual selections in the selectable tables, then click `Gerar documentos do grupo`.
4. For each patient, `src/app.py` builds the per-patient `protocol_and_report_content` from the selected Prosync/Oberon rows, thresholds, and extra sessions, reusing the existing processing helpers.
5. A new group utility partitions the selected micro/toxins across patients into a common set (names present in all patients) and per-patient unique sets, using normalized-name matching and the first-patient representative row.
6. If the common set is non-empty, `src/app.py` builds a shared content dict (common elements only, group name, no extra sessions) and generates shared `protocolo`, `orcamento`, and `controle`, applying the shared-session price multiplier.
7. For each patient, `src/app.py` builds an individual content dict (unique elements + that patient's extra sessions) and generates `protocolo`, `orcamento`, and `controle`, skipping empty ones.
8. For each patient, `src/app.py` builds a report content dict (unique micro + unique toxins + all crystals/food/emotions/patologias) and generates the `relatorio`.
9. `src/app.py` renders the `Compartilhado` section and per-patient sections with the existing data-uri download links, and notices where a document was skipped.

## Invariants / Non-negotiables

- INV-01: The existing single-patient `Processamento` tab behavior and outputs must not change.
- INV-02: All patients in a group share one clinic; there is one authoritative clinic state for the group.
- INV-03: Comparison uses each patient's manually selected rows only, never the full unfiltered results.
- INV-04: An element is shared only when common to ALL patients; partial-overlap subgroups are never produced in this version.
- INV-05: Empty documents are never generated.
- INV-06: The existing DOCX templates are not modified; the group feature only changes the content dicts passed to the generators.
- INV-07: The comparison logic is parameterized by the list of compared categories so report categories and a shared relatorio can be added later without restructuring.

## Technical Design

### Entities / Models

| Model | Key fields | Notes |
|-------|------------|-------|
| GroupPatientInput | `index`, `patient_name`, `prosync_file`, `oberon_files`, `oberon_thresholds`, `prosync_std`, `selected_extra_sessions` | One patient's raw inputs in the group tab. |
| PatientProcessedContent | `protocol_and_report_content` (`table_prosync`, `table_microorganism`, `table_toxins`, `extra_sessions`, `extra_session_prices`, `name`, ...) | Per-patient processed content, same shape used today. |
| GroupPartition | `common_elements`, `per_patient_unique` | Output of the comparison: common set (representative rows) and each patient's unique remainder. |

### Endpoints / Interfaces (if applicable)

| Method | Route / Signature | Description |
|--------|-------------------|-------------|
| N/A | Streamlit UI action: `Gerar documentos do grupo` | Processes all patients, runs the comparison, and generates the documents. |
| Function | `partition_group_elements(patients_content, compare_categories) -> GroupPartition` | Splits selected micro/toxins into common and per-patient-unique sets by normalized name. |
| Function | `build_shared_content(common_elements, patient_names) -> dict` | Builds the shared content dict (group name, no extra sessions). |
| Function | `build_individual_content(unique_elements, extra_sessions, patient_name) -> dict` | Builds a per-patient content dict for treatment documents. |
| Function | `build_individual_report_content(unique_micro, unique_toxins, other_categories, patient_name) -> dict` | Builds the per-patient report content. |

### Key Modules

- `src/app.py` - Render the new tab, the per-patient sub-tabs (reusing extracted form/processing helpers), trigger generation, and render the sectioned download UI.
- `src/utils/group.py` (new) - Own the comparison/partition logic and content-dict builders for shared and individual documents; parameterized by compared categories.
- `src/utils/protocol.py` / `src/utils/budget.py` - Add an optional `multiplier=1.0` parameter (backward compatible) applied to shared-session unit prices.
- `tests/test_group.py` (new) - Cover normalized-name matching, all-patients-common rule, first-patient representative, unique remainders, empty-set handling, and the multiplier.

### Refactor

- Extract from `src/app.py` the inline per-patient input rendering, per-patient processing (Prosync/Oberon -> selected content), and document generation into reusable helpers so both the single-patient tab and the group tab share them.

## Dependencies

- **Prerequisite features:** None new; builds on the existing generators and F-01 extra-sessions catalog.
- **External packages added:** N/A.
- **External services:** Existing Google Sheets extra-sessions catalog (read-only) per clinic.
- **Environment variables / secrets:** N/A new.

## Acceptance Criteria

1. A `Processamento em Grupo` tab exists and the single-patient tab is unchanged.
2. The group tab accepts 2 or 3 patients, one clinic for the group, with a full input form per patient in sub-tabs.
3. Clicking `Gerar documentos do grupo` processes every patient using their manual selections.
4. Micro/toxins common to ALL patients (by normalized name) produce shared `protocolo`, `orcamento`, and `controle` with the group name.
5. Each patient's unique micro/toxins + extra sessions produce that patient's individual `protocolo`, `orcamento`, and `controle`.
6. Each patient's `relatorio` shows unique micro + unique toxins + all crystals/food/emotions/patologias.
7. The shared-session multiplier (default 1.0) scales shared orcamento rows/total and shared protocolo totals; the default has no effect until changed.
8. No common set skips the shared documents with a notice; a patient with no unique elements skips their individual treatment documents.
9. Numbering, midterm cadence, and control weeks are independent per document.
10. Results appear in a `Compartilhado` section plus one section per patient with working download links.
11. Existing single-patient outputs and the existing DOCX templates are unchanged.
12. Unit tests cover the comparison, partitioning, empty cases, and the multiplier.

## Decisions

| Decision | Alternatives considered | Rationale |
|----------|-------------------------|-----------|
| Compare only micro + toxins in v1 | Compare all report categories now | Keeps scope contained; only treatment elements drive shared sessions. Partition is built extensible for later. |
| Common = present in ALL patients | Majority/subgroup (2 of 3) common | All-patients-common is deterministic and avoids combinatorial subgroup documents. |
| Independent numbering per document | Continuous numbering across shared + individual | Each document is a self-contained deliverable; simpler and predictable for the POC. |
| Extra sessions per patient | Group-level or both | Extra sessions are manually chosen per person and belong in that person's documents. |
| Shared name = list of patient names | Generic label or blank | Identifies the group while passing only a string, so no template changes are needed. |
| Multiplier on shared-session unit price | Multiply only the final total | Keeps rows and total consistent; default 1.0 is a no-op until confirmed with the client. |
| Individual relatorio = unique findings only | Full diagnostic (common + unique) | Matches the client's choice; uncompared categories are always shown because "unique" is undefined for them. |
| No anamnesis in the group tab | Replicate anamnesis per patient | Simplifies v1; anamnesis only feeds the individual report and can be added later. |
| Reuse existing generators via content dicts | New group-specific generators/templates | The four generators already consume the same content dict shape, so partitioning the content reuses everything. |

## Reviewer Checklist

- [ ] What problem does this feature solve, and for whom?
- [ ] What is explicitly out of scope?
- [ ] Which invariants must hold at all times?
- [ ] What is the end-to-end flow, and which module owns each step?
- [ ] What external systems or prerequisite features does it depend on?
- [ ] How will we know the feature is complete?
- [ ] Which decisions were deliberate, and what was rejected?
