# experiment/readers/

The fixed briefs the independent reader is given (protocol section 12.9; search-half IMPLEMENTATION doc
section 4.9): `rejection.txt`, `scenario.txt` and `rubric.txt`, and, from 2026-10-21, `knowledge.txt` (step 3 item 4:
the read of a knowledge-probe failure, `hc case reader <id> rejection --criterion not_known`; the other three
are unchanged). Each is the system text of one kind of read; what
the reader is shown besides is assembled by `src/horizon_compact/reader/material.py` from only what section 12.9
allows. `hc case reader` refuses unless these files, `experiment/models.toml` and the reader package are committed
and pushed, and each request record holds the brief's sha256. A change to a brief after the first read is a change
to the instrument: it is logged, with its reason, in the search-half doc's section 11.
