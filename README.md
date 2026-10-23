# VCET Hub

A student-focused academic resource portal for Vivekananda College of Engineering and Technology (VCET), Puttur. It organizes study materials and academic utilities in one place.

> **Project status:** Student project / prototype. Review upload permissions, data handling, and deployment configuration before exposing it to a public or production environment.

## Features

- Browse notes, lab manuals, question papers, and internal papers.
- Navigate resources by branch, semester, subject, and module.
- Preview or download supported PDFs and images.
- Admin-oriented upload and file-management pages.
- OCR-assisted text extraction for supported scanned notes.
- Chatbot that searches local academic resources before using an optional Groq API fallback.
- SGPA/CGPA calculator, VTU news page, FAQs, and student-resource pages.
- Responsive HTML/CSS/JavaScript interface.

## Project structure

```text
VCET-Hub/
└── vcet circle/
    ├── index.html
    ├── branch.html
    ├── semester.html
    ├── subject.html
    ├── module-select.html
    ├── module-view.html
    ├── question-view.html
    ├── internal-view.html
    ├── lab-view.html
    ├── sgpa.html
    ├── cgpa.html
    ├── chatbot.html
    ├── script.js
    ├── style.css
    └── backend/
        ├── app.py
        ├── news.py
        ├── requirements.txt
        └── .env.example
```

The backend provides Flask endpoints for file operations and chatbot-related workflows. It can use a local FAISS/Sentence Transformers index for relevant uploaded material, with Groq as an optional AI fallback when configured.

## Run locally

### 1. Prerequisites

Install Python, Git, Tesseract OCR, and Poppler (used by PDF conversion). The Sentence Transformers / FAISS stack may download model files on first use and can require substantial disk space.

### 2. Install backend dependencies

From the repository root:

```powershell
cd "vcet circle/backend"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

On macOS/Linux, activate with `source .venv/bin/activate`.

### 3. Configure the optional AI fallback

Copy `.env.example` to `.env` inside `vcet circle/backend`, then set `GROQ_API_KEY` to a **newly generated key**. Keep the real `.env` file private. Local-resource lookup can still work without this key, but AI fallback responses will be unavailable.

**Security notice:** a Groq key was previously committed in the public repository. It has been removed from the current source, but deleting a secret in a later commit does not remove it from Git history. Revoke the exposed key in Groq immediately. If needed, clean repository history before distributing further clones.

### 4. Start the backend

In the backend directory:

```powershell
python app.py
```

The Flask application starts on port `5000` in the current code. Keep it limited to local development until authentication, upload validation, secret handling, and deployment settings have been reviewed.

### 5. Serve the frontend

Open a second terminal at the `vcet circle` directory and run a simple local static server:

```powershell
python -m http.server 8080
```

Then open http://localhost:8080. Some frontend pages call the backend on localhost; run both processes while testing. The separate news endpoint in `backend/news.py` may be started independently if you are working on the news-upload feature.

## Responsible use and development notes

- Treat OCR output as unverified text; inspect important results manually.
- Never upload private student information, credentials, or sensitive documents to a public repository.
- Avoid committing real uploads, local logs, API keys, and generated caches.
- The current code is a learning prototype. A hidden admin link alone is not authentication or access control.
- Validate file uploads, apply authorization to administrative endpoints, and configure CORS and debug mode before any non-local deployment.

## Author

G. Rajasekhar Reddy · [GitHub](https://github.com/Rajureddy07)
