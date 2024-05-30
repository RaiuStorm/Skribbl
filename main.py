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
            rooms[room] = {"members":[], "messages":[]} # members will be [{"usr-id":"AAAA", "usr":"username"}] for security reasons yo
        session["name"] = user
        session["room"] = room
        return redirect(url_for("room"))
    return render_template("home.html")

@app.route("/room")
def room():
    user = session["name"]
    room = session["room"]
    if room not in rooms or not user:
        return redirect(url_for("home"))
    return render_template("room.html", room=room)
@socketio.on("connect")
def connect(auth):
    user = session["name"]
    room = session["room"]
    usr_id = len(rooms[room]["members"])+1
    session["usr-id"] = usr_id
    join_room(room)
    user_data = {"usr-id": usr_id, "user":user}
    rooms[room]["members"].append(user_data)
    content = "has joined the room. Have fun!"
    send({"msg":content, "usr":user, "usr-list": rooms[room]["members"]}, to=room)
    print(f"User {user} has connected to room {room}.")
@socketio.on("disconnect")
def disconnect():
    user = session["name"]
    room = session["room"]
    usr_id = session["usr-id"]
    leave_room(room)
    del rooms[room]["members"][usr_id]
    if len(rooms[room]["members"]) <= 0:
        del rooms[room]
    content = f"{user} has left the room. Shame on them!"
    send({"msg":content, "usr-list":rooms[room]["members"]}, to=room)
    print(f"User {user} has disconnected from room {room}.")
    # TODO check python code for problems and figure out the javascript side

if __name__ == "__main__":
    socketio.run(app, debug=True)