# Public Sources

`mildoc-lint` rules cite public, unclassified DoD, USMC, Navy, and NIST references only. None of these citations should be read as a compliance certification. They are public references that ground the deterministic rule logic.

To print sources from the CLI:

```bash
mildoc-lint rules
mildoc-lint rules --format json
```

---

## DoD CUI

- **DoD CUI Markings Training Aid (2024)** — mandatory CUI markings, banner shape, designation indicator block, "do not prefix `UNCLASSIFIED`" guidance.
  https://www.dodcui.mil/Portals/109/Documents/Desktop%20Aid%20Docs/Cleared%20CUI%20Training%20Aid%20-%20%20Markings%202024.pdf

- **DoD CUI Banner Line marking tip** — banner reflects overall marking; do not add categories or LDCs to banner lines.
  https://www.dodcui.mil/Training/Banner-Line/

- **DoD CUI Designation Indicator Block marking tip** — required block on documents containing CUI; includes Controlled by, category, dissemination/distribution, and POC.
  https://www.dodcui.mil/Home/Marking-Tips-for-CUI-Documents/CUI-Designation-Indicator-Block/

- **DoDI 5200.48** — establishes DoD CUI policy: identification, sharing, marking, safeguarding, storage, dissemination, destruction, and records management.
  https://www.esd.whs.mil/Portals/54/Documents/DD/issuances/dodi/520048p.PDF

## NIST (context only, not certification basis)

- **NIST SP 800-171 Rev. 3** — recommended security requirements for protecting confidentiality of CUI in nonfederal systems and organizations.
  https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-171r3.pdf

  `mildoc-lint` is a document-marking linter. It is not an 800-171 control framework. Citations here are context for the CUI rules, not a compliance claim.

## USMC orders

- **USMC FGHT 1004 Introduction to the Operations Order** — O-SMEAC / five-paragraph order purpose and structure.
  https://www.trngcmd.marines.mil/Portals/207/FGHT%201004%20Introduction%20to%20the%20Operations%20Order%20SO%20Excerpt.pdf

- **USMC Combat Orders Foundations (Basic Officer Course B2B2377)** — WARNORD and FRAGORD behavior; emphasis on early WARNORD issuance to maximize preparation time.
  https://www.trngcmd.marines.mil/Portals/207/Docs/TBS/B2B2377%20Combat%20Orders%20Foundations.pdf

## Naval correspondence

- **SECNAV M-5216.5 Department of the Navy Correspondence Manual** — Department of the Navy correspondence manual. `mildoc-lint`'s naval profile implements minimal surface checks (label order, subject-line shape) only.
  https://www.secnav.navy.mil/doni/manuals-secnav.aspx

## NAVAIR / NAMP / CSEC

- **NAVAIR Naval Aviation Maintenance Program** — public NAMP/CSEC entry point.
  https://www.navair.navy.mil/Naval-Aviation-Maintenance-Program

- **NAVAIR CSEC Help Guide** — public guide describing CSEC's checklist, audit, measurement, and discrepancy reporting role.
  https://www.navair.navy.mil/sites/g/files/jejdrs536/files/2020-10/csec_help_guide.pdf

  `mildoc-lint` does not include any CSEC checklist content. It only validates record shape.

## Repository / process context

- **Code.mil open-source guidance** — referenced as repo/process context for CDS open-source releases. Not a rule authority.

---

## Authority handling

URLs may move. The CLI prints stored authority titles, summaries, and URLs verbatim from `references.py`. If a link is dead, file an issue; the linter logic is unaffected because rules cite the *authority record*, not a live HTTP fetch.
