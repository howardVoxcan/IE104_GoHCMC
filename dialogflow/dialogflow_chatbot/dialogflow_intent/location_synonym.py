import csv
import pandas as pd
import re

# List of location names
locations = pd.read_csv('data/clean/data.csv')['LOCATION']

# Abbreviation map
abbrev_map = {
    "hotel": ["htl", "hotl", "hoetl"],
    "saigon": ["sg", "saigon", "sai gon", "sai-gon"],
    "airport": ["airprt", "airpt", "arpt"],
    "street": ["st", "strt", "st."],
    "restaurant": ["resto", "restaurent", "rest"],
    "market": ["mkt", "mrkt"],
    "park": ["pk", "prak"],
    "station": ["stn", "sta", "statn"],
    "metro": ["subway", "underground"],
    "café": ["cafe", "coffe", "coffé"],
    "museum": ["musuem", "muzeum"],
    "pagoda": ["pogoda", "pagdoa"],
    "temple": ["templ", "tempel"]
}

# Strip accents manually
def strip_accents(text):
    replacements = {
        "àáâãäå": "a", "èéêë": "e", "ìíîï": "i", "òóôõö": "o", "ùúûü": "u",
        "ýÿ": "y", "ç": "c", "ñ": "n", "đ": "d", "ÀÁÂÃÄÅ": "A", "ÈÉÊË": "E",
        "ÌÍÎÏ": "I", "ÒÓÔÕÖ": "O", "ÙÚÛÜ": "U", "Ý": "Y", "Ç": "C", "Ñ": "N", "Đ": "D"
    }
    for accented, replacement in replacements.items():
        text = re.sub(f"[{accented}]", replacement, text)
    return text

# Generate synonyms
def generate_synonyms(name):
    base = name.lower()
    base_unaccented = strip_accents(base)
    synonyms = set([base, base_unaccented])
    for key, variations in abbrev_map.items():
        if key in base:
            for v in variations:
                synonyms.add(base.replace(key, v))
                synonyms.add(base_unaccented.replace(key, v))
    return list(synonyms)

# Write to CSV with double quotes
with open("dialogflow/dialogflow_chatbot/locations.csv", mode="w", newline='', encoding="utf-8") as file:
    writer = csv.writer(file, quoting=csv.QUOTE_ALL)
    writer.writerow(["value", "synonym"])
    for loc in locations:
        for synonym in generate_synonyms(loc):
            writer.writerow([loc, synonym])

print("CSV generated: dialogflow_locations_extended.csv")