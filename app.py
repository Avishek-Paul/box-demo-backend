import os
from uuid import uuid4
import redis
from boxsdk import Client, JWTAuth, OAuth2
from flask import Flask, redirect, request, session
from flask_cors import CORS
from werkzeug.utils import secure_filename
from flask_session import Session

app = Flask(__name__)

app.secret_key = os.getenv("FLASK_SECRET_KEY", "default-value")
app.config["SESSION_TYPE"] = "redis"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True
app.config["SESSION_REDIS"] = redis.from_url("redis://localhost:6379")


Session(app)
CORS(app)

JWT_CONFIG = JWTAuth.from_settings_file("box_jwt_config.json")
CLIENT_ID = os.getenv("BOX_CLIENT_ID")
CLIENT_SECRET = os.getenv("BOX_CLIENT_SECRET")

auth = OAuth2(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
)

EXCLUDED_EXTENSIONS = []


def hello_world():

    if "access_token" in session and "refresh_token" in session:
        client = Client(
            OAuth2(
                client_id=CLIENT_ID,
                client_secret=CLIENT_SECRET,
                access_token=session.get("access_token"),
                refresh_token=session.get("refresh_token"),
            )
        )
        root = client.folder(folder_id="0").get()
        items = root.get_items(limit=50, offset=0)
        thegoods = (
            "<p>Box says these are some of your folders and items:</p>"
            + "<p>"
            + "<br/>".join([item.name for item in items])
            + "</p>"
        )
        return thegoods

    return redirect("/login")


@app.route("/folder")
def get_items():
    folder_id = request.args.get("id", 0)
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

    if folder_id != "0":
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


@app.route("/login")
def login():
    auth_url, csrf_token = auth.get_authorization_url("http://127.0.0.1:5000/oauth2")
    session["csrf_token"] = csrf_token
    return redirect(auth_url, code=302)


@app.route("/oauth2")
def oauth2():
    code = request.args.get("code")
    access_token, refresh_token = auth.authenticate(code)
    session["access_token"], session["refresh_token"] = access_token, refresh_token
    return redirect("/")


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
