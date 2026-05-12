import streamlit as st
import requests
from PIL import Image
import pytesseract
from io import BytesIO
import re

st.title("AI Workflow Assistant for Unstructured data Processing")

st.markdown("### Try sample inputs:")
st.code("Prescription: Amoxicillin 500mg twice daily for 7 days")
st.code("Prescription: Amoxicillin 500, take regularly")

st.markdown("""
### What this does:
- Extracts structured data from unstructured prescription text
- Identifies missing or ambiguous information
- Handles multiple medications
- Provides recommendation for next action
""")

st.markdown("## Input")

document_type = st.selectbox(
    "Select Document Type",
    ["prescription", "referral"]
    )

uploaded_file = st.file_uploader(
    f"Upload {document_type} document:",
    type=["png", "jpg", "jpeg", "pdf"]
)

def extract_text_from_image(file):
    try:
        file_bytes = file.getvalue()  # safer for Streamlit UploadedFile
        image = Image.open(BytesIO(file_bytes)).convert("RGB")
        text = pytesseract.image_to_string(image)
        return text
    except Exception as e:
        st.error(f"Image processing error: {str(e)}")
        return ""

def clean_ocr_text(text):
    # Remove random numbers / noise lines
    text = re.sub(r"\b(10|12|14|18|20)\b", "", text)

    # Remove repeated junk characters
    text = re.sub(r"(\b\w\b\s*){2,}", "", text)

    # Fix common OCR mistakes
    text = text.replace("twi ce", "twice")
    text = text.replace("Paraceptmol", "Paracetamol")

    # Merge broken lines
    text = " ".join(text.split())

    return text

def llm_clean_text(text: str):
    url = "http://127.0.0.1:8000/clean_text"

    try:
        response = requests.post(url, json={"text": text}, timeout=30)
    except requests.exceptions.ReadTimeout:
        st.error("LLM cleanup timed out. Proceeding without LLM cleanup.")
        return text

    if response.status_code == 200:
        return response.json().get("cleaned_text", "")
    else:
        st.error(f"LLM cleanup failed: {response.status_code}")
        return text
    
def extract_document(text: str):
    url = "http://127.0.0.1:8000/extract"

    payload = {
    "text": text,
    "document_type": document_type
        }

    response = requests.post(url, json=payload, timeout=10)

    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"API Error: {response.status_code}")
        st.text(response.text)
        return None

# Input handling
if uploaded_file is not None:
    raw_text = extract_text_from_image(uploaded_file)
    if not raw_text.strip():
        st.error("Unable to extract text from uploaded document")
        st.stop()
    cleaned_text = clean_ocr_text(raw_text)
    llm_cleaned_text = llm_clean_text(cleaned_text)
    st.subheader("Extracted Text")
    st.text(raw_text)

    st.subheader("Cleaned Text")
    st.text(llm_cleaned_text)

    text = llm_cleaned_text
else:
    text = st.text_area(f"Enter {document_type} text:", height=200)

if st.button("Process"):
    if not text or text.strip() == "":
        st.warning("Please provide input")
    else:
        try:
            output = extract_document(text)

            st.subheader("AI Analysis Result")

            confidence = output.get("confidence", "Low")

            if confidence == "High":
                st.success("✅ High Confidence Extraction")
            elif confidence == "Medium":
                st.warning("⚠ Medium Confidence Extraction")
            else:
                st.error("❌ Low Confidence Extraction")

            st.json(output)

        except Exception as e:
            st.error(f"Error: {str(e)}")