import subprocess
import time
import socket
import os
import sys
from PIL import Image

ISO = "/home/abz/abzos/abzOS-Debian-1.0-amd64.iso"
MON_SOCK = "/tmp/qemu_hypr.sock"
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

print("Launching QEMU Hyprland verification...")
proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=0)
os.set_blocking(proc.stdout.fileno(), False)

def send_qmp(cmd_str):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.connect(MON_SOCK)
        s.sendall(f"{cmd_str}\n".encode())
        time.sleep(0.3)
        s.close()
    except Exception as e:
        print("send_qmp err:", e)

time.sleep(2)
send_qmp("sendkey ret")

print("Waiting 65s for Sway & Waybar to initialize...")
time.sleep(65)

proc.stdin.write(b"echo '=== GRAPHICAL PROCESSES ==='\nps aux | grep -E 'sway|waybar|wofi|mako|Xorg|lightdm'\n")
proc.stdin.flush()
time.sleep(3)

ppm = "/tmp/hypr_screen.ppm"
png = "/home/abz/abzos/hypr_screen.png"
send_qmp(f"screendump {ppm}")
time.sleep(1)

# Also test launching terminal via Sway shortcut (Super+Return)
send_qmp("sendkey meta_l-ret")
time.sleep(4)

ppm2 = "/tmp/hypr_tiled.ppm"
png2 = "/home/abz/abzos/hypr_tiled.png"
send_qmp(f"screendump {ppm2}")
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
    im.save(png)
    colors = len(im.getcolors(200000) or [])
    print(f"\nInitial Sway screen: size={im.size}, colors={colors}, bbox={im.getbbox()}")

if os.path.exists(ppm2):
    im2 = Image.open(ppm2)
    im2.save(png2)
    colors2 = len(im2.getcolors(200000) or [])
    print(f"\nTiled window screen: size={im2.size}, colors={colors2}, bbox={im2.getbbox()}")
