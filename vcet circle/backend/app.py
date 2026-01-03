# backend_server.py
from flask import Flask, request, jsonify, send_from_directory
import os
import uuid
import numpy as np
from PIL import Image, ImageOps, ImageEnhance, ImageFilter
from pdf2image import convert_from_path
from flask_cors import CORS
from werkzeug.utils import secure_filename
import pytesseract
import faiss
import pickle
import datetime
from sentence_transformers import SentenceTransformer
import re
from difflib import SequenceMatcher
from groq import Groq  # ✅ Groq import

# new libs for scraping VTU results
import requests
from bs4 import BeautifulSoup

# ------------------ SETUP ------------------
app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
OLD_UPLOADS_FOLDER = "backend_old/uploads"  # ✅ Old support
TEMP_FOLDER = "temp_converted"
LOG_FILE = "uploads_log.pkl"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TEMP_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf", "txt"}

# ------------------ GROQ AI CONFIG ------------------
GROQ_API_KEY = "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"
client = Groq(api_key=GROQ_API_KEY)

# ------------------ AI INDEX ------------------
INDEX_FILE = "faiss_index.bin"
TEXTS_FILE = "faiss_texts.pkl"
model = SentenceTransformer("all-MiniLM-L6-v2")
index = None
texts, answers = [], []

if os.path.exists(INDEX_FILE) and os.path.exists(TEXTS_FILE):
    index = faiss.read_index(INDEX_FILE)
    with open(TEXTS_FILE, "rb") as f:
        data = pickle.load(f)
        texts = data["texts"]
        answers = data["answers"]

# ------------------ LOG HELPERS ------------------
def load_log():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "rb") as f:
            return pickle.load(f)
    return []


def save_log(log_data):
    with open(LOG_FILE, "wb") as f:
        pickle.dump(log_data, f)


# ------------------ HELPERS ------------------
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# Canonical subject aliases mapping
SUBJECT_ALIASES = {
    # Maths
    "math": "Mathematics-I",
    "maths": "Mathematics-I",
    "mathematics": "Mathematics-I",
    "mathematics-i": "Mathematics-I",
    "mathematics i": "Mathematics-I",

    # Chemistry
    "chem": "Applied-Chemistry",
    "chemistry": "Applied-Chemistry",
    "applied chemistry": "Applied-Chemistry",
    "applied-chemistry": "Applied-Chemistry",

    # English
    "english": "Communicative-English",
    "communicative english": "Communicative-English",
    "communicative-english": "Communicative-English",

    # Constitution
    "constitution": "Indian-Constitution",
    "indian constitution": "Indian-Constitution",
    "indian-constitution": "Indian-Constitution",

    # Physics / Mechanics / etc.
    "physics": "Engineering-Physics",
    "mechanics": "Engineering-Mechanics",
    "electronics": "Basic-Electronics",
    "programming": "Programming-in-C",
    "c programming": "Programming-in-C",
    "data structures": "Data-Structures",
    "data-structures": "Data-Structures",

    # EVS
    "evs": "Environmental-Studies",
    "environmental studies": "Environmental-Studies",
    "environmental-studies": "Environmental-Studies",

    # NEW: Software Engineering & Project Management aliases
    "se": "Software-Engineering-&-Project-Management",
    "sepm": "Software-Engineering-&-Project-Management",
    "software engineering": "Software-Engineering-&-Project-Management",
    "software engineering and project management": "Software-Engineering-&-Project-Management",
    "software engineering & project management": "Software-Engineering-&-Project-Management",

    # NEW: Research Methodology & IPR aliases (RMI)
    "rmi": "Research-Methodology-&-IPR",
    "research methodology": "Research-Methodology-&-IPR",
    "research methodology & ipr": "Research-Methodology-&-IPR",
    "research methodology and ipr": "Research-Methodology-&-IPR",
    # CD Branch Subjects

    # Computer Networks
    "cn": "Computer-Networks",
    "computer networks": "Computer-Networks",
    "computer-networks": "Computer-Networks",

    # Theory of Computation
    "tc": "Theory-of-Computation",
    "theory of computation": "Theory-of-Computation",
    "theory-of-computation": "Theory-of-Computation",

    # NOSQL
    "nosql": "NOSQL",
    "no sql": "NOSQL",

    # Data Visualization
    "dv": "Data-Visualization",
    "data visualization": "Data-Visualization",
    "data-visualization": "Data-Visualization",

    # Research Methodology & IPR (already added but adding full for CD)
    "research methodology and ipr": "Research-Methodology-&-IPR",
    "research methodology & ipr": "Research-Methodology-&-IPR",
    "rmi": "Research-Methodology-&-IPR",

    # Environmental Studies and E-waste
    "environmental studies and e-waste": "Environmental-Studies-and-E-waste",
    "evs e-waste": "Environmental-Studies-and-E-waste",
    "e waste": "Environmental-Studies-and-E-waste",
    "ewaste": "Environmental-Studies-and-E-waste",
    "environmental studies": "Environmental-Studies-and-E-waste",

}
# --- HOD Details ---
HOD_DATA = {
    "cse": "Dr. _______",  # fill your HODs
    "ai": "Dr. _______",
    "cd": "prof Roopa G K",
    "ece": "Dr. _______",
    "me": "Dr. _______",
    "civil": "Dr. _______",
    "data science": "Roopa G K",
    "ai & ml": "Dr. _______",
}


def alias_to_canonical(subject_raw: str):
    if not subject_raw:
        return ""
    s = subject_raw.strip().lower()
    if s in SUBJECT_ALIASES:
        return SUBJECT_ALIASES[s]

    normalized = re.sub(r"[-_\s]+", "", s)
    for k, v in SUBJECT_ALIASES.items():
        if normalized == re.sub(r"[-_\s]+", "", k):
            return v

    for k, v in SUBJECT_ALIASES.items():
        if normalized.startswith(re.sub(r"[-\s]+", "", k)) or re.sub(r"[-\s]+", "", k).startswith(normalized):
            return v

    if re.search(r"\bmath", s):
        return "Mathematics-I"

    # default: hyphenated Title-Case
    return re.sub(r"[\s_]+", "-", subject_raw.strip().title())


def normalize_name(name: str):
    if not name:
        return ""
    name = name.strip()
    if re.search(r"\bmath\b", name, re.I) or re.search(r"mathematics", name, re.I):
        return "Mathematics-I"
    mapped = alias_to_canonical(name)
    return mapped if mapped else re.sub(r"[\s_]+", "-", name.title())


def normalize_sem(sem):
    sem = str(sem).lower()
    sem = re.sub(r"(st|nd|rd|th)", "", sem)
    return sem.strip()


def build_path(branch, semester, subject, module):
    semester = normalize_sem(semester)
    subject = normalize_name(subject)
    module = normalize_name(module)
    folder_path = os.path.join(UPLOAD_FOLDER, branch, semester, subject, module)
    os.makedirs(folder_path, exist_ok=True)
    return folder_path


def preprocess_image(image_path):
    image = Image.open(image_path).convert("L")
    image = ImageOps.invert(image)
    image = ImageEnhance.Contrast(image).enhance(2.0)
    image = image.filter(ImageFilter.MedianFilter(size=3))
    image.save(image_path)
    return image_path


def extract_text_from_image(image_path):
    text = pytesseract.image_to_string(Image.open(image_path))
    return text.strip()


# -------- STRONG SUBJECT FOLDER FIND (handles &, spaces, etc.) --------
def clean_name(name: str) -> str:
    """Strip all non-alphanumeric for matching (spaces, -, _, &, etc.)."""
    return re.sub(r"[^a-z0-9]", "", (name or "").lower())


def find_subject_folder(base_path, branch, semester, subject_name):
    """
    Find subject folder even if name format differs:
    - spaces vs hyphens vs underscores
    - '&' vs 'and'
    - case differences
    """
    subject_root = os.path.join(base_path, branch, semester)
    if not os.path.exists(subject_root):
        return None

    target = clean_name(subject_name)

    for folder in os.listdir(subject_root):
        clean_folder = clean_name(folder)
        if clean_folder == target or target in clean_folder or clean_folder in target:
            return os.path.join(subject_root, folder)

    return None


# ------------------ VTU SCRAPER ------------------
VTU_RESULTS_URL = "https://results.vtu.ac.in"


def fetch_vtu_results():
    try:
        resp = requests.get(VTU_RESULTS_URL, timeout=8)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        results = []
        anchors = soup.find_all("a")
        for a in anchors:
            txt = (a.get_text() or "").strip()
            href = a.get("href") or ""
            if not txt:
                continue
            if re.search(r"result|results|semester|announc", txt, re.I):
                link = href
                if link and not link.startswith("http"):
                    link = requests.compat.urljoin(VTU_RESULTS_URL, link)
                results.append(f"{txt} — {link}" if link else txt)
            if len(results) >= 8:
                break

        if not results:
            for h in soup.find_all(["h2", "h3", "p"]):
                txt = (h.get_text() or "").strip()
                if re.search(r"result|semester|announc", txt, re.I):
                    results.append(txt)
                if len(results) >= 6:
                    break

        if not results:
            return ["No obvious results found. Visit https://results.vtu.ac.in"]

        return results
    except Exception as e:
        return [f"Unable to fetch VTU results: {str(e)}"]


# ------------------ FILE UPLOAD ------------------
@app.route("/upload", methods=["POST"])
def upload_file():
    try:
        file = request.files.get("file")
        branch = request.form.get("branch")
        semester = request.form.get("semester")
        subject = request.form.get("subject")
        module = request.form.get("module")

        if not file or not all([branch, semester, subject, module]):
            return jsonify({"status": "error", "message": "⚠ Missing fields"}), 400

        if not allowed_file(file.filename):
            return jsonify({"status": "error", "message": "❌ File type not allowed"}), 400

        normalized_subject = normalize_name(subject)
        folder_path = build_path(branch, semester, normalized_subject, module)
        filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
        file_path = os.path.join(folder_path, filename)
        file.save(file_path)

        logs = load_log()
        logs.append({
            "branch": branch.lower(),
            "semester": normalize_sem(semester),
            "subject": normalized_subject.lower(),
            "module": normalize_name(module).lower(),
            "filename": filename,
            "path": file_path,
            "uploaded_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        save_log(logs)

        return jsonify({
            "status": "success",
            "message": f"✅ File '{file.filename}' uploaded successfully!",
            "file": f"uploads/{branch}/{semester}/{normalized_subject}/{module}/{filename}"
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ------------------ FILE DELETE ------------------
@app.route("/delete_file", methods=["POST"])
def delete_file():
    try:
        data = request.get_json()
        branch = data.get("branch")
        semester = data.get("semester")
        subject = data.get("subject")
        module = data.get("module")
        filename = data.get("filename")

        if not all([branch, semester, subject, module, filename]):
            return jsonify({"success": False, "message": "Missing required data"}), 400

        file_path = os.path.join(
            UPLOAD_FOLDER,
            branch,
            normalize_sem(semester),
            normalize_name(subject),
            normalize_name(module),
            filename,
        )

        if os.path.isfile(file_path):
            os.remove(file_path)
            logs = load_log()
            updated_logs = [
                log for log in logs
                if not (
                    log.get("branch") == branch.lower()
                    and log.get("semester") == normalize_sem(semester)
                    and log.get("subject") == normalize_name(subject).lower()
                    and log.get("module") == normalize_name(module).lower()
                    and log.get("filename") == filename
                )
            ]
            save_log(updated_logs)
            return jsonify({"success": True, "message": "✅ File deleted successfully!"})
        else:
            return jsonify({"success": False, "message": "File not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500


# ------------------ CONVERT TO TEXT ------------------
@app.route("/convert", methods=["POST"])
def convert_to_text():
    file = request.files.get("file")
    branch = request.form.get("branch")
    semester = request.form.get("semester")
    subject = request.form.get("subject")
    module = request.form.get("module")

    if not file or not allowed_file(file.filename):
        return jsonify({"status": "error", "message": "Invalid or missing file"}), 400
    if not all([branch, semester, subject, module]):
        return jsonify({"status": "error", "message": "Missing required details"}), 400

    temp_filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
    temp_path = os.path.join(TEMP_FOLDER, temp_filename)
    file.save(temp_path)

    extracted_text = ""
    try:
        if file.filename.lower().endswith(".pdf"):
            pages = convert_from_path(temp_path)
            for page in pages:
                page_path = os.path.join(TEMP_FOLDER, f"{uuid.uuid4().hex}.png")
                page.save(page_path, "PNG")
                processed_path = preprocess_image(page_path)
                text = extract_text_from_image(processed_path)
                extracted_text += text + "\n\n"
        else:
            processed_path = preprocess_image(temp_path)
            text = extract_text_from_image(processed_path)
            extracted_text = text

        if not extracted_text.strip():
            extracted_text = "⚠ No readable text found."

        folder_path = build_path(branch, semester, subject, module)
        filename = f"converted_{uuid.uuid4().hex}.txt"
        filepath = os.path.join(folder_path, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(extracted_text)

        return jsonify({
            "status": "success",
            "text": extracted_text,
            "file": f"uploads/{branch}/{semester}/{subject}/{module}/{filename}",
            "message": "✅ Converted and saved successfully!"
        })
    except Exception as e:
        return jsonify({"status": "error", "message": f"Conversion failed: {str(e)}"}), 500
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


# ------------------ CORRECTED LIST FILES ------------------
@app.route("/images", methods=["GET"])
def list_images():
    branch = request.args.get("branch")
    semester = request.args.get("semester")
    subject = request.args.get("subject")
    module = request.args.get("module")

    # Normalize all components
    sem = normalize_sem(semester)
    subject_norm = normalize_name(subject)
    module_norm = normalize_name(module)

    # Flexible subject folder finder (handles &, etc.)
    folder = find_subject_folder(UPLOAD_FOLDER, branch, sem, subject_norm)
    if folder:
        folder_path = os.path.join(folder, module_norm)
    else:
        folder_path = os.path.join(UPLOAD_FOLDER, branch, sem, subject_norm, module_norm)

    if not os.path.exists(folder_path):
        return jsonify([])

    files = []
    for f in os.listdir(folder_path):
        correct_url = f"uploads/{branch}/{sem}/{subject_norm}/{module_norm}/{f}"
        files.append({
            "file": correct_url,
            "name": f,
            "type": f.split(".")[-1].lower()
        })

    return jsonify(sorted(files, key=lambda x: x["name"].lower()))


# ------------------ CHATBOT ------------------
@app.route("/chat", methods=["POST"])
def chat():
    try:
        user_query = request.get_json().get("message", "").strip()
        if not user_query:
            return jsonify({"reply": "⚠ Please enter a message."})

        user_query_lc = user_query.lower()
        branch_match = re.search(r"\b(cse|ece|ai|cd|me|civil)\b", user_query_lc)
        sem_match = re.search(r"(\d+)(?:st|nd|rd|th)?\s*sem", user_query_lc)
        module_match = re.search(r"module[-\s]*(\d+)", user_query_lc)
        subject_match = re.search(
            r"("
            r"mathematics[-\s]*i{0,3}|mathematics|maths?|math|m1|"

            r"applied[-\s]*chemistry|chemistry|"
            r"english|physics|mechanics|python|"
            r"data[-\s]*structures|oops|ai|ml|dbms|java|"
            r"environmental[-\s]*studies|evs|"

            # CD Branch Subjects
            r"computer[-\s]*networks|cn|"
            r"theory[-\s]*of[-\s]*computation|tc|"
            r"nosql|no[-\s]*sql|"
            r"data[-\s]*visualization|dv|"
            r"research[-\s]*methodology(?:\s*(?:and|&)\s*ipr)?|rmi|"
            r"environmental[-\s]*studies(?:\s*and\s*e[-\s]*waste)?|e[-\s]*waste"
            r")",
            user_query_lc,
    )



                # ---------- HOD checking (static answers) ----------
        if re.search(r"hod|head of department|who is the hod", user_query_lc):
            for branch_key, hod_name in HOD_DATA.items():
                if branch_key in user_query_lc:
                    return jsonify({"reply": f"👩‍🏫 The HOD of {branch_key.upper()} is **{hod_name}**."})

            return jsonify({"reply": "I found your HOD query, but please mention the branch (CSE, CD, AI, ECE, ME, Civil)."})

        # If user asks about 'result' or 'results' or 'marks', fetch VTU results
        if re.search(r"\b(result|results|marks|exam result|exam results|revaluation)\b", user_query_lc):
            results = fetch_vtu_results()
            # format into a short reply
            reply_lines = ["📢 Latest VTU Results / Notices:"]
            for r in results[:6]:
                reply_lines.append(f"- {r}")
            reply_lines.append("Visit https://results.vtu.ac.in for full details.")
            return jsonify({"reply": "\n".join(reply_lines)})

        # Try to locate uploaded files first (academic query)
        if branch_match and sem_match and subject_match:
            branch = branch_match.group(1).lower()
            semester = normalize_sem(sem_match.group(1))
            subject_raw = subject_match.group(1)
            # map subject alias to canonical folder (this makes maths/chem/chemistry flexible)
            subject = alias_to_canonical(subject_raw)
            module = f"Module{module_match.group(1)}" if module_match else ""

            subject_folder = find_subject_folder(UPLOAD_FOLDER, branch, semester, subject)
            found_files = []

            search_paths = []
            if subject_folder:
                search_paths.append(os.path.join(subject_folder, normalize_name(module)))
            old_subject_folder = find_subject_folder(OLD_UPLOADS_FOLDER, branch, semester, subject)
            if old_subject_folder:
                search_paths.append(os.path.join(old_subject_folder, normalize_name(module)))

            for search_path in search_paths:
                if os.path.exists(search_path):
                    for file in os.listdir(search_path):
                        if file.lower().endswith((".pdf", ".png", ".jpg", ".jpeg", ".txt")):
                            file_url = f"http://127.0.0.1:5000/{os.path.join(search_path, file).replace(os.sep, '/')}"
                            found_files.append({"name": file, "file_url": file_url})

            if found_files:
                return jsonify({
                    "reply": f"📂 Found {len(found_files)} file(s) for {subject} {module} ({branch.upper()} {semester}).",
                    "files": found_files
                })

        # If we reach here, no local academic files found — use Groq AI fallback.
        # Provide a strict system prompt so the assistant responds as VCET (VTU-affiliated) assistant.
        groq_system_prompt = (
            "You are VCET Hub's official assistant for Vivekananda College of Engineering and Technology (VCET), "
            "Puttur — affiliated with Visvesvaraya Technological University (VTU), Belagavi. "
            "Always answer academic questions using VTU curriculum/syllabus conventions. "
            "When users ask about subjects, syllabus, modules, exam patterns, or resources, prefer VTU syllabus and VTU official sources. "
            "When users ask about results/circulars/notifications, provide guidance and summary and point to official VTU/results pages (https://results.vtu.ac.in and https://vtu.ac.in). "
            "When users ask 'What is VCET' or 'What is VCET Hub', reply: 'Vivekananda College of Engineering and Technology, Puttur (VCET) — affiliated to VTU.' "
            "Only provide non-VTU external resources when specifically requested, and prefer official VTU/college materials where possible."
        )

        groq_response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": groq_system_prompt},
                {"role": "user", "content": user_query},
            ],
        )
        answer = groq_response.choices[0].message.content.strip()
        return jsonify({"reply": answer})

    except Exception as e:
        return jsonify({"reply": f"❌ Chatbot error: {str(e)}"})

# ------------------ SERVE FILES ------------------
@app.route("/uploads/<path:filename>")
def serve_uploads(filename):
    try:
        return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=False)
    except Exception:
        return jsonify({"status": "error", "message": "File not found"}), 404


# ------------------ MAIN ------------------
if __name__ == "__main__":
    app.run(debug=True, port=5000)