#!/usr/bin/env bash

bbook_maker \
  --model openai \
  --model_list "gemini-3.1-pro-preview-high" \
  --openai_key "123456" \
  --api_base "http://localhost:7860/v1" \
  --batch_size 500 \
  --language ml \
  --single_translate \
  --prompt "prompt.txt" \
  --book_name "book.txt"