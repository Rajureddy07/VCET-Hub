from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import uuid

app = Flask(__name__)
CORS(app)

NEWS_FOLDER = "news_images"

# Create folder if not exists
os.makedirs(NEWS_FOLDER, exist_ok=True)


# ---------------- GET NEWS IMAGES ----------------
@app.get("/get-news")
def get_news():
    files = sorted(os.listdir(NEWS_FOLDER))

    images = []
    for i, f in enumerate(files):
        images.append({
            "index": i,
            "filename": f,
            "url": f"http://127.0.0.1:5000/news/{f}"
        })

    return jsonify({"images": images})


# ---------------- SERVE NEWS IMAGE ----------------
@app.get("/news/<filename>")
def serve_image(filename):
    return send_from_directory(NEWS_FOLDER, filename)


# ---------------- UPLOAD NEWS IMAGE ----------------
@app.post("/upload-news")
def upload_news():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files["image"]

    ext = file.filename.split(".")[-1].lower()

    # Validate image extensions
    if ext not in ["jpg", "jpeg", "png", "webp"]:
        return jsonify({"error": "Invalid image format"}), 400

    filename = f"{uuid.uuid4()}.{ext}"

    file.save(os.path.join(NEWS_FOLDER, filename))

    return jsonify({
        "message": "Image uploaded successfully",
        "filename": filename,
        "url": f"http://127.0.0.1:5000/news/{filename}"
    })


# ---------------- DELETE NEWS IMAGE ----------------
@app.post("/delete-news")
def delete_news():
    data = request.json
    index = data.get("index")

    files = sorted(os.listdir(NEWS_FOLDER))

    if index is None or index < 0 or index >= len(files):
        return jsonify({"error": "Invalid index"}), 400

    file_to_delete = files[index]
    path = os.path.join(NEWS_FOLDER, file_to_delete)

    if os.path.exists(path):
        os.remove(path)

    return jsonify({"message": "Image deleted successfully"})


# ------------------- RUN SERVER --------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
