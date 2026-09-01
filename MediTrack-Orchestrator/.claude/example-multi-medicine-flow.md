# Example flow: doctor adds two medicines in one message

**Doctor types** (patient `INS12345` already open in ServicesPage, so the chat
already has patient context from earlier — no need to ask for it):

> "Paracetamol 3 times a day, Avil 0-0-1" *(presses Enter)*

This example is worth walking through specifically because it has **two
medicines in a single sentence**, and one detail (no dosage strength given for
either drug) that shows exactly why careful field-parsing rules matter, even
without a confirmation step (dropped per the v2 plan — see `plan.md` in this
folder).

---

## Step 1 — request leaves the browser

`ChatWidget` POSTs to `/chat` with:
- `message`: "Paracetamol 3 times a day, Avil 0-0-1"
- `insurance_number`: "INS12345" *(auto-attached — the patient was already open, doctor never typed it)*

## Step 2 — agent node reasons about intent

The orchestrator LLM gets the message, the system prompt, and all 6 tool
schemas. It recognizes this as a request to add medicines (dosage-shorthand
phrasing like "3 times a day" and "0-0-1" is a strong signal, same way it
already recognizes "what could cause these symptoms" as a `diagnose_patient`
request).

## Step 3 — the LLM parses both drugs itself

This is plain language understanding, not custom parsing code:
- **Paracetamol** → frequency: "3 times a day" → normalized to `1-1-1`
- **Avil** → `0-0-1` is standard clinical shorthand for
  morning-afternoon-night dosing → frequency stays `0-0-1`

**Neither drug has a dosage *strength*** (e.g. "500mg") in what the doctor
typed. Per the system-prompt rule, dosage is left blank rather than invented
— this is exactly the kind of gap this codebase has already been burned by
once before (the RAG service's own docs mention an earlier incident where the
LLM added a drug's generic name that wasn't actually in the retrieved data).

## Step 4 — one tool call for both medicines, written immediately

`add_medicine`'s parameter is a **list** of medicines
(`medicines: List<MedicineDto>`), not a single drug name string. So unlike
the *existing*, documented limitation with `drug_information` (which only
accepts one drug name per call, so asking about two drugs at once unreliably
gets only one answered — see `mcp-tool-flow.md` in `docs/`), `add_medicine`
was designed to take multiple entries in a single call. The LLM emits **one**
tool call, immediately (no confirmation turn in the v2 design):

```
add_medicine(
  medicines: [
    { name: "Paracetamol", dosage: "", frequency: "1-1-1", startDate: today, ... },
    { name: "Avil",        dosage: "", frequency: "0-0-1", startDate: today, ... }
  ]
)
```

(`insuranceNumber` is not something the LLM fills in at all — it's stripped
from what the model even sees, and `tool_node.py` injects "INS12345" from the
session automatically.)

## Step 5 — Backend executes it

The Backend's new MCP tool calls the **existing, unchanged**
`MedicineService.addMedicine(insuranceNumber, medicineDtoList)` — which
already accepts a list and already appends every entry in it to today's
date-bucket in a single MongoDB save. Both medicines land in the same write.

## Step 6 — reply, and the frontend auto-refreshes

Backend returns raw text: `"Medicine added successfully"`. The `/chat`
response also includes `tools_called: ["add_medicine"]`, which `ChatWidget`
maps to the `"medicines"` kind and uses to notify `ServicesPage` to silently
re-fetch the medicines data for `INS12345` — no manual refresh needed.
Checking ServicesPage's medicine tab afterward shows both Paracetamol and
Avil in today's entry, without the doctor doing anything beyond sending the
one chat message.

---

### The one thing to watch in real use
If the doctor's shorthand is genuinely ambiguous (e.g. they meant "Avil
0-0-1" as *once a day for 1 day* rather than *at night*), the model has no
way to know that from text alone, and — since confirmation was dropped —
nothing catches a wrong interpretation before it's saved. This is the direct
trade-off accepted when confirmation was removed from the design.
