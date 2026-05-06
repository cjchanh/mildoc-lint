# CUI Compliance Guide

`mildoc-lint` checks CUI marking shape only. It does not make designating-authority decisions. It does not determine whether information is actually CUI. It does not certify CMMC, RMF, NIST, or DoD compliance.

The CUI rules catch mechanical errors that cause inspection findings and rework: invalid banner forms, missing or incomplete designation indicator blocks, legacy markings (FOUO/SBU), and inconsistent portion marking.

Authoritative references are listed in [`SOURCES.md`](SOURCES.md). All rules are tied to public DoD guidance only.

---

## Rule reference

### `cui.invalid_banner`

**Severity:** ERROR

**What it checks:** detects invalid or legacy CUI banner forms anywhere in the document, including `U//CUI`, `UNCLASSIFIED//CUI`, `CUI//<CATEGORY>`, `CONTROLLED`, and `CONTROLLED UNCLASSIFIED INFORMATION` as a standalone banner.

**Why it exists:** DoD CUI marking guidance specifies the banner/footer is the standalone string `CUI`. Categories and limited dissemination controls belong in the designation indicator block, not the banner.

**What it does not decide:** whether the underlying content qualifies as CUI in the first place.

**Example fail:**
```
CUI//CTI
```

**Example pass:**
```
CUI
```

**Source:** DoD CUI Markings Training Aid (2024); DoD CUI Banner Line marking tip.

---

### `cui.legacy_marking`

**Severity:** WARN

**What it checks:** legacy or supplemental control markings: `FOUO`, `For Official Use Only`, `SBU`, `Sensitive But Unclassified`.

**Why it exists:** these labels were superseded by the CUI program. Surfacing them flags documents that may need re-marking under current DoD guidance.

**What it does not decide:** whether the document still qualifies for control under CUI.

**Example fail:**
```
FOR OFFICIAL USE ONLY
```

**Example pass:**
```
CUI
```

**Source:** DoDI 5200.48; DoD CUI Markings Training Aid (2024).

---

### `cui.missing_top_banner` / `cui.missing_bottom_banner`

**Severity:** ERROR

**What it checks:** when CUI context is detected (a designation indicator field is present, or a `CUI` line, or `//CUI`), every logical page is checked for a standalone `CUI` banner at top and footer.

**Why it exists:** DoD guidance requires `CUI` at the top and bottom of pages containing CUI.

**What it does not decide:** what counts as a "page" in non-paginated formats. The linter splits on form-feed and a heuristic line window. Authoritative pagination requires DOCX/PDF rendering; treat findings as advisory in non-paginated source files.

**Source:** DoD CUI Markings Training Aid (2024).

---

### `cui.missing_designation_indicator`

**Severity:** ERROR

**What it checks:** the absence of a CUI designation indicator block on documents in CUI context.

**Why it exists:** DoD guidance requires a designation indicator block on documents containing CUI. The block names who controlled the information, the category, the dissemination control or distribution statement, and a POC.

**What it does not decide:** whether the values in the block are correct, current, or authorized.

**Example fail:** the document is marked `CUI` at top/bottom but contains no `Controlled by:`, `CUI Category:`, `LDC:` / `Distribution Statement:`, or `POC:` line.

**Example pass:**
```
Controlled by: U.S. Marine Corps / Training Command
CUI Category: SP-PRCMT
LDC: FED ONLY
POC: trainingcmd-poc@example.invalid
```

**Source:** DoD CUI Designation Indicator Block marking tip.

---

### `cui.di_missing_controlled_by` / `cui.di_missing_category` / `cui.di_missing_ldc_or_distribution` / `cui.di_missing_poc`

**Severity:** ERROR

**What it checks:** when at least one designation indicator field is present, the linter checks the four canonical fields (`Controlled by:`, `CUI Category:` (or `Categories:`), `LDC:` or `Distribution Statement:`, and `POC:`) and flags the missing ones individually.

**Why it exists:** an incomplete designation indicator block leaves recipients without the information needed to handle the document correctly.

**What it does not decide:** whether the values are accurate.

**Source:** DoD CUI Designation Indicator Block marking tip.

---

### `cui.do_not_prefix_unclassified`

**Severity:** ERROR

**What it checks:** banners that prepend `UNCLASSIFIED` to `CUI`, e.g. `UNCLASSIFIED//CUI` or `U//CUI`.

**Why it exists:** DoD CUI guidance explicitly says not to prefix `CUI` with `UNCLASSIFIED` in the banner line.

**Example fail:**
```
UNCLASSIFIED//CUI
```

**Example pass:**
```
CUI
```

**Source:** DoD CUI Markings Training Aid (2024).

---

### `cui.portion_marking_recommended`

**Severity:** INFO

**What it checks:** if no portion markings appear in a CUI document, the linter notes that portion marking is optional for unclassified DoD CUI but recommended in DoD training guidance.

**Why it exists:** portion marking helps downstream handling and partial release decisions.

**What it does not decide:** whether portion marking is required by your specific DoD component or contract.

**Source:** DoD CUI Markings Training Aid (2024).

---

### `cui.inconsistent_portion_marking`

**Severity:** WARN

**What it checks:** when portion markings exist but content lines do not appear to be marked consistently. The check is heuristic and skips banners, headings, and designation indicator block lines.

**Why it exists:** inconsistent portion marking is a common inspection finding. If you mark some portions, mark all required portions.

**What it does not decide:** the correct portion mark for any specific portion. That is a content judgment.

**Source:** DoD CUI Markings Training Aid (2024).

---

### `cui.possible_unmarked_category`

**Severity:** WARN

**What it checks:** category indicator language (`export-controlled`, `ITAR`, `EAR99`, `CTI`, `Controlled Technical Information`, `OPSEC`, `NNPI`, `proprietary`) appearing in a document with no visible CUI marking.

**Why it exists:** if a document discusses content that often qualifies as CUI under a registered category, the absence of CUI marking is worth a human review.

**What it does not decide:** whether the content actually qualifies as CUI. The linter cannot make designation calls; only an authorized designating authority can.

**Source:** DoDI 5200.48.

---

## Edge cases

- **Mixed unclassified / CUI documents:** the linter treats CUI context as document-wide if any CUI signal is present. For mixed-page handling, manual review is required.
- **Markdown vs DOCX:** Markdown does not have hard pages. The linter uses a heuristic window. DOCX header/footer parsing is best-effort and depends on document structure.
- **PDF input:** requires the optional `pypdf` extra. Text extraction quality varies by source.
- **Synthetic data only:** all built-in examples are synthetic. The repo's safety policy forbids real CUI in fixtures.
