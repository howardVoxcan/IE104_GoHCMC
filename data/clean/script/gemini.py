# test_gemini_normalize_fixed.py
import os
import re
import csv
import random
import pandas as pd
import unidecode
from tqdm import tqdm
from dotenv import load_dotenv

# new recommended client import
from google import genai

load_dotenv()

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_KEY:
    raise ValueError("Missing GEMINI_API_KEY in environment/.env")

# configure client
client = genai.Client(api_key=GEMINI_KEY)

# ----------------- helpers -----------------
CJK_RE = re.compile(r"[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]+")

def normalize_location(text):
    if not isinstance(text, str):
        return ""
    text = CJK_RE.sub("", text)
    return unidecode.unidecode(text).strip()

def generate_code(idx):
    return f"AC{idx+1:03d}"

def sample_rating():
    r = random.random()
    if r < 0.03:
        return 3.5
    if r > 0.97:
        return 5.0
    # biased toward center using beta
    val = 3.8 + random.betavariate(5.0, 3.0) * (4.7 - 3.8)
    return round(val, 1)

def call_gemini_prompt(prompt, preferred_models=None):
    """
    Try to generate text using preferred_models list (in order).
    If fails, list available models and return None.
    """
    if preferred_models is None:
        preferred_models = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]

    for m in preferred_models:
        try:
            print(f"→ Calling Gemini model: {m}")
            resp = client.models.generate_content(model=m, contents=prompt)
            # resp may have .text or .content fields depending on SDK version
            if hasattr(resp, "text") and resp.text:
                return resp.text.strip()
            # sometimes resp is dict-like
            if isinstance(resp, dict):
                for k in ("text", "output", "content"):
                    if k in resp and resp[k]:
                        return resp[k].strip()
                # fallback: try responses list
                if "responses" in resp and resp["responses"]:
                    return resp["responses"][0].get("text", "").strip()
            # try attribute access
            try:
                return str(resp).strip()
            except Exception:
                pass
        except Exception as e:
            print(f"⚠️ Model {m} failed: {e}")
            # try next model
            continue

    # if all preferred models failed, attempt to list available models (for debugging)
    try:
        print("Attempting to list models from API (for diagnostics)...")
        models = client.models.list()
        print("Available models (sample 30 chars each):")
        for md in models:
            # md may be a dict or object
            name = md.get("name") if isinstance(md, dict) else getattr(md, "name", None)
            display = (name[:80] + "...") if name else str(md)[:80]
            print(" -", display)
    except Exception as e:
        print("⚠️ Could not list models:", e)

    return None

# ----------------- main test function -----------------
def test_normalize(input_csv="test_data.csv", output_csv="test_output.csv"):
    print("Starting test normalize (fixed)...")
    df = pd.read_csv(input_csv)
    n = len(df)
    print(f"Loaded {n} rows")

    # normalize LOCATION, generate CODE/TYPE
    df["LOCATION"] = df["LOCATION"].apply(lambda x: normalize_location(x) if pd.notna(x) else x)
    df["CODE"] = [generate_code(i) for i in range(n)]
    df["TYPE"] = "Accommodation"

    # Ensure numeric ratings: convert to numeric, invalid -> NaN -> fillna(0)
    if "RATING" in df.columns:
        df["RATING"] = pd.to_numeric(df["RATING"], errors="coerce").fillna(0.0)

    for i, row in tqdm(df.iterrows(), total=n, desc="Processing rows"):
        code = row["CODE"]

        # Rating fix: any <= 0 -> sample
        try:
            rating_val = float(row["RATING"]) if "RATING" in df.columns else 0.0
        except Exception:
            rating_val = 0.0
        if rating_val <= 0.0:
            new_rating = sample_rating()
            df.at[i, "RATING"] = new_rating
            print(f"{code}: rating set -> {new_rating}")

        # Address: call Gemini if empty
        if "Address" in df.columns and (pd.isna(row["Address"]) or not str(row["Address"]).strip()):
            prompt = f"Provide the full English postal address (one line) for the place named: '{row.get('Name', row.get('LOCATION', ''))}'. If unknown, answer briefly 'Address unknown'."
            addr = call_gemini_prompt(prompt)
            if addr:
                df.at[i, "Address"] = addr
                print(f"{code}: got address -> {addr}")

        # Description: call Gemini if empty
        if "Description" in df.columns and (pd.isna(row["Description"]) or not str(row["Description"]).strip()):
            long_desc = row.get("Long Description", "")
            if pd.notna(long_desc) and str(long_desc).strip():
                prompt = f"Summarize in one short English sentence: {long_desc}"
            else:
                prompt = f"Write one short English sentence describing the place named '{row.get('Name', row.get('LOCATION', ''))}'."
            desc = call_gemini_prompt(prompt)
            if desc:
                # keep only first sentence
                desc = re.split(r"[\\.\\!?]\\s+", desc.strip())[0].strip()
                df.at[i, "Description"] = desc
                print(f"{code}: got description -> {desc}")

    df.to_csv(output_csv, index=False, quoting=csv.QUOTE_NONNUMERIC)
    print(f"Saved output to {output_csv}")

if __name__ == "__main__":
    test_normalize()
