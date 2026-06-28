#!/usr/bin/bash
set -eux

# Sanity checks
command -v liveinst >/dev/null
command -v slitherer-anaconda >/dev/null

# Add Installer user and skeleton
install -Dm0644 /files/installer/anatase.ks \
    /usr/share/anatase-installer/anatase.ks
install -Dm0644 /files/installer/anatase.ks \
    /usr/share/anaconda/interactive-defaults.ks
install -Dm0644 /files/installer/anatase-webui.desktop \
    /etc/xdg/autostart/anatase-webui.desktop
install -Dm0755 /files/installer/anatase-webui.desktop \
    /etc/skel/Desktop/anatase-webui.desktop

if ! getent group wheel >/dev/null; then
    groupadd wheel
fi
install -dm0755 /var/spool/mail
if id -u anatase >/dev/null 2>&1; then
    usermod --append --groups wheel --shell /usr/bin/bash anatase
else
    useradd --create-home --shell /usr/bin/bash --groups wheel anatase
fi
passwd -d anatase || true
install -dm0755 -o anatase -g anatase /home/anatase
install -Dm0755 -o anatase -g anatase /files/installer/anatase-webui.desktop \
    /home/anatase/Desktop/anatase-webui.desktop

install -Dm0644 /files/installer/anaconda.conf \
    /etc/anaconda/conf.d/90-anatase-installer.conf

# Anaconda's automatic partitioning reuses an existing ESP if one is present on
# the selected boot disk. This can cause losing the boot option if the bios resets
# in dual boot scenarios
python3 <<'PY'
from glob import glob

path, = glob("/usr/lib*/python*/site-packages/pyanaconda/modules/storage/partitioning/automatic/utils.py")
with open(path) as f:
    text = f.read()
old = '''elif request.fstype in ("prepboot", "efi", "macefi", "hfs+") and \\
                (storage.bootloader.skip_bootloader or stage1_device):'''
new = '''elif request.fstype in ("prepboot", "efi", "macefi", "hfs+") and \\
                (storage.bootloader.skip_bootloader):'''
if new not in text:
    if old not in text:
        raise SystemExit(f"failed to find Anaconda ESP reuse check in {path}")
    with open(path, "w") as f:
        f.write(text.replace(old, new))
PY
rm -rf /usr/lib*/python*/site-packages/pyanaconda/modules/storage/partitioning/automatic/__pycache__

# Drop Fedora feedback/reporting UI from the Anaconda Web UI.
webui_dir=/usr/share/cockpit/anaconda-webui
if [ -f "${webui_dir}/index.css.gz" ]; then
    tmp_css=$(mktemp)
    gzip -cd "${webui_dir}/index.css.gz" > "${tmp_css}"
    cat >> "${tmp_css}" <<'EOF'

.feedback-section{display:none!important}
[id$="-bz-report-modal"] form > *:has(a[href*="bugzilla"]){display:none!important}
[id$="-bz-report-modal"] form > :is(hr,[role="separator"]):has(+ *:has(a[href*="bugzilla"])){display:none!important}
[id$="-bz-report-modal"] form > *:has([id$="-bz-report-modal-details"]) + :is(hr,[role="separator"]) + *,[id$="-bz-report-modal"] form > *:has([id$="-bugzilla-apikey"]){display:none!important}
[id$="-bz-report-modal"] form > *:has([id$="-bz-report-modal-details"]) + :is(hr,[role="separator"]){display:none!important}
EOF
    gzip -n -c "${tmp_css}" > "${webui_dir}/index.css.gz"
    rm -f "${tmp_css}"
fi

# Enable user
cat > /etc/plasmalogin.conf <<'EOF'
[Autologin]
User=anatase
Session=plasma.desktop
Relogin=true
EOF

install -dm0755 /etc/polkit-1/rules.d
cat > /etc/polkit-1/rules.d/49-anatase-liveinst.rules <<'EOF'
polkit.addRule(function(action, subject) {
    if (action.id == "org.fedoraproject.pkexec.liveinst" &&
        subject.user == "anatase" &&
        subject.active === true &&
        subject.local === true) {
        return polkit.Result.YES;
    }
});
EOF

# Install flathub apps
flatpak remote-add --system --if-not-exists --title "Flathub" \
    flathub https://dl.flathub.org/repo/flathub.flatpakrepo
flatpak remote-modify --system --enable flathub

flatpak_arch=$(uname -m)
flatpak install --system -y --noninteractive flathub \
    "app/org.kde.kcalc/${flatpak_arch}/stable" \
    "app/org.kde.okular/${flatpak_arch}/stable" \
    "app/org.kde.gwenview/${flatpak_arch}/stable" \
    "app/org.kde.kate/${flatpak_arch}/stable" \
    "app/org.kde.ark/${flatpak_arch}/stable" \
    "app/org.kde.filelight/${flatpak_arch}/stable"
flatpak update --system --appstream -y --noninteractive

rm -rf /var/lib/flatpak-installer
cp -alT /var/lib/flatpak /var/lib/flatpak-installer
