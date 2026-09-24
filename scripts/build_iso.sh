#!/bin/bash
set -e

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE_DIR="${BASE_DIR}/image"
ISO_NAME="${BASE_DIR}/abzOS-1.0-amd64.iso"
DOCKER_TAG="abzos:1.0"

echo "========================================================="
echo "           Building abzOS 1.0 (Arch Linux / DDE) ISO       "
echo "========================================================="

ISO_LABEL="ABZOS"

echo "=== [1/5] Building container image ==="
docker build -f "${BASE_DIR}/scripts/Dockerfile" -t "${DOCKER_TAG}" "${BASE_DIR}"

echo "=== [2/5] Preparing image directories ==="
rm -rf "${IMAGE_DIR}"
mkdir -p "${IMAGE_DIR}/arch/x86_64" "${IMAGE_DIR}/boot/grub"

CID=$(docker create "${DOCKER_TAG}")
trap 'docker rm "$CID" 2>/dev/null || true' EXIT

echo "=== [3/5] Extracting kernel and initramfs ==="
mkdir -p /tmp/abzos_boot
docker cp "$CID":/boot/. /tmp/abzos_boot/
VM_PATH=$(ls -t /tmp/abzos_boot/vmlinuz-linux 2>/dev/null | head -n 1)
INIT_PATH=$(ls -t /tmp/abzos_boot/initramfs-linux.img 2>/dev/null | head -n 1)

if [ -z "$VM_PATH" ] || [ -z "$INIT_PATH" ]; then
    echo "Error: kernel or initramfs not found in container boot directory"
    exit 1
fi

cp "$VM_PATH" "${IMAGE_DIR}/arch/x86_64/vmlinuz-linux"
cp "$INIT_PATH" "${IMAGE_DIR}/arch/x86_64/initramfs-linux.img"
rm -rf /tmp/abzos_boot
echo "Kernel: $(basename "$VM_PATH")"
echo "Initramfs: $(basename "$INIT_PATH")"

mkdir -p "${IMAGE_DIR}/boot/grub/themes/abzos" "${IMAGE_DIR}/boot/grub/fonts"
cp -r "${BASE_DIR}/scripts/grub-theme/"* "${IMAGE_DIR}/boot/grub/themes/abzos/" 2>/dev/null || true
if [ -f /usr/share/grub/unicode.pf2 ]; then
    cp /usr/share/grub/unicode.pf2 "${IMAGE_DIR}/boot/grub/fonts/"
fi

cat << GRUB > "${IMAGE_DIR}/boot/grub/grub.cfg"
set default="0"
set timeout=5

insmod all_video
insmod efi_gop
insmod efi_uga
insmod gfxterm
insmod png
insmod font

if [ -f /boot/grub/fonts/unicode.pf2 ]; then
    loadfont /boot/grub/fonts/unicode.pf2
fi

set gfxmode=1920x1080,1440x900,1280x1024,1024x768,auto
set gfxpayload=keep

terminal_output gfxterm

if [ -f /boot/grub/themes/abzos/theme.txt ]; then
    set theme=/boot/grub/themes/abzos/theme.txt
else
    set menu_color_normal=white/black
    set menu_color_highlight=cyan/black
fi

menuentry "abzOS 1.0 (Live Desktop)" {
    linux /arch/x86_64/vmlinuz-linux archisobasedir=arch archisolabel=${ISO_LABEL} cow_spacesize=2G console=tty0 console=ttyS0,115200
    initrd /arch/x86_64/initramfs-linux.img
}

menuentry "abzOS 1.0 (Safe Graphics - nomodeset)" {
    linux /arch/x86_64/vmlinuz-linux archisobasedir=arch archisolabel=${ISO_LABEL} cow_spacesize=2G nomodeset console=tty0 console=ttyS0,115200
    initrd /arch/x86_64/initramfs-linux.img
}
GRUB

echo "=== [4/5] Building squashfs from the container export ==="
echo "Preserving UIDs/GIDs/SUID, stripping container artifacts (.dockerenv), and configuring hostname..."
rm -f "${IMAGE_DIR}/arch/x86_64/airootfs.sfs"
python3 "${BASE_DIR}/scripts/stream_squashfs.py" "$CID" "${IMAGE_DIR}/arch/x86_64/airootfs.sfs"

echo "=== [5/5] Building bootable hybrid ISO (BIOS + UEFI) ==="
# The airootfs.sfs (full DDE + dev/pentest toolkit) is well over 4GB, which
# plain ISO9660 can't hold in one file. grub-mkrescue appends our "--" args
# to the END of its own generated xorriso command sequence, so passing
# -compliance there is too late (the size check already ran). Instead, feed
# grub-mkrescue a thin xorriso wrapper that injects the compliance rule as
# the very first command, before anything else runs.
XORRISO_WRAPPER="${BASE_DIR}/scripts/xorriso-large-iso-wrapper.sh"
cat << 'XORRISO_WRAP' > "${XORRISO_WRAPPER}"
#!/bin/bash
exec xorriso -compliance iso_9660_level=3 "$@"
XORRISO_WRAP
chmod +x "${XORRISO_WRAPPER}"

rm -f "${ISO_NAME}"
grub-mkrescue --xorriso="${XORRISO_WRAPPER}" -o "${ISO_NAME}" "${IMAGE_DIR}" -- -volid "${ISO_LABEL}"

(cd "${BASE_DIR}" && sha256sum "$(basename "${ISO_NAME}")" > "$(basename "${ISO_NAME}").sha256")

echo "========================================================="
echo "              abzOS 1.0 ISO created successfully!         "
echo "========================================================="
ls -lh "${ISO_NAME}"
cat "${ISO_NAME}.sha256"
