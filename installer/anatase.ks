# Kickstart defaults for the interactive Anatase installer.

ostreesetup --osname="anatase" --remote="anatase" --url="file:///ostree/repo" --ref="anatase" --nogpg

%post --erroronfail --nochroot --interpreter=/usr/bin/bash --log=/tmp/anaconda-efi-payload.log
target_efi="/mnt/sysimage/boot/efi"
if [ ! -d "$target_efi" ]; then
    echo "no target EFI system partition mounted; skipping EFI payload copy"
    exit 0
fi

efi_source="/usr/lib/ludos/efi"
if [ ! -d "$efi_source" ]; then
    echo "missing Anatase EFI payload directory: $efi_source" >&2
    exit 1
fi

cp -R --no-preserve=mode,ownership,timestamps "$efi_source/." "$target_efi/"
sync "$target_efi"
%end

%post --erroronfail --nochroot --interpreter=/usr/bin/bash --log=/tmp/anaconda-flatpaks.log
flatpak_source="/var/lib/flatpak-installer"
if [ ! -d "$flatpak_source" ]; then
    echo "no installer Flatpak snapshot found at $flatpak_source; skipping"
    exit 0
fi

deployment="$(ostree rev-parse --repo=/mnt/sysimage/ostree/repo ostree/0/1/0)"
deploy_dir="/mnt/sysimage/ostree/deploy/anatase/deploy/${deployment}.0"

if [ -z "$deploy_dir" ] || [ ! -d "$deploy_dir" ]; then
    echo "failed to find installed OSTree deployment for ${deployment}" >&2
    exit 1
fi

target="${deploy_dir}/var/lib/flatpak"
mkdir -p "$target"
rsync -aAXUHK --delete --open-noatime "$flatpak_source/" "$target/"
sync "$target"
%end

%post --erroronfail --log=/tmp/anaconda-flatpak-selinux.log
if [ -d /var/lib/flatpak ]; then
    restorecon -RFv /var/lib/flatpak
fi
%end
