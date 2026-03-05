#!/usr/bin/env bash

bbook_maker \
  -m openai \
  --model_lis "gemini-3.1-flash-lite-preview-high" \
  --openai_key "123456" \
  --api_base "http://localhost:7860/v1" \
  --language ml \
  --single_translate \
  --prompt "prompt.txt" \
  --book_name "book.txt"
