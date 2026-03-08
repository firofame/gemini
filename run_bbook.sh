#!/usr/bin/env bash

if [ -z "$1" ]; then
  echo "Usage: $0 <path_to_book>"
  exit 1
fi

bbook_maker \
  --model openai \
  --model_list "gemini-3.1-pro-preview-high" \
  --openai_key "123456" \
  --api_base "http://localhost:7860/v1" \
  --batch_size 500 \
  --language ml \
  --single_translate \
  --prompt "prompt.txt" \
  --book_name "$1"