#!/bin/bash
set -e

export DEBIAN_FRONTEND=noninteractive
export LC_ALL=C

echo "=== [1/6] Configuring DNS and Package Repositories ==="
# Setup DNS
echo "nameserver 8.8.8.8" > /etc/resolv.conf
echo "nameserver 1.1.1.1" >> /etc/resolv.conf

# Setup Ubuntu Noble official repositories
cat << 'SOURCES' > /etc/apt/sources.list
deb http://archive.ubuntu.com/ubuntu/ noble main restricted universe multiverse
deb http://archive.ubuntu.com/ubuntu/ noble-updates main restricted universe multiverse
deb http://security.ubuntu.com/ubuntu/ noble-security main restricted universe multiverse
deb http://archive.ubuntu.com/ubuntu/ noble-backports main restricted universe multiverse
SOURCES

apt-get update

echo "=== [2/6] Installing Developer Tools ==="
apt-get install -y --no-install-recommends \
    build-essential \
    gcc g++ make cmake gdb \
    git curl wget jq tree htop \
    unzip zip p7zip-full \
    python3 python3-pip python3-venv python3-dev pipx \
    neovim nano \
    tmux

echo "=== [3/6] Installing Cybersecurity and Kali-equivalent Tools ==="
# Preconfigure wireshark non-root capture
echo "wireshark-common wireshark-common/install-setuid boolean true" | debconf-set-selections

apt-get install -y --no-install-recommends \
    nmap masscan whois dnsutils net-tools traceroute iputils-ping \
    socat netcat-openbsd tcpdump \
    wireshark tshark \
    nikto sqlmap gobuster dirb ffuf \
    john hydra \
    aircrack-ng \
    binwalk radare2 strace ltrace hexedit

echo "=== [4/6] Configuring Users and System Identity ==="
# Set Hostname
echo "abzos" > /etc/hostname
cat << 'HOSTS' > /etc/hosts
127.0.0.1   localhost abzos
::1         localhost ip6-localhost ip6-loopback
HOSTS

# Set os-release & issue
cat << 'OSREL' > /etc/os-release
NAME="abzOS"
PRETTY_NAME="abzOS 1.0 (Developer & Cybersecurity Edition)"
ID=abzos
ID_LIKE="ubuntu debian"
VERSION_ID="1.0"
HOME_URL="https://github.com/akbarkhojayev"
SUPPORT_URL="https://github.com/akbarkhojayev"
BUG_REPORT_URL="https://github.com/akbarkhojayev"
OSREL

cat << 'ISSUE' > /etc/issue
abzOS 1.0 Developer & Cybersecurity Edition \n \l
ISSUE
cp /etc/issue /etc/issue.net

# Configure casper live user
cat << 'CASPER' > /etc/casper.conf
export USERNAME="abzos"
export USERFULLNAME="abzOS User"
export HOST="abzos"
export BUILD_SYSTEM="Ubuntu"
CASPER

# Ensure user abzos exists and has proper groups
if ! id "abzos" &>/dev/null; then
    useradd -m -s /bin/bash -u 1000 abzos
fi
echo "abzos:abzos" | chpasswd
echo "root:toor" | chpasswd

# Add abzos to administrative and hardware groups
usermod -aG sudo,adm,wireshark,netdev,audio,video,plugdev,cdrom abzos 2>/dev/null || true

# Passwordless sudo for live session
mkdir -p /etc/sudoers.d
echo "abzos ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/abzos
chmod 0440 /etc/sudoers.d/abzos

echo "=== [5/6] Configuring Modern Dark UI and Kali Styling ==="
mkdir -p /usr/share/backgrounds/abzos
mkdir -p /usr/share/pixmaps
mkdir -p /usr/share/icons/hicolor/128x128/apps

# Copy wallpapers and logos from scripts directory
if [ -f /scripts/abzos-dark.png ]; then
    cp /scripts/abzos-dark.png /usr/share/backgrounds/abzos/abzos-dark.png
    cp /scripts/abzos-dark.png /usr/share/xfce4/backdrops/xubuntu-wallpaper.png 2>/dev/null || true
fi

if [ -f /scripts/abzos-logo.png ]; then
    cp /scripts/abzos-logo.png /usr/share/pixmaps/abzos-logo.png
    cp /scripts/abzos-logo.png /usr/share/icons/hicolor/128x128/apps/abzos-logo.png
fi

# LightDM Greeter Configuration
cat << 'GREETER' > /etc/lightdm/lightdm-gtk-greeter.conf
[greeter]
background = /usr/share/backgrounds/abzos/abzos-dark.png
theme-name = Yaru-dark
icon-theme-name = WhiteSur-dark
font-name = Ubuntu 11
position = 50%,center 50%,center
indicators = ~spacer;~clock;~power
clock-format = %a, %d-%b  %H:%M
default-user-image = /usr/share/pixmaps/abzos-logo.png
GREETER

cat << 'LIGHTDM' > /etc/lightdm/lightdm.conf
[Seat:*]
autologin-user=abzos
autologin-user-timeout=0
greeter-session=lightdm-gtk-greeter
user-session=xfce
LIGHTDM

# Configure XFCE Default Theme (xsettings.xml)
for XSETTINGS in /etc/xdg/xdg-xubuntu/xfce4/xfconf/xfce-perchannel-xml/xsettings.xml /etc/xdg/xfce4/xfconf/xfce-perchannel-xml/xsettings.xml; do
    if [ -f "$XSETTINGS" ]; then
        sed -i 's/name="ThemeName" type="string" value="[^"]*"/name="ThemeName" type="string" value="Yaru-dark"/' "$XSETTINGS"
        sed -i 's/name="IconThemeName" type="string" value="[^"]*"/name="IconThemeName" type="string" value="WhiteSur-dark"/' "$XSETTINGS"
    fi
done

# Configure XFCE Window Manager (xfwm4.xml)
for XFWM in /etc/xdg/xdg-xubuntu/xfce4/xfconf/xfce-perchannel-xml/xfwm4.xml /etc/xdg/xfce4/xfconf/xfce-perchannel-xml/xfwm4.xml; do
    if [ -f "$XFWM" ]; then
        sed -i 's/name="theme" type="string" value="[^"]*"/name="theme" type="string" value="Yaru-dark"/' "$XFWM"
    fi
done

# Configure XFCE Desktop Wallpaper (xfce4-desktop.xml)
for DESKTOP_XML in /etc/xdg/xdg-xubuntu/xfce4/xfconf/xfce-perchannel-xml/xfce4-desktop.xml /etc/xdg/xfce4/xfconf/xfce-perchannel-xml/xfce4-desktop.xml; do
    if [ -f "$DESKTOP_XML" ]; then
        sed -i 's|/usr/share/xfce4/backdrops/xubuntu-wallpaper.png|/usr/share/backgrounds/abzos/abzos-dark.png|g' "$DESKTOP_XML"
    fi
done

# Configure Whisker Menu Defaults
WHISKER_CONF="/etc/xdg/xdg-xubuntu/xfce4/whiskermenu/defaults.rc"
if [ -f "$WHISKER_CONF" ]; then
    sed -i 's|^button-icon=.*|button-icon=/usr/share/pixmaps/abzos-logo.png|' "$WHISKER_CONF"
    sed -i 's|^button-title=.*|button-title=abzOS|' "$WHISKER_CONF"
    sed -i 's|^show-button-title=.*|show-button-title=true|' "$WHISKER_CONF"
fi

# Configure Terminal Colors (Nord / Kali Dark)
mkdir -p /etc/xdg/xdg-xubuntu/xfce4/terminal /etc/xdg/xfce4/terminal
cat << 'TERMRC' > /etc/xdg/xdg-xubuntu/xfce4/terminal/terminalrc
[Configuration]
FontName=Monospace 11
ColorPalette=#1e1e1e;#f44747;#608b4e;#dcdcaa;#569cd6;#c586c0;#4ec9b0;#d4d4d4;#808080;#f44747;#608b4e;#dcdcaa;#569cd6;#c586c0;#4ec9b0;#ffffff
ColorBackground=#0d1117
ColorForeground=#c9d1d9
ColorCursor=#00f0ff
ScrollingBar=TERMINAL_SCROLLBAR_NONE
ScrollingUnlimited=TRUE
BackgroundMode=TERMINAL_BACKGROUND_TRANSPARENT
BackgroundDarkness=0.92
TERMRC
cp /etc/xdg/xdg-xubuntu/xfce4/terminal/terminalrc /etc/xdg/xfce4/terminal/terminalrc 2>/dev/null || true

# Banner and Prompts
cat << 'BANNER' > /etc/abzos_banner.txt
\033[01;36m
        _           ____   _____ 
       | |         / __ \ / ____|
  __ _ | |__  ____| |  | | (___  
 / _` || '_ \|_  /| |  | |\___ \ 
| (_| || |_) |/ / | |__| |____) |
 \__,_||_.__//___|\____/|_____/ 
\033[01;35m  [ abzOS 1.0 - Developer & Cybersecurity Edition ]\033[00m
BANNER

cat << 'BASH_EXTRA' > /etc/skel/.bash_aliases
# abzOS Developer & Security Aliases
alias ll='ls -lah --color=auto'
alias la='ls -A --color=auto'
alias l='ls -CF --color=auto'
alias grep='grep --color=auto'
alias myip='curl -s https://ifconfig.me/ip || hostname -I'
alias ports='netstat -tulpn'
alias cls='clear && cat /etc/abzos_banner.txt'
alias update='sudo apt update && sudo apt upgrade -y'

# Custom Kali-Style Prompt
PS1="\[\033[01;36m\]┌──(\[\033[01;32m\]\u㉿\h\[\033[01;36m\])-[\[\033[01;37m\]\w\[\033[01;36m\]]\n\[\033[01;36m\]└─\[\033[01;32m\]\$\[\033[00m\] "
BASH_EXTRA

# Append to /etc/skel/.bashrc and user bashrc
if ! grep -q "abzos_banner.txt" /etc/skel/.bashrc 2>/dev/null; then
    cat << 'BASHRC_APPEND' >> /etc/skel/.bashrc

# abzOS Greeting
if [ -f /etc/abzos_banner.txt ] && [ -t 1 ]; then
    echo -e "$(cat /etc/abzos_banner.txt)"
fi
if [ -f ~/.bash_aliases ]; then
    . ~/.bash_aliases
fi
BASHRC_APPEND
fi

# Copy skel to user abzos home
cp -r /etc/skel/. /home/abzos/
chown -R abzos:abzos /home/abzos

echo "=== [6/6] Creating Cybersecurity Application Menu Entries ==="
mkdir -p /usr/share/desktop-directories
mkdir -p /usr/share/applications

# Create .desktop launchers for CLI security tools so they appear in GUI menus!
create_terminal_app() {
    local name="$1"
    local exec_cmd="$2"
    local comment="$3"
    local icon="$4"
    local filename="$5"
    cat << APPDT > "/usr/share/applications/${filename}.desktop"
[Desktop Entry]
Name=${name}
Comment=${comment}
Exec=xfce4-terminal -T "${name}" -e "bash -c '${exec_cmd}; echo; echo Press Enter to exit...; read'"
Icon=${icon}
Terminal=false
Type=Application
Categories=Network;Security;System;
APPDT
}

create_terminal_app "Nmap Security Scanner" "nmap --help" "Network exploration and security auditing" "network-wired" "abzos-nmap"
create_terminal_app "Sqlmap" "sqlmap -h" "Automatic SQL injection tool" "server-database" "abzos-sqlmap"
create_terminal_app "Nikto Web Scanner" "nikto -H" "Web server security scanner" "web-browser" "abzos-nikto"
create_terminal_app "John the Ripper" "john" "Password cracker" "dialog-password" "abzos-john"
create_terminal_app "Hydra" "hydra -h" "Very fast network logon cracker" "security-high" "abzos-hydra"
create_terminal_app "Radare2" "r2 -h" "Reverse engineering framework" "utilities-terminal" "abzos-radare2"
create_terminal_app "Aircrack-ng" "aircrack-ng --help" "Wireless network auditing" "network-wireless" "abzos-aircrack"
create_terminal_app "Gobuster" "gobuster -h" "Directory/file & DNS busting tool" "system-search" "abzos-gobuster"

# Clean up apt caches
apt-get clean
rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

echo "=== Setup complete! abzOS is ready. ==="
