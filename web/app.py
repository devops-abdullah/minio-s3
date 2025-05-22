import os
import boto3
import threading
import time
from flask import Flask, request, send_from_directory, render_template_string, abort

DATA_DIR = os.environ.get('DATA_DIR', '/data')
S3_BUCKET = os.environ['S3_BUCKET']
S3_ENDPOINT = os.environ['S3_ENDPOINT']
ACCESS_KEY = os.environ['S3_ACCESS_KEY']
SECRET_KEY = os.environ['S3_SECRET_KEY']

# Boto3 client
session = boto3.session.Session()
s3 = session.client(
    service_name='s3',
    endpoint_url=S3_ENDPOINT,
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
)

# In-memory cache
INDEX_CACHE = []

# Background index refresh function
def update_index():
    global INDEX_CACHE
    while True:
        try:
            response = s3.list_objects_v2(Bucket=S3_BUCKET)
            INDEX_CACHE = [item['Key'] for item in response.get('Contents', [])]
            print("✅ Refreshed index from MinIO")
        except Exception as e:
            print(f"⚠️ Failed to refresh index: {e}")
        time.sleep(60)

app = Flask(__name__)
started = False

@app.before_request
def start_background_index():
    global started
    if not started:
        threading.Thread(target=update_index, daemon=True).start()
        started = True

@app.route('/')
def index():
    return render_template_string('''
    <!doctype html>
    <html lang="en">
    <head>
        <title>File Browser</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
        <style>
            body { padding: 2rem; background-color: #f8f9fa; }
            .toast-container { position: fixed; bottom: 1rem; right: 1rem; z-index: 1055; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2 class="mb-4">📂 Available Files (cached)</h2>
            <ul class="list-group file-list mb-5">
                {% for file in files %}
                <li class="list-group-item d-flex justify-content-between align-items-center">
                    <a href="/files/{{file}}">{{file}}</a>
                </li>
                {% endfor %}
                {% if not files %}
                <li class="list-group-item text-muted">No files found.</li>
                {% endif %}
            </ul>

            <h4 class="mb-3">⬆️ Upload Files</h4>
            <form id="upload-form" enctype="multipart/form-data" class="row g-3">
                <div class="col-auto">
                    <input type="file" name="file" class="form-control" multiple>
                </div>
                <div class="col-auto">
                    <button type="submit" class="btn btn-primary">Upload</button>
                </div>
            </form>
        </div>

        <div class="toast-container">
            <div class="toast align-items-center text-bg-success border-0" id="uploadToast" role="alert">
                <div class="d-flex">
                    <div class="toast-body">
                        ✅ Files uploaded successfully!
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        </div>

        <script>
            document.getElementById('upload-form').addEventListener('submit', async function (e) {
                e.preventDefault();
                const form = e.target;
                const formData = new FormData(form);
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });
                if (response.status === 204) {
                    const toast = new bootstrap.Toast(document.getElementById('uploadToast'));
                    toast.show();
                    setTimeout(() => window.location.reload(), 2000); // Refresh file list after toast
                }
            });
        </script>
    </body>
    </html>
    ''', files=INDEX_CACHE)


@app.route('/upload', methods=['POST'])
def upload():
    files = request.files.getlist('file')
    for f in files:
        if f and f.filename:
            local_path = os.path.join(DATA_DIR, f.filename)
            f.save(local_path)
            print(f"✅ Uploaded {f.filename} to local storage")
    return '', 204  # No content, frontend handles the toast

@app.route('/files/<path:filename>')
def serve_file(filename):
    path = os.path.join(DATA_DIR, filename)

    # If file doesn't exist locally, try downloading from MinIO
    if not os.path.exists(path):
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'wb') as f:
                s3.download_fileobj(S3_BUCKET, filename, f)
            print(f"📥 Downloaded {filename} from MinIO")
        except Exception as e:
            return f"❌ File not found locally or in MinIO: {e}", 404

    try:
        return send_from_directory(DATA_DIR, filename)
    except Exception as e:
        return f"❌ Error serving file: {e}", 500

if __name__ == '__main__':
    os.makedirs(DATA_DIR, exist_ok=True)
    app.run(host='0.0.0.0', port=5000)
