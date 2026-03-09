#!/usr/bin/env bash

if [ -z "$1" ]; then
  echo "Usage: $0 <path_to_book>"
  exit 1
fi

bbook_maker \
  --model openai \
  --model_list "gemini-3.1-pro-high" \
  --openai_key "sk-8e2af9daeacb423e9ac505c1faa6c976" \
  --api_base "http://127.0.0.1:8045/v1" \
  --batch_size 100 \
  --language ml \
  --single_translate \
  --prompt "prompt.txt" \
  --book_name "$1"