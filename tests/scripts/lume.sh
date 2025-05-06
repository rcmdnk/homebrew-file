#!/usr/bin/env bash

PROJECT_DIR=$PWD
IMAGE=macos-sequoia-xcode:latest

trap 'lume stop $IMAGE;exit 0' SIGINT SIGTERM
lume run "$IMAGE" --no-display  --shared-dir "$PROJECT_DIR:ro" &
LUME_PID=$!
wait $LUME_PID
