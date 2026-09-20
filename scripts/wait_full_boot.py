import subprocess
import time
import socket
import os
import sys
from PIL import Image

ISO = "/home/abz/abzos/abzOS-Debian-1.0-amd64.iso"
MON_SOCK = "/tmp/qemu_full.sock"
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

print("Waiting 95s for complete XFCE desktop to load on QEMU TCG...")
time.sleep(95)

proc.stdin.write(b"echo '=== FINAL PROCESSES ==='\nps aux | grep -E 'xfce|xfwm4|xfdesktop|xfce4-panel'\n")
proc.stdin.flush()
time.sleep(3)

ppm = "/tmp/full_screen.ppm"
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

print(all_out.decode(errors='replace')[-1500:])

if os.path.exists(ppm):
    im = Image.open(ppm)
    im.save("/home/abz/abzos/full_screen.png")
    colors = len(im.getcolors(200000) or [])
    print(f"\nFinal captured screen: size={im.size}, colors={colors}, bbox={im.getbbox()}")
else:
    print("No PPM")
