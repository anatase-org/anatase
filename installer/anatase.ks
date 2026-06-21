# Kickstart defaults for the interactive Anatase installer.

ostreesetup --osname="anatase" --remote="anatase" --url="file:///ostree/repo" --ref="master" --nogpg

%post --erroronfail --nochroot --interpreter=/usr/bin/bash --log=/tmp/anaconda-flatpaks.log
read -r osname checksum serial < <(
    ostree admin --sysroot=/mnt/sysimage status --json |
        python3 -c 'import json, sys
deployment = json.load(sys.stdin)["deployments"][0]
print(deployment["osname"], deployment["checksum"], deployment.get("deployserial", deployment.get("serial", "")))
'
)

deploy_dir="/mnt/sysimage/ostree/deploy/${osname}/deploy/${checksum}.${serial}"
if [ -z "$serial" ] || [ ! -d "$deploy_dir" ]; then
    deploy_dir=$(find "/mnt/sysimage/ostree/deploy/${osname}/deploy" \
        -maxdepth 1 -type d -name "${checksum}.*" | sort | head -n 1)
fi

if [ -z "$deploy_dir" ] || [ ! -d "$deploy_dir" ]; then
    echo "failed to find installed OSTree deployment for ${osname}:${checksum}" >&2
    exit 1
fi

target="${deploy_dir}/var/lib"
mkdir -p "$target"
rsync -aAXUHK --open-noatime /var/lib/flatpak "$target"
sync "$target"
%end

%post --erroronfail --log=/tmp/anaconda-flatpak-selinux.log
if [ -d /var/lib/flatpak ]; then
    chcon -R -t var_lib_t /var/lib/flatpak
fi
%end
