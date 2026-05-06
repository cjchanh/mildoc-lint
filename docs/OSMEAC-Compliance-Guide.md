# O-SMEAC Compliance Guide

`mildoc-lint` is an unclassified, training-grade structural linter for orders that follow the USMC O-SMEAC / five-paragraph order convention. It does not generate tactical plans or validate tactical soundness. It does not replace command review.

Authoritative references are listed in [`SOURCES.md`](SOURCES.md).

---

## What it covers

| Order type | Detection trigger | Behavior |
|---|---|---|
| OPORD / O-SMEAC | `OPORD`, `OPLAN`, `O-SMEAC`, `SMEAC`, `operation order`, `combat order` | five-paragraph structure check, mission heuristics, execution subelements |
| WARNORD | `WARNORD`, `WARNO`, `warning order` | preparation timeline / PCC / PCI / rehearsal cue check, sparse-content check |
| FRAGORD | `FRAGORD`, `FRAGO`, `fragmentary order` | base-order reference check, "no change" language for omitted sections |

If none of the trigger phrases appear, the OSMEAC rules stay silent unless the profile is forced (`--profile osmeac` or `--profile all`).

---

## Rule reference

### Structure: five-paragraph order

Required sections (each missing one is reported):

- `osmeac.missing_situation`
- `osmeac.missing_mission`
- `osmeac.missing_execution`
- `osmeac.missing_admin_logistics`
- `osmeac.missing_command_signal`

**Severity:** ERROR

**Source:** USMC FGHT 1004 *Introduction to the Operations Order*.

### Orientation

`osmeac.orientation_absent`

**Severity:** INFO

**What it checks:** O-SMEAC includes an Orientation segment before the SMEAC body when terrain or model briefing is appropriate.

**What it does not decide:** whether the order needs orientation. For some orders it is unnecessary.

---

### Mission

`osmeac.mission_incomplete_heuristic`

**Severity:** WARN

**What it checks:** mission section presence of cues for *task / when / where / why*. Cues are pattern-based:

- **Task:** verbs (seize, secure, destroy, disrupt, support, conduct, provide, defend, etc.).
- **When:** `NLT`, `NET`, `on order`, `upon`, four-digit time, calendar dates.
- **Where:** `vicinity`, `vic.`, `grid`, `OBJ`, `AO`, `AA`, `BP`, `CP`, `route`.
- **Why / purpose:** `in order to`, `IOT`, `so that`, `purpose`.

**What it does not decide:** the truth or feasibility of the mission. The check only flags missing cues.

`osmeac.mission_too_long`

**Severity:** WARN

**What it checks:** the Mission section is more than four non-blank lines. Mission statements are conventionally one sentence.

**Source:** USMC FGHT 1004.

---

### Execution

`osmeac.execution_missing_common_subelements`

**Severity:** WARN

**What it checks:** the Execution section for common subelement labels: commander's intent, concept of operations, tasks, coordinating instructions.

**What it does not decide:** which subelements are mandatory for any specific order. For minor orders, a reduced subelement set may be deliberate.

**Source:** USMC FGHT 1004.

---

### FRAGORD

`osmeac.fragord_missing_base_order`

**Severity:** ERROR

**What it checks:** a FRAGORD/FRAGO is detected but no base-order reference (`base order`, `base OPORD`, `to OPORD`, `references`, `Ref:`) appears.

`osmeac.fragord_no_change_absent`

**Severity:** WARN

**What it checks:** a FRAGORD omits sections without explicit "No change" language.

**Source:** USMC Combat Orders Foundations.

---

### WARNORD

`osmeac.warnord_prep_time_missing`

**Severity:** INFO

**What it checks:** a WARNORD is detected but no preparation cues appear (`timeline`, `schedule`, `backbrief`, `rehearsal`, `inspection`, `PCC`, `PCI`).

**Why it exists:** WARNORDs exist to maximize subordinate preparation time. If known prep events aren't included, the order is doing less work than it could.

`osmeac.warnord_too_sparse`

**Severity:** WARN

**What it checks:** a WARNORD with neither Mission nor Execution sections present.

**Source:** USMC Combat Orders Foundations.

---

## Boundary

- The linter does not validate tactical soundness, feasibility, or correctness of any plan.
- It does not generate orders. The `mildoc-lint new` subcommand prints a five-paragraph skeleton; the operator must populate it.
- It is calibrated against unclassified USMC training material. Joint, Army, Air Force, or Navy doctrine may use different conventions.
