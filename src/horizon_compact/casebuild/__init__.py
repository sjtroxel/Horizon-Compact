"""The case builder: from public filings to an anonymized dossier (Phase 5 code half, IMPLEMENTATION doc).

Run code, not frozen. Its output never enters the repository: it is written to the private appendix, whose
location is local configuration only (``appendix.py``). Every document and figure passes the cut-off filter
(``cutoff.py``) before anything reads it. Nothing here calls a model, AWS or the SEC except the one explicit
transport a person constructs by hand (``edgar.UrllibTransport``); tests use fakes.
"""
