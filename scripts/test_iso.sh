#!/bin/bash
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ISO_PATH="${BASE_DIR}/abzOS-1.0-amd64.iso"

if [ ! -f "$ISO_PATH" ]; then
    echo "Error: ISO not found at $ISO_PATH"
    echo "Run ./scripts/build_iso.sh first."
    exit 1
fi

echo "Launching abzOS 1.0 (Arch Linux - Deepin Edition) in QEMU virtual machine..."
# 6GB RAM (the live squashfs alone is ~6GB, so 2GB was causing heavy swapping)
# and virtio-vga-gl + gl=on give the guest real GPU-accelerated OpenGL via
# virgl instead of falling back to slow CPU software rendering for KWin's
# compositing -- both were major sources of the sluggishness in earlier tests.
qemu-system-x86_64 \
    -m 6144 \
    -smp 4 \
    -cdrom "$ISO_PATH" \
    -boot d \
    -device virtio-vga-gl \
    -display gtk,gl=on,zoom-to-fit=on \
    -device virtio-serial-pci \
    -chardev spicevmc,id=vdagent,name=vdagent \
    -device virtserialport,chardev=vdagent,name=com.redhat.spice.0 \
    -enable-kvm 2>/dev/null || \
qemu-system-x86_64 \
    -m 6144 \
    -smp 4 \
    -cdrom "$ISO_PATH" \
    -boot d \
    -vga virtio \
    -display gtk,zoom-to-fit=on
