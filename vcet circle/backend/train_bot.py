# ----------------------------- #
#   VCET Hub Bot Trainer (Final Complete Version)
#   Author: Gounolla Rajasekhar Reddy
# ----------------------------- #

import os
import pickle
import faiss
from sentence_transformers import SentenceTransformer
import numpy as np
from PyPDF2 import PdfReader
import easyocr

# ------------------ CONFIG ------------------ #
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
INDEX_FILE = os.path.join(BASE_DIR, "faiss_index.bin")
TEXTS_FILE = os.path.join(BASE_DIR, "faiss_texts.pkl")

# ------------------ LOAD MODEL ------------------ #
print("🚀 Loading SentenceTransformer model (all-MiniLM-L6-v2)...")
model = SentenceTransformer("all-MiniLM-L6-v2")

# ------------------ OCR READER ------------------ #
reader = easyocr.Reader(["en"], gpu=False)

# ------------------ BUILT-IN KNOWLEDGE ------------------ #
base_knowledge = {
    "what is vcet hub": "VCET Hub (also called VCET Circle) is a digital platform for Vivekananda College of Engineering and Technology (VCET), Puttur — created by Gounolla Rajasekhar Reddy for students to easily access notes, lab manuals, question papers, and internal papers.",
    "who created vcet hub": "VCET Hub was developed by Gounolla Rajasekhar Reddy, a Computer Science and Data Science student at VCET, Puttur.",
    "what is vcet": "VCET stands for Vivekananda College of Engineering and Technology, a premier engineering institution in Puttur, Karnataka.",
    "where is vcet located": "VCET is located in Puttur, Dakshina Kannada district, Karnataka, India.",
    "who is the founder of vcet hub": "VCET Hub was founded and maintained by Gounolla Rajasekhar Reddy for the benefit of VCET students.",
    "how to access notes": "You can access notes by selecting your branch, semester, subject, and module. Each module page contains uploaded PDFs or images by the admin, available for preview or download.",
    "how many modules are there": "Each subject in VCET Hub has 5 modules: Module 1 to Module 5.",
    "hi": "👋 Hello! I’m your VCET Hub AI assistant. You can ask like: 'CSE 3rd sem Python Module 1 PDF' or say 'recent uploads'.",
    "hello": "👋 Hi there! I’m the VCET Hub Bot. You can ask for notes like: 'CSE 1st sem Maths Module 2 PDF'.",
    "who are you": "I’m the VCET Hub Chatbot, built by Gounolla Rajasekhar Reddy to help students easily find study materials.",
    "what can you do": "I can help you find notes, lab manuals, question papers, and internal papers for your branch, semester, subject, and module in VCET Hub.",
    "thanks": "You're welcome! 😊 Happy studying at VCET Hub!",
    "thank you": "You're welcome! If you need more help, just ask.",
}

texts = list(base_knowledge.keys())
answers = list(base_knowledge.values())
file_paths = ["[builtin_knowledge]" for _ in texts]

# ------------------ SCAN UPLOADED FILES ------------------ #
print(f"📂 Scanning uploaded notes inside '{UPLOAD_FOLDER}' ...")

for root, _, files in os.walk(UPLOAD_FOLDER):
    for file in files:
        if file.lower().endswith((".pdf", ".txt", ".png", ".jpg", ".jpeg")):
            path = os.path.join(root, file)
            relative_path = os.path.relpath(path, BASE_DIR).replace("\\", "/")

            # Expected: uploads/<branch>/<semester>/<subject>/<module>/<file>
            parts = relative_path.split("/")
            branch = semester = subject = module = None
            if len(parts) >= 6:
                branch = parts[1]
                semester = parts[2]
                subject = parts[3]
                module = parts[4]

            extracted_text = ""

            # ------------------ PDF TEXT ------------------ #
            if file.lower().endswith(".pdf"):
                try:
                    reader_pdf = PdfReader(path)
                    for page in reader_pdf.pages:
                        extracted_text += page.extract_text() or ""
                except Exception as e:
                    print(f"⚠ Error reading PDF {file}: {e}")
                    continue

            # ------------------ TEXT FILES ------------------ #
            elif file.lower().endswith(".txt"):
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        extracted_text = f.read()
                except Exception as e:
                    print(f"⚠ Error reading text file {file}: {e}")
                    continue

            # ------------------ IMAGE OCR ------------------ #
            elif file.lower().endswith((".png", ".jpg", ".jpeg")):
                try:
                    result = reader.readtext(path, detail=0, paragraph=True)
                    extracted_text = " ".join(result)
                except Exception as e:
                    print(f"⚠ OCR failed for {file}: {e}")
                    continue

            if not extracted_text.strip():
                continue

            # ------------------ Description ------------------ #
            desc = f"{branch or 'Unknown'} {semester or 'Unknown'} {subject or 'Unknown'} {module or 'Unknown'} notes uploaded."

            # ------------------ Download Button ------------------ #
            ext = file.split(".")[-1].upper()
            download_html = (
                f'<a href="http://127.0.0.1:5000/{relative_path}" target="_blank" '
                f'class="download-btn">📘 {subject or "Unknown"} - {module or ""} ({branch or "Unknown"} {semester or ""}) → View File</a>'
            )

            # ------------------ Add to Knowledge ------------------ #
            texts.append(desc + " " + extracted_text[:800])
            answers.append(download_html)
            file_paths.append(relative_path)

            print(f"✅ Indexed: {relative_path}")

# ------------------ CHECK ------------------ #
if not texts:
    print("❌ No files found in uploads or built-in knowledge.")
    print("💡 Upload some PDFs or images first, then rerun this script!")
    exit()

print(f"\n✅ Total knowledge items: {len(texts)} (including general VCET info)")

# ------------------ CREATE EMBEDDINGS ------------------ #
print("\n🧠 Generating embeddings for chatbot training...")
embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=True)

# ------------------ CREATE FAISS INDEX ------------------ #
dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(embeddings)

# ------------------ SAVE INDEX AND TEXTS ------------------ #
faiss.write_index(index, INDEX_FILE)
with open(TEXTS_FILE, "wb") as f:
    pickle.dump({"texts": texts, "answers": answers, "paths": file_paths}, f)

# ------------------ COMPLETION ------------------ #
print("\n✅ VCET Hub Chatbot training completed successfully!")
print(f"📦 Saved FAISS index → {INDEX_FILE}")
print(f"📜 Saved text/answer mappings → {TEXTS_FILE}")
print("🎯 Chatbot trained with:")
print("   🏫 General VCET Hub knowledge")
print("   📚 Uploaded notes (PDFs, text, and images)")
print("\n💬 Run app.py to start your chatbot backend.")
