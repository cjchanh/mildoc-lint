from __future__ import annotations

TEMPLATES: dict[str, str] = {
    "cui-designation-block": """Controlled by: [organization/component and office]
CUI Category: [category or categories from the CUI Registry]
LDC: [limited dissemination control] OR Distribution Statement: [B-F]
POC: [name/phone/email or authorized organizational mailbox]
""",
    "opord": """OPORD [NUMBER] - [TITLE]

Orientation
[Terrain/model/map orientation, only as needed.]

1. Situation
  a. Enemy Forces
  b. Friendly Forces
  c. Attachments/Detachments

2. Mission
[WHO] will [WHAT] at [WHEN] in/at [WHERE] in order to [WHY].

3. Execution
  a. Commander's Intent
  b. Concept of Operations
  c. Tasks
  d. Coordinating Instructions

4. Administration and Logistics
  a. Administration
  b. Logistics

5. Command and Signal
  a. Command
  b. Signal
""",
    "warnord": """WARNORD [NUMBER] - [TITLE]

1. Situation
[Known higher-order situation. Unknowns may be updated later.]

2. Mission
[Known mission statement or pending mission cue.]

3. Execution
  a. Initial guidance
  b. Timeline / PCC / PCI / rehearsals

4. Administration and Logistics
[Known admin/logistics instructions.]

5. Command and Signal
[Known command/signal instructions.]
""",
    "fragord": """FRAGORD [NUMBER] TO OPORD [BASE ORDER]

References: [base order / map / annexes]

1. Situation
[Changes only, or: No changes.]

2. Mission
[Changed mission, or: No changes.]

3. Execution
[Changed execution details, or: No changes.]

4. Administration and Logistics
[Changes only, or: No changes.]

5. Command and Signal
[Changes only, or: No changes.]
""",
    "naval-letter": """From: [Originator]
To: [Recipient]

Subj: [NORMAL WORD ORDER, ALL CAPS, NO TERMINAL PUNCTUATION]

Ref: (a) [Reference]
Encl: (1) [Enclosure]

1. [Body paragraph.]
""",
    "namp-discrepancy": """NAMP/CSEC Discrepancy Record

Reference: [NAMP/CSEC/local checklist reference]
Discrepancy: [objective description of discrepancy]
Owner/OPR: [work center/shop/person]
Corrective Action: [root cause and corrective action]
Due Date: YYYY-MM-DD
Status: Open | In Progress | Closed | Verified
Evidence: [attachment/log/photo/record identifier]
""",
}


def render_template(name: str) -> str:
    try:
        return TEMPLATES[name]
    except KeyError as exc:
        names = ", ".join(sorted(TEMPLATES))
        raise ValueError(f"unknown template '{name}', expected one of: {names}") from exc
