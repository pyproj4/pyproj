#!/bin/bash
pip install sphinx sphinx_rtd_theme
cd docs && make html && cd ..
