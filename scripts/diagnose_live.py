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

print("Launching QEMU...")
proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

def send_qmp(cmd_str):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.connect(MON_SOCK)
        s.sendall(f"{cmd_str}\n".encode())
        time.sleep(0.3)
        s.close()
    except Exception as e:
        print(f"send_qmp error for {cmd_str}: {e}")

time.sleep(2)
print("Sending Enter to GRUB...")
send_qmp("sendkey ret")

start_time = time.time()
output = []
logged_in = False

print("Waiting for root prompt on serial...")
while time.time() - start_time < 65:
    r, _, _ = select.select([proc.stdout], [], [], 0.5)
    if r:
        line = proc.stdout.readline()
        if not line: break
        output.append(line)
        if "root@abzos:~#" in line or "root@abzos:" in line or "automatic login" in line:
            print("Detected root prompt!")
            logged_in = True
            break

time.sleep(2)
proc.stdin.write("\nexport PAGER=cat\nexport SYSTEMD_PAGER=cat\nstty cols 200\n")
proc.stdin.flush()
time.sleep(1)

commands = [
    "echo '=== SYSTEMCTL LIGHTDM ==='",
    "systemctl status lightdm --no-pager",
    "echo '=== PS AUX GRAPHICAL ==='",
    "ps aux | grep -E 'Xorg|X|lightdm|sway|waybar|mako'",
    "echo '=== LIGHTDM LOG ==='",
    "cat /var/log/lightdm/lightdm.log",
    "echo '=== X-0 LOG ==='",
    "cat /var/log/lightdm/x-0.log",
    "echo '=== SEAT0 GREETER LOG ==='",
    "cat /var/log/lightdm/seat0-greeter.log",
    "echo '=== XSESSION ERRORS ==='",
    "cat /home/abzos/.xsession-errors",
    "echo '=== USER LOGIND STATUS ==='",
    "loginctl session-status 1 --no-pager",
    "echo '=== FGCONSOLE ==='",
    "fgconsole",
    "echo '=== SWITCH TO VT7 ==='",
    "chvt 7",
    "echo '=== DIAGNOSTICS COMPLETE ==='"
]

print("Sending commands...")
for c in commands:
    proc.stdin.write(c + "\n")
    proc.stdin.flush()
    time.sleep(0.8)

diag_out = []
end_time = time.time() + 20
while time.time() < end_time:
    r, _, _ = select.select([proc.stdout], [], [], 0.5)
    if r:
        line = proc.stdout.readline()
        if not line: break
        diag_out.append(line)
        if "=== DIAGNOSTICS COMPLETE ===" in line:
            print("Finished collecting output!")
            break

with open("/home/abz/abzos/full_diag.txt", "w") as f:
    f.writelines(output)
    f.writelines(diag_out)

print("Capturing screendump...")
ppm_path = "/tmp/diag_screen.ppm"
png_path = "/home/abz/abzos/diag_screen.png"
send_qmp(f"screendump {ppm_path}")
time.sleep(1)

send_qmp("quit")
proc.terminate()
proc.wait()

if os.path.exists(ppm_path):
    im = Image.open(ppm_path)
    im.save(png_path, "PNG")
    colors = len(im.getcolors(200000) or [])
    bbox = im.getbbox()
    print(f"Screen captured: size={im.size}, colors={colors}, bbox={bbox}")

print("Diagnosis done. See /home/abz/abzos/full_diag.txt")
