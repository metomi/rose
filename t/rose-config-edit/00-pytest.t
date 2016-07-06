#!/bin/bash
set -eu

# These unit tests are run with py.test, which requires the 'pytest-tap' plugin
# to output in TAP format

skip_all() {
    echo "1..0 # SKIP $@"
    exit
}

if ! python -c 'import pytest, tap'; then
    skip_all 'Python package "pytest-tap" not installed'
else
    # Ask py.test to output in TAP format
    py.test --tap-stream
fi
