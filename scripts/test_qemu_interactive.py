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

print("Starting QEMU...")
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
        print("send_qmp error:", e)

time.sleep(2)
print("Sending RET to GRUB...")
send_qmp("sendkey ret")

all_output = b""
start = time.time()
logged_in = False
sent_cmd = False

while time.time() - start < 70:
    r, _, _ = select.select([proc.stdout], [], [], 0.5)
    if r:
        try:
            chunk = os.read(proc.stdout.fileno(), 4096)
            if not chunk: break
            all_output += chunk
            sys.stdout.buffer.write(chunk)
            sys.stdout.buffer.flush()
        except Exception:
            pass

    if not logged_in and (b"login:" in all_output or time.time() - start > 35):
        print("\n>>> Logging in as root...")
        proc.stdin.write(b"\nroot\n")
        proc.stdin.flush()
        time.sleep(1)
        proc.stdin.write(b"toor\n")
        proc.stdin.flush()
        logged_in = True

    if logged_in and not sent_cmd and (time.time() - start > 45):
        print("\n>>> Running diagnostic commands...")
        cmds = [
            "ps aux | grep -E 'Xorg|X |lightdm'",
            "systemctl status lightdm",
            "ls -la /var/log/lightdm",
            "cat /var/log/lightdm/lightdm.log",
            "cat /var/log/lightdm/x-0.log",
            "cat /var/log/Xorg.0.log",
            "journalctl -u lightdm -n 30 --no-pager",
            "ls -la /dev/dri /dev/fb*"
        ]
        for c in cmds:
            proc.stdin.write(f"echo '=== {c} ==='\n{c}\n".encode())
            proc.stdin.flush()
            time.sleep(1)
        sent_cmd = True
        break

# wait for command output
end_wait = time.time() + 15
while time.time() < end_wait:
    r, _, _ = select.select([proc.stdout], [], [], 0.5)
    if r:
        try:
            chunk = os.read(proc.stdout.fileno(), 4096)
            if chunk:
                all_output += chunk
                sys.stdout.buffer.write(chunk)
                sys.stdout.buffer.flush()
        except Exception:
            pass

send_qmp("screendump /tmp/inter_screen.ppm")
time.sleep(1)
send_qmp("quit")
proc.terminate()
proc.wait()

with open("/home/abz/abzos/inter_output.txt", "wb") as f:
    f.write(all_output)

print("\nDone! Screen dump:")
if os.path.exists("/tmp/inter_screen.ppm"):
    from PIL import Image
    im = Image.open("/tmp/inter_screen.ppm")
    im.save("/home/abz/abzos/inter_screen.png")
    print(f"Captured: {im.size}, colors: {len(im.getcolors(1000) or [])}")
