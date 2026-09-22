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
    fonts-dejavu-core fonts-font-awesome fonts-jetbrains-mono fonts-roboto \
    spice-vdagent qemu-guest-agent \
    open-vm-tools open-vm-tools-desktop \
    network-manager network-manager-gnome \
    wpasupplicant wireless-tools rfkill \
    bluez blueman \
    pipewire pipewire-pulse wireplumber pavucontrol alsa-utils pulseaudio-utils \
    acpi acpid upower \
    dosfstools ntfs-3g exfatprogs e2fsprogs parted \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# --- 3. XFCE4 Desktop Environment, Utilities, Installer & Daily Apps ---------
RUN apt-get update && apt-get install -y --no-install-recommends \
    xfce4-session xfwm4 xfce4-panel xfdesktop4 thunar xfce4-terminal kitty \
    xfce4-whiskermenu-plugin xfce4-settings xfce4-pulseaudio-plugin \
    xfce4-power-manager xfce4-notifyd xfce4-screenshooter xfce4-taskmanager xfce4-appfinder \
    thunar-volman thunar-archive-plugin gvfs gvfs-backends file-roller \
    mousepad tumbler \
    firefox-esr \
    vlc mpv ristretto atril galculator gdebi xdg-user-dirs \
    calamares calamares-settings-debian \
    grub-efi-amd64-bin grub-pc-bin efibootmgr gparted \
    ffmpeg gstreamer1.0-plugins-ugly gstreamer1.0-plugins-bad \
    conky-all picom tilda cava gnome-console \
    lightdm lightdm-gtk-greeter light-locker \
    xfce4-genmon-plugin \
    python3-gi gir1.2-gtk-3.0 gir1.2-glib-2.0 python3-dbus \
    brightnessctl redshift \
    adwaita-icon-theme yaru-theme-icon desktop-base \
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
RUN groupadd -f autologin && \
    groupadd -f netdev && \
    (id -u abzos >/dev/null 2>&1 || useradd -m -s /bin/bash -u 1000 -U abzos) && \
    echo "abzos:abzos" | chpasswd && \
    echo "root:toor" | chpasswd && \
    usermod -aG sudo,adm,audio,video,plugdev,cdrom,netdev,autologin abzos && \
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
PRETTY_NAME="abzOS 1.0 (Debian 12 Bookworm - XFCE Edition)"
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
abzOS 1.0 (Debian 12 Bookworm - XFCE Edition) \n \l
ISSUE
RUN cp /etc/issue /etc/issue.net

# --- 7. Branding, Wallpapers, Themes & Icons ---------------------------------
RUN mkdir -p /usr/share/backgrounds/abzos /usr/share/backgrounds/xfce /usr/share/pixmaps \
             /usr/share/themes /usr/share/icons

COPY scripts/wallpaper-t1.jpg /usr/share/backgrounds/abzos/wallpaper-t1.jpg
COPY scripts/abzos-logo.png /usr/share/pixmaps/abzos-logo.png
COPY scripts/assets/icons-custom/abzos-controlcenter.png /usr/share/pixmaps/abzos-controlcenter.png
COPY scripts/assets/icons-custom/abzos-notifications.png /usr/share/pixmaps/abzos-notifications.png

# Set global default system wallpapers to wallpaper-t1.jpg
RUN cp /usr/share/backgrounds/abzos/wallpaper-t1.jpg /usr/share/backgrounds/xfce/xfce-blue.jpg && \
    cp /usr/share/backgrounds/abzos/wallpaper-t1.jpg /usr/share/backgrounds/xfce/xfce-teal.jpg && \
    cp /usr/share/backgrounds/abzos/wallpaper-t1.jpg /usr/share/backgrounds/xfce/xfce-verticals.png && \
    cp /usr/share/backgrounds/abzos/wallpaper-t1.jpg /usr/share/backgrounds/xfce/xfce-stripes.png

RUN mkdir -p /etc/alternatives /usr/share/images/desktop-base && \
    ln -sf /usr/share/backgrounds/abzos/wallpaper-t1.jpg /etc/alternatives/desktop-background && \
    ln -sf /usr/share/backgrounds/abzos/wallpaper-t1.jpg /usr/share/images/desktop-base/desktop-background && \
    ln -sf /usr/share/backgrounds/abzos/wallpaper-t1.jpg /usr/share/images/desktop-base/default

# Copy Ant-Dracula and Ant-Nebula themes and Tela-circle icons
COPY scripts/assets/themes/ /usr/share/themes/
COPY scripts/assets/icons/ /usr/share/icons/

# Install the new stylized "A" abzOS logo in all icon sizes
COPY scripts/abzos-logo-*.png /usr/share/icons/
RUN for sz in 16 24 32 48 64 128 256 512; do \
        if [ -f "/usr/share/icons/abzos-logo-$sz.png" ]; then \
            mkdir -p /usr/share/icons/hicolor/${sz}x${sz}/apps; \
            mv "/usr/share/icons/abzos-logo-$sz.png" /usr/share/icons/hicolor/${sz}x${sz}/apps/abzos-logo.png; \
        fi; \
    done && \
    cp /usr/share/pixmaps/abzos-logo.png /usr/share/icons/hicolor/scalable/apps/abzos-logo.png 2>/dev/null || true && \
    cp /usr/share/pixmaps/abzos-logo.png /usr/share/icons/Tela-circle/scalable/apps/abzos-logo.png 2>/dev/null || true && \
    cp /usr/share/pixmaps/abzos-logo.png /usr/share/icons/Tela-circle/scalable/apps/distributor-logo-debian.png 2>/dev/null || true && \
    cp /usr/share/pixmaps/abzos-logo.png /usr/share/icons/Tela-circle/scalable/apps/distributor-logo.png 2>/dev/null || true && \
    cp /usr/share/pixmaps/abzos-logo.png /usr/share/icons/Yaru-dark/scalable/apps/abzos-logo.png 2>/dev/null || true && \
    cp /usr/share/pixmaps/abzos-logo.png /usr/share/icons/Yaru-dark/scalable/apps/distributor-logo-debian.png 2>/dev/null || true && \
    cp /usr/share/pixmaps/abzos-logo.png /usr/share/icons/Yaru-dark/scalable/apps/distributor-logo.png 2>/dev/null || true && \
    ln -sf /usr/share/themes/Ant-Dracula /usr/share/themes/Dracula 2>/dev/null || true

# --- 7b. macOS-style WhiteSur theme, icons & cursors -------------------------
# Built from source (no Debian package exists); GTK theme uses the project's
# own pre-built release tarball (no sassc/build step needed), icons and
# cursors are generated by their upstream install scripts, then the git
# checkouts and one-off build tools are removed again.
RUN apt-get update && apt-get install -y --no-install-recommends git xz-utils optipng && \
    git clone --depth 1 https://github.com/vinceliuice/WhiteSur-gtk-theme.git /tmp/whitesur-gtk && \
    tar -xf /tmp/whitesur-gtk/release/WhiteSur-Dark.tar.xz -C /usr/share/themes && \
    git clone --depth 1 https://github.com/vinceliuice/WhiteSur-icon-theme.git /tmp/whitesur-icon && \
    (cd /tmp/whitesur-icon && bash install.sh -d /usr/share/icons -n WhiteSur || true) && \
    git clone --depth 1 https://github.com/vinceliuice/WhiteSur-cursors.git /tmp/whitesur-cursor && \
    mkdir -p /usr/share/icons/WhiteSur-cursors && \
    cp -r /tmp/whitesur-cursor/dist/* /usr/share/icons/WhiteSur-cursors/ && \
    cp /usr/share/pixmaps/abzos-logo.png /usr/share/icons/WhiteSur/apps/scalable/abzos-logo.svg 2>/dev/null || true; \
    cp /usr/share/pixmaps/abzos-logo.png /usr/share/icons/WhiteSur/apps/scalable/distributor-logo-debian.svg 2>/dev/null || true; \
    cp /usr/share/pixmaps/abzos-logo.png /usr/share/icons/WhiteSur/apps/scalable/distributor-logo.svg 2>/dev/null || true; \
    rm -rf /tmp/whitesur-gtk /tmp/whitesur-icon /tmp/whitesur-cursor && \
    apt-get purge -y optipng && apt-get autoremove -y && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN chmod -R a+rX /usr/share/themes /usr/share/icons && \
    (which gtk-update-icon-cache >/dev/null 2>&1 && gtk-update-icon-cache -f -t /usr/share/icons/WhiteSur || true) && \
    (which gtk-update-icon-cache >/dev/null 2>&1 && gtk-update-icon-cache -f -t /usr/share/icons/Yaru-dark || true) && \
    (which gtk-update-icon-cache >/dev/null 2>&1 && gtk-update-icon-cache -f -t /usr/share/icons/Tela-circle || true)

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

# --- 8. LightDM Configuration (Autologin to XFCE) -----------------------------
RUN mkdir -p /etc/lightdm && \
    cat << 'LIGHTDM' > /etc/lightdm/lightdm.conf
[Seat:*]
autologin-user=abzos
autologin-user-timeout=0
autologin-session=xfce
user-session=xfce
greeter-session=lightdm-gtk-greeter
pam-autologin-service=lightdm-autologin
xserver-command=X -core
LIGHTDM

RUN cat << 'GREETER' > /etc/lightdm/lightdm-gtk-greeter.conf
[greeter]
background = /usr/share/backgrounds/abzos/wallpaper-t1.jpg
theme-name = WhiteSur-Dark
icon-theme-name = WhiteSur
cursor-theme-name = WhiteSur-cursors
font-name = JetBrains Mono Regular 10
position = 50%,center 50%,center
default-user-image = /usr/share/pixmaps/abzos-logo.png
GREETER

RUN mkdir -p /var/lib/lightdm/data /var/log/lightdm /var/cache/lightdm && \
    chown -R lightdm:lightdm /var/lib/lightdm /var/log/lightdm /var/cache/lightdm && \
    chmod 755 /var/lib/lightdm /var/lib/lightdm/data && \
    chmod 750 /var/log/lightdm

# Default user session files
RUN echo "exec startxfce4" > /etc/skel/.xsession && \
    echo "exec startxfce4" > /etc/skel/.xinitrc && \
    chmod +x /etc/skel/.xsession /etc/skel/.xinitrc

# --- 9. Staged Configurations (GTK 3, Picom, Conky, Cava, Tilda) -------------
RUN mkdir -p /etc/skel/.config/gtk-3.0 /etc/xdg/gtk-3.0 \
             /etc/skel/.config/gtk-4.0 /etc/xdg/gtk-4.0 \
             /etc/skel/.config/kitty /etc/xdg/kitty \
             /etc/skel/.config/picom /etc/xdg/picom \
             /etc/skel/.config/conky /etc/xdg/conky \
             /etc/skel/.config/cava \
             /etc/skel/.config/tilda

COPY scripts/assets/config/gtk-3.0/gtk.css /etc/skel/.config/gtk-3.0/gtk.css
COPY scripts/assets/config/gtk-3.0/gtk.css /etc/xdg/gtk-3.0/gtk.css
COPY scripts/assets/config/gtk-3.0/gtk.css /etc/skel/.config/gtk-4.0/gtk.css
COPY scripts/assets/config/gtk-3.0/gtk.css /etc/xdg/gtk-4.0/gtk.css

COPY scripts/assets/config/gtk-3.0/settings.ini /etc/skel/.config/gtk-3.0/settings.ini
COPY scripts/assets/config/gtk-3.0/settings.ini /etc/xdg/gtk-3.0/settings.ini
COPY scripts/assets/config/gtk-3.0/settings.ini /etc/skel/.config/gtk-4.0/settings.ini
COPY scripts/assets/config/gtk-3.0/settings.ini /etc/xdg/gtk-4.0/settings.ini

RUN cat << 'GTK2' > /etc/skel/.gtkrc-2.0
gtk-theme-name="WhiteSur-Dark"
gtk-icon-theme-name="WhiteSur"
gtk-font-name="JetBrains Mono Regular 9"
GTK2
RUN cp /etc/skel/.gtkrc-2.0 /etc/gtk-2.0/gtkrc 2>/dev/null || true

COPY scripts/assets/config/kitty/kitty.conf /etc/skel/.config/kitty/kitty.conf
COPY scripts/assets/config/kitty/kitty.conf /etc/xdg/kitty/kitty.conf

COPY scripts/assets/config/picom/picom.conf /etc/skel/.config/picom/picom.conf
COPY scripts/assets/config/picom/picom.conf /etc/xdg/picom/picom.conf

COPY scripts/assets/config/conky/conky.conf /etc/skel/.config/conky/conky.conf
COPY scripts/assets/config/conky/conky.conf /etc/xdg/conky/conky.conf

COPY scripts/assets/config/cava/config /etc/skel/.config/cava/config
COPY scripts/assets/config/tilda/config_0 /etc/skel/.config/tilda/config_0

# Autostart Picom & Conky
RUN cat << 'AUTO' > /etc/xdg/autostart/picom.desktop
[Desktop Entry]
Type=Application
Name=Picom Compositor
Exec=picom -b --config /etc/xdg/picom/picom.conf
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
StartupNotify=false
AUTO

RUN cat << 'AUTO' > /etc/xdg/autostart/conky.desktop
[Desktop Entry]
Type=Application
Name=Conky Clock & Monitor
Exec=sh -c "sleep 2 && conky -c /etc/skel/.config/conky/conky.conf -d"
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
StartupNotify=false
AUTO

# --- 9b. abzOS Control Center & Notification Center ---------------------
COPY scripts/assets/apps/abzos_ui_common.py /usr/local/bin/abzos_ui_common.py
COPY scripts/assets/apps/abzos-control-center /usr/local/bin/abzos-control-center
COPY scripts/assets/apps/abzos-notification-center /usr/local/bin/abzos-notification-center
COPY scripts/assets/apps/abzos-notification-logger /usr/local/bin/abzos-notification-logger
COPY scripts/assets/apps/abzos-genmon-clock /usr/local/bin/abzos-genmon-clock
COPY scripts/assets/apps/abzos-genmon-controlcenter /usr/local/bin/abzos-genmon-controlcenter
RUN chmod +x /usr/local/bin/abzos-control-center /usr/local/bin/abzos-notification-center \
             /usr/local/bin/abzos-notification-logger /usr/local/bin/abzos-genmon-clock \
             /usr/local/bin/abzos-genmon-controlcenter

RUN mkdir -p /etc/xdg/autostart && \
    cat << 'AUTO' > /etc/xdg/autostart/abzos-notification-logger.desktop
[Desktop Entry]
Type=Application
Name=abzOS Notification History Logger
Comment=Passively logs notifications for the Notification Center (does not replace xfce4-notifyd)
Exec=/usr/local/bin/abzos-notification-logger
Hidden=false
NoDisplay=true
X-GNOME-Autostart-enabled=true
StartupNotify=false
AUTO

# genmon panel plugin configs: flat key=value rc files, one per plugin id,
# read by xfce4-genmon-plugin. Command's stdout supplies <txt>/<img>/<click>/<tool>.
RUN mkdir -p /etc/xdg/xfce4/panel /etc/skel/.config/xfce4/panel && \
    cat << 'GENMON' > /etc/xdg/xfce4/panel/genmon-16.rc
Command=/usr/local/bin/abzos-genmon-controlcenter
UpdatePeriod=5000
UseLabel=false
Font=
GENMON
RUN cat << 'GENMON' > /etc/xdg/xfce4/panel/genmon-18.rc
Command=/usr/local/bin/abzos-genmon-clock
UpdatePeriod=5000
UseLabel=false
Font=JetBrains Mono 9
GENMON
RUN cp /etc/xdg/xfce4/panel/genmon-16.rc /etc/skel/.config/xfce4/panel/genmon-16.rc && \
    cp /etc/xdg/xfce4/panel/genmon-18.rc /etc/skel/.config/xfce4/panel/genmon-18.rc

# --- 10. XFCE Theme, Window Manager, Wallpaper & Panel Setup -----------------
RUN mkdir -p /etc/xdg/xfce4/xfconf/xfce-perchannel-xml /etc/skel/.config/xfce4/xfconf/xfce-perchannel-xml

# XFCE xsettings (WhiteSur-Dark macOS-style theme, WhiteSur icons, JetBrains Mono font)
RUN cat << 'XSET' > /etc/xdg/xfce4/xfconf/xfce-perchannel-xml/xsettings.xml
<?xml version="1.0" encoding="UTF-8"?>
<channel name="xsettings" version="1.0">
  <property name="Net" type="empty">
    <property name="ThemeName" type="string" value="WhiteSur-Dark"/>
    <property name="IconThemeName" type="string" value="WhiteSur"/>
    <property name="DoubleClickTime" type="int" value="400"/>
    <property name="DoubleClickDistance" type="int" value="5"/>
    <property name="DndDragThreshold" type="int" value="8"/>
    <property name="CursorBlink" type="bool" value="true"/>
    <property name="CursorBlinkTime" type="int" value="1200"/>
    <property name="SoundThemeName" type="string" value="default"/>
    <property name="EnableEventSounds" type="bool" value="false"/>
    <property name="EnableInputFeedbackSounds" type="bool" value="false"/>
  </property>
  <property name="Xft" type="empty">
    <property name="DPI" type="empty"/>
    <property name="Antialias" type="int" value="1"/>
    <property name="Hinting" type="int" value="1"/>
    <property name="HintStyle" type="string" value="hintslight"/>
    <property name="RGBA" type="string" value="rgb"/>
  </property>
  <property name="Gtk" type="empty">
    <property name="FontName" type="string" value="JetBrains Mono Regular 9"/>
    <property name="MonospaceFontName" type="string" value="JetBrains Mono 10"/>
    <property name="CursorThemeName" type="string" value="WhiteSur-cursors"/>
    <property name="CursorThemeSize" type="int" value="24"/>
    <property name="DecorationLayout" type="string" value="menu:minimize,maximize,close"/>
    <property name="ApplicationPreferDarkTheme" type="bool" value="true"/>
    <property name="ButtonImages" type="bool" value="true"/>
    <property name="MenuImages" type="bool" value="true"/>
  </property>
</channel>
XSET

# XFCE Window Manager (WhiteSur-Dark macOS-style, compositing off because picom handles it)
RUN cat << 'XFWM' > /etc/xdg/xfce4/xfconf/xfce-perchannel-xml/xfwm4.xml
<?xml version="1.0" encoding="UTF-8"?>
<channel name="xfwm4" version="1.0">
  <property name="general" type="empty">
    <property name="theme" type="string" value="WhiteSur-Dark"/>
    <property name="title_font" type="string" value="JetBrains Mono Medium 9"/>
    <property name="title_alignment" type="string" value="left"/>
    <property name="button_layout" type="string" value="CHM|"/>
    <property name="use_compositing" type="bool" value="false"/>
    <property name="box_resize" type="bool" value="false"/>
    <property name="box_move" type="bool" value="false"/>
    <property name="workspace_count" type="int" value="4"/>
  </property>
</channel>
XFWM

# XFCE Desktop Wallpaper & Icons (Unsplash mountain wallpaper on all monitors)
RUN cat << 'XDESK' > /etc/xdg/xfce4/xfconf/xfce-perchannel-xml/xfce4-desktop.xml
<?xml version="1.0" encoding="UTF-8"?>
<channel name="xfce4-desktop" version="1.0">
  <property name="backdrop" type="empty">
    <property name="screen0" type="empty">
      <property name="monitor0" type="empty">
        <property name="workspace0" type="empty">
          <property name="color-style" type="int" value="0"/>
          <property name="image-style" type="int" value="5"/>
          <property name="last-image" type="string" value="/usr/share/backgrounds/abzos/wallpaper-t1.jpg"/>
        </property>
      </property>
      <property name="monitorVirtual-1" type="empty">
        <property name="workspace0" type="empty">
          <property name="color-style" type="int" value="0"/>
          <property name="image-style" type="int" value="5"/>
          <property name="last-image" type="string" value="/usr/share/backgrounds/abzos/wallpaper-t1.jpg"/>
        </property>
      </property>
      <property name="monitorVirtual1" type="empty">
        <property name="workspace0" type="empty">
          <property name="color-style" type="int" value="0"/>
          <property name="image-style" type="int" value="5"/>
          <property name="last-image" type="string" value="/usr/share/backgrounds/abzos/wallpaper-t1.jpg"/>
        </property>
      </property>
      <property name="monitordefault" type="empty">
        <property name="workspace0" type="empty">
          <property name="color-style" type="int" value="0"/>
          <property name="image-style" type="int" value="5"/>
          <property name="last-image" type="string" value="/usr/share/backgrounds/abzos/wallpaper-t1.jpg"/>
        </property>
      </property>
    </property>
  </property>
  <property name="desktop-icons" type="empty">
    <property name="style" type="int" value="0"/>
  </property>
</channel>
XDESK

# XFCE Bottom Modern Panel (Theme 1 layout: Whisker, Pager, Launchers, Window Buttons, Tray, Clock, Actions)
RUN mkdir -p /etc/xdg/xfce4/panel
RUN cat << 'XPANEL' > /etc/xdg/xfce4/panel/default.xml
<?xml version="1.0" encoding="UTF-8"?>
<channel name="xfce4-panel" version="1.0">
  <property name="configver" type="int" value="2"/>
  <property name="panels" type="array">
    <value type="int" value="1"/>
    <value type="int" value="2"/>
    <property name="dark-mode" type="bool" value="true"/>
    <property name="panel-1" type="empty">
      <property name="position" type="string" value="p=8;x=0;y=0"/>
      <property name="length" type="uint" value="100"/>
      <property name="position-locked" type="bool" value="true"/>
      <property name="icon-size" type="uint" value="21"/>
      <property name="size" type="uint" value="34"/>
      <property name="plugin-ids" type="array">
        <value type="int" value="1"/>
        <value type="int" value="3"/>
        <value type="int" value="4"/>
        <value type="int" value="5"/>
        <value type="int" value="6"/>
        <value type="int" value="7"/>
        <value type="int" value="8"/>
        <value type="int" value="9"/>
        <value type="int" value="10"/>
        <value type="int" value="11"/>
        <value type="int" value="12"/>
        <value type="int" value="40"/>
        <value type="int" value="13"/>
      </property>
    </property>
    <property name="panel-2" type="empty">
      <property name="position" type="string" value="p=2;x=0;y=0"/>
      <property name="length" type="uint" value="100"/>
      <property name="position-locked" type="bool" value="true"/>
      <property name="icon-size" type="uint" value="16"/>
      <property name="size" type="uint" value="26"/>
      <property name="plugin-ids" type="array">
        <value type="int" value="23"/>
        <value type="int" value="24"/>
        <value type="int" value="25"/>
        <value type="int" value="26"/>
        <value type="int" value="27"/>
        <value type="int" value="28"/>
        <value type="int" value="29"/>
        <value type="int" value="30"/>
        <value type="int" value="31"/>
        <value type="int" value="32"/>
        <value type="int" value="33"/>
        <value type="int" value="34"/>
        <value type="int" value="35"/>
        <value type="int" value="36"/>
        <value type="int" value="14"/>
        <value type="int" value="18"/>
        <value type="int" value="21"/>
        <value type="int" value="22"/>
        <value type="int" value="16"/>
        <value type="int" value="20"/>
      </property>
    </property>
  </property>
  <property name="plugins" type="empty">
    <property name="plugin-1" type="string" value="whiskermenu">
      <property name="button-title" type="string" value="abzOS"/>
      <property name="button-icon" type="string" value="/usr/share/pixmaps/abzos-logo.png"/>
      <property name="show-button-title" type="bool" value="false"/>
      <property name="show-button-icon" type="bool" value="true"/>
    </property>
    <property name="plugin-3" type="string" value="separator">
      <property name="expand" type="bool" value="false"/>
      <property name="style" type="uint" value="1"/>
    </property>
    <property name="plugin-4" type="string" value="launcher">
      <property name="items" type="array">
        <value type="string" value="abzos-installer.desktop"/>
      </property>
    </property>
    <property name="plugin-5" type="string" value="launcher">
      <property name="items" type="array">
        <value type="string" value="thunar.desktop"/>
      </property>
    </property>
    <property name="plugin-6" type="string" value="launcher">
      <property name="items" type="array">
        <value type="string" value="abzos-terminal.desktop"/>
      </property>
    </property>
    <property name="plugin-7" type="string" value="launcher">
      <property name="items" type="array">
        <value type="string" value="firefox-esr.desktop"/>
      </property>
    </property>
    <property name="plugin-8" type="string" value="launcher">
      <property name="items" type="array">
        <value type="string" value="xfce4-appfinder.desktop"/>
      </property>
    </property>
    <property name="plugin-9" type="string" value="launcher">
      <property name="items" type="array">
        <value type="string" value="mpv.desktop"/>
      </property>
    </property>
    <property name="plugin-10" type="string" value="launcher">
      <property name="items" type="array">
        <value type="string" value="mousepad.desktop"/>
      </property>
    </property>
    <property name="plugin-11" type="string" value="launcher">
      <property name="items" type="array">
        <value type="string" value="abzos-nmap.desktop"/>
      </property>
    </property>
    <property name="plugin-12" type="string" value="launcher">
      <property name="items" type="array">
        <value type="string" value="xfce4-taskmanager.desktop"/>
      </property>
    </property>
    <property name="plugin-40" type="string" value="launcher">
      <property name="items" type="array">
        <value type="string" value="xfce-settings-manager.desktop"/>
      </property>
    </property>
    <property name="plugin-13" type="string" value="tasklist">
      <property name="grouping" type="uint" value="1"/>
      <property name="flat-buttons" type="bool" value="true"/>
      <property name="show-handle" type="bool" value="false"/>
    </property>
    <property name="plugin-23" type="string" value="separator">
      <property name="expand" type="bool" value="false"/>
      <property name="style" type="uint" value="0"/>
    </property>
    <property name="plugin-24" type="string" value="separator">
      <property name="expand" type="bool" value="false"/>
      <property name="style" type="uint" value="0"/>
    </property>
    <property name="plugin-25" type="string" value="separator">
      <property name="expand" type="bool" value="false"/>
      <property name="style" type="uint" value="0"/>
    </property>
    <property name="plugin-26" type="string" value="separator">
      <property name="expand" type="bool" value="false"/>
      <property name="style" type="uint" value="0"/>
    </property>
    <property name="plugin-27" type="string" value="separator">
      <property name="expand" type="bool" value="false"/>
      <property name="style" type="uint" value="0"/>
    </property>
    <property name="plugin-28" type="string" value="separator">
      <property name="expand" type="bool" value="false"/>
      <property name="style" type="uint" value="0"/>
    </property>
    <property name="plugin-29" type="string" value="separator">
      <property name="expand" type="bool" value="false"/>
      <property name="style" type="uint" value="0"/>
    </property>
    <property name="plugin-30" type="string" value="separator">
      <property name="expand" type="bool" value="false"/>
      <property name="style" type="uint" value="0"/>
    </property>
    <property name="plugin-31" type="string" value="separator">
      <property name="expand" type="bool" value="false"/>
      <property name="style" type="uint" value="0"/>
    </property>
    <property name="plugin-32" type="string" value="separator">
      <property name="expand" type="bool" value="false"/>
      <property name="style" type="uint" value="0"/>
    </property>
    <property name="plugin-33" type="string" value="separator">
      <property name="expand" type="bool" value="false"/>
      <property name="style" type="uint" value="0"/>
    </property>
    <property name="plugin-34" type="string" value="separator">
      <property name="expand" type="bool" value="false"/>
      <property name="style" type="uint" value="0"/>
    </property>
    <property name="plugin-35" type="string" value="separator">
      <property name="expand" type="bool" value="false"/>
      <property name="style" type="uint" value="0"/>
    </property>
    <property name="plugin-36" type="string" value="separator">
      <property name="expand" type="bool" value="false"/>
      <property name="style" type="uint" value="0"/>
    </property>
    <property name="plugin-14" type="string" value="separator">
      <property name="expand" type="bool" value="true"/>
      <property name="style" type="uint" value="0"/>
    </property>
    <property name="plugin-18" type="string" value="genmon"/>
    <property name="plugin-21" type="string" value="launcher">
      <property name="items" type="array">
        <value type="string" value="abzos-notifications.desktop"/>
      </property>
    </property>
    <property name="plugin-22" type="string" value="separator">
      <property name="expand" type="bool" value="true"/>
      <property name="style" type="uint" value="0"/>
    </property>
    <property name="plugin-16" type="string" value="genmon"/>
    <property name="plugin-20" type="string" value="launcher">
      <property name="items" type="array">
        <value type="string" value="abzos-controlcenter.desktop"/>
      </property>
    </property>
  </property>
</channel>
XPANEL

RUN cp /etc/xdg/xfce4/panel/default.xml /etc/xdg/xfce4/xfconf/xfce-perchannel-xml/xfce4-panel.xml

# XFCE Terminal theme matching dotfiles
RUN mkdir -p /etc/xdg/xfce4/terminal /etc/skel/.config/xfce4/terminal
COPY scripts/assets/config/xfce4/terminal/terminalrc /etc/xdg/xfce4/terminal/terminalrc
COPY scripts/assets/config/xfce4/terminal/terminalrc /etc/skel/.config/xfce4/terminal/terminalrc

# Whisker menu default configuration
RUN mkdir -p /etc/skel/.config/xfce4/panel
RUN cat << 'WMCONF' > /etc/skel/.config/xfce4/panel/whiskermenu-1.rc
button-title=abzOS
button-icon=/usr/share/pixmaps/abzos-logo.png
show-button-title=false
show-button-icon=true
category-icon-size=1
item-icon-size=1
load-hierarchy=true
launcher-show-tooltip=false
show-command-settings=false
show-command-lockscreen=false
show-command-switchuser=false
show-command-logoutuser=false
show-command-logout=false
favorites=abzos-installer.desktop,abzos-terminal.desktop,thunar.desktop,firefox-esr.desktop,mpv.desktop,ristretto.desktop,atril.desktop,galculator.desktop,mousepad.desktop,abzos-nmap.desktop,abzos-sqlmap.desktop,abzos-wireshark.desktop
WMCONF

# Copy default XFCE configs to /etc/skel
RUN cp -r /etc/xdg/xfce4/xfconf /etc/skel/.config/xfce4/

# --- 11. Modern Terminal Fetch & Shell Styling --------------------------------
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
 ${c_cyan}  / /____\\ \\    ${c_magenta}Desktop:${c_reset}  XFCE 4.18 (Dark Edition)
 ${c_cyan} / /      \\ \\   ${c_magenta}Terminal:${c_reset} Kitty / abzOS Terminal
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

# Show the abzOS system banner on every new interactive shell (kitty tab/window)
if [ -t 1 ] && command -v abzos-fetch >/dev/null 2>&1; then
    abzos-fetch
fi
BASHRC

RUN cp -f /etc/skel/.bashrc /root/.bashrc

# Set Kitty as the primary default terminal (matches abzos-terminal.desktop, panel launcher, and kitty.conf theme)
RUN update-alternatives --set x-terminal-emulator /usr/bin/kitty 2>/dev/null || true

# --- 12. Application Launchers ------------------------------------------------
RUN mkdir -p /usr/share/applications

RUN cat << 'APPDT' > /usr/share/applications/abzos-controlcenter.desktop
[Desktop Entry]
Name=Power
GenericName=Power Options
Comment=Log out, restart, suspend, or shut down
Exec=xfce4-session-logout
Icon=/usr/share/pixmaps/abzos-controlcenter.png
Terminal=false
Type=Application
NoDisplay=false
Categories=Settings;System;
APPDT

RUN cat << 'APPDT' > /usr/share/applications/abzos-notifications.desktop
[Desktop Entry]
Name=Notifications
GenericName=Notification Center
Comment=Recent notifications and calendar
Exec=/usr/local/bin/abzos-notification-center
Icon=/usr/share/pixmaps/abzos-notifications.png
Terminal=false
Type=Application
NoDisplay=false
Categories=Utility;
APPDT

RUN cat << 'APPDT' > /usr/share/applications/abzos-terminal.desktop
[Desktop Entry]
Name=Terminal
GenericName=Terminal
Comment=Modern Console Terminal
Exec=kitty
Icon=utilities-terminal
Terminal=false
Type=Application
Categories=System;TerminalEmulator;Development;
APPDT

RUN cat << 'APPDT' > /usr/share/applications/abzos-files.desktop
[Desktop Entry]
Name=File Manager
Comment=Browse files and filesystem
Exec=thunar %U
Icon=system-file-manager
Terminal=false
Type=Application
Categories=System;Utility;
APPDT

RUN cat << 'APPDT' > /usr/share/applications/abzos-editor.desktop
[Desktop Entry]
Name=Text Editor
Comment=Simple text and code editor
Exec=mousepad %U
Icon=accessories-text-editor
Terminal=false
Type=Application
Categories=Utility;TextEditor;Development;
APPDT

RUN cat << 'APPDT' > /usr/share/applications/abzos-cava.desktop
[Desktop Entry]
Name=Cava Audio Visualizer
Comment=Console Audio Visualizer
Exec=xfce4-terminal -T "Cava Audio Visualizer" -e cava
Icon=multimedia-audio-player
Terminal=false
Type=Application
Categories=AudioVideo;Audio;
APPDT

RUN cat << 'APPDT' > /usr/share/applications/abzos-tilda.desktop
[Desktop Entry]
Name=Tilda Drop-down Terminal
Comment=Quake-style drop-down terminal
Exec=tilda
Icon=utilities-terminal
Terminal=false
Type=Application
Categories=System;TerminalEmulator;
APPDT

RUN cat << 'APPDT' > /usr/share/applications/abzos-nmap.desktop
[Desktop Entry]
Name=Nmap Scanner
Comment=Network exploration and security auditing
Exec=xfce4-terminal -T "Nmap Scanner" -e "bash -c 'nmap --help; echo; echo Press Enter to exit...; read'"
Icon=network-wired-symbolic
Terminal=false
Type=Application
Categories=Network;Security;System;
APPDT

RUN cat << 'APPDT' > /usr/share/applications/abzos-sqlmap.desktop
[Desktop Entry]
Name=Sqlmap
Comment=Automatic SQL injection tool
Exec=xfce4-terminal -T "Sqlmap" -e "bash -c 'sqlmap -h; echo; echo Press Enter to exit...; read'"
Icon=network-server
Terminal=false
Type=Application
Categories=Network;Security;System;
APPDT

RUN cat << 'APPDT' > /usr/share/applications/abzos-john.desktop
[Desktop Entry]
Name=John the Ripper
Comment=Password hash cracker
Exec=xfce4-terminal -T "John the Ripper" -e "bash -c 'john; echo; echo Press Enter to exit...; read'"
Icon=dialog-password-symbolic
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
Icon=network-wireless-symbolic
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

RUN cat << 'APPDT' > /usr/share/applications/abzos-wireshark.desktop
[Desktop Entry]
Name=Wireshark / TShark
Comment=Network traffic packet capture and analysis
Exec=xfce4-terminal -T "TShark Packet Capture" -e "bash -c 'tshark --help; echo; echo Press Enter to exit...; read'"
Icon=network-wired-symbolic
Terminal=false
Type=Application
Categories=Network;Security;System;
APPDT

# Prepare launcher desktop files inside /etc/xdg/xfce4/panel launcher directories
RUN for i in 4 5 6 7 8 9 10 11 12 20 21 40; do \
        mkdir -p /etc/xdg/xfce4/panel/launcher-$i /etc/skel/.config/xfce4/panel/launcher-$i; \
    done && \
    (test -f /usr/share/applications/abzos-installer.desktop && cp /usr/share/applications/abzos-installer.desktop /etc/xdg/xfce4/panel/launcher-4/ || true) && \
    (test -f /usr/share/applications/thunar.desktop && cp /usr/share/applications/thunar.desktop /etc/xdg/xfce4/panel/launcher-5/ || true) && \
    (test -f /usr/share/applications/abzos-terminal.desktop && cp /usr/share/applications/abzos-terminal.desktop /etc/xdg/xfce4/panel/launcher-6/ || true) && \
    (test -f /usr/share/applications/firefox-esr.desktop && cp /usr/share/applications/firefox-esr.desktop /etc/xdg/xfce4/panel/launcher-7/ || true) && \
    (test -f /usr/share/applications/xfce4-appfinder.desktop && cp /usr/share/applications/xfce4-appfinder.desktop /etc/xdg/xfce4/panel/launcher-8/ || true) && \
    (test -f /usr/share/applications/mpv.desktop && cp /usr/share/applications/mpv.desktop /etc/xdg/xfce4/panel/launcher-9/ || true) && \
    (test -f /usr/share/applications/mousepad.desktop && cp /usr/share/applications/mousepad.desktop /etc/xdg/xfce4/panel/launcher-10/ || true) && \
    (test -f /usr/share/applications/abzos-nmap.desktop && cp /usr/share/applications/abzos-nmap.desktop /etc/xdg/xfce4/panel/launcher-11/ || true) && \
    (test -f /usr/share/applications/xfce4-taskmanager.desktop && cp /usr/share/applications/xfce4-taskmanager.desktop /etc/xdg/xfce4/panel/launcher-12/ || true) && \
    (test -f /usr/share/applications/abzos-controlcenter.desktop && cp /usr/share/applications/abzos-controlcenter.desktop /etc/xdg/xfce4/panel/launcher-20/ || true) && \
    (test -f /usr/share/applications/abzos-notifications.desktop && cp /usr/share/applications/abzos-notifications.desktop /etc/xdg/xfce4/panel/launcher-21/ || true) && \
    (test -f /usr/share/applications/xfce-settings-manager.desktop && cp /usr/share/applications/xfce-settings-manager.desktop /etc/xdg/xfce4/panel/launcher-40/ || true) && \
    cp -r /etc/xdg/xfce4/panel/launcher-* /etc/skel/.config/xfce4/panel/

# Rename Thunar's menu/taskbar label to "File Manager" (its own window
# titlebar still shows "<folder> - Thunar" at runtime -- that's Thunar's
# own hardcoded behavior, same as every other file manager, and isn't
# controllable via desktop files or xfconf).
RUN sed -i '0,/^Name=Thunar File Manager$/s//Name=File Manager/' /usr/share/applications/thunar.desktop && \
    sed -i '0,/^Icon=org.xfce.thunar$/s//Icon=system-file-manager/' /usr/share/applications/thunar.desktop

# --- 13. Finalize permissions and system targets ------------------------------
RUN cp -a /etc/skel/. /home/abzos/ && chown -R abzos:abzos /home/abzos

RUN ln -sf /lib/systemd/system/graphical.target /etc/systemd/system/default.target && \
    ln -sf /lib/systemd/system/lightdm.service /etc/systemd/system/display-manager.service

# Enable NetworkManager & spice-vdagent in systemd
RUN systemctl enable NetworkManager.service 2>/dev/null || true
RUN systemctl enable spice-vdagentd.service 2>/dev/null || true

RUN chmod 1777 /tmp /var/tmp && \
    chmod 0640 /etc/shadow && \
    chmod 4755 /usr/bin/sudo /bin/su
