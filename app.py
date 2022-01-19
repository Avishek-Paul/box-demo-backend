from uuid import uuid4
from boxsdk import Client, JWTAuth
from flask import Flask, request
from flask_cors import CORS
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

JWT_CONFIG = JWTAuth.from_settings_file("box_jwt_config.json")
EXCLUDED_EXTENSIONS = []


@app.route("/folder")
def get_items():
    folder_id = int(request.args.get("id", 0))
    client = Client(JWT_CONFIG)
    root = client.folder(folder_id=folder_id).get()
    items = root.get_items(limit=50, offset=0)

    box_files = []
    for item in items:
        file_info = {
            "id": item.id,
            "name": item.name,
            "shared_link": item.get_shared_link(),
            "type": item.type,
        }
        if item.type == "folder":
            curr_folder = item.get()
            file_info["num_items"] = curr_folder.item_collection["total_count"]
        box_files.append(file_info)

    folder_info = {
        "id": folder_id,
        "name": root.name,
    }

    if folder_id != 0:
        folder_info["parent"] = {"id": root.parent.id, "name": root.parent.name}

    return {"folder": folder_info, "files": box_files}


@app.route("/folder", methods=["POST"])
def create_folder():
    folder_name = request.args.get("name", str(uuid4()))
    parent_folder_id = request.args.get("id", 0)
    client = Client(JWT_CONFIG)
    subfolder = client.folder(parent_folder_id).create_subfolder(folder_name)
    return {
        "folder_id": subfolder.id,
        "name": subfolder.name,
        "parent_folder_id": subfolder.parent.id,
    }


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() not in EXCLUDED_EXTENSIONS
    )


@app.route("/upload", methods=["POST"])
def upload_file():
    if request.method == "POST":
        folder_id = request.args.get("folder_id", 0)
        if "file" not in request.files:
            return {"error": "no_file_provided"}
        file = request.files["file"]
        if file.filename == "":
            return {"error": "no_filename_provided"}
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            client = Client(JWT_CONFIG)
            try:
                box_file = client.folder(folder_id).upload_stream(file, filename)
                box_file_dict = {
                    "id": box_file.id,
                    "name": box_file.name,
                    "embed_url": box_file.get_embed_url(),
                    "folder_id": box_file.parent.id,
                }
                return box_file_dict
            except Exception as error:
                return {
                    "error": error.code,
                    "name": error.context_info["conflicts"]["name"],
                }


app.run(host="0.0.0.0", debug=True)
