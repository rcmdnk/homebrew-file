#!/usr/bin/env bash

for f in "$@";do
  echo 'test content' > "$f"
done
