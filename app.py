from boxsdk import OAuth2, Client, JWTAuth
from flask import Flask, redirect, request, session, flash
from flask_session import Session
import redis
from werkzeug.utils import secure_filename
from flask_cors import CORS
import os

app = Flask(__name__)

app.secret_key = "super secret key"
app.config["SESSION_TYPE"] = "redis"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True
app.config["SESSION_REDIS"] = redis.from_url("redis://localhost:6379")


Session(app)
CORS(app)

JWT_CONFIG = JWTAuth.from_settings_file("box_jwt_config.json")
CLIENT_ID = "uk7qibnrff37zjirky6jlmzdcjfoi6ar"
CLIENT_SECRET = "YlA2LUCG6qmthkGBVcr95eVpOHm2Iu6W"
APP_TOKEN = "EYryn4JFrVdmxoo8BP5RJbYJ2Ka0DreL"

auth = OAuth2(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
)

EXCLUDED_EXTENSIONS = []
UPLOAD_FOLDER = "/home/impas/upload/"


@app.route("/")
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
        box_files.append(
            {
                "id": item.id,
                "name": item.name,
                "shared_link": item.get_shared_link(),
            }
        )
    return {"folder_id": folder_id, "files": box_files}


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
        # check if the post request has the file part
        if "file" not in request.files:
            return {"error": "no_file_provided"}
        file = request.files["file"]
        if file.filename == "":
            return {"error": "no_filename_provided"}
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            client = Client(JWT_CONFIG)
            try:
                box_file = client.folder(0).upload_stream(file, filename)
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


app.run(host="0.0.0.0", debug=True, port=4000)

# https://yasoob.me/posts/how-to-setup-and-deploy-jwt-auth-using-react-and-flask/
