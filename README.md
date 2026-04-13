# 📄 Government Document Management System (OCR-Based)

## 🚀 Live Demo

🌐 https://document-management-system-298c.onrender.com

---

## 📌 Project Overview

The **Government Document Management System** is a web-based application that allows users to upload, process, and manage documents using **OCR (Optical Character Recognition)**.

It automatically:

* Extracts text from documents (PDF/Image)
* Detects document type (Aadhaar, PAN, Invoice, Marksheet)
* Stores structured data
* Prevents duplicate uploads
* Enables search and retrieval

---

## 🛠️ Tech Stack

### Backend

* Python
* Flask

### Libraries Used

* rapidfuzz (duplicate detection)
* pdfplumber (PDF text extraction)
* requests (OCR API integration)
* spacy (NLP - optional)

### Frontend

* HTML (index.html)

### Deployment

* GitHub
* Render (Cloud Hosting)

### OCR

* OCR.space API (instead of pytesseract for cloud compatibility)

---

## ⚙️ Features

✅ Upload documents (PDF/Image)
✅ Automatic OCR text extraction
✅ Document type detection
✅ Structured data extraction
✅ Duplicate document detection
✅ Search functionality
✅ API access with key authentication
✅ Delete and preview documents

---

## 📂 Project Structure

```
project/
│── api1.py
│── requirements.txt
│── Procfile
│── index.html
│── document.json
│── uploads/
```

---

## 📤 How to Use

### 1. Open Website

Visit:

```
https://document-management-system-298c.onrender.com
```

---

### 2. Upload Document

* Choose a PDF or image
* Click upload
* System will process automatically

---

### 3. View Documents

```
/documents
```

---

### 4. Search Documents

```
/search?keyword=your_text
```

Example:

```
/search?keyword=pan
```

---

### 5. API Access

#### Endpoint:

```
/api/document?key=VALUE
```

#### Header:


x-api-key: mysecureapikey123

### 6. Delete Document

```
/delete/<document_id>
```

---

## ⚠️ Limitations

* Free hosting may sleep after inactivity
* Uploaded files are not permanently stored
* OCR API (free key) has limited speed

---

## 🔮 Future Improvements

* User authentication system
* Cloud storage (AWS / Firebase)
* Advanced OCR (Tesseract via Docker)
* Improved UI/UX
* Dashboard analytics

---

## 👨‍💻 Author

**Rohan Rahi**

---

## ⭐ Conclusion

This project demonstrates:

* Real-world OCR implementation
* Backend API development
* Cloud deployment
* Data processing and automation

---

👉 *Feel free to fork, improve, and use this project!* 🚀
