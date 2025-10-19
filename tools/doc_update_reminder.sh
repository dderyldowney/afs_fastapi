#!/bin/bash

git diff --cached --name-only | grep -E "\.py$" | xargs -r -I {} echo "⚠ Reminder: Python file {} modified. Please ensure documentation (docstrings, relevant .md files) is updated."