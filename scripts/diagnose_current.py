import subprocess
import time
import socket
import os
import select

ISO = "/home/abz/abzos/abzOS-Debian-1.0-amd64.iso"
MON_SOCK = "/tmp/q_mon.sock"
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

proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
os.set_blocking(proc.stdout.fileno(), False)

time.sleep(2)
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect(MON_SOCK)
s.sendall(b"sendkey ret\n")
s.close()

all_log = open("/home/abz/abzos/current_boot_log.txt", "wb")
start = time.time()
logged_in = False
sent = False

while time.time() - start < 75:
    r, _, _ = select.select([proc.stdout], [], [], 0.5)
    if r:
        try:
            chunk = os.read(proc.stdout.fileno(), 4096)
            if chunk:
                all_log.write(chunk)
                all_log.flush()
        except: pass

    if not sent and time.time() - start > 45:
        proc.stdin.write(b"\necho '=== LIGHTDM LOG ==='\ncat /var/log/lightdm/lightdm.log\necho '=== PS ALL ==='\nps aux\necho '=== XSESSION ERRORS ==='\ncat /home/abzos/.xsession-errors\n")
        proc.stdin.flush()
        sent = True

all_log.close()

# capture screenshot
try:
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect(MON_SOCK)
    s.sendall(b"screendump /tmp/current_boot.ppm\n")
    time.sleep(1)
    s.sendall(b"quit\n")
    s.close()
except: pass

proc.terminate()
proc.wait()

from PIL import Image
if os.path.exists("/tmp/current_boot.ppm"):
    im = Image.open("/tmp/current_boot.ppm")
    im.save("/home/abz/abzos/current_boot.png")
    print(f"Captured screen: size={im.size}, colors={len(im.getcolors(200000) or [])}")
