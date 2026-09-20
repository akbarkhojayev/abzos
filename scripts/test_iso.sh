#!/bin/bash
ISO_PATH="/home/abz/abzos/abzOS-1.0-amd64.iso"

if [ ! -f "$ISO_PATH" ]; then
    echo "Error: ISO not found at $ISO_PATH"
    echo "Run ./scripts/build_iso.sh first."
    exit 1
fi

echo "Launching abzOS 1.0 (Pure Debian 12) in QEMU virtual machine..."
qemu-system-x86_64 \
    -m 2048 \
    -smp 2 \
    -cdrom "$ISO_PATH" \
    -boot d \
    -vga std \
    -display gtk \
    -enable-kvm 2>/dev/null || \
qemu-system-x86_64 \
    -m 2048 \
    -smp 2 \
    -cdrom "$ISO_PATH" \
    -boot d \
    -vga std
