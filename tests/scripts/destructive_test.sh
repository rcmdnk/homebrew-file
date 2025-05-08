#!/usr/bin/env bash
if pytest --help | grep -q -- '-n numprocesses';then
  pytest -s -vvv -n0 -p no:cacheprovider -o "markers=destructive" -c /dev/null tests/test_destructive.py
else
  pytest -s -vvv -p no:cacheprovider -o "markers=destructive" -c /dev/null tests/test_destructive.py
fi
