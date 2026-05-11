from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import Request
from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
from fastapi.staticfiles import StaticFiles
import os
import json

app = FastAPI()
print("CORRECT MAIN FILE LOADED")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
# Request schema
class AnalyzeRequest(BaseModel):
    text: str
    document_type: str
    
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):

    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )
# OpenAI setup
def get_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    return OpenAI(api_key=api_key)

# Core extraction logic
def extract_prescription(text: str):
    try:
        client = get_client()

        prompt = f"""
Extract prescription details.

If multiple medications are present, return them as a list.

Return strictly in JSON format:

{{
  "medications": [
    {{
      "name": "",
      "dosage": "",
      "frequency": "",
      "duration": ""
    }}
  ],
  "issues": [],
  "confidence": "High | Medium | Low",
  "recommendation": ""
}}

Rules:
- Each medication should be a separate object
- If information is missing or unclear, mark as "Missing"
- Add issues for ambiguity or missing fields
- If multiple medications create confusion, add an issue
- Add a confidence level:
  - High = clear and complete information
  - Medium = minor ambiguity or missing information
  - Low = major ambiguity, OCR issues, or unclear interpretation
- If confidence is Low, recommendation should advise human review

Prescription:
{text}
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content

        # Debug logs
        print("RAW RESPONSE:", response)
        print("CONTENT:", content)

        # Clean markdown code block if present
        if "```" in content:
            parts = content.split("```")
            for part in parts:
                if "{" in part and "}" in part:
                    content = part.strip()
                    break

        return json.loads(content)

    except Exception as e:
        print("ERROR:", str(e))
        return {
            "error": str(e)
        }

# Referral extraction logic
def extract_referral(text: str):
    try:
        client = get_client()

        prompt = f"""
Extract referral details.

Return strictly in JSON format:

{{
  "specialist": "",
  "diagnosis": "",
  "referral_reason": "",
  "urgency": "",
  "issues": [],
  "confidence": "High | Medium | Low"
}}

Rules:
- If information is missing, return "Missing"
- Add issues for ambiguity or unclear text
- Confidence should reflect clarity of the referral

Referral:
{text}
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content

        return json.loads(content)

    except Exception as e:
        print("ERROR:", str(e))
        return {
            "error": str(e)
        }

# API endpoint
@app.post("/extract")
def extract(data: AnalyzeRequest):

    print("DOCUMENT TYPE:", data.document_type)

    if data.document_type.lower() == "prescription":
        return extract_prescription(data.text)

    elif data.document_type.lower() == "referral":
        return extract_referral(data.text)

    return {
        "error": "Unsupported document type"
    }
# ✅ ADD THIS NEW ENDPOINT (separate, not inside function)
@app.post("/clean_text")
def clean_text(data: AnalyzeRequest):
    try:
        client = get_client()

        prompt = f"""
Clean and correct the following OCR-extracted prescription text.

Fix:
- spelling mistakes
- broken words
- spacing issues

Do NOT add new information.
Return ONLY the corrected text.

Text:
{data.text}
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        return {
            "cleaned_text": response.choices[0].message.content.strip()
        }

    except Exception as e:
        return {"error": str(e)}
