#!/usr/bin/bash
set -eux

command -v liveinst >/dev/null
command -v slitherer-anaconda >/dev/null

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

# Defer to KDE for user creation
install -dm0755 /etc/anaconda/conf.d
cat > /etc/anaconda/conf.d/90-anatase-installer.conf <<'EOF'
[User Interface]
hidden_spokes =
    PasswordSpoke
    UserSpoke
hidden_webui_pages =
    anaconda-screen-accounts
can_change_root = False
can_change_users = False
EOF

# Kill the reporting flow for bugzilla
rm -f \
    /etc/libreport/events/report_Bugzilla.conf \
    /etc/libreport/events.d/bugzilla_anaconda_event.conf \
    /etc/libreport/events.d/bugzilla_event.conf \
    /etc/libreport/plugins/bugzilla.conf \
    /etc/libreport/plugins/bugzilla_format.conf \
    /etc/libreport/plugins/bugzilla_format_anaconda.conf \
    /etc/libreport/plugins/bugzilla_format_analyzer_libreport.conf \
    /etc/libreport/plugins/bugzilla_format_kernel.conf \
    /etc/libreport/plugins/bugzilla_formatdup.conf \
    /etc/libreport/plugins/bugzilla_formatdup_anaconda.conf \
    /etc/libreport/plugins/bugzilla_formatdup_analyzer_libreport.conf \
    /usr/bin/reporter-bugzilla \
    /usr/sbin/reporter-bugzilla \
    /usr/share/libreport/conf.d/plugins/bugzilla.conf \
    /usr/share/libreport/events/report_Bugzilla.xml \
    /usr/share/libreport/events/watch_Bugzilla.xml \
    /usr/share/libreport/workflows/workflow_AnacondaFedora.xml
if [ -f /etc/libreport/workflows.d/anaconda_event.conf ]; then
    sed -i \
        -e '/workflow_AnacondaFedora/d' \
        -e '/workflow_AnacondaRHELBugzilla/d' \
        /etc/libreport/workflows.d/anaconda_event.conf
fi

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

repo=/ostree/repo
if [ ! -d "${repo}/objects" ]; then
    echo "installer OSTree repo is missing objects: ${repo}" >&2
    exit 1
fi

commit_count=$(find "${repo}/objects" -type f -name '*.commit' | wc -l)
if [ "${commit_count}" -eq 0 ]; then
    echo "installer OSTree repo has no commit objects: ${repo}" >&2
    exit 1
fi

newest_commit=$(
    find "${repo}/objects" -type f -name '*.commit' | while read -r path; do
        object=${path##*/}
        object_dir=${path%/*}
        object_prefix=${object_dir##*/}
        checksum="${object_prefix}${object%.commit}"
        commit_date=$(ostree --repo="${repo}" show "${checksum}" | sed -n 's/^Date:  //p')
        commit_time=$(date -u -d "${commit_date}" +%s)
        printf '%s %s\n' "${commit_time}" "${checksum}"
    done | sort -n | tail -n 1 | awk '{print $2}'
)
if [ -z "${newest_commit}" ]; then
    echo "failed to determine newest OSTree commit in ${repo}" >&2
    exit 1
fi

if ostree --repo="${repo}" refs | grep -qx master; then
    ostree --repo="${repo}" refs --delete master
fi
ostree --repo="${repo}" refs --create=master "${newest_commit}"
ostree --repo="${repo}" summary --update
