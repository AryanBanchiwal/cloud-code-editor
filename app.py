from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.secret_key = "secret123"

socketio = SocketIO(app, cors_allowed_origins="*")

# dummy users (login id/password)
users = {
    "aryan": "1234"
}

# store rooms
rooms = {}

# ---------------- LOGIN ROUTE ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username in users and users[username] == password:
            session["username"] = username
            return redirect(url_for("index"))
        else:
            return "Invalid username or password"

    return render_template("login.html")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))

# ---------------- HOME ----------------
@app.route("/")
def index():
    if "username" not in session:
        return redirect(url_for("login"))
    return render_template("index.html")

# ---------------- SOCKET JOIN ----------------
@socketio.on("join_room")
def handle_join(data):
    room_id = data["room_id"]
    username = session.get("username")

    if room_id not in rooms:
        rooms[room_id] = {
            "code": "<h1>Hello Cloud Editor</h1>",
            "users": []
        }

    if username not in rooms[room_id]["users"]:
        rooms[room_id]["users"].append(username)

    emit("load_code", {"code": rooms[room_id]["code"]})
    emit("receive_message", {
        "user": "System",
        "message": username + " joined"
    }, room=room_id)

# ---------------- SOCKET CODE CHANGE ----------------
@socketio.on("code_change")
def handle_code_change(data):
    room_id = data["room_id"]
    code = data["code"]

    if room_id in rooms:
        rooms[room_id]["code"] = code

    emit("code_update", {"code": code}, room=room_id, include_self=False)

# ---------------- RUN ----------------
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)