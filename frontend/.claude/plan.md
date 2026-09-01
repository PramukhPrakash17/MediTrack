# Chat-driven "add medicine / add note / add lab report" feature (v2 — no confirmation, auto-refresh)

## Context

Today the chat (MediTrack-Orchestrator) only *reads*: it routes a doctor's
question to one of three MCP tools (`diagnose_patient`, `drug_information`,
`analyze_xray`) and returns whatever that RAG/X-ray service says, verbatim.
It has no connection to the Backend at all, and the Backend itself has no
MCP surface — it's plain REST, consumed only by the frontend's `ServicesPage`.

The ask: let a doctor also *write* through chat — add a medicine, add a
free-text note, and add a lab/blood report (PDF or photographed report),
reusing the same Document AI extraction the existing lab-report upload
already does. Two decisions were revisited from the original design pass:

- **No confirmation step.** Originally planned as a two-turn "propose, then
  wait for yes" flow. Explicitly dropped per the user's call: writes happen
  in a single turn, same shape as the existing read-only tools. Flagged once
  for the record: there is still no edit/delete for medicines or notes
  anywhere in the app, so a misparsed entry (wrong dosage, wrong date, a bad
  OCR read on a report) has no in-app way to be corrected after the fact.
  Accepted trade-off, not revisited further.
- **Frontend auto-refresh.** New requirement: once something is added via
  chat, `ServicesPage` should reflect it without the doctor manually
  re-searching or switching tabs.

Reused patterns from the rest of the codebase: MCP tool exposure (same as
Drug-RAG-Service/RAG/Xray-Service already do), and server-side injection of
values the LLM must never invent (`insuranceNumber`, `tempPath` — same
mechanism already used for the X-ray `temp_path` today).

Confirmed answers from earlier discussion, still in effect:
- **Patient context**: auto-use whichever patient is open in `ServicesPage`
  (via a new shared context). If none is open and the doctor asks to add
  something, the assistant asks for the insurance number in-chat once and
  remembers it for the rest of that consultation. Read-only questions
  (diagnose/drug/x-ray) need no patient at all.
- **Lab report differentiation**: reuse the *existing* Document AI
  lab-report pipeline as-is (no new processor). X-ray vs. lab-report intent
  is resolved by the LLM from the doctor's wording (same mechanism it
  already uses to choose between the three existing tools), reinforced with
  explicit tool-description guardrails so it doesn't guess.
- **Medicine field parsing rules** (from the multi-medicine walkthrough):
  normalize frequency into morning-afternoon-night shorthand (e.g. `1-0-1`);
  leave dosage strength blank if the doctor didn't state one, never invent a
  number; resolve relative dates ("next week," "for 5 days") against the
  actual current date, which must be injected into the system prompt since
  the model has no live clock of its own.

## Backend changes (`Backend/`)

1. **`pom.xml`** — add `spring-ai-bom` (`1.1.7`, in `dependencyManagement`)
   and `spring-ai-starter-mcp-server-webmvc`, mirroring
   `Drug-RAG-Service/pom.xml`. (Backend is Spring Boot 3.5.3, siblings are
   3.5.14 — try as-is first; bump the parent version only if the BOM pulls
   in an incompatible dependency.)

2. **`application.properties`** — add:
   ```
   spring.ai.mcp.server.type=sync
   spring.ai.mcp.server.protocol=STREAMABLE
   spring.ai.mcp.server.name=Backend-server
   spring.ai.mcp.server.version=1.0.0
   ```

3. **New `Service/BackendMcpTool.java`** — `@Component`, mirroring
   `Drug-RAG-Service/.../DrugMcpTool.java` / `RAG/.../SymptomsMcpTool.java`
   (`@McpTool`/`@McpToolParam`, package `org.springaicommunity.mcp.annotation`
   — confirmed via compilation that this is the correct package for
   spring-ai-bom 1.1.7, matching Drug-RAG-Service; RAG's
   `org.springframework.ai.mcp.annotation` only exists under spring-ai
   2.0.0-M4). Two tools, each writing immediately (no confirmation step):
   - `add_medicine(insuranceNumber, medicines: List<MedicineDto>)` → calls
     existing `MedicineService.addMedicine` unchanged.
   - `add_doctor_note(insuranceNumber, note: String)` → builds a
     `NotesRequestDto`, calls existing `NotesService.saveNotes` unchanged.
   Lab reports are **not** an MCP tool on Backend at all — per the
   "multipart, not file path" requirement, the Orchestrator calls Backend's
   existing `POST /api/labreport/upload/{insuranceNumber}` REST endpoint
   directly with real multipart/form-data bytes (see Orchestrator changes
   below). No Backend code changes needed for lab reports —
   `LabReportController`/`LabReportService` stay exactly as they are today.

## Orchestrator changes (`MediTrack-Orchestrator/`)

1. **`app/config/settings.py`** — add `backend_mcp_url: str` (for
   add_medicine/add_doctor_note MCP discovery) and `backend_base_url: str`
   (e.g. `http://backend:8080`, for the direct multipart lab-report call);
   add `"backend": settings.backend_mcp_url` to `MCP_SERVER_URLS`.

2. **`app/graph/state.py`** — add `insurance_number: Optional[str]` to
   `ConsultationState` (persists across turns via the existing checkpointer,
   same as `temp_path` does today).

3. **`app/api/schemas.py`** — add `tools_called: list[str]` to
   `ChatResponse`, so the frontend can tell *which* tool(s) ran this turn
   without re-parsing the reply text. Populated directly from data the
   server already tracks (see below) — no new LLM cost.

4. **`app/api/chat.py`**:
   - Accept `insurance_number: str | None = Form(None)`; only set
     `graph_input["insurance_number"]` when the frontend actually sent one
     (omit the key otherwise), same "don't clobber existing state" pattern
     already used for `temp_path`.
   - Rename the upload field from `image` to `attachment`; extend
     `ALLOWED_IMAGE_TYPES` → `ALLOWED_ATTACHMENT_TYPES = {.jpg, .jpeg, .png, .pdf}`.
   - In the response, set `tools_called = [o["tool"] for o in
     result_state.get("raw_tool_outputs") or []]` — this list already exists
     server-side per turn, just wasn't surfaced to the caller before.

5. **`app/mcp_client/tool_registry.py`**:
   - Generalize `_hide_temp_path` into `_hide_params(parameters, names)`.
   - Hide `insuranceNumber` on `add_medicine`/`add_doctor_note`'s
     MCP-discovered schema (server-injected, never LLM-supplied).
   - Hand-register a schema for `add_lab_report` alongside the
     MCP-discovered ones — it isn't discovered from any server since Backend
     exposes no MCP tool for it. No LLM-visible parameters at all
     (insuranceNumber and the attachment are both injected server-side in
     `tool_node.py`).
   - Add `ADD_LAB_REPORT_DESCRIPTION_OVERRIDE` ("...save a blood/lab report
     document the doctor attached and asked to add/save/record. Not for
     X-ray images.") and tighten `XRAY_TOOL_DESCRIPTION_OVERRIDE` with the
     converse.

6. **`app/graph/tool_node.py`** — generalize the existing
   `if tool_name == XRAY_TOOL_NAME` block into per-tool injection:
   - For `add_medicine` / `add_doctor_note` / `add_lab_report`: inject
     `insuranceNumber` from `state["insurance_number"]`; if state has none
     *and* the LLM didn't supply one either, return "No patient is selected
     — ask the doctor for the insurance number first" (mirrors the existing
     "no X-ray uploaded" message). If the LLM *did* supply one (because it
     just asked and got an answer), pass it through **and** carry it forward
     into returned state so it's remembered for the rest of the
     consultation.
   - `add_lab_report` is special-cased entirely in `_execute`: instead of
     dispatching to an MCP session, read the attachment from
     `state["temp_path"]` (if missing, return "No document was attached"),
     read its bytes locally, and issue a real multipart/form-data `POST` to
     `{backend_base_url}/api/labreport/upload/{insuranceNumber}` (e.g. via
     `httpx`) — reusing Backend's existing endpoint unchanged. The raw
     response text becomes this turn's tool output, same as every other
     tool.

7. **`app/graph/agent_node.py`** — extend `SYSTEM_PROMPT`:
   - Today's actual date is injected into the prompt (e.g. "Today's date is
     2026-08-19.") so relative dates ("next week," "for 5 days") resolve
     correctly — the model has no other way to know the current date.
   - Call a write tool as soon as the necessary details are present in the
     doctor's message — no propose/wait-for-confirmation step.
   - Frequency values are normalized to morning-afternoon-night shorthand
     (e.g. `1-0-1`, `0-0-1`) before being passed as the `frequency` field.
   - Dosage strength is left blank if the doctor didn't state one — never
     invented.
   - Attachment routing: "analyze/check for a fracture" → `analyze_xray`;
     "add/save this lab/blood report" → `add_lab_report`; if genuinely
     ambiguous, ask rather than guess.
   - `insuranceNumber`/`tempPath` are supplied automatically — never invent
     them (extends the existing "never invent a filesystem path" line).

## Infra (`docker-compose.yml`)

- `meditrack-orchestrator` service: add `BACKEND_MCP_URL:
  http://backend:8080/mcp` and `BACKEND_BASE_URL: http://backend:8080` to
  `environment`, add `BACKEND_MCP_URL` to `WAIT_FOR_URLS`, add
  `backend: condition: service_started` to `depends_on`.
- No volume mount needed on the `backend` service — lab reports travel as
  real multipart bytes over a direct HTTP call now, not a shared-filesystem
  path, so Backend never needs access to `orchestrator_temp_uploads`.

## Frontend changes (`frontend/src/`)

1. **New `patient/PatientContext.js`** — mirrors `auth/AuthContext.js`'s
   shape. Holds two things:
   - `activeInsuranceNumber` + setter — the patient currently open in
     `ServicesPage`, read by `ChatWidget` to auto-attach patient context.
   - A change-notification piece: `notifyDataChanged(kinds)` (where `kinds`
     is a subset of `["medicines", "notes", "labReports"]`) plus the state
     backing it (e.g. `{ kinds, token }`, `token` incrementing on every
     call so a `useEffect` elsewhere can detect a fresh event even if the
     same `kinds` repeats).
   Wrapped in `App.js` alongside the existing `AuthProvider`.

2. **`pages/ServicesPage/ServicesPage.js`**:
   - Call `setActiveInsuranceNumber(insuranceNumber)` in the existing
     `searchPatient()` success path.
   - New `useEffect` watching the context's change-notification token. On
     change, for each affected kind, do a **targeted** refresh reusing
     existing functions/endpoints rather than the heavier `searchPatient()`
     (which resets forms/pagination/loading state wholesale):
     - `medicines`: re-fetch `GET /api/medicine/getLast5Medicines/{id}` into
       `patientData.medicines`; if `activeTab === "medicines"`, also call
       the existing `fetchDetailedMedicines()`.
     - `notes`: same pattern with `getlatestnotes` /
       `fetchDetailedNotes()`.
     - `labReports`: same pattern with `getLatestLabReport` /
       `fetchDetailedLabReports()`.
   - Because `activeInsuranceNumber` is the single source of truth both
     `ChatWidget` and the Backend's write tools use, the patient being
     refreshed here is guaranteed to be the same one that was just written
     to — no risk of refreshing the wrong patient's screen.

3. **`components/ChatWidget/ChatWidget.js`**:
   - Read `activeInsuranceNumber` via the new `usePatient()` hook; append it
     as `insurance_number` in the `/chat` FormData whenever set.
   - Rename the file field to `attachment`, extend `<input accept>` to
     include `.pdf`.
   - After a `/chat` response, map any of `add_medicine` /
     `add_doctor_note` / `add_lab_report` present in `response.tools_called`
     to their matching kind and call `notifyDataChanged([...kinds])` —
     this is what triggers `ServicesPage`'s auto-refresh.
   - Show the active patient's insurance number in the widget header as a
     visibility cue, since writes now silently target whichever patient is
     shown there.

## Verification

- **Backend**: run standalone, confirm existing REST endpoints (including
  `/api/labreport/upload/{id}`) are unaffected, and the new MCP endpoint
  lists `add_medicine` and `add_doctor_note` only (check via the
  orchestrator's own startup tool-discovery log, same as the other three
  servers).
- **Orchestrator**: `docker-compose up`, then via `curl /chat` or the
  frontend: (1) ask to add a medicine with no patient open → expect the
  "select a patient" message; (2) open a patient, ask again → single turn,
  immediate write, raw `"Medicine added successfully"` reply; confirm via
  `GET /api/medicine/getMedicines/{id}` that it persisted; (3) send a
  multi-medicine message (e.g. the Paracetamol + Avil example) → confirm
  both land in one `add_medicine` call, one Mongo write; (4) attach a PDF
  and ask to add it as a lab report → confirm it POSTs multipart to
  Backend's existing `/api/labreport/upload` endpoint (not through MCP) and
  persists; (5) attach a JPG and ask to check for a fracture → confirm it
  still routes to `analyze_xray`, not `add_lab_report`.
- **Frontend**: `npm start`, open a patient, open chat, add a medicine/note
  via chat, confirm `ServicesPage`'s summary panel (and the relevant tab, if
  open) updates on its own without a manual re-search or tab click. Switch
  to a different patient in `ServicesPage` and confirm the chat widget's
  header updates and a subsequent chat write targets the new patient, not
  the old one.

## Verification results (live, against the running docker-compose stack)

All backend/orchestrator flows below were exercised for real (Groq, Document
AI, MySQL, MongoDB) and passed. Two real bugs were caught this way and fixed
in `tool_registry.py`:

1. **Groq rejected calls missing `insuranceNumber`.** Backend's Java
   `@McpToolParam(required = true)` makes the MCP-discovered schema mark
   `insuranceNumber` as required; Groq validates tool-call arguments
   strictly against that schema and threw a 400 (`missing properties:
   'insuranceNumber'`) whenever the LLM correctly tried to omit it. Fixed by
   demoting it to optional in the LLM-facing schema only (`_make_optional`)
   - Backend/tool_node.py still always guarantee a real value before the
     actual MCP call.
2. **The model asked for the insurance number before ever trying the tool**,
   even with a patient already selected and `insurance_number` sent by the
   frontend - because that value lives only in server-side state, the LLM
   has no way to see it without attempting the call. Same failure mode
   `XRAY_TOOL_DESCRIPTION_OVERRIDE` already existed to prevent; fixed by
   adding equivalent "you do not need to know X - call the tool and it will
   report if it's missing" overrides for `add_medicine`, `add_doctor_note`,
   and `add_lab_report`.

Confirmed working after the fixes:
- No patient open → asks for insurance number → doctor replies → write
  succeeds, `tools_called: ["add_medicine"]`.
- Patient pre-known (frontend-sent `insurance_number`, never mentioned in
  chat text) → immediate single-turn write.
- "Paracetamol 3 times a day, Avil 0-0-1" → one `add_medicine` call, both
  meds in one Mongo write, dosage left blank, frequency normalized to
  `1-1-1` / `0-0-1`.
- `add_doctor_note` → note text persisted verbatim.
- PDF attached + "add this blood report" → real multipart POST to Backend's
  existing `/api/labreport/upload` endpoint → Document AI extracted both
  test rows correctly → persisted.
- JPG attached + "check this x-ray for a fracture" → still routes to
  `analyze_xray`, not `add_lab_report` - disambiguation holds even with the
  new tool in the mix.
- `insurance_number` persists across turns without resending it - a
  follow-up "add ibuprofen 400mg once daily" with no insurance number
  anywhere in that turn's request still landed on the correct patient,
  proving server-side state (not LLM inference from chat history) is what's
  carrying it forward.
- Frontend container builds and serves (HTTP 200) with the new
  `PatientContext`/`ChatWidget`/`ServicesPage` changes; no new ESLint
  warnings introduced (three pre-existing warnings in `ServicesPage.js` are
  unrelated to this feature).
