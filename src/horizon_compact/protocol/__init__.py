"""The pre-registration's machinery (Phase 3.5 IMPLEMENTATION doc section 4): the frozen code sets, the lock,
the official-sweep gate and the case mode.

Run code under decision 1, not frozen. A change to which files a frozen set holds changes that set's hash,
so the gate refuses it against the lock like any other change to the set.
"""
