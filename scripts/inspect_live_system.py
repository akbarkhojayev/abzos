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

# Helper to read until prompt
def read_until_prompt(timeout=60):
    buf = ""
    start = time.time()
    while time.time() - start < timeout:
        r, _, _ = select.select([proc.stdout], [], [], 0.5)
        if r:
            line = proc.stdout.readline()
            if not line: break
            buf += line
            if "root@abzos:~#" in line or "root@abzos:" in line:
                return buf
    return buf

print("Waiting for prompt on serial...")
out = read_until_prompt(65)
print("Initial boot output captured (length:", len(out), ")")

def run_cmd(c):
    proc.stdin.write(c + "\n")
    proc.stdin.flush()
    return read_until_prompt(10)

proc.stdin.write("export SYSTEMD_PAGER=cat\nexport PAGER=cat\n")
proc.stdin.flush()
time.sleep(1)

commands = [
    "systemctl is-active lightdm",
    "systemctl status lightdm",
    "journalctl -u lightdm -n 30",
    "ps aux | grep -E 'Xorg|X|lightdm|sway|waybar'",
    "ls -la /var/log/lightdm",
    "cat /var/log/lightdm/lightdm.log",
    "cat /var/log/lightdm/x-0.log",
    "cat /var/log/lightdm/seat0-greeter.log",
    "fgconsole",
    "loginctl"
]

results = {}
for c in commands:
    print(f"Running: {c}")
    results[c] = run_cmd(c)

with open("/home/abz/abzos/live_debug_report.txt", "w") as f:
    for c, res in results.items():
        f.write(f"\n===== CMD: {c} =====\n{res}\n")

# Take screendump
send_qmp("screendump /tmp/live_screen.ppm")
time.sleep(1)
send_qmp("quit")
proc.terminate()
proc.wait()

if os.path.exists("/tmp/live_screen.ppm"):
    im = Image.open("/tmp/live_screen.ppm")
    im.save("/home/abz/abzos/live_screen.png")
    print(f"Captured screen: size={im.size}, colors={len(im.getcolors(200000) or [])}, bbox={im.getbbox()}")
