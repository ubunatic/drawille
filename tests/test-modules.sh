#!/usr/bin/env bash
# test main module usage from the commandline
set -o errexit  # halt on any error
set -o xtrace   # print shell commands
python -m drawille -h      > /dev/null
python -m drawille --run rect

