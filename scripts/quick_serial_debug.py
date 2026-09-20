import subprocess
import time
import socket
import os
import sys
import select
from PIL import Image

ISO = "/home/abz/abzos/abzOS-Debian-1.0-amd64.iso"
MON_SOCK = "/tmp/qemu_mon.sock"
if os.path.exists(MON_SOCK):
    os.unlink(MON_SOCK)

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

proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

def send_qmp(cmd_str):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.connect(MON_SOCK)
        s.sendall(f"{cmd_str}\n".encode())
        time.sleep(0.3)
        s.close()
    except Exception as e:
        print("send_qmp error:", e)

time.sleep(2)
send_qmp("sendkey ret")

print("Waiting 45s for boot...")
time.sleep(45)

script = """
exec 2>&1
echo "=== CHECKING PROCESSES ==="
ps aux | grep -E 'lightdm|X|sway|waybar|wofi'
echo "=== LIGHTDM STATUS ==="
systemctl status lightdm --no-pager
echo "=== LIGHTDM LOG ==="
cat /var/log/lightdm/lightdm.log 2>/dev/null || true
echo "=== X-0 LOG ==="
cat /var/log/lightdm/x-0.log 2>/dev/null || true
echo "=== FGCONSOLE & SEATS ==="
fgconsole
loginctl --no-pager
echo "=== HOME DIR ==="
ls -la /home/abzos
echo "=== XSESSION ERRORS ==="
cat /home/abzos/.xsession-errors 2>/dev/null || true
echo "=== JOURNAL GRAPHICAL ==="
journalctl -b --no-pager | grep -iE 'lightdm|sway|wayland|drm|xorg' | tail -n 40
echo "=== ALL_DONE_MARKER ==="
"""

proc.stdin.write(script + "\n")
proc.stdin.flush()

print("Reading output...")
collected = ""
start = time.time()
while time.time() - start < 15:
    r, _, _ = select.select([proc.stdout], [], [], 0.5)
    if r:
        line = proc.stdout.readline()
        if not line: break
        collected += line
        if "=== ALL_DONE_MARKER ===" in line:
            print("Found marker!")
            break

with open("/home/abz/abzos/quick_debug.txt", "w") as f:
    f.write(collected)

send_qmp("screendump /tmp/quick_screen.ppm")
time.sleep(1)
send_qmp("quit")
proc.terminate()
proc.wait()

if os.path.exists("/tmp/quick_screen.ppm"):
    im = Image.open("/tmp/quick_screen.ppm")
    im.save("/home/abz/abzos/quick_screen.png")
    print(f"Captured screen: size={im.size}, colors={len(im.getcolors(200000) or [])}, bbox={im.getbbox()}")

print("Saved report to /home/abz/abzos/quick_debug.txt")
