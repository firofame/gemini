#!/usr/bin/env bash

if [ -z "$1" ]; then
  echo "Usage: $0 <path_to_book>"
  exit 1
fi

bbook_maker \
  --model google \
  --language ml \
  --single_translate \
  --prompt "prompt.txt" \
  --book_name "$1"