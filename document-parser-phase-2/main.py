from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from openai import OpenAI
from pydantic import BaseModel
import json
import os


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


class AnalyzeRequest(BaseModel):
    text: str
    document_type: str


class TextRequest(BaseModel):
    text: str


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


def get_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    return OpenAI(api_key=api_key)


def load_knowledge_context(document_type: str):
    knowledge = ""

    try:
        if document_type == "prescription":
            with open(
                "knowledge_base/antibiotics_guidelines.txt",
                "r"
            ) as file:
                knowledge += file.read() + "\n"

            with open(
                "knowledge_base/pain_management_guidelines.txt",
                "r"
            ) as file:
                knowledge += file.read() + "\n"

        elif document_type == "referral":
            with open(
                "knowledge_base/cardiology_guidelines.txt",
                "r"
            ) as file:
                knowledge += file.read() + "\n"

    except Exception as e:
        print("KNOWLEDGE LOAD ERROR:", str(e))

    return knowledge


def extract_prescription(text: str):
    try:
        client = get_client()
        knowledge_context = load_knowledge_context("prescription")
        prompt = f"""
Extract prescription details.

If multiple medications are present, return them as a list.

Return strictly in JSON format:

{{
  "summary": {{
    "medications": [
      {{
        "name": "",
        "dosage": "",
        "frequency": "",
        "duration": ""
      }}
    ]
  }},
  "issues": [],
  "confidence": "High | Medium | Low",
  "recommendation": ""
}}

Rules:
- Each medication should be a separate object
- If information is missing or unclear, mark as "Missing"
- "as needed" or PRN instructions represent frequency/usage guidance, not duration
- Do not mark duration as missing if medication is clearly intended for symptom-based use
- Only mark duration as missing if a fixed treatment course is expected but absent
- Add issues for ambiguity or missing fields
- If multiple medications create confusion, add an issue
- Add a confidence level:
  - High = clear and complete information
  - Medium = minor ambiguity or missing information
  - Low = major ambiguity, OCR issues, or unclear interpretation
- If confidence is Low, recommendation should advise human review

Knowledge Context:
{knowledge_context}

Prescription:
{text}
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={"type": "json_object"},
        )

        return json.loads(response.choices[0].message.content)

    except Exception as e:
        print("ERROR:", str(e))
        return {"error": str(e)}


def extract_referral(text: str):
    try:
        client = get_client()
        knowledge_context = load_knowledge_context("referral")
        prompt = f"""
Extract referral details.

Return strictly in JSON format:

{{
  "summary": {{
    "specialist": "",
    "diagnosis": "",
    "referral_reason": "",
    "urgency": ""
  }},
  "issues": [],
  "confidence": "High | Medium | Low",
  "recommendation": ""
}}

Rules:
- If information is missing, return "Missing"
- Add issues for ambiguity or unclear text
- Confidence should reflect clarity of the referral
- If confidence is Low, recommendation should advise human review

Knowledge Context:
{knowledge_context}

Referral:
{text}
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={"type": "json_object"},
        )

        return json.loads(response.choices[0].message.content)

    except Exception as e:
        print("ERROR:", str(e))
        return {"error": str(e)}


@app.post("/extract")
def extract(data: AnalyzeRequest):
    document_type = data.document_type.lower()

    if document_type == "prescription":
        return extract_prescription(data.text)

    if document_type == "referral":
        return extract_referral(data.text)

    return {"error": "Unsupported document type"}


@app.post("/clean_text")
def clean_text(data: TextRequest):
    try:
        client = get_client()

        prompt = f"""
Clean and correct the following OCR-extracted healthcare document text.

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
            temperature=0,
        )

        return {"cleaned_text": response.choices[0].message.content.strip()}

    except Exception as e:
        return {"error": str(e)}
