import socket as sc
import threading as th
import json
import os

IP = input("Enter IPv4: ")
PORT = int(input("Enter port: "))
USERNAME = input("Enter Username: ")

print("Connecting...")

sock = sc.socket(sc.AF_INET, sc.SOCK_STREAM)
sock.settimeout(5)

Active = True

try:
    sock.connect((IP,PORT))

    sock.send(json.dumps({"type": "connected", "args": {"username": USERNAME}}).encode())

    def send_thread():
        global Active
        while True:
            if Active:
                com = input(">>> ")
                if com.startswith("/"):
                    if com == "/leave":
                        sock.send(json.dumps({"type": "leave", "args": {"username": USERNAME}}).encode())
                        print("Leaving...")
                else:
                    if Active:
                        sock.send(json.dumps({"type": "message", "args": {"username": USERNAME, "message": com}}).encode())
            else:
                break
        return 1

    def recv_thread():
        global Active
        while True:
            if Active:
                try:
                    compressedData = sock.recv(1024*16)
                    data = json.loads(compressedData.decode())
                    if data["type"] == "message_history":
                        if os.name == "nt":
                            os.system("cls")
                        else:
                            os.system("clear -x")
                        print(data["args"]["history"])
                    if data["type"] == "check":
                        pass
                    if data["type"] == "leave_ready":
                        Active = False
                        sock.close()
                except:
                    if Active:
                        print("RECV ERR")
                    else:
                        pass
            else:
                break
        return 1

    SendThread = th.Thread(target=send_thread)
    SendThread.start()
    RecvThread = th.Thread(target=recv_thread)
    RecvThread.start()
except sc.timeout:
    print("Timed out!")

except Exception as e:
    print("Connection failed!")
    print(e)