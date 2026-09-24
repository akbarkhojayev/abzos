FROM archlinux:latest

# --- 0. Pacman keyring & mirrors ----------------------------------------------
RUN pacman-key --init && pacman-key --populate archlinux && \
    pacman -Sy --noconfirm archlinux-keyring && \
    pacman -Syu --noconfirm

# --- 1. Base system, kernel & init -------------------------------------------
RUN pacman -S --noconfirm --needed \
    base linux linux-firmware linux-headers \
    mkinitcpio mkinitcpio-archiso \
    intel-ucode amd-ucode \
    sudo nano dbus polkit \
    grub efibootmgr dosfstools

# --- 2. Hardware Firmware & Drivers (Complete hardware & VM support) ---------
RUN pacman -S --noconfirm --needed \
    xorg-server xorg-xinit xorg-xrandr \
    xf86-video-amdgpu xf86-video-ati xf86-video-nouveau xf86-video-vesa \
    xf86-input-libinput \
    mesa vulkan-icd-loader vulkan-intel vulkan-radeon libva-mesa-driver \
    spice-vdagent qemu-guest-agent open-vm-tools \
    networkmanager wpa_supplicant wireless_tools rfkill \
    bluez bluez-utils \
    pipewire pipewire-pulse pipewire-alsa wireplumber pavucontrol alsa-utils \
    acpi acpid upower \
    ntfs-3g exfatprogs e2fsprogs parted

# --- 3. DDE (Deepin Desktop Environment) + Daily Apps -------------------------
# `deepin` and `deepin-extra` are official Arch package groups (extra repo) --
# no AUR or third-party repo needed for the desktop itself.
RUN pacman -S --noconfirm --needed deepin deepin-extra ddm

RUN pacman -S --noconfirm --needed \
    firefox vlc mpv gparted file-roller xdg-user-dirs pcmanfm-qt

# --- 3b. Replace the broken Deepin File Manager with PCManFM-Qt -------------
# dde-file-manager-daemon (Arch's deepin-file-manager package) only ships the
# backend services (DeviceManager, RecentManager, TagManager, VaultManager);
# it never actually creates a GUI window. Confirmed live: calling its D-Bus
# org.freedesktop.FileManager1.Open method (which is what the dock/app-grid
# launcher's "dde-file-manager -n %u" ultimately triggers) returns success
# but opens nothing, with or without a real path -- a genuine gap in this
# package build, not something fixable from a wrapper script. PCManFM-Qt is a
# real, working Qt file manager, so the existing "File Manager" launcher
# (same icon/name the dock already shows) is repointed at it instead.
RUN sed -i \
    -e 's|^Exec=.*|Exec=pcmanfm-qt %U|' \
    -e '/^Actions=/d' \
    /usr/share/applications/dde-file-manager.desktop && \
    sed -i '/^\[Desktop Action new-window\]/,$d' /usr/share/applications/dde-file-manager.desktop && \
    mkdir -p /etc/xdg && \
    cat << 'MIMEAPPS' > /etc/xdg/mimeapps.list
[Default Applications]
inode/directory=pcmanfm-qt.desktop
MIMEAPPS

# --- 4. Developer & Cybersecurity Toolkit -------------------------------------
RUN pacman -S --noconfirm --needed \
    base-devel gdb git curl wget jq tree htop python python-pip \
    nmap net-tools iputils traceroute whois \
    tcpdump socat openbsd-netcat wireshark-cli wireshark-qt \
    sqlmap john hydra aircrack-ng binwalk hexedit strace ltrace

# --- 4b. Calamares installer (built from its AUR source) ---------------------
# Calamares isn't in Arch's official repos -- Arch ships no installer of its
# own -- so it's built here from its actual upstream release via the AUR
# PKGBUILD, using only official-repo build dependencies (no third-party
# binary repo involved). makepkg refuses to run as root, hence the throwaway
# build user.
RUN pacman -S --noconfirm --needed \
    kcoreaddons kpmcore libpwquality qt6-declarative qt6-svg yaml-cpp \
    extra-cmake-modules libglvnd ninja qt6-tools qt6-translations && \
    useradd -m builder && \
    echo "builder ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/builder && \
    su builder -c 'cd /tmp && git clone --depth 1 https://aur.archlinux.org/calamares.git && cd calamares && makepkg -s --noconfirm' && \
    pacman -U --noconfirm /tmp/calamares/*.pkg.tar.zst && \
    rm -rf /tmp/calamares /home/builder && \
    userdel builder && rm -f /etc/sudoers.d/builder

# --- 5. System configuration & Dynamic Display Setup -------------------------
RUN echo "LANG=en_US.UTF-8" > /etc/locale.conf && \
    sed -i 's/^#en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen

# Pre-set timezone/keymap so systemd-firstboot doesn't prompt interactively
# (and delay) on every live boot.
RUN ln -sf /usr/share/zoneinfo/UTC /etc/localtime && \
    echo "KEYMAP=us" > /etc/vconsole.conf

RUN cat << 'DISP' > /usr/local/bin/abzos-display-setup
#!/bin/bash
# 1. Start spice-vdagent for auto-resizing in QEMU/KVM
if command -v spice-vdagent >/dev/null 2>&1; then
    spice-vdagent || true
fi

# 2. Start open-vm-tools daemon if in VMware
if command -v vmtoolsd >/dev/null 2>&1; then
    vmtoolsd -n vmusr &>/dev/null &
fi

# 3. Auto-detect display output and pick best native resolution
for output in $(xrandr 2>/dev/null | grep " connected" | awk '{print $1}'); do
    xrandr --output "$output" --auto || true
done
DISP
RUN chmod +x /usr/local/bin/abzos-display-setup

RUN mkdir -p /etc/xdg/autostart && \
    cat << 'AUTO' > /etc/xdg/autostart/abzos-display.desktop
[Desktop Entry]
Type=Application
Name=abzOS Display Auto-Setup
Exec=/usr/local/bin/abzos-display-setup
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
AUTO

# --- 6. User & Identity -------------------------------------------------------
RUN (id -u abzos >/dev/null 2>&1 || useradd -m -s /bin/bash -u 1000 -U abzos) && \
    echo "abzos:abzos" | chpasswd && \
    echo "root:toor" | chpasswd && \
    usermod -aG wheel,audio,video,storage,optical,network,power abzos && \
    mkdir -p /etc/sudoers.d && \
    echo "abzos ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/abzos && \
    chmod 0440 /etc/sudoers.d/abzos

# Serial console root autologin for instant debugging & verification
RUN mkdir -p /etc/systemd/system/serial-getty@ttyS0.service.d && \
    cat << 'AUTOLOGIN' > /etc/systemd/system/serial-getty@ttyS0.service.d/autologin.conf
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin root --noclear %I 115200 $TERM
AUTOLOGIN

RUN echo "abzos" > /etc/hostname

RUN cat << 'OSREL' > /etc/os-release
NAME="abzOS"
PRETTY_NAME="abzOS 1.0 (Arch Linux - Deepin Edition)"
ID=abzos
ID_LIKE=arch
VERSION_ID="1.0"
VERSION="1.0"
LOGO=abzos-logo
HOME_URL="https://github.com/akbarkhojayev"
SUPPORT_URL="https://github.com/akbarkhojayev"
BUG_REPORT_URL="https://github.com/akbarkhojayev"
OSREL

RUN cat << 'ISSUE' > /etc/issue
abzOS 1.0 (Arch Linux - Deepin Edition) \n \l
ISSUE
RUN cp /etc/issue /etc/issue.net

# --- 7. Branding, Wallpaper & Icons -------------------------------------------
RUN mkdir -p /usr/share/backgrounds/abzos /usr/share/pixmaps /usr/share/icons

COPY scripts/wallpaper-t1.jpg /usr/share/backgrounds/abzos/wallpaper-t1.jpg
COPY scripts/wallpaper-t1.png /usr/share/backgrounds/abzos/wallpaper-t1.png
COPY scripts/abzos-logo.png /usr/share/pixmaps/abzos-logo.png
RUN chmod -R a+rX /usr/share/backgrounds/abzos /usr/share/pixmaps

# Replace every static wallpaper image DDE ships (both its "backgrounds" and
# "wallpapers" trees) directly with our own -- dde-appearance's actual
# default (picked via deepin-default-settings / its DConfig schema) isn't a
# single predictable file, so instead of reverse-engineering that config we
# just make every candidate file be our own image, guaranteeing whichever
# one gets picked shows abzOS branding. Live-wallpaper videos and the solid
# color swatches are left alone since those are opt-in extras, not defaults.
RUN find /usr/share/backgrounds/deepin /usr/share/wallpapers/deepin -maxdepth 1 -type f \( -iname '*.jpg' -o -iname '*.jpeg' \) 2>/dev/null \
        -exec cp /usr/share/backgrounds/abzos/wallpaper-t1.jpg {} \; ; \
    find /usr/share/backgrounds/deepin /usr/share/wallpapers/deepin -maxdepth 1 -type f -iname '*.png' 2>/dev/null \
        -exec cp /usr/share/backgrounds/abzos/wallpaper-t1.png {} \; ; \
    true

COPY scripts/abzos-logo-*.png /usr/share/icons/
RUN for sz in 16 24 32 48 64 128 256 512; do \
        if [ -f "/usr/share/icons/abzos-logo-$sz.png" ]; then \
            mkdir -p /usr/share/icons/hicolor/${sz}x${sz}/apps; \
            mv "/usr/share/icons/abzos-logo-$sz.png" /usr/share/icons/hicolor/${sz}x${sz}/apps/abzos-logo.png; \
        fi; \
    done && \
    mkdir -p /usr/share/icons/hicolor/scalable/apps && \
    cp /usr/share/pixmaps/abzos-logo.png /usr/share/icons/hicolor/scalable/apps/abzos-logo.png 2>/dev/null || true && \
    chmod -R a+rX /usr/share/icons/hicolor && \
    (which gtk-update-icon-cache >/dev/null 2>&1 && gtk-update-icon-cache -f -t /usr/share/icons/hicolor || true)

# Configure Calamares GUI Installer & Branding
COPY scripts/assets/calamares/branding/abzos /etc/calamares/branding/abzos
COPY scripts/assets/calamares/modules/ /etc/calamares/modules/
COPY scripts/assets/calamares/settings.conf /etc/calamares/settings.conf
COPY scripts/assets/calamares/abzos-calamares /usr/local/bin/abzos-calamares
COPY scripts/assets/calamares/abzos-installer.desktop /usr/share/applications/abzos-installer.desktop
RUN chmod +x /usr/local/bin/abzos-calamares /usr/share/applications/abzos-installer.desktop && \
    chmod -R a+rX /etc/calamares && \
    mkdir -p /etc/skel/Desktop && \
    cp /usr/share/applications/abzos-installer.desktop /etc/skel/Desktop/ && \
    chmod +x /etc/skel/Desktop/abzos-installer.desktop

# --- 8. DDM Configuration (Autologin straight into DDE) ----------------------
RUN cat << 'DDMCONF' > /etc/ddm.conf
[Autologin]
User=abzos
Session=deepin.desktop
Relogin=false

[General]
HaltCommand=/usr/bin/systemctl poweroff
RebootCommand=/usr/bin/systemctl reboot
DDMCONF

# --- 8b. KWin performance defaults (snappy on VMs and low-end GPUs) ----------
# Compositing animations/effects (blur, fade, scale, translucency) are heavy
# under software-rendered or weaker GPUs; turn animation speed to instant and
# disable the costliest effects so window management feels snappy everywhere,
# while leaving compositing itself on (so shadows/transparency still work).
RUN mkdir -p /etc/skel/.config && \
    cat << 'KWINRC' > /etc/skel/.config/kwinrc
[Compositing]
AnimationSpeed=1
Enabled=true
GLCore=false

[Plugins]
blurEnabled=false
contrastEnabled=false
kwin4_effect_fadeEnabled=false
kwin4_effect_fadedesktopEnabled=false
kwin4_effect_frozenappEnabled=false
kwin4_effect_maximizeEnabled=false
kwin4_effect_morphingpopupsEnabled=false
kwin4_effect_scaleEnabled=false
kwin4_effect_translucencyEnabled=false
magiclampEnabled=false
sheetEnabled=false
slideEnabled=false
slidingpopupsEnabled=false
wobblywindowsEnabled=false
zoomEnabled=false
KWINRC
RUN cp /etc/skel/.config/kwinrc /root/.config/kwinrc 2>/dev/null || (mkdir -p /root/.config && cp /etc/skel/.config/kwinrc /root/.config/kwinrc)

# --- 8c. Dark DDE theme (dock, control center, window chrome) ----------------
# dde-appearance has no static config file for its default theme -- it's set
# live via its own D-Bus API (org.deepin.dde.Appearance1's Set method) once
# the session is running. Applying it once on first login, via a marker file
# so it never re-runs, is the correct way to bake in a lasting default.
RUN cat << 'THEMESH' > /usr/local/bin/abzos-apply-dark-theme
#!/bin/bash
marker="$HOME/.config/.abzos-dark-theme-applied"
log="$HOME/.cache/abzos-dark-theme.log"
mkdir -p "$(dirname "$log")"
exec >>"$log" 2>&1
echo "--- $(date) pid=$$ HOME=$HOME DBUS_SESSION_BUS_ADDRESS=$DBUS_SESSION_BUS_ADDRESS XDG_RUNTIME_DIR=$XDG_RUNTIME_DIR ---"

if [ -f "$marker" ]; then
    echo "marker already present, exiting"
    exit 0
fi

for i in $(seq 1 30); do
    current="$(busctl --user get-property org.deepin.dde.Appearance1 /org/deepin/dde/Appearance1 org.deepin.dde.Appearance1 GlobalTheme 2>&1)"
    echo "attempt $i: GlobalTheme=$current"
    if [ "$current" = 's "nirvana.dark"' ]; then
        echo "already dark"
        break
    fi
    busctl --user call org.deepin.dde.Appearance1 /org/deepin/dde/Appearance1 org.deepin.dde.Appearance1 Set ss globaltheme nirvana.dark
    busctl --user call org.deepin.dde.Appearance1 /org/deepin/dde/Appearance1 org.deepin.dde.Appearance1 Set ss gtk deepin-dark
    sleep 2
done

mkdir -p "$(dirname "$marker")"
touch "$marker"
echo "done, marker written"
THEMESH
RUN chmod +x /usr/local/bin/abzos-apply-dark-theme

# XDG autostart (/etc/xdg/autostart) turned out not to be honored by DDE's
# session startup, so this runs as a systemd --user service instead, tied to
# default.target -- guaranteed to start with every user session regardless
# of which desktop environment reads (or doesn't read) XDG autostart entries.
RUN mkdir -p /etc/systemd/user/default.target.wants && \
    cat << 'UNIT' > /etc/systemd/user/abzos-dark-theme.service
[Unit]
Description=Apply abzOS dark theme on first login

[Service]
Type=oneshot
ExecStart=/usr/local/bin/abzos-apply-dark-theme

[Install]
WantedBy=default.target
UNIT
RUN ln -sf /etc/systemd/user/abzos-dark-theme.service /etc/systemd/user/default.target.wants/abzos-dark-theme.service

# --- 9. Modern Terminal Fetch & Shell Styling --------------------------------
RUN cat << 'FETCH' > /usr/local/bin/abzos-fetch
#!/bin/bash
c_cyan="\033[1;36m"
c_blue="\033[1;34m"
c_magenta="\033[1;35m"
c_green="\033[1;32m"
c_yellow="\033[1;33m"
c_white="\033[1;37m"
c_gray="\033[0;90m"
c_reset="\033[0m"

user="$(whoami)"
host="$(hostname)"
kernel="$(uname -r)"
mem_info="$(free -h 2>/dev/null | awk '/^Mem:/ {print $3 "/" $2}')"
pkgs="$(pacman -Qq 2>/dev/null | wc -l)"

echo -e "
 ${c_cyan}      /\\        ${c_cyan}${user}${c_gray}@${c_blue}${host}${c_reset}
 ${c_cyan}     /  \\       ${c_gray}-------------------------${c_reset}
 ${c_cyan}    / /\\ \\      ${c_magenta}OS:${c_reset}       abzOS 1.0 (Arch Linux)
 ${c_cyan}   / /__\\ \\     ${c_magenta}Kernel:${c_reset}   ${kernel}
 ${c_cyan}  / /____\\ \\    ${c_magenta}Desktop:${c_reset}  Deepin (DDE)
 ${c_cyan} / /      \\ \\   ${c_magenta}Terminal:${c_reset} Deepin Terminal
 ${c_cyan}/_/        \\_\\  ${c_magenta}Memory:${c_reset}   ${mem_info}
                 ${c_magenta}Packages:${c_reset} ${pkgs} (pacman)

 ${c_gray}●${c_reset} ${c_cyan}●${c_reset} ${c_blue}●${c_reset} ${c_magenta}●${c_reset} ${c_green}●${c_reset} ${c_yellow}●${c_reset} ${c_white}●${c_reset}
"
FETCH
RUN chmod +x /usr/local/bin/abzos-fetch

RUN cat << 'BASHRC' >> /etc/skel/.bashrc
PS1='\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '

alias ll='ls -alF --color=auto'
alias la='ls -A --color=auto'
alias l='ls -CF --color=auto'
alias grep='grep --color=auto'
alias ports='ss -tulpn'
alias myip='curl -s https://ifconfig.me/ip || hostname -I'
alias update='sudo pacman -Syu'

# Show the abzOS system banner on every new interactive shell
if [ -t 1 ] && command -v abzos-fetch >/dev/null 2>&1; then
    abzos-fetch
fi
BASHRC

RUN cp -f /etc/skel/.bashrc /root/.bashrc

# --- 10. Application Launchers (security-tool desktop entries) ---------------
RUN mkdir -p /usr/share/applications

RUN cat << 'APPDT' > /usr/share/applications/abzos-nmap.desktop
[Desktop Entry]
Name=Nmap Scanner
Comment=Network exploration and security auditing
Exec=deepin-terminal -e bash -c "nmap --help; echo; echo Press Enter to exit...; read"
Icon=network-wired-symbolic
Terminal=false
Type=Application
Categories=Network;Security;System;
APPDT

RUN cat << 'APPDT' > /usr/share/applications/abzos-sqlmap.desktop
[Desktop Entry]
Name=Sqlmap
Comment=Automatic SQL injection tool
Exec=deepin-terminal -e bash -c "sqlmap -h; echo; echo Press Enter to exit...; read"
Icon=network-server
Terminal=false
Type=Application
Categories=Network;Security;System;
APPDT

RUN cat << 'APPDT' > /usr/share/applications/abzos-john.desktop
[Desktop Entry]
Name=John the Ripper
Comment=Password hash cracker
Exec=deepin-terminal -e bash -c "john; echo; echo Press Enter to exit...; read"
Icon=dialog-password-symbolic
Terminal=false
Type=Application
Categories=Security;System;
APPDT

RUN cat << 'APPDT' > /usr/share/applications/abzos-hydra.desktop
[Desktop Entry]
Name=Hydra
Comment=Very fast network logon cracker
Exec=deepin-terminal -e bash -c "hydra -h; echo; echo Press Enter to exit...; read"
Icon=security-high
Terminal=false
Type=Application
Categories=Network;Security;System;
APPDT

RUN cat << 'APPDT' > /usr/share/applications/abzos-aircrack.desktop
[Desktop Entry]
Name=Aircrack-ng
Comment=Wireless network auditing
Exec=deepin-terminal -e bash -c "aircrack-ng --help; echo; echo Press Enter to exit...; read"
Icon=network-wireless-symbolic
Terminal=false
Type=Application
Categories=Network;Security;System;
APPDT

RUN cat << 'APPDT' > /usr/share/applications/abzos-binwalk.desktop
[Desktop Entry]
Name=Binwalk
Comment=Firmware analysis tool
Exec=deepin-terminal -e bash -c "binwalk --help; echo; echo Press Enter to exit...; read"
Icon=system-search
Terminal=false
Type=Application
Categories=Development;Security;System;
APPDT

RUN cat << 'APPDT' > /usr/share/applications/abzos-wireshark.desktop
[Desktop Entry]
Name=Wireshark / TShark
Comment=Network traffic packet capture and analysis
Exec=deepin-terminal -e bash -c "tshark --help; echo; echo Press Enter to exit...; read"
Icon=network-wired-symbolic
Terminal=false
Type=Application
Categories=Network;Security;System;
APPDT

# --- 11. mkinitcpio: bake the archiso live-boot hooks into the initramfs -----
RUN mkdir -p /etc/mkinitcpio.conf.d && \
    cat << 'ARCHISOCONF' > /etc/mkinitcpio.conf.d/archiso.conf
HOOKS=(base udev microcode modconf kms memdisk archiso archiso_loop_mnt block filesystems keyboard)
COMPRESSION="xz"
COMPRESSION_OPTIONS=(-9e)
ARCHISOCONF
RUN KVER=$(ls /usr/lib/modules | head -n1) && \
    mkinitcpio -c /etc/mkinitcpio.conf.d/archiso.conf -k "${KVER}" -g /boot/initramfs-linux.img

# --- 12. Finalize permissions and system targets ------------------------------
RUN cp -a /etc/skel/. /home/abzos/ && chown -R abzos:abzos /home/abzos

RUN ln -sf /usr/lib/systemd/system/graphical.target /etc/systemd/system/default.target && \
    ln -sf /usr/lib/systemd/system/ddm.service /etc/systemd/system/display-manager.service

RUN systemctl enable NetworkManager.service 2>/dev/null || true
RUN systemctl enable bluetooth.service 2>/dev/null || true

RUN chmod 1777 /tmp /var/tmp && \
    chmod 0640 /etc/shadow && \
    chmod 4755 /usr/bin/sudo /bin/su
