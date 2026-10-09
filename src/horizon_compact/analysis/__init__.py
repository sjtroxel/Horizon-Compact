"""The frozen analysis code (Phase 3 IMPLEMENTATION doc section 4). Phase 3.5 hashes this folder.

It imports nothing outside the package except the experiment loader and the standard and analysis-group
libraries (numpy, scipy, statsmodels). It never imports ``horizon_compact.simulation``; the simulations import
the analysis, never the other way (``tests/test_architecture.py`` holds both rules).
"""

# The version of the results object (doc section 4). It changes when the object's fields or meaning do.
# 2 (step 12): shares' intervals are Welch t-intervals, not bootstrap; the seed and resample fields went, and
# the degrees of freedom and decision 10's two rules came in.
RESULTS_VERSION = 2
