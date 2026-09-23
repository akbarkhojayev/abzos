FROM debian:bookworm-slim
ENV DEBIAN_FRONTEND=noninteractive

# Enable contrib/non-free/non-free-firmware and preseed wireshark's setuid prompt
RUN echo "wireshark-common wireshark-common/install-setuid boolean true" | debconf-set-selections && \
    (sed -i 's/Components: main/Components: main contrib non-free non-free-firmware/g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
     sed -i 's/main/main contrib non-free non-free-firmware/g' /etc/apt/sources.list)

# --- 1. Base system, kernel & init -------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    linux-image-amd64 \
    live-boot live-config live-config-systemd \
    systemd-sysv dbus-x11 dbus-user-session \
    sudo nano kbd ca-certificates \
    accountsservice policykit-1-gnome polkitd \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# --- 2. Hardware Firmware & Drivers (Complete hardware & VM support) ---------
RUN apt-get update && apt-get install -y --no-install-recommends \
    firmware-linux firmware-linux-free firmware-linux-nonfree firmware-misc-nonfree \
    firmware-iwlwifi firmware-realtek firmware-atheros firmware-brcm80211 firmware-sof-signed \
    intel-microcode amd64-microcode \
    xserver-xorg-core xserver-xorg-legacy \
    xserver-xorg-video-all xserver-xorg-video-qxl \
    xserver-xorg-video-intel xserver-xorg-video-amdgpu xserver-xorg-video-ati \
    xserver-xorg-video-nouveau xserver-xorg-video-vmware \
    xserver-xorg-video-fbdev xserver-xorg-video-vesa \
    libgl1-mesa-dri mesa-vulkan-drivers mesa-va-drivers \
    xserver-xorg-input-all xserver-xorg-input-libinput xserver-xorg-input-synaptics \
    xinit x11-xserver-utils xfonts-base \
    fonts-dejavu-core fonts-jetbrains-mono fonts-roboto \
    spice-vdagent qemu-guest-agent \
    open-vm-tools open-vm-tools-desktop \
    network-manager \
    wpasupplicant wireless-tools rfkill \
    bluez \
    pipewire pipewire-pulse wireplumber pavucontrol alsa-utils pulseaudio-utils \
    acpi acpid upower \
    dosfstools ntfs-3g exfatprogs e2fsprogs parted \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# --- 3. GNOME Desktop Environment, Installer & Daily Apps --------------------
# gnome-core is Debian's curated "complete but not bloated" GNOME meta-package:
# GDM, Shell, Mutter, Nautilus, Settings, Text Editor, Disks, Calculator,
# Evince, Eog, System Monitor, etc. It's installed WITH recommends (unlike the
# rest of this Dockerfile) because it's specifically designed around that
# mechanism to pull in a fully working desktop; the handful of recommended
# packages we don't want -- a second terminal, a second video player, and a
# legacy tray-icon network applet that GNOME Shell's own indicator replaces --
# are purged again immediately after.
RUN apt-get update && apt-get install -y gnome-core gnome-console && \
    (apt-get purge -y gnome-terminal network-manager-gnome totem || true) && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y --no-install-recommends \
    firefox-esr vlc mpv gparted file-roller gdebi xdg-user-dirs \
    calamares calamares-settings-debian \
    grub-efi-amd64-bin grub-pc-bin efibootmgr \
    ffmpeg gstreamer1.0-plugins-ugly gstreamer1.0-plugins-bad \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# --- 4. Developer & Cybersecurity Toolkit -------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc g++ make gdb \
    git curl wget jq tree htop python3 python3-pip \
    nmap net-tools iputils-ping traceroute whois \
    tcpdump socat netcat-traditional tshark \
    sqlmap john hydra aircrack-ng \
    binwalk hexedit strace ltrace \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# --- 5. System configuration & Dynamic Display Setup -------------------------
RUN mkdir -p /etc/X11 && \
    echo "allowed_users=anybody" > /etc/X11/Xwrapper.config && \
    echo "needs_root_rights=yes" >> /etc/X11/Xwrapper.config

RUN echo "LANG=C.UTF-8" > /etc/default/locale && \
    echo "LC_ALL=C.UTF-8" >> /etc/default/locale

# Dynamic screen resolution & spice-vdagent startup script
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
RUN groupadd -f netdev && \
    (id -u abzos >/dev/null 2>&1 || useradd -m -s /bin/bash -u 1000 -U abzos) && \
    echo "abzos:abzos" | chpasswd && \
    echo "root:toor" | chpasswd && \
    usermod -aG sudo,adm,audio,video,plugdev,cdrom,netdev abzos && \
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
PRETTY_NAME="abzOS 1.0 (Debian 12 Bookworm - GNOME Edition)"
ID=abzos
ID_LIKE=debian
VERSION_ID="1.0"
VERSION="1.0 (Bookworm)"
VERSION_CODENAME=bookworm
LOGO=abzos-logo
HOME_URL="https://github.com/akbarkhojayev"
SUPPORT_URL="https://github.com/akbarkhojayev"
BUG_REPORT_URL="https://github.com/akbarkhojayev"
OSREL

RUN cat << 'ISSUE' > /etc/issue
abzOS 1.0 (Debian 12 Bookworm - GNOME Edition) \n \l
ISSUE
RUN cp /etc/issue /etc/issue.net

# --- 7. Branding, Wallpaper & Icons -------------------------------------------
RUN mkdir -p /usr/share/backgrounds/abzos /usr/share/pixmaps /usr/share/icons

COPY scripts/wallpaper-t1.jpg /usr/share/backgrounds/abzos/wallpaper-t1.jpg
COPY scripts/abzos-logo.png /usr/share/pixmaps/abzos-logo.png
RUN chmod -R a+rX /usr/share/backgrounds/abzos /usr/share/pixmaps

# Install the "A" abzOS logo in all icon sizes (used by GNOME Settings' About
# panel via /etc/os-release's LOGO= key, and by the app grid/taskbar wherever
# an app or the distro references "abzos-logo" as an icon name).
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
    cp /usr/share/applications/abzos-installer.desktop /usr/share/applications/install-debian.desktop && \
    mkdir -p /etc/skel/Desktop && \
    cp /usr/share/applications/abzos-installer.desktop /etc/skel/Desktop/ && \
    chmod +x /etc/skel/Desktop/abzos-installer.desktop

# --- 8. GDM3 Configuration (Autologin straight into GNOME) -------------------
RUN mkdir -p /etc/gdm3 && \
    cat << 'GDMCONF' > /etc/gdm3/daemon.conf
[daemon]
AutomaticLoginEnable=true
AutomaticLogin=abzos
WaylandEnable=false

[security]

[xdmcp]

[chooser]

[debug]
GDMCONF

# GDM greeter background & logo -- the standard GNOME mechanism (a dedicated
# dconf profile/database for the "gdm" system user) rather than a config file,
# since gnome-shell's login screen reads its look from dconf like any other
# GNOME session.
RUN mkdir -p /etc/dconf/profile /etc/dconf/db/gdm.d && \
    cat << 'PROFILE' > /etc/dconf/profile/gdm
user-db:user
system-db:gdm
file-db:/usr/share/gdm/greeter-dconf-defaults
PROFILE
RUN cat << 'GDMDB' > /etc/dconf/db/gdm.d/00-abzos
[org/gnome/desktop/background]
picture-uri='file:///usr/share/backgrounds/abzos/wallpaper-t1.jpg'
picture-uri-dark='file:///usr/share/backgrounds/abzos/wallpaper-t1.jpg'
picture-options='zoom'

[org/gnome/login-screen]
logo='/usr/share/pixmaps/abzos-logo.png'
GDMDB

# --- 9. System-wide GNOME defaults (wallpaper, dark style, fonts, favorites) -
# Stock GNOME Shell + Adwaita's built-in dark variant -- no custom GTK theme,
# icon theme, or shell theme package needed. This is the single source of
# truth for look-and-feel defaults (every user gets these on first login, but
# remains completely free to change them afterwards -- nothing here is locked).
RUN mkdir -p /etc/dconf/profile /etc/dconf/db/local.d && \
    cat << 'PROFILE' > /etc/dconf/profile/user
user-db:user
system-db:local
PROFILE
RUN cat << 'DCONF' > /etc/dconf/db/local.d/00-abzos
[org/gnome/desktop/background]
picture-uri='file:///usr/share/backgrounds/abzos/wallpaper-t1.jpg'
picture-uri-dark='file:///usr/share/backgrounds/abzos/wallpaper-t1.jpg'
picture-options='zoom'

[org/gnome/desktop/screensaver]
picture-uri='file:///usr/share/backgrounds/abzos/wallpaper-t1.jpg'
picture-options='zoom'

[org/gnome/desktop/interface]
color-scheme='prefer-dark'
font-name='Roboto 10'
document-font-name='Roboto 10'
monospace-font-name='JetBrains Mono 10'

[org/gnome/shell]
favorite-apps=['org.gnome.Nautilus.desktop', 'org.gnome.Console.desktop', 'firefox-esr.desktop', 'org.gnome.TextEditor.desktop', 'abzos-installer.desktop']
DCONF
RUN dconf update

# --- 10. Modern Terminal Fetch & Shell Styling --------------------------------
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
uptime_str="$(uptime -p 2>/dev/null | sed 's/up //' || echo 'just now')"
shell_name="$(basename "$SHELL")"
mem_info="$(free -h 2>/dev/null | awk '/^Mem:/ {print $3 "/" $2}')"
pkgs="$(dpkg-query -f '.\n' -W 2>/dev/null | wc -l)"

echo -e "
 ${c_cyan}      /\\        ${c_cyan}${user}${c_gray}@${c_blue}${host}${c_reset}
 ${c_cyan}     /  \\       ${c_gray}-------------------------${c_reset}
 ${c_cyan}    / /\\ \\      ${c_magenta}OS:${c_reset}       abzOS 1.0 (Debian 12 Bookworm)
 ${c_cyan}   / /__\\ \\     ${c_magenta}Kernel:${c_reset}   ${kernel}
 ${c_cyan}  / /____\\ \\    ${c_magenta}Desktop:${c_reset}  GNOME 43
 ${c_cyan} / /      \\ \\   ${c_magenta}Terminal:${c_reset} GNOME Console
 ${c_cyan}/_/        \\_\\  ${c_magenta}Memory:${c_reset}   ${mem_info}
                 ${c_magenta}Packages:${c_reset} ${pkgs} (dpkg)

 ${c_gray}●${c_reset} ${c_cyan}●${c_reset} ${c_blue}●${c_reset} ${c_magenta}●${c_reset} ${c_green}●${c_reset} ${c_yellow}●${c_reset} ${c_white}●${c_reset}
"
FETCH
RUN chmod +x /usr/local/bin/abzos-fetch

# Configure GNOME Console default night/dark theme
RUN cat << 'GCONF' > /usr/share/glib-2.0/schemas/99_abzos_console.gschema.override
[org.gnome.Console]
theme='night'
font-scale=1.0
GCONF
RUN glib-compile-schemas /usr/share/glib-2.0/schemas/ 2>/dev/null || true

RUN cat << 'BASHRC' >> /etc/skel/.bashrc
case "$TERM" in
    xterm*|rxvt*|kgx*)
        PS1='\[\e]0;\u@\h: \w\a\]\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '
        ;;
    *)
        PS1='\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '
        ;;
esac

alias ll='ls -alF --color=auto'
alias la='ls -A --color=auto'
alias l='ls -CF --color=auto'
alias grep='grep --color=auto'
alias ports='netstat -tulpn'
alias myip='curl -s https://ifconfig.me/ip || hostname -I'
alias update='sudo apt update && sudo apt upgrade -y'

# Show the abzOS system banner on every new interactive shell
if [ -t 1 ] && command -v abzos-fetch >/dev/null 2>&1; then
    abzos-fetch
fi
BASHRC

RUN cp -f /etc/skel/.bashrc /root/.bashrc

# Set GNOME Console as the primary default terminal
RUN update-alternatives --set x-terminal-emulator /usr/bin/kgx 2>/dev/null || true

# --- 11. Application Launchers (security-tool desktop entries) ---------------
# GNOME Shell's own Activities overview replaces the need for a taskbar/panel
# launcher list -- these desktop files just need to exist under
# /usr/share/applications so they show up in the app grid and search.
RUN mkdir -p /usr/share/applications

RUN cat << 'APPDT' > /usr/share/applications/abzos-nmap.desktop
[Desktop Entry]
Name=Nmap Scanner
Comment=Network exploration and security auditing
Exec=kgx -T "Nmap Scanner" -e "bash -c 'nmap --help; echo; echo Press Enter to exit...; read'"
Icon=network-wired-symbolic
Terminal=false
Type=Application
Categories=Network;Security;System;
APPDT

RUN cat << 'APPDT' > /usr/share/applications/abzos-sqlmap.desktop
[Desktop Entry]
Name=Sqlmap
Comment=Automatic SQL injection tool
Exec=kgx -T "Sqlmap" -e "bash -c 'sqlmap -h; echo; echo Press Enter to exit...; read'"
Icon=network-server
Terminal=false
Type=Application
Categories=Network;Security;System;
APPDT

RUN cat << 'APPDT' > /usr/share/applications/abzos-john.desktop
[Desktop Entry]
Name=John the Ripper
Comment=Password hash cracker
Exec=kgx -T "John the Ripper" -e "bash -c 'john; echo; echo Press Enter to exit...; read'"
Icon=dialog-password-symbolic
Terminal=false
Type=Application
Categories=Security;System;
APPDT

RUN cat << 'APPDT' > /usr/share/applications/abzos-hydra.desktop
[Desktop Entry]
Name=Hydra
Comment=Very fast network logon cracker
Exec=kgx -T "Hydra" -e "bash -c 'hydra -h; echo; echo Press Enter to exit...; read'"
Icon=security-high
Terminal=false
Type=Application
Categories=Network;Security;System;
APPDT

RUN cat << 'APPDT' > /usr/share/applications/abzos-aircrack.desktop
[Desktop Entry]
Name=Aircrack-ng
Comment=Wireless network auditing
Exec=kgx -T "Aircrack-ng" -e "bash -c 'aircrack-ng --help; echo; echo Press Enter to exit...; read'"
Icon=network-wireless-symbolic
Terminal=false
Type=Application
Categories=Network;Security;System;
APPDT

RUN cat << 'APPDT' > /usr/share/applications/abzos-binwalk.desktop
[Desktop Entry]
Name=Binwalk
Comment=Firmware analysis tool
Exec=kgx -T "Binwalk" -e "bash -c 'binwalk --help; echo; echo Press Enter to exit...; read'"
Icon=system-search
Terminal=false
Type=Application
Categories=Development;Security;System;
APPDT

RUN cat << 'APPDT' > /usr/share/applications/abzos-wireshark.desktop
[Desktop Entry]
Name=Wireshark / TShark
Comment=Network traffic packet capture and analysis
Exec=kgx -T "TShark Packet Capture" -e "bash -c 'tshark --help; echo; echo Press Enter to exit...; read'"
Icon=network-wired-symbolic
Terminal=false
Type=Application
Categories=Network;Security;System;
APPDT

# --- 12. Finalize permissions and system targets ------------------------------
RUN cp -a /etc/skel/. /home/abzos/ && chown -R abzos:abzos /home/abzos

RUN ln -sf /lib/systemd/system/graphical.target /etc/systemd/system/default.target && \
    ln -sf /lib/systemd/system/gdm3.service /etc/systemd/system/display-manager.service

# Enable NetworkManager & spice-vdagent in systemd
RUN systemctl enable NetworkManager.service 2>/dev/null || true
RUN systemctl enable spice-vdagentd.service 2>/dev/null || true

RUN chmod 1777 /tmp /var/tmp && \
    chmod 0640 /etc/shadow && \
    chmod 4755 /usr/bin/sudo /bin/su
