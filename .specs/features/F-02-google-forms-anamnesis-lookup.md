# F-02 - Google Forms Anamnesis Lookup

## Scope

**In scope:**
- Add a visual-only anamnesis lookup section to the Streamlit processing flow.
- Move the clinic selector to the top of the `Processamento` tab and use it as the single clinic source for anamnesis, reports, budgets, and extra sessions.
- Read anamnesis responses from clinic-specific Google Forms response spreadsheets for Bienestar and VitaeFlux.
- Let staff search by patient name, pick one candidate when multiple responses match, and view all questions/responses in a selectable table.
- Keep missing anamnesis results and technical lookup failures separate in the UI.
- Add unit-testable parsing, normalization, search, and table-building logic.

**Out of scope:**
- Writing data to Google Forms, Google Sheets, or Google Drive.
- Versioning patient anamnesis data in local fallback files.
- Including anamnesis answers in generated report, protocol, or budget DOCX files.
- Building an administrative screen to edit spreadsheet configuration or validate form schemas.
- Supporting Alecrim anamnesis in this version.

## Context & Motivation

The app already uses Google Sheets for the dynamic extra sessions catalog described in `.specs/features/F-01-google-sheets-extra-sessions.md`. Clinics also maintain Google Forms anamnesis questionnaires whose responses are stored in clinic-specific Google Sheets. Staff need to retrieve a patient's anamnesis by name while preparing the existing processing flow, without opening the Google Sheet manually.

The first version is a read-only operational lookup. It should make the anamnesis visible and selectable in the UI, while deliberately avoiding downstream document-generation changes until the report inclusion rules are defined.

## Business Rules

- RN-01: Anamnesis lookup is clinic-specific; the selected clinic determines which response spreadsheet is queried.
- RN-02: Bienestar and VitaeFlux are the only clinics with anamnesis lookup support in this version.
- RN-03: Alecrim must remain selectable for the existing app flow, but its anamnesis section must show that anamnesis is unavailable.
- RN-04: Staff search by patient name and explicitly trigger the lookup with a `Buscar` action.
- RN-05: A patient may have zero, one, or multiple matching anamnesis responses.
- RN-06: A missing anamnesis is not an error and must not block uploads or document generation.
- RN-07: A technical/configuration failure is an unavailable lookup state and must be shown separately from "no result".
- RN-08: All columns from the selected spreadsheet row are displayed as question/answer rows.
- RN-09: Selected anamnesis question rows are kept only in the page session for this feature and are not passed to report, protocol, or budget generation.

## Functional Requirements

- [ ] RF-01: The `Clínica` selector appears at the top of the `Processamento` tab, before file uploads and before the anamnesis lookup section.
- [ ] RF-02: The app uses the top-level clinic selection as the only selected clinic value for anamnesis, extra sessions, report template selection, budget generation, and output filenames.
- [ ] RF-03: The anamnesis section appears below the top clinic/patient controls and before the Prosync/Oberon upload sections.
- [ ] RF-04: For Bienestar and VitaeFlux, staff can enter a patient name and click `Buscar` to run the lookup.
- [ ] RF-05: The lookup does not run on every text edit; it only runs from the explicit search action.
- [ ] RF-06: Empty or whitespace-only search terms are rejected with a user-facing validation message and do not call Google Sheets.
- [ ] RF-07: Search normalizes casing and repeated whitespace for both the typed patient name and sheet values.
- [ ] RF-08: Search accepts partial name matches after normalization.
- [ ] RF-09: If no matching response exists, the UI shows `Nenhuma anamnese encontrada para este paciente nesta clínica.` and leaves the rest of the app usable.
- [ ] RF-10: If exactly one matching response exists, the app can select it automatically and render its question/answer table.
- [ ] RF-11: If multiple matching responses exist, the UI shows a candidate selector before rendering the table.
- [ ] RF-12: Candidate labels include the patient name and, when available, timestamp and email metadata.
- [ ] RF-13: The selected response renders as rows with `Pergunta`, `Resposta`, and `Selecionado`.
- [ ] RF-14: The selectable table follows the existing `render_selectable_table` behavior in `src/app.py`.
- [ ] RF-15: Changing clinic or changing the searched patient clears stale anamnesis candidates, selected candidate, and selected question rows.
- [ ] RF-16: Google Sheets errors shown in the UI are sanitized and do not include secrets, service account payloads, private keys, stack traces, or raw SDK errors.

## System Flow

1. `src/app.py` renders the `Processamento` tab and places the `selected_company` selectbox at the top of the tab.
2. `src/app.py` renders the patient name input near the clinic selector so the same value can be used by the report flow and by the anamnesis lookup.
3. `src/app.py` renders an anamnesis section before the file upload sections.
4. If the selected clinic is Alecrim, `src/app.py` shows an informational unavailable state and does not call the anamnesis loader.
5. For Bienestar or VitaeFlux, `src/app.py` reads Google configuration from `st.secrets` using `read_secret_section("google_sheets")` and `read_secret_section("google_service_account")`.
6. When staff click `Buscar`, `src/app.py` validates that the patient name is non-empty after trimming whitespace.
7. `src/app.py` calls a new utility in `src/utils/anamnesis_sheet.py`, passing the clinic name, search term, spreadsheet id, worksheet name, optional configured name column, and service account info.
8. `src/utils/anamnesis_sheet.py` opens the clinic spreadsheet with `gspread` in read-only mode and returns `worksheet.get_all_records(default_blank="")`.
9. `src/utils/anamnesis_sheet.py` resolves the patient name column from the configured header or from supported aliases.
10. `src/utils/anamnesis_sheet.py` normalizes records and returns candidate matches for the searched name.
11. `src/app.py` stores the lookup state in `st.session_state`, including status, candidates, selected candidate index, and selectable row selection.
12. If no candidate matches, `src/app.py` renders the no-result warning and keeps the rest of the processing flow available.
13. If multiple candidates match, `src/app.py` renders a candidate selector using labels built from name, timestamp, and email when those fields exist.
14. After one candidate is selected, `src/app.py` converts the full response row into question/answer rows and renders them through the existing selectable-table pattern.
15. `Gerar Relatório` continues to use Prosync/Oberon/extra session data only; it does not include anamnesis data in this feature.

## Invariants / Non-negotiables

- INV-01: Patient anamnesis data must never be committed to the repository as fallback JSON, fixtures copied from production, screenshots, or documentation examples with real patient content.
- INV-02: The app must never show Google service account secrets, private keys, or raw credential payloads in Streamlit UI errors.
- INV-03: Missing anamnesis data must never block the existing upload, processing, report, protocol, or budget flows.
- INV-04: Alecrim support must not be inferred from the existing clinic enum; it remains unavailable for anamnesis until explicitly configured in a future feature.
- INV-05: The clinic selector must have one authoritative state key; downstream flows must not maintain divergent clinic selections.
- INV-06: Anamnesis row selection must not affect generated DOCX outputs in this feature.

## Technical Design

### Entities / Models

| Model | Key fields | Notes |
|-------|------------|-------|
| AnamnesisConfig | `clinic_name`, `spreadsheet_id`, `worksheet_name`, `name_column` | Built from `st.secrets`; `name_column` is optional. |
| AnamnesisCandidate | `record_index`, `patient_name`, `timestamp`, `email`, `record` | Represents one matching Google Forms response row. |
| AnamnesisQuestionAnswer | `Pergunta`, `Resposta` | Derived from every column in the selected response row before adding `Selecionado` in the UI. |
| AnamnesisLookupState | `status`, `message`, `candidates`, `selected_candidate_index` | Stored in `st.session_state` for the Streamlit page session. |

### Endpoints / Interfaces (if applicable)

| Method | Route / Signature | Description |
|--------|-------------------|-------------|
| N/A | Streamlit UI action: `Buscar` | Triggers the anamnesis lookup for the selected clinic and typed patient name. |
| Function | `load_google_sheet_records(spreadsheet_id, worksheet_name, service_account_info) -> list[dict]` | Reads all response records from Google Sheets in read-only mode. |
| Function | `resolve_patient_name_column(records, configured_name_column=None) -> str` | Finds the name column from configuration or supported aliases. |
| Function | `search_anamnesis_candidates(records, search_term, name_column) -> list[dict]` | Returns normalized partial-name matches. |
| Function | `build_question_answer_rows(record) -> list[dict]` | Converts one response row into `Pergunta`/`Resposta` table rows. |

### Key Modules

- `src/app.py` - Move clinic/patient controls to the top of the processing tab and render the anamnesis lookup UI/state.
- `src/utils/anamnesis_sheet.py` - Own Google Sheets loading, header normalization, patient-name matching, candidate labeling data, and question/answer row construction.
- `tests/test_anamnesis_sheet.py` - Cover normalization, search behavior, duplicate candidates, no-result behavior, and failure states.
- `.streamlit/secrets.toml.example` - Document the required anamnesis Google Sheets configuration without real credentials.

## Dependencies

- **Prerequisite features:** F-01 for the existing Google Sheets service account pattern and `gspread` dependency.
- **External packages added:** N/A - reuse existing `gspread`.
- **External services:** Google Sheets API and Google Drive API in read-only mode through the existing service account.
- **Environment variables:** N/A - Streamlit secrets are used instead.
- **Streamlit secrets:**
  - `[google_service_account]` - existing service account payload used by `gspread.service_account_from_dict`.
  - `[google_sheets].bienestar_anamnesis_spreadsheet_id` - Bienestar Google Forms response spreadsheet id.
  - `[google_sheets].bienestar_anamnesis_tab` - Bienestar worksheet/tab name.
  - `[google_sheets].bienestar_anamnesis_name_column` - optional explicit Bienestar patient name header.
  - `[google_sheets].vitaeflux_anamnesis_spreadsheet_id` - VitaeFlux Google Forms response spreadsheet id.
  - `[google_sheets].vitaeflux_anamnesis_tab` - VitaeFlux worksheet/tab name.
  - `[google_sheets].vitaeflux_anamnesis_name_column` - optional explicit VitaeFlux patient name header.

## Acceptance Criteria

1. `Clínica` appears before the upload sections and remains the selected clinic used by all existing clinic-dependent behavior.
2. Bienestar and VitaeFlux show an anamnesis search input and `Buscar` button.
3. Alecrim shows anamnesis unavailable without attempting a Google Sheets read.
4. Clicking `Buscar` with a blank name shows validation and does not call the remote loader.
5. Searching for a name that has no matching response shows `Nenhuma anamnese encontrada para este paciente nesta clínica.` and still allows file uploads and DOCX generation.
6. Searching for a duplicated name shows multiple candidates instead of silently picking the wrong response.
7. Selecting a candidate renders all response columns as question/answer rows with selectable checkboxes.
8. Technical/configuration failures show a sanitized unavailable message and do not break the rest of the page.
9. Generated report, protocol, and budget DOCX outputs do not include anamnesis data.
10. Unit tests cover name-column resolution, normalized search, no-result behavior, duplicate candidates, question/answer conversion, and unavailable lookup states.
11. `.streamlit/secrets.toml.example` documents the new keys without real credentials.

## Decisions

| Decision | Alternatives considered | Rationale |
|----------|-------------------------|-----------|
| Keep v1 visual-only | Include anamnesis in report DOCX; export a separate anamnesis document | The immediate need is lookup during processing, and report inclusion rules are not defined yet. |
| Support Bienestar and VitaeFlux only | Support all clinics; make clinic support fully dynamic | Only Bienestar and VitaeFlux were requested for anamnesis spreadsheets; Alecrim should not imply support without a configured source. |
| Use explicit `Buscar` action | Search automatically while typing; require exact normalized name | A button avoids unstable intermediate states while preserving partial-name search convenience. |
| List duplicate candidates | Use the newest response automatically; block duplicate names | Staff need to choose the correct response, and timestamps/emails can help disambiguate without rejecting valid data. |
| No local fallback for anamnesis | Add JSON fallback like extra sessions | Anamnesis is patient-sensitive data and must not be versioned in the repository. |
| Show all columns as question/answer rows | Hide metadata by default; configure included questions per clinic | The future report-selection workflow needs visibility into all available fields, and row selection can prepare that path. |

## Reviewer Checklist

- [ ] What problem does this feature solve, and for whom?
- [ ] What is explicitly out of scope?
- [ ] Which invariants must hold at all times?
- [ ] What is the end-to-end flow, and which module owns each step?
- [ ] What external systems or prerequisite features does it depend on?
- [ ] How will we know the feature is complete?
- [ ] Which decisions were deliberate, and what was rejected?
