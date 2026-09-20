import subprocess
import time
import socket
import os
import sys
import select

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

time.sleep(40) # wait for boot
print("Logging in...")
proc.stdin.write(b"\nroot\ntoor\n")
proc.stdin.flush()
time.sleep(3)

print("Running deep session inspection...")
cmds = [
    "echo '=== WHOAMI / PWD ==='",
    "id",
    "echo '=== FGCONSOLE ==='",
    "fgconsole",
    "echo '=== PS AUX FULL ==='",
    "ps -ef",
    "echo '=== XSESSION ERRORS ==='",
    "cat /home/abzos/.xsession-errors",
    "echo '=== DISPLAY TEST ==='",
    "su - abzos -c 'DISPLAY=:0 xrandr'",
    "su - abzos -c 'DISPLAY=:0 xprop -root'",
    "echo '=== ROOT WINDOW TEST ==='",
    "su - abzos -c 'DISPLAY=:0 xwininfo -root -tree'",
    "echo '=== TRY DRAWING RED TO SCREEN ==='",
    "su - abzos -c 'DISPLAY=:0 xsetroot -solid red'",
    "echo '=== TEST DONE ==='"
]

for c in cmds:
    proc.stdin.write(f"{c}\n".encode())
    proc.stdin.flush()
    time.sleep(1)

time.sleep(5)
# capture screen after drawing red
send_qmp("screendump /tmp/test_red.ppm")
time.sleep(1)
send_qmp("quit")
proc.terminate()
proc.wait()

all_out = b""
while True:
    r, _, _ = select.select([proc.stdout], [], [], 0.5)
    if r:
        try:
            chunk = os.read(proc.stdout.fileno(), 4096)
            if not chunk: break
            all_out += chunk
        except Exception:
            break
    else:
        break

with open("/home/abz/abzos/xsession_inspection.txt", "wb") as f:
    f.write(all_out)

if os.path.exists("/tmp/test_red.ppm"):
    from PIL import Image
    im = Image.open("/tmp/test_red.ppm")
    im.save("/home/abz/abzos/test_red.png")
    print(f"Red test screen: {im.size}, colors: {len(im.getcolors(1000) or [])}")

print("Inspection completed!")
