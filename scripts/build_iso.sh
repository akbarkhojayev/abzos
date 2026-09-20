#!/bin/bash
set -e

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE_DIR="${BASE_DIR}/image"
ISO_NAME="${BASE_DIR}/abzOS-1.0-amd64.iso"
DOCKER_TAG="abzos:1.0"

echo "========================================================="
echo "         Building abzOS 1.0 (Debian 12 Bookworm) ISO      "
echo "========================================================="

echo "=== [1/5] Building container image ==="
docker build -f "${BASE_DIR}/scripts/Dockerfile" -t "${DOCKER_TAG}" "${BASE_DIR}"

echo "=== [2/5] Preparing image directories ==="
rm -rf "${IMAGE_DIR}"
mkdir -p "${IMAGE_DIR}/live" "${IMAGE_DIR}/boot/grub"

CID=$(docker create "${DOCKER_TAG}")
trap 'docker rm "$CID" 2>/dev/null || true' EXIT

echo "=== [3/5] Extracting kernel and initramfs ==="
mkdir -p /tmp/abzos_boot
docker cp "$CID":/boot/. /tmp/abzos_boot/
VM_PATH=$(ls -t /tmp/abzos_boot/vmlinuz-* 2>/dev/null | head -n 1)
INIT_PATH=$(ls -t /tmp/abzos_boot/initrd.img-* 2>/dev/null | head -n 1)

if [ -z "$VM_PATH" ] || [ -z "$INIT_PATH" ]; then
    echo "Error: kernel or initrd not found in container boot directory"
    exit 1
fi

cp "$VM_PATH" "${IMAGE_DIR}/live/vmlinuz"
cp "$INIT_PATH" "${IMAGE_DIR}/live/initrd.img"
rm -rf /tmp/abzos_boot
echo "Kernel: $(basename "$VM_PATH")"
echo "Initrd: $(basename "$INIT_PATH")"

cat << 'GRUB' > "${IMAGE_DIR}/boot/grub/grub.cfg"
set default="0"
set timeout=5

insmod efi_gop
insmod efi_uga
insmod gfxterm
terminal_output gfxterm

set menu_color_normal=white/black
set menu_color_highlight=cyan/black

menuentry "abzOS 1.0 (Debian 12 Bookworm)" {
    linux /live/vmlinuz boot=live components quiet console=tty0 console=ttyS0,115200 username=abzos user-fullname="abzOS User"
    initrd /live/initrd.img
}

menuentry "abzOS 1.0 (Safe Graphics / Failsafe Mode - nomodeset)" {
    linux /live/vmlinuz boot=live components nomodeset console=tty0 console=ttyS0,115200 username=abzos user-fullname="abzOS User"
    initrd /live/initrd.img
}
GRUB

echo "=== [4/5] Building squashfs from the container export ==="
echo "Preserving UIDs/GIDs/SUID, stripping container artifacts (.dockerenv), and configuring hostname..."
rm -f "${IMAGE_DIR}/live/filesystem.squashfs"
python3 "${BASE_DIR}/scripts/stream_squashfs.py" "$CID" "${IMAGE_DIR}/live/filesystem.squashfs"

echo "=== [5/5] Building bootable hybrid ISO (BIOS + UEFI) ==="
rm -f "${ISO_NAME}"
grub-mkrescue -o "${ISO_NAME}" "${IMAGE_DIR}" -- -volid "abzOS_1_0"

(cd "${BASE_DIR}" && sha256sum "$(basename "${ISO_NAME}")" > "$(basename "${ISO_NAME}").sha256")

echo "========================================================="
echo "              abzOS 1.0 ISO created successfully!         "
echo "========================================================="
ls -lh "${ISO_NAME}"
cat "${ISO_NAME}.sha256"
