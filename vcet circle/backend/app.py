from flask import Flask, request, send_from_directory, jsonify
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# Set upload folder path
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'backend', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ----------------------------
# Helper: Get folder path
# ----------------------------
def get_upload_path(branch, semester, subject, module=None):
    subject = secure_filename(subject)
    if module:
        module = secure_filename(module)
        return os.path.join(app.config['UPLOAD_FOLDER'], branch, semester, subject, module)
    else:
        return os.path.join(app.config['UPLOAD_FOLDER'], branch, semester, subject)

# ----------------------------
# Route: Upload file
# ----------------------------
@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files.get('file')
    branch = request.form.get('branch')
    semester = request.form.get('semester')
    subject = request.form.get('subject')
    module = request.form.get('module')  # Optional

    if not all([file, branch, semester, subject]):
        return jsonify({'error': 'Missing data'}), 400

    upload_path = get_upload_path(branch, semester, subject, module)
    os.makedirs(upload_path, exist_ok=True)

    filename = secure_filename(file.filename)
    file_path = os.path.join(upload_path, filename)
    file.save(file_path)

    # Return relative URL path
    rel_path = os.path.relpath(file_path, app.config['UPLOAD_FOLDER']).replace("\\", "/")
    return jsonify({'url': f'uploads/{rel_path}'})

# ----------------------------
# Route: List uploaded files
# ----------------------------
@app.route('/images')
def list_files():
    branch = request.args.get('branch')
    semester = request.args.get('semester')
    subject = request.args.get('subject')
    module = request.args.get('module')  # Optional

    if not all([branch, semester, subject]):
        return jsonify([])

    folder_path = get_upload_path(branch, semester, subject, module)
    if not os.path.exists(folder_path):
        return jsonify([])

    files = os.listdir(folder_path)
    file_urls = [f'uploads/{branch}/{semester}/{secure_filename(subject)}'
                 + (f'/{secure_filename(module)}' if module else '')
                 + f'/{f}' for f in files]
    return jsonify(file_urls)

# ----------------------------
# Route: Serve uploaded files
# ----------------------------
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ----------------------------
# Route: Delete file (admin only)
# ----------------------------
@app.route('/delete', methods=['POST'])
def delete_file():
    data = request.get_json()
    branch = data.get('branch')
    semester = data.get('semester')
    subject = data.get('subject')
    module = data.get('module')  # Optional
    filename = data.get('filename')

    if not all([branch, semester, subject, filename]):
        return jsonify({'status': 'fail', 'message': 'Missing data'}), 400

    folder_path = get_upload_path(branch, semester, subject, module)
    file_path = os.path.join(folder_path, secure_filename(filename))

    if os.path.exists(file_path):
        os.remove(file_path)
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'fail', 'message': 'File not found'}), 404

# ----------------------------
# Run server
# ----------------------------
if __name__ == '__main__':
    app.run(debug=True)
