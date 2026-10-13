# Errata to the pre-registration protocol, version 1

`protocol-v1.md` is frozen at `prereg-v1` (`649e8b9b8f1dde0e3698be0d279b62fef07ad70b`, tagged 2026-10-13), and its
hash is in the lock. Section 14 allows one kind of change after the tag without a new version: **an erratum, which
changes no computation, no content and no rule.** Each one is listed here, dated, with the text as tagged and how it
should be read. The protocol itself is never edited, and no lock hashes this file.

## 2026-10-13: notes left from drafting

Written by Claude (Opus) the day of the tag, before any official run; reviewed by sjtroxel.

**E1. The status line** (the second and third bullets at the top). As tagged:

> **Status:** DRAFT, written section by section in Phase 3.5 (build step 10) and reviewed by him one section at a
> time. [...] **Sections drafted:** all fifteen; 1 reviewed (his, 2026-10-09), 2 to 15 awaiting his review.

**Read as:** *Status: frozen at `prereg-v1`. All fifteen sections were reviewed and approved by him: section 1 on
2026-10-09, sections 2 to 15 on 2026-10-12, and the three corrections made after that approval (sections 1.1, 1.6
and 2.7) on 2026-10-13, before the tag.* The rest of that bullet stands: no bracket holds a value still to be
supplied, and each bracket that remains records how a passage was reached.

**E2. "For his review" in drafting notes.** Nine bracketed notes say a passage was drafted, added, settled or
corrected "for his review" (sections 2.2, 2.4, 2.6, 2.7, 5, 7.4, 9.4 twice, and 9.5). **Read each as:** reviewed and
approved with sections 2 to 15 on 2026-10-12, except the correction in 2.7, which was read and accepted on
2026-10-13, before the tag. No word of the passages themselves changes.

**E3. Section 2's opening note.** As tagged: *"[2.5 and 2.6 wait for build steps 7 and 8.]"* **Read as:** both
sections were written before the tag. Section 2.5 records that step 8 was not run (decided 2026-10-12), and section
2.6 records step 7's result.

**E4. Section 4's opening note.** As tagged: *"[Each hash in this section is written on tag day from the lock
(`prereg.lock`); the lock is the authority.]"* **Read as:** no hash was added to section 4 on tag day (a document
cannot hold the hash of the commit that contains it); every content and instrument hash is in
`experiment/protocol/prereg.lock`, which is the authority, as the note says.

**E5. Section 15's opening note.** As tagged: *"[Filled on tag day: the protocol commit, the tag object, the CI run,
the tag ruleset as read back, the Software Heritage archive's identifier and visit date, the release, and the gate's
dry runs against the tag (`docs/phases/evidence/phase-3.5/tag-record.md`).]"* **Read as:** those values are recorded
in `docs/phases/evidence/phase-3.5/tag-record.md`, not in this document, which was committed before any of them
existed. In short: protocol commit `649e8b9`; tag object `c949580`; CI run `38355727520`; ruleset `24974909`;
Software Heritage snapshot `swh:1:snp:df7dda44d8cf804cf004e73031249c8e5fe45e00`, visited 2026-10-13T06:24:52Z.
