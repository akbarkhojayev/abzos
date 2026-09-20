#!/bin/bash
set -e

BASE_DIR="/home/abz/abzos"
DEB_IMAGE="${BASE_DIR}/debian_image"
ISO_NAME="${BASE_DIR}/abzOS-Debian-1.0-amd64.iso"

echo "========================================================="
echo "   Building abzOS 1.0 (Pure Debian 12 Bookworm) Live ISO  "
echo "========================================================="

echo "=== [1/4] Preparing image directories ==="
rm -rf "${DEB_IMAGE}"
mkdir -p "${DEB_IMAGE}/live" "${DEB_IMAGE}/boot/grub"

CID=$(docker create abzos-debian:final)
trap 'docker rm "$CID" 2>/dev/null || true' EXIT

echo "=== [2/4] Extracting Debian Kernel and Initramfs ==="
mkdir -p /tmp/deb_boot
docker cp "$CID":/boot/. /tmp/deb_boot/
VM_PATH=$(ls -t /tmp/deb_boot/vmlinuz-* 2>/dev/null | head -n 1)
INIT_PATH=$(ls -t /tmp/deb_boot/initrd.img-* 2>/dev/null | head -n 1)

if [ -z "$VM_PATH" ] || [ -z "$INIT_PATH" ]; then
    echo "Error: kernel or initrd not found in container boot directory"
    exit 1
fi

cp "$VM_PATH" "${DEB_IMAGE}/live/vmlinuz"
cp "$INIT_PATH" "${DEB_IMAGE}/live/initrd.img"
rm -rf /tmp/deb_boot
echo "Kernel: $(basename $VM_PATH)"
echo "Initrd: $(basename $INIT_PATH)"

# Configure GRUB
cat << 'GRUB' > "${DEB_IMAGE}/boot/grub/grub.cfg"
set default="0"
set timeout=5

insmod efi_gop
insmod efi_uga
insmod gfxterm
terminal_output gfxterm

set menu_color_normal=white/black
set menu_color_highlight=cyan/black

menuentry "abzOS 1.0 (Debian 12 Bookworm - Hyprland Edition)" {
    linux /live/vmlinuz boot=live components quiet console=tty0 console=ttyS0,115200 username=abzos user-fullname="abzOS User"
    initrd /live/initrd.img
}

menuentry "abzOS 1.0 (Safe Graphics / Failsafe Mode - nomodeset)" {
    linux /live/vmlinuz boot=live components nomodeset console=tty0 console=ttyS0,115200 username=abzos user-fullname="abzOS User"
    initrd /live/initrd.img
}
GRUB

echo "=== [3/4] Building Clean SquashFS from Docker export ==="
echo "Preserving UIDs/GIDs/SUID, stripping container artifacts (.dockerenv), and configuring hostname..."
rm -f "${DEB_IMAGE}/live/filesystem.squashfs"
python3 "${BASE_DIR}/scripts/stream_squashfs.py" "$CID" "${DEB_IMAGE}/live/filesystem.squashfs"

echo "=== [4/4] Building Bootable Hybrid Debian ISO ==="
rm -f "${ISO_NAME}"
grub-mkrescue -o "${ISO_NAME}" "${DEB_IMAGE}" -- -volid "abzOS_Deb12"

sha256sum "${ISO_NAME}" > "${ISO_NAME}.sha256"
echo "========================================================="
echo "   abzOS (Pure Debian 12) ISO Created Successfully!     "
echo "========================================================="
ls -lh "${ISO_NAME}"
