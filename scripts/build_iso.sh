#!/bin/bash
set -e

BASE_DIR="/home/abz/abzos"
CHROOT_DIR="${BASE_DIR}/chroot"
IMAGE_DIR="${BASE_DIR}/image"
ISO_NAME="${BASE_DIR}/abzOS-1.0-amd64.iso"

echo "========================================================="
echo "       abzOS 1.0 ISO Build Pipeline Started             "
echo "========================================================="

echo "[1/5] Updating kernel and initramfs in casper directory..."
LATEST_VMLINUZ=$(ls -t ${CHROOT_DIR}/boot/vmlinuz-* 2>/dev/null | head -n 1)
LATEST_INITRD=$(ls -t ${CHROOT_DIR}/boot/initrd.img-* 2>/dev/null | head -n 1)

if [ -n "$LATEST_VMLINUZ" ] && [ -n "$LATEST_INITRD" ]; then
    cp "$LATEST_VMLINUZ" "${IMAGE_DIR}/casper/vmlinuz"
    cp "$LATEST_INITRD" "${IMAGE_DIR}/casper/initrd"
    echo "  -> Copied $(basename $LATEST_VMLINUZ) & $(basename $LATEST_INITRD)"
fi

echo "[2/5] Calculating filesystem size..."
printf $(du -sx --block-size=1 "${CHROOT_DIR}" | cut -f1) > "${IMAGE_DIR}/casper/filesystem.size"

echo "[3/5] Building SquashFS filesystem (this may take a few minutes)..."
rm -f "${IMAGE_DIR}/casper/filesystem.squashfs"
mksquashfs "${CHROOT_DIR}" "${IMAGE_DIR}/casper/filesystem.squashfs" \
    -comp xz \
    -b 1048576 \
    -noappend \
    -all-root \
    -e boot \
    -wildcards

echo "[4/5] Building Bootable Hybrid ISO (UEFI + BIOS)..."
rm -f "${ISO_NAME}"
grub-mkrescue -o "${ISO_NAME}" "${IMAGE_DIR}" -- -volid "abzOS_1_0"

echo "[5/5] Generating SHA256 checksum..."
cd "${BASE_DIR}"
sha256sum "$(basename ${ISO_NAME})" > "${ISO_NAME}.sha256"

echo "========================================================="
echo "       abzOS 1.0 ISO Created Successfully!              "
echo "========================================================="
ls -lh "${ISO_NAME}"
cat "${ISO_NAME}.sha256"
