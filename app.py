from flask import Flask, request, jsonify
import threading, time, socket, json, os, signal, atexit
import requests, jwt, urllib3
from datetime import datetime
from google.protobuf.timestamp_pb2 import Timestamp

from SpamReqInvApiMain import *
from SpamReqInvApiSetting import *

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ===============================
# ACCOUNTS
# ===============================
ACCOUNTS = {
    "4262891717": "PASSWORD_1",   # MASTER
    "4262894242": "PASSWORD_2",
    "4262900525": "PASSWORD_3",
    "4262902857": "PASSWORD_4",
    "4262905460": "PASSWORD_5"
}

MASTER_ACCOUNT_ID = "4262891717"

app = Flask(__name__)
clients = {}
shutting_down = False

shared_0500_info = {
    "got": False,
    "idT": None,
    "squad": None,
    "AutH": None
}

# ===============================
# TCP BOT CLIENT
# ===============================
class TcpBotConnectMain:
    def __init__(self, account_id, password):
        self.account_id = account_id
        self.password = password
        self.key = None
        self.iv = None
        self.socket_client = None
        self.DaTa2 = None
        self.AutH = None

    # -------------------------------
    # SOCKET CHECK
    # -------------------------------
    def is_socket_connected(self):
        try:
            self.socket_client.send(b'')
            return True
        except:
            return False

    # -------------------------------
    # SAFE 0500 (MASTER ONLY)
    # -------------------------------
    def get_0500_slow(self, team_code, ghost_name, wait_time=4, max_retries=2):
        global shared_0500_info

        for _ in range(max_retries):
            try:
                # JOIN ONCE
                self.socket_client.send(
                    GenJoinSquadsPacket(team_code, self.key, self.iv)
                )

                start = time.time()
                while time.time() - start < wait_time:
                    if self.DaTa2 and '0500' in self.DaTa2.hex()[:4]:
                        data = json.loads(
                            DeCode_PackEt(self.DaTa2.hex()[10:])
                        )

                        idT = data["5"]["data"]["1"]["data"]
                        sq = data["5"]["data"]["31"]["data"]

                        shared_0500_info.update({
                            "got": True,
                            "idT": idT,
                            "squad": sq,
                            "AutH": self.AutH
                        })

                        self.socket_client.send(
                            ghost_pakcet(idT, ghost_name, sq, self.key, self.iv)
                        )
                        time.sleep(0.2)
                        self.socket_client.send(
                            ExiT('000000', self.key, self.iv)
                        )
                        return True

                    time.sleep(0.1)

                self.socket_client.send(ExiT('000000', self.key, self.iv))
                time.sleep(2)

            except:
                pass

        return False

    # -------------------------------
    # COMMAND EXECUTION
    # -------------------------------
    def execute_command(self, command):
        global shared_0500_info

        if not self.is_socket_connected():
            return "Socket not connected"

        if command.startswith("/niva="):
            parts = command[6:].split("&", 1)
            if len(parts) < 2:
                return "Invalid format"

            team_code, ghost_name = parts

            # MASTER
            if self.account_id == MASTER_ACCOUNT_ID:
                shared_0500_info["got"] = False

                ok = self.get_0500_slow(team_code, ghost_name)
                if not ok:
                    return f"0500 not received for {team_code}"

                return "niva master success"

            # GHOST
            else:
                wait = 0
                while not shared_0500_info["got"] and wait < 10:
                    time.sleep(0.5)
                    wait += 1

                if not shared_0500_info["got"]:
                    return "Timeout waiting master"

                self.socket_client.send(
                    GenJoinSquadsPacket(shared_0500_info["idT"], self.key, self.iv)
                )
                time.sleep(0.3)
                self.socket_client.send(ExiT('000000', self.key, self.iv))
                self.socket_client.send(
                    ghost_pakcet(
                        shared_0500_info["idT"],
                        ghost_name,
                        shared_0500_info["squad"],
                        self.key,
                        self.iv
                    )
                )
                return "niva ghost success"

        return "Unknown command"

    # -------------------------------
    # CONNECTION (KEEP YOUR ORIGINAL)
    # -------------------------------
    def run(self):
        # ⚠️ Keep your existing token + socket connect logic here
        pass


# ===============================
# ROUTES
# ===============================
@app.route("/")
def home():
    return """
<!DOCTYPE html>
<html>
<head>
<title>NIVA GHOST BOT</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
body{
margin:0;
width:100vw;
height:100vh;
display:flex;
align-items:center;
justify-content:center;
background:#000;
color:#fff;
font-family:Arial,Helvetica,sans-serif;
}
h1{
font-size:clamp(3rem,10vw,7rem);
letter-spacing:6px;
}
</style>
</head>
<body>
<h1>NIVA GHOST BOT</h1>
</body>
</html>
"""

@app.route("/niva", methods=["GET"])
def niva_command():
    teamcode = request.args.get("teamcode")
    if not teamcode:
        return jsonify({"error": "teamcode required"}), 400

    names = {
        "4262891717": "[b][c][ff9999]Nivashini",
        "4262894242": "[b][c][99ff99]insta : [ffff99]ft_rosie._",
        "4262900525": "[b][c][9999ff]Ꭱꭷနεㅤʚĭɞ",
        "4262902857": "[b][c][ff99ff]Ꭱꭷနεㅤʚĭɞ",
        "4262905460": "[b][c][ffff99]insta :[99ff99] ft_rosie._"
    }

    results = {}
    for aid, client in clients.items():
        name = names.get(aid, aid)
        res = client.execute_command(f"/niva={teamcode}&{name}")
        results[aid] = res

    return jsonify({"results": results})


# ===============================
# STARTUP
# ===============================
def cleanup():
    print("Shutting down...")

atexit.register(cleanup)

if __name__ == "__main__":
    for aid, pwd in ACCOUNTS.items():
        c = TcpBotConnectMain(aid, pwd)
        clients[aid] = c
        threading.Thread(target=c.run, daemon=True).start()
        time.sleep(2)

    port = int(os.environ.get("PORT", 15040))
    app.run(host="0.0.0.0", port=port)
