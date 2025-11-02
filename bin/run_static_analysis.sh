#!/bin/bash

OUTPUT_FILE="logs/static_analysis.log"
mkdir -p logs

echo "Running static analysis..."

echo "Running ruff..." > "$OUTPUT_FILE"
ruff check . >> "$OUTPUT_FILE" 2>&1

echo "Running pyright..." >> "$OUTPUT_FILE"
pyright afs_fastapi >> "$OUTPUT_FILE" 2>&1

echo "Static analysis complete. Results are in $OUTPUT_FILE"
