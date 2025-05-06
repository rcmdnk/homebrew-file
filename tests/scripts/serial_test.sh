#!/usr/bin/env bash
pytest -p no:cacheprovider -o "markers=serial" -c /dev/null tests/test_serial.py
