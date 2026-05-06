## Summary

Describe the change in one or two sentences.

## Boundary Checklist

- [ ] This change contains no CUI, PII, real unit documents, customer data, controlled technical data, operational details, or non-public checklist content.
- [ ] Examples and fixtures are synthetic.
- [ ] Public docs do not claim compliance certification, classification review, CUI determination, tactical-plan generation, or endorsement by a government organization.
- [ ] New or changed rules are deterministic and backed by public sources.
- [ ] README and docs match implemented behavior.

## Verification

- [ ] `python -m pytest`
- [ ] `ruff check .`
- [ ] `mildoc-lint lint examples --profile all`
