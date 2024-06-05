from flask import Flask, render_template, redirect, url_for, session, request
from flask_socketio import SocketIO, send, join_room, leave_room
import random
from string import ascii_uppercase

app = Flask(__name__)
app.config['SECRET_KEY'] = "pzIM5UX2e9U8jdB56zz3HHoV5tAVdEZ220Uq8IiVLA"
socketio = SocketIO(app)
rooms = {}

def generate_code(length):
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)
        if code not in rooms:
            break
    return code

@app.route("/", methods=["POST", "GET"])
def home():
    session.clear()
    if request.method == "POST":
        user = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)
        if join != False and not user or create != False and not user:
            return render_template("home.html", error="No username entered")
        if join != False and not code:
            return render_template("home.html",error="No code provided")
        room = code
        if join != False and room not in rooms:
            return render_template("home.html", error="Room does not exist")
        elif create != False:
            room = generate_code(4)
            rooms[room] = {"members":[], "messages":[]} # members will be [{"usr-id":0", "usr":"username"}] for security reasons yo
        session["name"] = user
        session["room"] = room
        return redirect(url_for("room"))
    return render_template("home.html")

@app.route("/room")
def room():
    user = session.get("name")
    room = session.get("room")
    if room not in rooms or not user:
        return redirect(url_for("home"))
    return render_template("room.html", room=room)
@socketio.on("connect")
def connect(auth):
    user = session.get("name")
    room = session.get("room")
    usr_id = len(rooms[room]["members"])
    session["usr-id"] = usr_id
    join_room(room)
    user_data = {"usr-id": usr_id, "user":user}
    rooms[room]["members"].append(user_data)
    content = "has joined the room. Have fun!"
    send({"msg":content, "usr":user, "usrList": rooms[room]["members"]}, to=room)
    print(f"User {user} has connected to room {room}.")
@socketio.on("disconnect")
def disconnect():
    user = session.get("name")
    room = session.get("room")
    usr_id = session.get("usr-id")
    leave_room(room)
    if room in rooms:
        del rooms[room]["members"][usr_id]
        if len(rooms[room]["members"]) <= 0:
            del rooms[room]
            return
    content = f"{user} has left the room. Shame on them!"
    send({"msg":content, "usr":user, "usrList":rooms[room]["members"]}, to=room)
    print(f"User {user} has disconnected from room {room}.")

@socketio.on("message")
def send_msg(data):
    user = session.get("name")
    room = session.get("room")
    send({"msg":data["msg"], "usr":user}, to=room)
    rooms[room]["messages"].append(data["msg"])

if __name__ == "__main__":
    socketio.run(app, debug=True)