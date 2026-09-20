import subprocess
import time
import socket
import os
import sys
import select
from PIL import Image

ISO = "/home/abz/abzos/abzOS-Debian-1.0-amd64.iso"
MON_SOCK = "/tmp/qemu_verify.sock"
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

print("Starting QEMU verification...")
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
print("Sending RET to GRUB...")
send_qmp("sendkey ret")

all_out = b""
start = time.time()
sent_diag = False

while time.time() - start < 50:
    r, _, _ = select.select([proc.stdout], [], [], 0.5)
    if r:
        try:
            chunk = os.read(proc.stdout.fileno(), 4096)
            if not chunk: break
            all_out += chunk
            sys.stdout.buffer.write(chunk)
            sys.stdout.buffer.flush()
        except Exception:
            pass

    if not sent_diag and (b"root@abzos" in all_out or b"login:" in all_out or time.time() - start > 40):
        print("\n>>> Running diagnostics via serial...")
        cmds = [
            "echo '=== SYSTEMD VIRT ==='",
            "systemd-detect-virt",
            "echo '=== SYSTEMCTL LIGHTDM ==='",
            "systemctl status lightdm --no-pager",
            "echo '=== PS GRAPHICAL ==='",
            "ps aux | grep -E 'Xorg|X |lightdm|xfce|xfwm4|xfdesktop|thunar'",
            "echo '=== ACTIVE VT ==='",
            "fgconsole",
            "echo '=== XSESSION ERRORS ==='",
            "cat /home/abzos/.xsession-errors",
            "echo '=== XORG LOG ==='",
            "tail -n 25 /var/log/Xorg.0.log"
        ]
        for c in cmds:
            proc.stdin.write(f"{c}\n".encode())
            proc.stdin.flush()
            time.sleep(0.8)
        sent_diag = True
        break

# wait for command output
end_wait = time.time() + 10
while time.time() < end_wait:
    r, _, _ = select.select([proc.stdout], [], [], 0.5)
    if r:
        try:
            chunk = os.read(proc.stdout.fileno(), 4096)
            if not chunk: break
            all_out += chunk
            sys.stdout.buffer.write(chunk)
            sys.stdout.buffer.flush()
        except Exception:
            pass

print("Capturing screendump...")
ppm = "/tmp/iso_verify.ppm"
png = "/home/abz/abzos/iso_verify.png"
send_qmp(f"screendump {ppm}")
time.sleep(1)
send_qmp("quit")
proc.terminate()
proc.wait()

with open("/home/abz/abzos/verify_output.txt", "wb") as f:
    f.write(all_out)

if os.path.exists(ppm):
    im = Image.open(ppm)
    im.save(png)
    colors = len(im.getcolors(maxcolors=200000) or [])
    print(f"\nCaptured screen: size={im.size}, colors={colors}, bbox={im.getbbox()}")
else:
    print("\nNo PPM generated")

