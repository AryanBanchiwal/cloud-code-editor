from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_socketio import SocketIO, emit, join_room
import requests
import os

app = Flask(__name__)
app.secret_key = "cloud_editor_secret_key_2026"

socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

users = {
    "aryan": "1234",
    "test": "1234"
}

rooms = {}

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username in users and users[username] == password:
            session["username"] = username
            return redirect(url_for("index"))
        else:
            error = "Invalid username or password"

    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))

@app.route("/")
def index():
    if "username" not in session:
        return redirect(url_for("login"))
    return render_template("index.html", username=session["username"])

@app.route("/run", methods=["POST"])
def run_code():
    data = request.get_json()
    code = data.get("code")
    language = data.get("language")

    versions = {
        "python": {"language": "python", "version": "3.10.0"},
        "javascript": {"language": "javascript", "version": "18.15.0"},
        "java": {"language": "java", "version": "15.0.2"},
        "cpp": {"language": "c++", "version": "10.2.0"}
    }

    if language == "html":
        return jsonify({
            "output": code,
            "type": "html"
        })

    if language not in versions:
        return jsonify({
            "output": "Language not supported",
            "type": "text"
        })

    try:
        payload = {
            "language": versions[language]["language"],
            "version": versions[language]["version"],
            "files": [
                {
                    "content": code
                }
            ]
        }

        response = requests.post(
            "https://emkc.org/api/v2/piston/execute",
            json=payload,
            timeout=15
        )

        result = response.json()

        output = ""

        if "run" in result:
            output = result["run"].get("output") or result["run"].get("stderr") or ""

        if output.strip() == "":
            output = "No output generated."

        return jsonify({
            "output": output,
            "type": "text"
        })

    except Exception as e:
        return jsonify({
            "output": "Error while running code: " + str(e),
            "type": "text"
        })

@socketio.on("join_room")
def handle_join(data):
    room_id = data.get("room_id")
    username = data.get("username", "User")

    join_room(room_id)

    if room_id not in rooms:
        rooms[room_id] = {
            "code": "print('Hello Cloud Editor')",
            "users": []
        }

    if username not in rooms[room_id]["users"]:
        rooms[room_id]["users"].append(username)

    emit("load_code", {"code": rooms[room_id]["code"]})

    emit("receive_message", {
        "user": "System",
        "message": username + " joined the room"
    }, room=room_id)

@socketio.on("code_change")
def handle_code_change(data):
    room_id = data.get("room_id")
    code = data.get("code")

    if room_id in rooms:
        rooms[room_id]["code"] = code

    emit("code_update", {"code": code}, room=room_id, include_self=False)

@socketio.on("send_message")
def handle_message(data):
    room_id = data.get("room_id")
    username = data.get("username")
    message = data.get("message")

    emit("receive_message", {
        "user": username,
        "message": message
    }, room=room_id)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port)