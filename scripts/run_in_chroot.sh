#!/bin/bash
set -e

CHROOT_DIR="/chroot"
COMMAND="$@"

cleanup() {
    echo "Unmounting chroot pseudo-filesystems..."
    umount -lf ${CHROOT_DIR}/dev/pts 2>/dev/null || true
    umount -lf ${CHROOT_DIR}/dev 2>/dev/null || true
    umount -lf ${CHROOT_DIR}/sys 2>/dev/null || true
    umount -lf ${CHROOT_DIR}/proc 2>/dev/null || true
}

trap cleanup EXIT

echo "Mounting /proc, /sys, /dev into chroot..."
mount -t proc /proc ${CHROOT_DIR}/proc
mount -t sysfs /sys ${CHROOT_DIR}/sys
mount --bind /dev ${CHROOT_DIR}/dev
mount --bind /dev/pts ${CHROOT_DIR}/dev/pts

echo "Executing command in chroot: $COMMAND"
chroot ${CHROOT_DIR} $COMMAND

echo "Chroot execution finished successfully."
