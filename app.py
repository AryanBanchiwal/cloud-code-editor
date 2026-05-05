from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, emit, join_room
import os

app = Flask(__name__)
app.secret_key = "secret123"

socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

users = {
    "aryan": "1234"
}

rooms = {}

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username in users and users[username] == password:
            session["username"] = username
            return redirect("/editor")

    return render_template("login.html")

@app.route("/editor")
def editor():
    if "username" not in session:
        return redirect("/")
    return render_template("index.html", username=session["username"])

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@socketio.on("join_room")
def handle_join(data):
    room = data["room"]
    username = data["username"]

    join_room(room)

    if room not in rooms:
        rooms[room] = ""

    emit("load_code", {"code": rooms[room]})

    emit("chat", {
        "user": "System",
        "msg": username + " joined"
    }, room=room)

@socketio.on("code")
def handle_code(data):
    room = data["room"]
    code = data["code"]

    rooms[room] = code
    emit("update", {"code": code}, room=room, include_self=False)

@socketio.on("chat")
def handle_chat(data):
    emit("chat", data, room=data["room"])

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)