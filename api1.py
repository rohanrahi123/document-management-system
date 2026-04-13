
from flask import Flask, request, jsonify, render_template, send_from_directory
from rapidfuzz import fuzz
import os
import json
import uuid

import re
import spacy

#  NEW (OCR SUPPORT)


API_KEY = "mysecureapikey123"

def verify_api_key(request):
    key = request.headers.get("x-api-key")
    if key != API_KEY:
        return False
    return True

# APP INITIALIZATION

app = Flask(__name__, template_folder=".")

# Load NLP model (optional support)
try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
except:
    nlp = None

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# File paths
JSON_FILE = os.path.join(BASE_DIR, "documents.json")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

# Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Create JSON storage file if not exists
if not os.path.exists(JSON_FILE):
    with open(JSON_FILE, "w") as f:
        json.dump([], f)

# 🔥 SET TESSERACT PATH (CHANGE IF DIFFERENT)


# UTILITY FUNCTIONS

# Read all stored documents
def read_documents():
    try:
        with open(JSON_FILE, "r") as f:
            return json.load(f)
    except:
        return []

# Write documents to JSON file
def write_documents(data):
    with open(JSON_FILE, "w") as f:
        json.dump(data, f, indent=4)

def clean_text(text):
    text = text.lower()
    text = re.sub(r"\s+", " ", text)  # normalize spaces
    text = re.sub(r"[^a-z0-9 ]", "", text)  # remove symbols/noise
    return text.strip()

# TEXT EXTRACTION (UPDATED WITH OCR SUPPORT)


import requests

def extract_text_from_pdf(file_path):

    full_text = ""

    # 1️⃣ Try normal extraction
    try:
        import pdfplumber
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
    except:
        pass

    # 2️⃣ If no text → use OCR API
    if len(full_text.strip()) < 30:

        print("🔍 Using OCR API...")

        try:
            url = "https://api.ocr.space/parse/image"

            with open(file_path, 'rb') as f:
                response = requests.post(
                    url,
                    files={"file": f},
                    data={
                        "apikey": "helloworld",  # free key
                        "language": "eng"
                    }
                )

            result = response.json()

            full_text = result["ParsedResults"][0]["ParsedText"]

        except Exception as e:
            print("❌ OCR API Failed:", e)

    return full_text.strip()

    
    # 2️ If Less Text → Assume Scanned PDF
    
    if len(full_text.strip()) < 30:

        print("🔍 Scanned document detected. Running OCR...")

        try:
            images = convert_from_path(file_path)

            for image in images:
                ocr_text = pytesseract.image_to_string(image)
                full_text += ocr_text + "\n"

        except Exception as e:
            print("❌ OCR Failed:", e)

    return full_text.strip()


# STRUCTURED FIELD EXTRACTION (UNCHANGED)


def extract_structured_fields(text):

    data = {}
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    text_lower = text.lower()

    doc_type = detect_document_type(text)
    data["Detected Document Type"] = doc_type

    # Aadhaar Card Extraction
    
    if doc_type == "Aadhaar Card":

        aadhaar = re.findall(r"\b\d{4}\s?\d{4}\s?\d{4}\b", text)
        if aadhaar:
            data["Aadhaar Number"] = list(set(aadhaar))

        # Name = line before Aadhaar number
        for i, line in enumerate(lines):
            if re.search(r"\d{4}\s?\d{4}\s?\d{4}", line):
                if i > 0:
                    name = lines[i-1]
                    if not re.search(r"\d", name):
                        data["Name"] = [name]
                break

        dob = re.findall(r"\b\d{2}/\d{2}/\d{4}\b", text)
        if dob:
            data["Date of Birth"] = list(set(dob))

        gender = re.findall(r"\bMale\b|\bFemale\b", text, re.IGNORECASE)
        if gender:
            data["Gender"] = list(set(gender))

    # PAN Card Extraction
    
    elif doc_type == "PAN Card":

        pan = re.findall(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", text)
        if pan:
            data["PAN Number"] = list(set(pan))

        for i, line in enumerate(lines):
            if re.search(r"[A-Z]{5}[0-9]{4}[A-Z]", line):
                if i > 0:
                    name = lines[i-1]
                    if not re.search(r"\d", name):
                        data["Name"] = [name]
                break

        for line in lines:
            if "father" in line.lower():
                data["Father Name"] = [line]

    # Marksheet Extraction
    
    elif doc_type == "Marksheet":

        roll = re.findall(r"Roll\s*No[:\s]*([A-Za-z0-9\-]+)", text, re.IGNORECASE)
        if roll:
            data["Roll Number"] = roll

        for line in lines:
            if "name" in line.lower():
                data["Student Name"] = [line.split(":")[-1].strip()]
                break

        subject_marks = {}
        matches = re.findall(r"([A-Za-z ]+)\s+(\d{1,3})", text)
        for subject, mark in matches:
            if int(mark) <= 100:
                subject_marks[subject.strip()] = mark

        if subject_marks:
            data["Subject Marks"] = subject_marks

        total = re.findall(r"Total[:\s]*([0-9]+)", text, re.IGNORECASE)
        if total:
            data["Total Marks"] = total

    # Invoice Extraction
    
    elif doc_type == "Invoice":

        invoice = re.findall(r"Invoice\s*(No|Number)[:\s]*([A-Za-z0-9\-]+)", text, re.IGNORECASE)
        if invoice:
            data["Invoice Number"] = [invoice[0][1]]

        gstin = re.findall(r"\b\d{2}[A-Z]{5}[0-9]{4}[A-Z][A-Z0-9]{3}\b", text)
        if gstin:
            data["GSTIN"] = list(set(gstin))

        date = re.findall(r"\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b", text)
        if date:
            data["Date"] = list(set(date))

    return data

# DOCUMENT TYPE DETECTION (UNCHANGED)

def detect_document_type(text):

    text_lower = text.lower()

    scores = {
        "Aadhaar Card": 0,
        "PAN Card": 0,
        "Marksheet": 0,
        "Invoice": 0
    }

    # Aadhaar indicators
    if "uidai" in text_lower:
        scores["Aadhaar Card"] += 3
    if re.search(r"\b\d{4}\s?\d{4}\s?\d{4}\b", text):
        scores["Aadhaar Card"] += 4
    if "government of india" in text_lower:
        scores["Aadhaar Card"] += 2
    if "Adhar Number" in text_lower:
        scores["Aadhaar Card"] += 2

    # PAN indicators
    if "income tax department" in text_lower:
        scores["PAN Card"] += 3
    if re.search(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", text):
        scores["PAN Card"] += 4
    if "permanent account number" in text_lower:
        scores["PAN Card"] += 2
    if "PAN" in text_lower:
        scores["PAN Card"] += 2
    

    # Marksheet indicators
    if "marksheet" in text_lower:
        scores["Marksheet"] += 3
    if "roll no" in text_lower:
        scores["Marksheet"] += 3
    if "subject" in text_lower:
        scores["Marksheet"] += 2
    if "Pass Year" in text_lower:
        scores["Marksheet"] += 2
    if "School Name" in text_lower:
        scores["Marksheet"] += 3

    # Invoice indicators
    if "invoice" in text_lower:
        scores["Invoice"] += 3
    if "gstin" in text_lower:
        scores["Invoice"] += 3
    if "tax invoice" in text_lower:
        scores["Invoice"] += 2
    if "GeM Invoice Date" in text_lower:
        scores["Invoice"] +=2

    # Select highest score
    detected_type = max(scores, key=scores.get)

    # If no strong match
    if scores[detected_type] < 3:
        return "Unknown Document"

    return detected_type

# DUPLICATE DETECTION (UNCHANGED)


def is_duplicate(new_text, new_fields, documents):

    new_clean = clean_text(new_text)

    for doc in documents:
        existing_text = doc.get("full_text", "")
        existing_clean = clean_text(existing_text)

        # 🔹 1. TEXT SIMILARITY CHECK
        similarity = fuzz.token_sort_ratio(new_clean, existing_clean)

        if similarity >= 90:
            print(f"⚠ Duplicate detected (Text Similarity: {similarity}%)")
            return True

        # 🔹 2. FIELD-BASED CHECK (extra safety)
        existing_fields = doc.get("fields", {})

        for key in ["Aadhaar Number", "PAN Number", "Invoice Number", "GSTIN"]:
            if key in new_fields and key in existing_fields:
                if set(new_fields[key]) & set(existing_fields[key]):
                    print(f"⚠ Duplicate detected (Field match: {key})")
                    return True

    return False


# MASK SENSITIVE DATA (UNCHANGED)


def mask_sensitive_data(fields):

    masked = {}

    for key, values in fields.items():

        masked_values = []

        for value in values:

            if "Aadhaar" in key:
                masked_values.append("XXXX XXXX " + value[-4:])

            elif "PAN" in key:
                masked_values.append(value[:3] + "XXXXX" + value[-1])

            else:
                masked_values.append(value)

        masked[key] = masked_values

    return masked

# ROUTES

@app.route("/api/document", methods=["GET"])
def get_document_by_key():

    if not verify_api_key(request):
        return jsonify({"error": "Unauthorized"}), 401

    search_key = request.args.get("key")

    if not search_key:
        return jsonify({"error": "Key is required"}), 400

    documents = read_documents()

    for doc in documents:

        fields = doc.get("fields", {})

        for value in fields.values():
            if search_key in str(value):
                return jsonify({
                    "status": "success",
                    "document_type": doc.get("document_type"),
                    "file_name": doc.get("file_name"),
                    "fields": fields
                })

    return jsonify({
        "status": "not_found",
        "message": "No document found"
    }), 404

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload_document():

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    full_text = extract_text_from_pdf(file_path)

    # Reject unreadable file
    if not full_text.strip() or len(full_text.strip()) < 20:
        return jsonify({
            "error": "Uploaded document is not readable (Blank or corrupted)."
        })

    fields = extract_structured_fields(full_text)
    doc_type = detect_document_type(full_text)

    documents = read_documents()

    if is_duplicate(full_text, fields, documents):
      return jsonify({
        "error": "This document is already uploaded (Duplicate detected)."
    })

    document_data = {
        "id": str(uuid.uuid4()),
        "file_name": file.filename,
        "document_type": doc_type,
        "fields": fields,
        "full_text": full_text
    }

    documents.append(document_data)
    write_documents(documents)

    return jsonify({
        "message": "Document uploaded successfully.",
        "document_type_detected": doc_type
    })


@app.route("/documents")
def list_documents():

    documents = read_documents()

    summary = []

    for doc in documents:
        summary.append({
            "id": doc.get("id"),
            "file_name": doc.get("file_name"),
            "document_type": doc.get("document_type", "Unknown")
        })

    return jsonify(summary)


@app.route("/document/<doc_id>")
def get_document(doc_id):

    documents = read_documents()

    for doc in documents:
        if doc.get("id") == doc_id:
            return jsonify(doc)

    return jsonify({"error": "Document not found"}), 404


@app.route("/search")
def search_document():

    keyword = request.args.get("keyword", "").lower()
    documents = read_documents()

    results = []

    for doc in documents:

        full_text = doc.get("full_text", "").lower()
        fields = str(doc.get("fields", "")).lower()
        file_name = doc.get("file_name", "").lower()

        if (
            keyword in full_text
            or keyword in fields
            or keyword in file_name
        ):
            results.append(doc)

    if not results:
        return jsonify({"message": "No document found"})

    return jsonify(results)


@app.route("/delete/<doc_id>", methods=["DELETE"])
def delete_document(doc_id):

    documents = read_documents()
    documents = [doc for doc in documents if doc.get("id") != doc_id]
    write_documents(documents)

    return jsonify({"message": "Document deleted successfully"})


@app.route("/preview/<filename>")
def preview_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


# RUN SERVER



if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        debug=True,
        use_reloader=False
    )




