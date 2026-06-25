# Kickstart defaults for the interactive Anatase installer.

#
# Installer
#

ostreesetup --osname="anatase" --remote="anatase" --url="file:///ostree/repo" --ref="os" --nogpg

#
# Boot configuration
#

%post --erroronfail --nochroot --interpreter=/usr/bin/bash --log=/tmp/anaconda-efi-payload.log
# Copy our MOK key to the efi root so that users have access to it

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

#
# Mountpoint rename
#

%post --erroronfail --nochroot --interpreter=/usr/bin/bash --log=/tmp/anaconda-filesystem-labels.log
set -euo pipefail

label_mount() {
    local mountpoint="$1"
    local label="$2"
    local source=""
    local fstype=""

    if ! mountpoint -q "$mountpoint"; then
        echo "$mountpoint is not mounted; skipping $label"
        return 0
    fi

    if ! read -r source fstype < <(
        findmnt --first-only -nro SOURCE,FSTYPE --mountpoint "$mountpoint"
    ); then
        echo "failed to resolve mounted filesystem for $mountpoint" >&2
        return 1
    fi

    if [ -z "$source" ] || [ -z "$fstype" ]; then
        echo "failed to resolve mounted filesystem for $mountpoint" >&2
        return 1
    fi

    case "$fstype" in
        vfat|fat|msdos)
            fatlabel "$source" "$label"
            ;;
        ext2|ext3|ext4)
            e2label "$source" "$label"
            ;;
        btrfs)
            if [ "$mountpoint" != /mnt/sysimage ]; then
                echo "$mountpoint is a Btrfs subvolume; skipping $label"
                return 0
            fi
            btrfs filesystem label "$mountpoint" "$label"
            ;;
        *)
            echo "unsupported filesystem type for $mountpoint: $fstype" >&2
            return 1
            ;;
    esac
}

label_mount /mnt/sysimage/boot/efi ANATASE_EFI
label_mount /mnt/sysimage/boot ANATASE_BOOT
label_mount /mnt/sysimage ANATASE_DISK
%end

#
# Flatpack configuration
#

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
