import socket as sc
import threading as th
import json
import os
import requests as rq
import sys
import lzma
lzd = lzma.LZMADecompressor()
lzc = lzma.LZMACompressor()

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

VERS = "1.0.52"

AUTOUPDATEDATA = rq.get("https://raw.githubusercontent.com/Spalishe/python-chat/main/autoupdate/client/latestversion.txt")
VERSIONLIST = rq.get("https://raw.githubusercontent.com/Spalishe/python-chat/main/autoupdate/client/versionlist.txt")
def checkExistVersion(ver):
    Arr = VERSIONLIST.text.splitlines()
    if ver in Arr:
        return True
    
    return False

print(f"{bcolors.OKCYAN}Checking for updates...{bcolors.ENDC}")
if VERS != AUTOUPDATEDATA.text:
    print(f"{bcolors.OKGREEN}Update found! New version {AUTOUPDATEDATA.text} is available. You can install it with --upgrade {AUTOUPDATEDATA.text}{bcolors.ENDC}")
else:
    print(f"{bcolors.OKBLUE}Installed last version {VERS}{bcolors.ENDC}")

ARGV = sys.argv

IPArgs = ""
PortArgs = 0
UsernameArgs = ""
TimeoutArgs = 0
DEBUG = False

for i in range(1,len(ARGV)):
    KEY = ARGV[i]
    if KEY.lower() == "--debug":
        DEBUG = True
        print(f"{bcolors.OKGREEN}[DEBUG] Debug mode is enabled. You will receive all information off connection and program status.{bcolors.ENDC}")
    if KEY.lower() == "--ip" or KEY.upper() == "-I":
        IPArgs = ARGV[i]
    if KEY.lower() == "--port" or KEY.upper() == "-P":
        PortArgs = int(ARGV[i])
    if KEY.lower() == "--username" or KEY.upper() == "-U":
        UsernameArgs = ARGV[i]
    if KEY.lower() == "--timeout" or KEY.upper() == "-T":
        TimeoutArgs = int(ARGV[i])
    if KEY.lower() == "--upgrade":
        ver = ARGV[i+1] if not ARGV[i+1].startswith("-") else "0" 
        if ver != "0":
            if checkExistVersion(ver):
                print(f"{bcolors.OKGREEN}[UPDATE] Found version {ver}, downloading...{bcolors.ENDC}")
                UPDATEDATA = rq.get("https://raw.githubusercontent.com/Spalishe/python-chat/main/autoupdate/client/" + ver + "/client.py")
                f = open(os.path.realpath(__file__), "w")
                f.write(UPDATEDATA.text)
                f.close()
                print(f"{bcolors.OKGREEN}[UPDATE] Updated succesfully.{bcolors.ENDC}")
                os._exit(0)
            else:
                print(f"{bcolors.FAIL}[UPDATE] Version {ver} is not exists!{bcolors.ENDC}")
                os._exit(0)
        else:
            print("List of existing versions:\n" + VERSIONLIST.text)
            os._exit(0)
    if KEY.lower() == "--help" or KEY == "-?":
        print("""List of available arguments: 
        --ip or -I: Specifies connection IPv4 address   
        --port or -P: Specifies connection port
        --username or -U: Specifies your nickname
        --timeout or -T: Indicates after what number of seconds the timeout will occur
        --upgrade: Upgrades program to selected version
        --help: Shows this menu
        --debug: Enables debug mode
    """)
        os._exit(0)

IP = IPArgs if IPArgs != "" else input("Enter IPv4: ")
PORT = PortArgs if PortArgs != 0 else int(input("Enter port: "))
USERNAME = UsernameArgs if UsernameArgs != "" else input("Enter Username: ")

print(f"{bcolors.OKBLUE}Connecting...{bcolors.ENDC}")

sock = sc.socket(sc.AF_INET, sc.SOCK_STREAM)
sock.settimeout(TimeoutArgs if TimeoutArgs >= 3 else 5)

Active = True

try:
    sock.connect((IP,PORT))

    print(f"{bcolors.OKGREEN}[CONNECTION] Connected succesfully!{bcolors.ENDC}")

    sock.send(lzc.compress(json.dumps({"type": "connected", "args": {"username": USERNAME, "debug": DEBUG}}).encode()))

    def send_thread():
        global Active
        while True:
            if Active:
                com = input(">>> ")
                if com.startswith("/"):
                    if com == "/leave":
                        sock.send(lzc.compress(json.dumps({"type": "leave", "args": {"username": USERNAME}}).encode()))
                        print(f"{bcolors.FAIL}Leaving...{bcolors.ENDC}")
                else:
                    if Active:
                        sock.send(lzc.compress(json.dumps({"type": "message", "args": {"username": USERNAME, "message": com}}).encode()))
            else:
                break
        return 1

    def recv_thread():
        global Active
        while True:
            if Active:
                try:
                    compressedData = sock.recv(1024*16)
                    data = json.loads(lzd.decompress(compressedData).decode())
                    if data["type"] == "message_history":
                        if os.name == "nt":
                            os.system("cls")
                        else:
                            os.system("clear -x")
                        hist = data["args"]["history"]
                        print(f"{bcolors.OKCYAN}{hist}{bcolors.ENDC}")
                    if data["type"] == "check":
                        pass
                    if data["type"] == "leave_ready":
                        Active = False
                        sock.close()
                except:
                    if Active:
                        print(f"{bcolors.FAIL}[CONNECTION] Server was shutted down or your internet connection has been lost.{bcolors.ENDC}")
                        Active = False
                        sock.close()
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
    print(f"{bcolors.FAIL}[CONNECTION] Timed out!{bcolors.ENDC}")

except Exception as e:
    print(f"{bcolors.FAIL}[CONNECTION] Excepted an error!{bcolors.ENDC}")
    print(e)