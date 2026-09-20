import subprocess
import time
import socket
import os
import sys
import select
from PIL import Image

ISO = "/home/abz/abzos/abzOS-Debian-1.0-amd64.iso"
MON_SOCK = "/tmp/qemu_wait.sock"
if os.path.exists(MON_SOCK): os.unlink(MON_SOCK)

cmd = [
    "qemu-system-x86_64",
    "-m", "2048",
    "-smp", "2",
    "-cdrom", ISO,
    "-boot", "d",
    "-vga", "std",
    "-display", "none",
    "-serial", "stdio",
    "-monitor", f"unix:{MON_SOCK},server,nowait"
]

proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=0)
os.set_blocking(proc.stdout.fileno(), False)

def send_qmp(cmd_str):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.connect(MON_SOCK)
        s.sendall(f"{cmd_str}\n".encode())
        time.sleep(0.3)
        s.close()
    except Exception:
        pass

time.sleep(2)
send_qmp("sendkey ret")

print("Waiting 50s for boot + XFCE initialization...")
time.sleep(50)

print("Running inspection...")
cmds = [
    "ps aux | grep -E 'Xorg|X |lightdm|xfce|xfwm4|xfdesktop|thunar'",
    "cat /var/log/lightdm/lightdm.log | tail -n 25",
    "cat /home/abzos/.xsession-errors 2>/dev/null",
    "cat /var/log/Xorg.0.log | tail -n 25"
]

for c in cmds:
    proc.stdin.write(f"echo '=== {c} ==='\n{c}\n".encode())
    proc.stdin.flush()
    time.sleep(1)

time.sleep(5)
ppm = "/tmp/wait_screen.ppm"
send_qmp(f"screendump {ppm}")
time.sleep(1)
send_qmp("quit")
proc.terminate()
proc.wait()

all_out = b""
while True:
    try:
        chunk = os.read(proc.stdout.fileno(), 4096)
        if not chunk: break
        all_out += chunk
    except Exception:
        break

with open("/home/abz/abzos/wait_output.txt", "wb") as f:
    f.write(all_out)

if os.path.exists(ppm):
    im = Image.open(ppm)
    im.save("/home/abz/abzos/wait_screen.png")
    colors = len(im.getcolors(200000) or [])
    print(f"\nCaptured: size={im.size}, colors={colors}, bbox={im.getbbox()}")
