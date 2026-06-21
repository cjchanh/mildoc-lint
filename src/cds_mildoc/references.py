"""Public authorities used by built-in rules.

URLs are intentionally public and unclassified. Closed/customer rule packs should live outside
this module and should not be committed with operational examples or CUI.
"""

AUTHORITIES: dict[str, dict[str, str]] = {
    "DOD_CUI_MARKING_2024": {
        "title": "DoD CUI Markings Training Aid, 2024",
        "url": "https://www.dodcui.mil/Portals/109/Documents/Desktop%20Aid%20Docs/Cleared%20CUI%20Training%20Aid%20-%20%20Markings%202024.pdf",
        "retrieved_at_utc": "2026-06-20T00:00:00Z",
        "summary": "Mandatory DoD CUI markings include CUI at top/bottom and a CUI designation indicator block; categories belong in the designation block, not the banner.",
    },
    "DOD_CUI_BANNER_LINE": {
        "title": "DoD CUI Banner Line marking tip",
        "url": "https://www.dodcui.mil/Training/Banner-Line/",
        "retrieved_at_utc": "2026-06-20T00:00:00Z",
        "summary": "CUI banner lines reflect the overall marking; DoD guidance says not to add categories or LDCs to banner lines.",
    },
    "DOD_CUI_DI_BLOCK": {
        "title": "DoD CUI Designation Indicator Block marking tip",
        "url": "https://www.dodcui.mil/Home/Marking-Tips-for-CUI-Documents/CUI-Designation-Indicator-Block/",
        "retrieved_at_utc": "2026-06-20T00:00:00Z",
        "summary": "CUI designation indicator blocks are required on documents containing CUI and include Controlled by, category, dissemination/distribution, and POC information.",
    },
    "DODI_5200_48": {
        "title": "DoDI 5200.48 Controlled Unclassified Information",
        "url": "https://www.esd.whs.mil/Portals/54/Documents/DD/issuances/dodi/520048p.PDF",
        "retrieved_at_utc": "2026-06-20T00:00:00Z",
        "summary": "Establishes DoD policy for identifying, sharing, marking, safeguarding, storage, dissemination, destruction, and records management of CUI.",
    },
    "NIST_800_171R3": {
        "title": "NIST SP 800-171 Rev. 3",
        "url": "https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-171r3.pdf",
        "retrieved_at_utc": "2026-06-20T00:00:00Z",
        "summary": "Recommended security requirements for protecting confidentiality of CUI in nonfederal systems and organizations.",
    },
    "USMC_OSMEAC_FGHT1004": {
        "title": "USMC FGHT 1004 Introduction to the Operations Order",
        "url": "https://www.trngcmd.marines.mil/Portals/207/FGHT%201004%20Introduction%20to%20the%20Operations%20Order%20SO%20Excerpt.pdf",
        "retrieved_at_utc": "2026-06-20T00:00:00Z",
        "summary": "O-SMEAC/five-paragraph format is used across U.S., NATO, and allied forces; standard formats prevent omissions and expedite understanding.",
    },
    "USMC_COMBAT_ORDERS_FOUNDATIONS": {
        "title": "USMC Combat Orders Foundations, Basic Officer Course",
        "url": "https://www.trngcmd.marines.mil/Portals/207/Docs/TBS/B2B2377%20Combat%20Orders%20Foundations.pdf",
        "retrieved_at_utc": "2026-06-20T00:00:00Z",
        "summary": "Defines warning orders and fragmentary orders and emphasizes issuing WARNORDs early to maximize preparation time.",
    },
    "NAVAIR_NAMP_CSEC": {
        "title": "NAVAIR Naval Aviation Maintenance Program - CSEC Files",
        "url": "https://www.navair.navy.mil/Naval-Aviation-Maintenance-Program",
        "retrieved_at_utc": "2026-06-20T00:00:00Z",
        "summary": "CSEC provides checklists and audit capabilities for programs mandated within COMNAVAIRFORINST 4790.2.",
    },
    "NAVAIR_CSEC_HELP": {
        "title": "NAVAIR CSEC Help Guide",
        "url": "https://www.navair.navy.mil/sites/g/files/jejdrs536/files/2020-10/csec_help_guide.pdf",
        "retrieved_at_utc": "2026-06-20T00:00:00Z",
        "summary": "CSEC supports checklist auditing, measurement, discrepancy reporting, and correction of discrepant checkpoints.",
    },
    "SECNAV_5216_5": {
        "title": "SECNAV M-5216.5 Department of the Navy Correspondence Manual",
        "url": "https://www.marines.mil/portals/1/publications/secnav%20m%205216.5.pdf",
        "retrieved_at_utc": "2026-06-20T00:00:00Z",
        "summary": "Department of the Navy correspondence manual; built-in checks are intentionally limited to common line-label and subject-format issues.",
    },
}


def source(rule_key: str) -> str:
    ref = AUTHORITIES.get(rule_key)
    if not ref:
        return rule_key
    return f"{ref['title']} - {ref['url']}"
