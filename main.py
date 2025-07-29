import json
import os
import re
from dotenv import load_dotenv
from openai import OpenAI

# Завантаження змінних із .env
load_dotenv()

json_file = os.getenv("JSON_FILE")
start_time = float(os.getenv("START_TIME"))
end_time = float(os.getenv("END_TIME"))
api_key = os.getenv("OPENAI_API_KEY")

# Завантаження JSON
with open(json_file, "r", encoding="utf-8") as f:
    data = json.load(f)

# Витяг сегментів у заданому діапазоні
segments = [
    seg for seg in data["segments"]
    if seg["end"] > start_time and seg["start"] < end_time
]
extracted_text = " ".join(seg["text"].strip() for seg in segments)

# Промпт до GPT
prompt = f"""Проанализируй следующий фрагмент текста из новостного видео:

\"\"\"{extracted_text}\"\"\"

Сгенерируй:
1. Пять коротких и ёмких заголовков (на русском языке, как список с нумерацией).
2. Пять-десять тематических тегов (как JSON-массив слов, без решеток).
3. Пять вариантов краткого описания (по 2–3 предложения, также в нумерованном списке).
"""

# Запит до OpenAI GPT-4o
client = OpenAI(api_key=api_key)

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "Ты помощник, который создает заголовки, описания и теги для новостного видео."},
        {"role": "user", "content": prompt}
    ],
    temperature=0.7
)

reply = response.choices[0].message.content.strip()

# Парсинг заголовків
headlines = re.findall(r"^\s*1\.\s*(.+?)(?:\n2\.|\Z)", reply, re.DOTALL)
if not headlines:
    headlines = re.findall(r"^\s*\d+\.\s*(.+)", reply, re.MULTILINE)

headlines = [h.strip() for h in headlines[:5]]

# Парсинг тегів
tags_match = re.search(r"\[([^\]]+)\]", reply, re.DOTALL)
tags = []
if tags_match:
    try:
        tags_raw = f"[{tags_match.group(1)}]"
        tags = json.loads(tags_raw)
        tags = [t.strip() for t in tags if isinstance(t, str)]
    except json.JSONDecodeError:
        tags = []

# Парсинг описів
descriptions_section = re.split(r"(?i)описания|описание", reply)
descriptions_text = descriptions_section[-1] if len(descriptions_section) > 1 else reply
description_matches = re.findall(r"\d+\.\s*(.+)", descriptions_text)
descriptions = [d.strip() for d in description_matches[:5]]

# Підготовка до запису
output_data = {
    "source_file": json_file,
    "start_time": start_time,
    "end_time": end_time,
    "input_text": extracted_text,
    "headlines": headlines,
    "tags": tags,
    "descriptions": descriptions,
    "raw_response": reply
}

# Запис у JSON
with open("output.json", "w", encoding="utf-8") as out:
    json.dump(output_data, out, indent=2, ensure_ascii=False)

print("✅ Збережено в 'output.json'")

