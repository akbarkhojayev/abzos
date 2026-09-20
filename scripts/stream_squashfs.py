#!/usr/bin/env python3
import sys
import os
import tarfile
import subprocess
import io

if len(sys.argv) < 3:
    print(f"Usage: {sys.argv[0]} <docker_container_id> <output_squashfs_path>")
    sys.exit(1)

cid = sys.argv[1]
squashfs_path = sys.argv[2]

print(f"[*] Exporting container {cid} and streaming to mksquashfs...")

p_in = subprocess.Popen(['docker', 'export', cid], stdout=subprocess.PIPE, bufsize=1048576)
p_out = subprocess.Popen([
    'mksquashfs', '-', squashfs_path,
    '-tar', '-comp', 'xz', '-b', '1048576', '-noappend',
    '-wildcards', '-e', 'boot'
], stdin=subprocess.PIPE, bufsize=1048576)

tar_in = tarfile.open(fileobj=p_in.stdout, mode='r|*')
tar_out = tarfile.open(fileobj=p_out.stdin, mode='w|')

count = 0
excluded = 0

for member in tar_in:
    # Match any variant of .dockerenv
    basename = os.path.basename(member.name.rstrip('/'))
    if basename == '.dockerenv' or member.name in ('.dockerenv', '/.dockerenv', 'dockerenv'):
        print(f"[*] Stripping container artifact: {member.name}")
        excluded += 1
        continue

    norm_name = member.name.lstrip('./')
    if norm_name == 'etc/hostname':
        data = b'abzos\n'
        member.size = len(data)
        tar_out.addfile(member, io.BytesIO(data))
        count += 1
        continue
    if norm_name == 'etc/hosts':
        data = b'127.0.0.1\tlocalhost\n127.0.1.1\tabzos\n::1\tlocalhost ip6-localhost ip6-loopback\n'
        member.size = len(data)
        tar_out.addfile(member, io.BytesIO(data))
        count += 1
        continue
    
    f = tar_in.extractfile(member) if member.isreg() else None
    tar_out.addfile(member, f)
    count += 1

tar_out.close()
p_out.stdin.close()
ret = p_out.wait()
p_in.wait()

if ret != 0:
    print(f"[!] mksquashfs failed with return code {ret}")
    sys.exit(ret)

print(f"[+] Successfully wrote squashfs: {count} items included, {excluded} container markers removed.")
