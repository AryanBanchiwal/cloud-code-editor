import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret123'

socketio = SocketIO(app)

rooms = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join_room')
def handle_join(data):
    username = data['username']
    room_id = data['room_id']

    join_room(room_id)

    if room_id not in rooms:
        rooms[room_id] = {
            "code": "<h1>Hello Cloud Editor</h1>\n<p>This is my code editor.</p>",
            "users": []
        }

    if username not in rooms[room_id]["users"]:
        rooms[room_id]["users"].append(username)

    print("JOIN EVENT RECEIVED:", data)

    emit("load_code", {"code": rooms[room_id]["code"]})
    emit("receive_message", {"user": "System", "message": username + " joined"}, room=room_id)

@socketio.on('code_change')
def handle_code_change(data):
    room_id = data['room_id']
    code = data['code']

    rooms[room_id]["code"] = code

    emit("code_update", {"code": code}, room=room_id, include_self=False)

@socketio.on('send_message')
def handle_message(data):
    room_id = data['room_id']
    username = data['username']
    message = data['message']

    emit("receive_message", {
        "user": username,
        "message": message
    }, room=room_id)

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=5000, debug=True, allow_unsafe_werkzeug=True)
