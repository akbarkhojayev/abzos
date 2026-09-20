FROM debian:bookworm-slim
ENV DEBIAN_FRONTEND=noninteractive

# Enable contrib/non-free (firmware) and preseed wireshark's setuid prompt
RUN echo "wireshark-common wireshark-common/install-setuid boolean true" | debconf-set-selections && \
    (sed -i 's/Components: main/Components: main contrib non-free non-free-firmware/g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
     sed -i 's/main/main contrib non-free non-free-firmware/g' /etc/apt/sources.list)

# --- Base system: kernel, live-boot, init, display stack -------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    linux-image-amd64 \
    live-boot live-config live-config-systemd \
    systemd-sysv dbus-x11 dbus-user-session \
    xserver-xorg-core xserver-xorg-legacy xserver-xorg-video-all \
    xserver-xorg-video-vmware \
    xinit x11-xserver-utils xfonts-base fonts-dejavu-core \
    accountsservice policykit-1-gnome polkitd \
    lightdm lightdm-gtk-greeter \
    sudo nano kbd ca-certificates \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# --- Sway / Wayland desktop -------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    sway waybar wofi swaybg swaylock mako-notifier xwayland \
    adwaita-icon-theme desktop-base fonts-font-awesome \
    brightnessctl pulseaudio pulseaudio-utils pavucontrol \
    xfce4-terminal thunar \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# --- Developer & cybersecurity toolset ---------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc g++ make gdb \
    git curl wget jq tree htop python3 python3-pip \
    nmap net-tools iputils-ping traceroute whois \
    tcpdump socat netcat-traditional tshark \
    sqlmap john hydra aircrack-ng \
    binwalk hexedit strace ltrace \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Xwrapper: allow X to be started by lightdm/startx without a setuid root binary
RUN mkdir -p /etc/X11 && \
    echo "allowed_users=anybody" > /etc/X11/Xwrapper.config && \
    echo "needs_root_rights=yes" >> /etc/X11/Xwrapper.config

# Graphics config tuned for QEMU/VM display adapters
RUN mkdir -p /etc/X11/xorg.conf.d && \
    cat << 'XCONF' > /etc/X11/xorg.conf.d/10-vm-graphics.conf
Section "ServerFlags"
    Option "DontVTSwitch" "off"
    Option "AIGLX" "off"
EndSection

Section "Device"
    Identifier "Modeset0"
    Driver "modesetting"
    Option "AccelMethod" "none"
    Option "ShadowFB" "true"
EndSection

Section "Extensions"
    Option "GLX" "Disable"
EndSection
XCONF

RUN echo "LANG=C.UTF-8" > /etc/default/locale && \
    echo "LC_ALL=C.UTF-8" >> /etc/default/locale

# Wayland/Sway environment tuned for software rendering in a VM
RUN echo "NO_AT_SPI=1" >> /etc/environment && \
    echo "GTK_A11Y=none" >> /etc/environment && \
    echo "WLR_NO_HARDWARE_CURSORS=1" >> /etc/environment && \
    echo "WLR_RENDERER_ALLOW_SOFTWARE=1" >> /etc/environment && \
    echo "WLR_RENDERER=pixman" >> /etc/environment && \
    echo "XDG_CURRENT_DESKTOP=sway" >> /etc/environment && \
    echo "MOZ_ENABLE_WAYLAND=1" >> /etc/environment && \
    mkdir -p /etc/xdg/autostart && \
    printf '[Desktop Entry]\nType=Application\nName=AT-SPI\nHidden=true\n' > /etc/xdg/autostart/at-spi-dbus-bus.desktop

# --- User & identity ---------------------------------------------------------
RUN groupadd -f autologin && \
    groupadd -f netdev && \
    (id -u abzos >/dev/null 2>&1 || useradd -m -s /bin/bash -u 1000 -U abzos) && \
    echo "abzos:abzos" | chpasswd && \
    echo "root:toor" | chpasswd && \
    usermod -aG sudo,adm,audio,video,plugdev,cdrom,netdev,autologin abzos && \
    mkdir -p /etc/sudoers.d && \
    echo "abzos ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/abzos && \
    chmod 0440 /etc/sudoers.d/abzos

# Serial console root autologin, for headless debugging
RUN mkdir -p /etc/systemd/system/serial-getty@ttyS0.service.d && \
    cat << 'AUTOLOGIN' > /etc/systemd/system/serial-getty@ttyS0.service.d/autologin.conf
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin root --noclear %I 115200 $TERM
AUTOLOGIN

RUN echo "abzos" > /etc/hostname

RUN cat << 'OSREL' > /etc/os-release
NAME="abzOS"
PRETTY_NAME="abzOS 1.0 (Debian 12 Bookworm)"
ID=abzos
ID_LIKE=debian
VERSION_ID="1.0"
VERSION="1.0 (Bookworm)"
VERSION_CODENAME=bookworm
HOME_URL="https://github.com/akbarkhojayev"
SUPPORT_URL="https://github.com/akbarkhojayev"
BUG_REPORT_URL="https://github.com/akbarkhojayev"
OSREL
RUN cat << 'ISSUE' > /etc/issue
abzOS 1.0 (Debian 12 Bookworm) \n \l
ISSUE
RUN cp /etc/issue /etc/issue.net

# --- Branding -----------------------------------------------------------------
RUN mkdir -p /usr/share/backgrounds/abzos /usr/share/pixmaps
COPY scripts/abzos-dark.png /usr/share/backgrounds/abzos/abzos-dark.png
COPY scripts/abzos-logo.png /usr/share/pixmaps/abzos-logo.png

RUN mkdir -p /etc/alternatives /usr/share/images/desktop-base && \
    ln -sf /usr/share/backgrounds/abzos/abzos-dark.png /etc/alternatives/desktop-background && \
    ln -sf /usr/share/backgrounds/abzos/abzos-dark.png /usr/share/images/desktop-base/desktop-background && \
    ln -sf /usr/share/backgrounds/abzos/abzos-dark.png /usr/share/images/desktop-base/default

# --- LightDM: autologin straight into the Sway session -----------------------
RUN mkdir -p /etc/lightdm && \
    cat << 'LIGHTDM' > /etc/lightdm/lightdm.conf
[Seat:*]
autologin-user=abzos
autologin-user-timeout=0
autologin-session=sway
user-session=sway
greeter-session=lightdm-gtk-greeter
pam-autologin-service=lightdm-autologin
xserver-command=X -core
display-setup-script=/usr/bin/chvt 7
session-setup-script=/usr/bin/chvt 7
LIGHTDM

RUN cat << 'GREETER' > /etc/lightdm/lightdm-gtk-greeter.conf
[greeter]
background = /usr/share/backgrounds/abzos/abzos-dark.png
theme-name = Adwaita
icon-theme-name = Adwaita
font-name = Sans 11
position = 50%,center 50%,center
default-user-image = /usr/share/pixmaps/abzos-logo.png
GREETER

RUN mkdir -p /var/lib/lightdm/data /var/log/lightdm /var/cache/lightdm && \
    chown -R lightdm:lightdm /var/lib/lightdm /var/log/lightdm /var/cache/lightdm && \
    chmod 755 /var/lib/lightdm /var/lib/lightdm/data && \
    chmod 750 /var/log/lightdm

# Session launcher: sets up XDG_RUNTIME_DIR and Wayland env before exec'ing sway
RUN cat << 'SESS' > /usr/local/bin/abzos-session
#!/bin/bash
if [ -z "$XDG_RUNTIME_DIR" ]; then
    export XDG_RUNTIME_DIR="/run/user/$(id -u)"
    if [ ! -d "$XDG_RUNTIME_DIR" ]; then
        export XDG_RUNTIME_DIR="/tmp/runtime-$(id -u)"
    fi
fi
mkdir -p "$XDG_RUNTIME_DIR"
chmod 0700 "$XDG_RUNTIME_DIR"

export WLR_NO_HARDWARE_CURSORS=1
export WLR_RENDERER_ALLOW_SOFTWARE=1
export WLR_RENDERER=pixman
export XDG_CURRENT_DESKTOP=sway
export XDG_SESSION_TYPE=wayland
export MOZ_ENABLE_WAYLAND=1

if [ -n "$DISPLAY" ]; then
    export WLR_BACKENDS=x11
fi

exec sway "$@"
SESS
RUN chmod +x /usr/local/bin/abzos-session

RUN mkdir -p /usr/share/xsessions && rm -rf /usr/share/wayland-sessions
RUN cat << 'DESKENTRY' > /usr/share/xsessions/sway.desktop
[Desktop Entry]
Name=abzOS Desktop
Comment=Dynamic Tiling Desktop
Exec=/usr/local/bin/abzos-session
Type=Application
DesktopNames=sway
DESKENTRY
RUN echo "exec /usr/local/bin/abzos-session" > /etc/skel/.xsession && \
    echo "exec /usr/local/bin/abzos-session" > /etc/skel/.xinitrc && \
    chmod +x /etc/skel/.xsession /etc/skel/.xinitrc

# =============================================================================
# Sway configuration
# =============================================================================
RUN mkdir -p /etc/sway /etc/skel/.config/sway
RUN cat << 'SWAYCONF' > /etc/sway/config
set $mod Mod4

set $left h
set $down j
set $up k
set $right l

set $term xfce4-terminal
set $menu wofi --show drun --prompt "Search abzOS..."

output * bg /usr/share/backgrounds/abzos/abzos-dark.png fill

gaps inner 8
gaps outer 6
default_border pixel 2
default_floating_border pixel 2

client.focused          #00f0ff #11121d #ffffff #00f0ff #00f0ff
client.focused_inactive #282c34 #11121d #abb2bf #282c34 #282c34
client.unfocused        #181a1f #11121d #7f848e #181a1f #181a1f
client.urgent           #ff0055 #11121d #ffffff #ff0055 #ff0055

font pango:DejaVu Sans Mono 10

bindsym $mod+Return exec $term
bindsym $mod+d exec $menu
bindsym $mod+space exec $menu
bindsym $mod+q kill
bindsym $mod+e exec thunar
bindsym $mod+f fullscreen toggle
bindsym $mod+Shift+space floating toggle

bindsym $mod+$left focus left
bindsym $mod+$down focus down
bindsym $mod+$up focus up
bindsym $mod+$right focus right
bindsym $mod+Left focus left
bindsym $mod+Down focus down
bindsym $mod+Up focus up
bindsym $mod+Right focus right

bindsym $mod+Shift+$left move left
bindsym $mod+Shift+$down move down
bindsym $mod+Shift+$up move up
bindsym $mod+Shift+$right move right
bindsym $mod+Shift+Left move left
bindsym $mod+Shift+Down move down
bindsym $mod+Shift+Up move up
bindsym $mod+Shift+Right move right

bindsym $mod+b splith
bindsym $mod+v splitv

bindsym $mod+1 workspace number 1
bindsym $mod+2 workspace number 2
bindsym $mod+3 workspace number 3
bindsym $mod+4 workspace number 4
bindsym $mod+5 workspace number 5
bindsym $mod+6 workspace number 6
bindsym $mod+7 workspace number 7
bindsym $mod+8 workspace number 8
bindsym $mod+9 workspace number 9

bindsym $mod+Shift+1 move container to workspace number 1
bindsym $mod+Shift+2 move container to workspace number 2
bindsym $mod+Shift+3 move container to workspace number 3
bindsym $mod+Shift+4 move container to workspace number 4
bindsym $mod+Shift+5 move container to workspace number 5
bindsym $mod+Shift+6 move container to workspace number 6
bindsym $mod+Shift+7 move container to workspace number 7
bindsym $mod+Shift+8 move container to workspace number 8
bindsym $mod+Shift+9 move container to workspace number 9

bindsym $mod+s layout stacking
bindsym $mod+w layout tabbed
bindsym $mod+t layout toggle split

bindsym $mod+Shift+c reload
bindsym $mod+Shift+e exec swaynag -t warning -m 'Exit abzOS Session?' -B 'Yes, exit' 'swaymsg exit'

bindsym XF86AudioRaiseVolume exec pactl set-sink-volume @DEFAULT_SINK@ +5%
bindsym XF86AudioLowerVolume exec pactl set-sink-volume @DEFAULT_SINK@ -5%
bindsym XF86AudioMute exec pactl set-sink-mute @DEFAULT_SINK@ toggle

bar {
    swaybar_command waybar
}

exec_always swaybg -i /usr/share/backgrounds/abzos/abzos-dark.png -m fill
exec mako
SWAYCONF
RUN cp /etc/sway/config /etc/skel/.config/sway/config

# =============================================================================
# Waybar: top status bar
# =============================================================================
RUN mkdir -p /etc/xdg/waybar /etc/skel/.config/waybar
RUN cat << 'WAYBARCONF' > /etc/xdg/waybar/config
{
    "layer": "top",
    "position": "top",
    "height": 34,
    "margin-top": 6,
    "margin-left": 10,
    "margin-right": 10,
    "modules-left": ["custom/logo", "sway/workspaces", "sway/mode"],
    "modules-center": ["sway/window"],
    "modules-right": ["cpu", "memory", "network", "pulseaudio", "clock", "custom/power"],
    "custom/logo": {
        "format": "abzOS",
        "tooltip": false,
        "on-click": "wofi --show drun"
    },
    "sway/workspaces": {
        "disable-scroll": true,
        "all-outputs": true,
        "format": "{name}"
    },
    "sway/window": {
        "format": "{}",
        "max-length": 45
    },
    "cpu": {
        "format": " {usage}%",
        "interval": 2
    },
    "memory": {
        "format": " {}%",
        "interval": 2
    },
    "network": {
        "format-wifi": " {essid}",
        "format-ethernet": "{ipaddr}",
        "format-disconnected": "No network"
    },
    "pulseaudio": {
        "format": " {volume}%",
        "format-muted": " Mute",
        "on-click": "pavucontrol"
    },
    "clock": {
        "format": " {:%H:%M - %Y-%m-%d}",
        "tooltip-format": "<tt><small>{calendar}</small></tt>"
    },
    "custom/power": {
        "format": "",
        "tooltip": false,
        "on-click": "swaymsg exit"
    }
}
WAYBARCONF

RUN cat << 'WAYBARCSS' > /etc/xdg/waybar/style.css
* {
    border: none;
    border-radius: 0;
    font-family: "Font Awesome 6 Free", "DejaVu Sans Mono", monospace;
    font-size: 13px;
    min-height: 0;
}

window#waybar {
    background: transparent;
}

#custom-logo,
#workspaces,
#window,
#cpu,
#memory,
#network,
#pulseaudio,
#clock,
#custom-power {
    background: rgba(17, 18, 29, 0.85);
    color: #e0e6ed;
    border-radius: 10px;
    border: 1px solid rgba(0, 240, 255, 0.35);
    padding: 2px 10px;
    margin: 0 3px;
}

#custom-logo {
    color: #00f0ff;
    font-weight: bold;
    border-color: #00f0ff;
}

#workspaces button {
    padding: 0 5px;
    color: #8892b0;
    border-radius: 6px;
}

#workspaces button.focused {
    color: #00f0ff;
    background: rgba(0, 240, 255, 0.2);
    font-weight: bold;
}

#cpu { color: #ff79c6; }
#memory { color: #bd93f9; }
#network { color: #50fa7b; }
#pulseaudio { color: #f1fa8c; }
#clock { color: #00f0ff; font-weight: bold; }
#custom-power { color: #ff5555; font-weight: bold; }
WAYBARCSS

RUN cp /etc/xdg/waybar/config /etc/skel/.config/waybar/config && \
    cp /etc/xdg/waybar/style.css /etc/skel/.config/waybar/style.css

# =============================================================================
# Wofi: application launcher
# =============================================================================
RUN mkdir -p /etc/wofi /etc/skel/.config/wofi
RUN cat << 'WOFICONF' > /etc/wofi/config
width=500
height=380
location=center
show=drun
prompt=Search abzOS Apps & Tools...
filter_rate=100
allow_markup=true
no_actions=true
halign=fill
orientation=vertical
content_halign=fill
insensitive=true
allow_images=true
image_size=28
WOFICONF

RUN cat << 'WOFICSS' > /etc/wofi/style.css
window {
    margin: 0px;
    background-color: rgba(17, 18, 29, 0.95);
    border: 2px solid #00f0ff;
    border-radius: 12px;
    font-family: "DejaVu Sans Mono", monospace;
    font-size: 14px;
}

#input {
    margin: 10px;
    border-radius: 8px;
    border: 1px solid #00f0ff;
    background-color: #1a1c2b;
    color: #ffffff;
    padding: 8px;
}

#inner-box { margin: 5px; background-color: transparent; }
#outer-box { margin: 0px; background-color: transparent; }

#entry {
    padding: 6px 10px;
    margin: 2px 5px;
    border-radius: 6px;
    color: #e0e6ed;
}

#entry:selected {
    background-color: rgba(0, 240, 255, 0.25);
    color: #00f0ff;
    font-weight: bold;
}

#text { margin: 2px; }
WOFICSS

RUN cp /etc/wofi/config /etc/skel/.config/wofi/config && \
    cp /etc/wofi/style.css /etc/skel/.config/wofi/style.css

# =============================================================================
# Mako: notifications
# =============================================================================
RUN mkdir -p /etc/mako /etc/skel/.config/mako
RUN cat << 'MAKOCONF' > /etc/mako/config
background-color=#11121dF0
text-color=#ffffff
border-color=#00f0ff
border-size=2
border-radius=10
default-timeout=5000
font=DejaVu Sans Mono 11
padding=12
margin=10
MAKOCONF
RUN cp /etc/mako/config /etc/skel/.config/mako/config

# --- Shell branding -----------------------------------------------------------
RUN cat << 'BANNER' > /etc/abzos_banner.txt
\033[01;36m
        _           ____   _____
       | |         / __ \ / ____|
  __ _ | |__  ____| |  | | (___
 / _` || '_ \|_  /| |  | |\___ \
| (_| || |_) |/ / | |__| |____) |
 \__,_||_.__//___|\____/|_____/
\033[01;35m  [ abzOS 1.0 - Developer & Cybersecurity Edition ]\033[00m
BANNER

RUN cat << 'BASHRC' >> /etc/skel/.bashrc
if [ -f /etc/abzos_banner.txt ] && [ -t 1 ]; then
    echo -e "$(cat /etc/abzos_banner.txt)"
fi
alias ll='ls -lah --color=auto'
alias la='ls -A --color=auto'
alias l='ls -CF --color=auto'
alias grep='grep --color=auto'
alias ports='netstat -tulpn'
alias myip='curl -s https://ifconfig.me/ip || hostname -I'
alias update='sudo apt update && sudo apt upgrade -y'
PS1="\[\033[01;36m\]┌──(\[\033[01;32m\]\u㉿\h\[\033[01;36m\])-[\[\033[01;37m\]\w\[\033[01;36m\]]\n\[\033[01;36m\]└─\[\033[01;32m\]\$\[\033[00m\] "
BASHRC

# --- Application launchers for the bundled security tools --------------------
RUN mkdir -p /usr/share/applications

RUN cat << 'APPDT' > /usr/share/applications/abzos-terminal.desktop
[Desktop Entry]
Name=abzOS Terminal
Comment=abzOS Developer & Security Terminal
Exec=xfce4-terminal
Icon=utilities-terminal
Terminal=false
Type=Application
Categories=System;TerminalEmulator;
APPDT

RUN cat << 'APPDT' > /usr/share/applications/abzos-files.desktop
[Desktop Entry]
Name=File Manager
Comment=Browse files and filesystem
Exec=thunar
Icon=system-file-manager
Terminal=false
Type=Application
Categories=System;Utility;
APPDT

RUN cat << 'APPDT' > /usr/share/applications/abzos-nmap.desktop
[Desktop Entry]
Name=Nmap Scanner
Comment=Network exploration and security auditing
Exec=xfce4-terminal -T "Nmap Scanner" -e "bash -c 'nmap --help; echo; echo Press Enter to exit...; read'"
Icon=network-wired
Terminal=false
Type=Application
Categories=Network;Security;System;
APPDT

RUN cat << 'APPDT' > /usr/share/applications/abzos-sqlmap.desktop
[Desktop Entry]
Name=Sqlmap
Comment=Automatic SQL injection tool
Exec=xfce4-terminal -T "Sqlmap" -e "bash -c 'sqlmap -h; echo; echo Press Enter to exit...; read'"
Icon=server-database
Terminal=false
Type=Application
Categories=Network;Security;System;
APPDT

RUN cat << 'APPDT' > /usr/share/applications/abzos-john.desktop
[Desktop Entry]
Name=John the Ripper
Comment=Password hash cracker
Exec=xfce4-terminal -T "John the Ripper" -e "bash -c 'john; echo; echo Press Enter to exit...; read'"
Icon=dialog-password
Terminal=false
Type=Application
Categories=Security;System;
APPDT

RUN cat << 'APPDT' > /usr/share/applications/abzos-hydra.desktop
[Desktop Entry]
Name=Hydra
Comment=Very fast network logon cracker
Exec=xfce4-terminal -T "Hydra" -e "bash -c 'hydra -h; echo; echo Press Enter to exit...; read'"
Icon=security-high
Terminal=false
Type=Application
Categories=Network;Security;System;
APPDT

RUN cat << 'APPDT' > /usr/share/applications/abzos-aircrack.desktop
[Desktop Entry]
Name=Aircrack-ng
Comment=Wireless network auditing
Exec=xfce4-terminal -T "Aircrack-ng" -e "bash -c 'aircrack-ng --help; echo; echo Press Enter to exit...; read'"
Icon=network-wireless
Terminal=false
Type=Application
Categories=Network;Security;System;
APPDT

RUN cat << 'APPDT' > /usr/share/applications/abzos-binwalk.desktop
[Desktop Entry]
Name=Binwalk
Comment=Firmware analysis tool
Exec=xfce4-terminal -T "Binwalk" -e "bash -c 'binwalk --help; echo; echo Press Enter to exit...; read'"
Icon=system-search
Terminal=false
Type=Application
Categories=Development;Security;System;
APPDT

# --- Finalize ------------------------------------------------------------------
RUN cp -a /etc/skel/. /home/abzos/ && chown -R abzos:abzos /home/abzos

RUN ln -sf /lib/systemd/system/graphical.target /etc/systemd/system/default.target && \
    ln -sf /lib/systemd/system/lightdm.service /etc/systemd/system/display-manager.service

RUN chmod 1777 /tmp /var/tmp && \
    chmod 0640 /etc/shadow && \
    chmod 4755 /usr/bin/sudo /bin/su
