"""What the memo scan sends its two models, and how their replies are read (Phase 5.5 doc §5.4).

Pure functions over strings, like ``material.py``: no file, no provider, no record. ``caseprobe/memos.py``
owns those. Two passes read a model-written text for a company name (protocol §12.11):

* ``memo-names`` (Haiku 5.5): a batch of memos under opaque ids, answered with the names found in each. The
  ids are positions in a shuffled batch (``m1``, ``m2``, ...), never a run id and never anything that holds an
  objective; a reply must account for every id of its batch.
* ``memo`` (the independent reader): one memo and the words flagged in it, answered per flagged word and for
  the memo as a whole. A memo is *confirmed* if any answer is "yes", *unclear* if none is and any is
  "cannot_tell", and *cleared* otherwise.

Nothing here can carry a dossier, a result or an objective: the builders take a memo's text and words only.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, ConfigDict, ValidationError

from horizon_compact.reader.read import json_object

NAMES_BATCH = 25
Answer = Literal["yes", "no", "cannot_tell"]
CONFIRMED, UNCLEAR, CLEARED = "confirmed", "unclear", "cleared"


@dataclass(frozen=True)
class MemoMaterial:
    user: str
    parts: dict[str, str]  # part name -> sha256 of the text sent


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def batch_ids(count: int) -> tuple[str, ...]:
    """Opaque ids for a batch of ``count`` memos: positions in the shuffled batch, nothing more."""
    return tuple(f"m{n}" for n in range(1, count + 1))


def names_material(texts: Sequence[str]) -> MemoMaterial:
    """One batch for the ``memo-names`` brief; ``texts`` are in the batch's shuffled order."""
    blocks = [
        f"[memo {memo_id}]\n{text.strip()}\n[end of memo {memo_id}]"
        for memo_id, text in zip(batch_ids(len(texts)), texts, strict=True)
    ]
    user = "\n\n".join(blocks)
    return MemoMaterial(user, {"Memos": _sha256(user)})


def memo_material(text: str, words: Sequence[str]) -> MemoMaterial:
    """One flagged memo and its numbered flagged words for the ``memo`` brief."""
    listed = "\n".join(f"{n}. {word}" for n, word in enumerate(words, start=1)) or "(none)"
    memo = f"[Memo]\n{text.strip()}\n[end of Memo]"
    flagged = f"[Flagged words]\n{listed}\n[end of Flagged words]"
    return MemoMaterial(
        f"{memo}\n\n{flagged}",
        {"Memo": _sha256(text.strip()), "Flagged words": _sha256(listed)},
    )


# --- the replies the two briefs ask for -----------------------------------------------------------------


class _Names(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)
    memos: dict[str, list[str]]


class _Flag(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)
    flag: int
    names_a_real_company: Answer
    reason: str


class _Memo(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)
    flags: list[_Flag]
    memo: Answer


def parse_names_reply(
    text: str, ids: Sequence[str]
) -> tuple[dict[str, list[str]] | None, str | None]:
    """The names found per id, or the reason the reply is not an account of exactly ``ids`` (a kind of
    failure, never the text). A name is a non-blank string; a blank one is dropped, not a failure."""
    parsed = json_object(text)
    if parsed is None:
        return None, "the reply holds no JSON object"
    try:
        reply = _Names.model_validate(parsed)
    except ValidationError:
        return None, "the reply does not fit the brief's format"
    if set(reply.memos) != set(ids):
        return None, "the reply does not account for every memo of its batch, and only those"
    return {i: [n.strip() for n in reply.memos[i] if n.strip()] for i in ids}, None


@dataclass(frozen=True)
class MemoVerdict:
    verdict: str  # CONFIRMED, UNCLEAR or CLEARED
    answers: dict[str, str]  # "memo" and "1", "2", ... to the reader's answer


def parse_memo_reply(text: str, flag_count: int) -> tuple[MemoVerdict | None, str | None]:
    """The reader's verdict on a memo, or the reason the reply is not one. Every flagged word is answered
    exactly once, and the memo as a whole is answered."""
    parsed = json_object(text)
    if parsed is None:
        return None, "the reply holds no JSON object"
    try:
        reply = _Memo.model_validate(parsed)
    except ValidationError:
        return None, "the reply does not fit the brief's format"
    if sorted(f.flag for f in reply.flags) != list(range(1, flag_count + 1)):
        return None, "the reply does not answer every flagged word exactly once"
    answers: dict[str, str] = {str(f.flag): f.names_a_real_company for f in reply.flags}
    answers["memo"] = reply.memo
    return MemoVerdict(verdict_of(answers), answers), None


def verdict_of(answers: Mapping[str, str]) -> str:
    """One "yes" confirms a name; else one "cannot_tell" leaves the memo unclear; else it is cleared."""
    if "yes" in answers.values():
        return CONFIRMED
    if "cannot_tell" in answers.values():
        return UNCLEAR
    return CLEARED
