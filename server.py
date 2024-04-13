import socket as sc
import threading as th
from datetime import datetime as dt
import json
import time
import traceback
import requests as rq
import sys
import os
import base64

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

VERS = "1.0.3"

try:
    AUTOUPDATEDATA = rq.get("https://raw.githubusercontent.com/Spalishe/python-chat/main/autoupdate/server/latestversion.txt",timeout=5)
    VERSIONLIST = rq.get("https://raw.githubusercontent.com/Spalishe/python-chat/main/autoupdate/server/versionlist.txt",timeout=5)
    def checkExistVersion(ver):
        Arr = VERSIONLIST.text.splitlines()
        if ver in Arr:
            return True
        
        return False

    print(f"{bcolors.OKCYAN}[UPDATE] Checking for updates...{bcolors.ENDC}")
    if VERS != AUTOUPDATEDATA.text:
        print(f"{bcolors.OKGREEN}[UPDATE] Update found! New version {AUTOUPDATEDATA.text} is available. You can install it with --upgrade {AUTOUPDATEDATA.text}{bcolors.ENDC}")
    else:
        print(f"{bcolors.OKBLUE}[UPDATE] Installed last version {VERS}{bcolors.ENDC}")
except:
    print(f"{bcolors.FAIL}[UPDATE] Can't request autoupdate data. Please check your internet connection and try again.{bcolors.ENDC}")

ARGV = sys.argv

for i in range(1,len(ARGV)):
    KEY = ARGV[i]
    if KEY.lower() == "--upgrade":
        ver = ARGV[i+1] if not ARGV[i+1].startswith("-") else "0" 
        if ver != "0":
            if checkExistVersion(ver):
                print(f"{bcolors.OKGREEN}[UPDATE] Found version {ver}, downloading...{bcolors.ENDC}")
                UPDATEDATA = rq.get("https://raw.githubusercontent.com/Spalishe/python-chat/main/autoupdate/server/" + ver + "/server.py")
                f = open(os.path.realpath(__file__), "w")
                f.write(UPDATEDATA.text)
                f.close()
                print(f"{bcolors.OKGREEN}[UPDATE] Updated succesfully.{bcolors.ENDC}")
                os._exit(0)
        else:
            print(f"{bcolors.FAIL}[UPDATE] Version {ver} is not exists!{bcolors.ENDC}")
            os._exit(0)
    if KEY.lower() == "--help" or KEY == "-?":
        print("""List of available arguments: 
    --upgrade: Upgrades program to selected version
    --help: Shows this menu
""")
        os._exit(0)

MessageHistory = []
MessageHistoryDEBUG = []
ConnList = []

IP = "192.168.1.29" 
PORT = 57632
MAXCONN = 10

sock = sc.socket(sc.AF_INET, sc.SOCK_STREAM)
sock.bind((IP, PORT))
sock.listen(MAXCONN)

print(f"{bcolors.OKGREEN}---== SERVER SUCCESFULLY STARTED ==---{bcolors.ENDC}")
print(f"{bcolors.OKGREEN}[IPv4] {IP}{bcolors.ENDC}")
print(f"{bcolors.OKGREEN}[Port] {PORT}{bcolors.ENDC}")
print(f"{bcolors.OKGREEN}[Max Connections] {MAXCONN}{bcolors.ENDC}")
print(f"{bcolors.OKGREEN}---==   WAITING FOR CONNECTION   ==---{bcolors.ENDC}")

def getUsernameByConn(conn):
    for conndata in ConnList:
        if conndata["conn"] == conn:
            return conndata["username"]
        
def getParamByConn(conn, param):
    for conndata in ConnList:
        if conndata["conn"] == conn:
            return conndata[param]


def checkIfHasValue(conn):
    for conndata in ConnList:
        if conndata["conn"] == conn:
            return True
        
    return False

def client_thread_check(clientconn,clientaddr):
    TimeOutCount = 0
    while True:
        time.sleep(1)
        if checkIfHasValue(clientconn):
            clientconn.sendall(base64.b64encode(json.dumps({"type":"check"}).encode()))
            TimeOutCount = 0
        else:
            TimeOutCount = TimeOutCount + 1
            if TimeOutCount >= 5:
                break
    
    return 1

def client_thread(clientconn,clientaddr):
    while True:
        try:
            compressedData = clientconn.recv(1024**2)
            b64dec = base64.b64decode(compressedData)
            if b64dec != b'':
                data = json.loads(b64dec)
                now = dt.now().strftime("%d/%m/%Y %H:%M:%S")
                if data["type"] == "connected":
                    usrn = data["args"]["username"]
                    debug = data["args"]["debug"]
                    send_to_all(now, clientaddr, "SERVER", f"User {usrn} joined to chat.")
                    ConnList.append({"conn": clientconn, "addr": clientaddr, "username": usrn, "debug": debug})
                    clientconn.sendall(base64.b64encode(json.dumps({"type": "message_history", "args": {"history": ''.join(MessageHistory)}}).encode()))
                if data["type"] == "message":
                    usrn = data["args"]["username"]
                    send_to_all(now, clientaddr, usrn, data["args"]["message"])
                if data["type"] == "leave":
                    usrn = data["args"]["username"]
                    debug = getParamByConn(clientconn, "debug")
                    usr = getUsernameByConn(clientconn)
                    ConnList.remove({"conn": clientconn, "addr": clientaddr, "username": usr, "debug": debug})
                    send_to_all(now, clientaddr, "SERVER", f"User {usrn} leaved from chat.")
                    clientconn.sendall(base64.b64encode(json.dumps({"type":"leave_ready"}).encode()))
        except sc.timeout:
            usr = getUsernameByConn(clientconn)
            debug = getParamByConn(clientconn, "debug")
            ConnList.remove({"conn": clientconn, "addr": clientaddr, "username": usr, "debug": debug})
            send_to_all(now, clientaddr, "SERVER", f"User {usr} timed out!")
            break
        except sc.error:
            usr = getUsernameByConn(clientconn)
            debug = getParamByConn(clientconn, "debug")
            ConnList.remove({"conn": clientconn, "addr": clientaddr, "username": usr, "debug": debug})
            send_to_all(now, clientaddr, "SERVER", f"User {usr} errored!")
            print(f"{bcolors.FAIL}{traceback.format_exc()}{bcolors.ENDC}")
            break
    return 1

def send_to_all(time, addr, username, message):
    print(f"{bcolors.OKBLUE}[{time}] {username}: {message}{bcolors.ENDC}")
    MessageHistory.append(f"[{time}] {username}: {message}\n")
    MessageHistoryDEBUG.append(f"[{time}] {username}{addr}: {message}\n")
    for conndata in ConnList:
        conn = conndata["conn"]
        DEBUG = getParamByConn(conn, "debug")
        try:
            conn.sendall(base64.b64encode(json.dumps({"type": "message_history", "args": {"history": ''.join(MessageHistoryDEBUG if DEBUG else MessageHistory)}}).encode()))
        except ConnectionAbortedError:
            continue

while True:
    conn, addr = sock.accept()
    thr = th.Thread(target = client_thread,args=[conn,addr])
    print(f"{bcolors.OKGREEN}---= NEW CONNECTION {addr} =---{bcolors.ENDC}")
    thr.start()
    thrc = th.Thread(target = client_thread_check, args=[conn,addr])
    thrc.start()