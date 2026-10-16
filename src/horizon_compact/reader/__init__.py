"""The independent reader (protocol section 12.9; search-half IMPLEMENTATION doc section 4.9, decision 3).

A model from another vendor that has not seen the grid's results reads each rejection on criterion 3 or 4,
each case's scenario and each case's rubric, from a fixed brief and only the material section 12.9 allows.
This package is outside ``casebuild/`` on purpose: the builder must never import anything that could carry
the company's outcome, and the reader reads the rubric. Nothing here imports the analysis, the sweep or the
simulation, so no result can reach a reader (``tests/test_architecture.py`` proves it).
"""
