import subprocess
import time
import os
from PIL import Image

ISO_PATH = "/home/abz/abzos/abzOS-Debian-1.0-amd64.iso"
print(f"Testing ISO: {ISO_PATH}")

PPM_PATH = "/tmp/abzos_screen.ppm"
PNG_PATH = "/home/abz/abzos/abzos_boot_screenshot.png"
ART_PATH = "/home/abz/.gemini/antigravity/brain/32301160-1ee1-4e90-a3b2-6bcc199915d3/abzos_boot_screenshot.png"

cmd = [
    "qemu-system-x86_64",
    "-m", "2048",
    "-smp", "2",
    "-cdrom", ISO_PATH,
    "-boot", "d",
    "-vga", "virtio",
    "-display", "none",
    "-monitor", "stdio"
]

proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

try:
    print("Waiting 3s for GRUB...")
    time.sleep(3)
    proc.stdin.write("sendkey ret\n")
    proc.stdin.flush()
    
    print("Waiting 65s for full system and XFCE desktop boot...")
    time.sleep(65)
    
    print("Capturing screendump...")
    proc.stdin.write(f"screendump {PPM_PATH}\n")
    proc.stdin.flush()
    time.sleep(2)
    
    proc.stdin.write("quit\n")
    proc.stdin.flush()
    proc.wait(timeout=5)
except Exception as e:
    print(f"Exception: {e}")
    proc.kill()

if os.path.exists(PPM_PATH):
    img = Image.open(PPM_PATH)
    img.save(PNG_PATH, "PNG")
    img.save(ART_PATH, "PNG")
    print(f"Screenshot successfully saved to {PNG_PATH}")
else:
    print("PPM was not generated.")
