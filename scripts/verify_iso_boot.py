import subprocess
import time
import socket
import os
import sys
import select
from PIL import Image

ISO = "/home/abz/abzos/abzOS-1.0-amd64.iso"
MON_SOCK = "/tmp/qemu_verify.sock"
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
    "-monitor", f"unix:{MON_SOCK},server,nowait",
]

print("Starting QEMU verification...", flush=True)
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
        print("send_qmp err:", e, flush=True)


def pump(seconds):
    """Read+echo QEMU serial output for the given duration; returns bytes read."""
    out = b""
    end = time.time() + seconds
    while time.time() < end:
        r, _, _ = select.select([proc.stdout], [], [], 0.5)
        if r:
            try:
                chunk = os.read(proc.stdout.fileno(), 4096)
                if not chunk:
                    break
                out += chunk
                sys.stdout.buffer.write(chunk)
                sys.stdout.buffer.flush()
            except Exception:
                pass
    return out


time.sleep(2)
print("Sending RET to GRUB...", flush=True)
send_qmp("sendkey ret")

all_out = b""
start = time.time()

# Wait for the getty login banner to appear (kernel/live-boot finished),
# up to 60s, then give the graphical target (lightdm -> sway) time to settle
# before typing anything -- the custom abzOS prompt never contains "root@",
# so we can't detect shell-readiness from the prompt text itself.
while time.time() - start < 60:
    all_out += pump(1)
    if b"login:" in all_out:
        break

print("\n>>> Login banner seen, waiting for the graphical session to settle...", flush=True)
all_out += pump(25)

print("\n>>> Running diagnostics via serial...", flush=True)
cmds = [
    "",
    "echo '=== SYSTEMD VIRT ==='",
    "systemd-detect-virt",
    "echo '=== DEFAULT TARGET ==='",
    "systemctl get-default",
    "echo '=== SYSTEMCTL LIGHTDM ==='",
    "systemctl status lightdm --no-pager",
    "echo '=== PS GRAPHICAL ==='",
    "ps aux | grep -E 'Xorg|lightdm|sway|waybar' | grep -v grep",
    "echo '=== ACTIVE VT ==='",
    "fgconsole",
    "echo '=== XSESSION ERRORS ==='",
    "cat /home/abzos/.xsession-errors 2>&1",
    "echo '=== XORG LOG ==='",
    "tail -n 25 /var/log/Xorg.0.log 2>&1",
    "echo '=== DIAG_DONE ==='",
]
for c in cmds:
    proc.stdin.write(f"{c}\n".encode())
    proc.stdin.flush()
    time.sleep(0.6)

all_out += pump(15)

print("Capturing screendump...", flush=True)
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
    print(f"\nCaptured screen: size={im.size}, colors={colors}, bbox={im.getbbox()}", flush=True)
else:
    print("\nNo PPM generated", flush=True)
