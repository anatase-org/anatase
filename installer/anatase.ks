# Kickstart defaults for the interactive Anatase installer.

#
# Installer
#

ostreesetup --osname="anatase" --remote="anatase" --url="file:///ostree/repo" --ref="os" --nogpg

%post --erroronfail --nochroot --interpreter=/usr/bin/bash --log=/tmp/anaconda-ostree-layer.log
set -euo pipefail

source_repo="/ostree/repo"
target_repo="/mnt/sysimage/ostree/repo"
layer_ref="ostree/container/blob/sha256_3A_1111111111111111111111111111111111111111111111111111111111111111"

if [ ! -d "${source_repo}/objects" ]; then
    echo "installer OSTree repo is missing objects: ${source_repo}" >&2
    exit 1
fi

if [ ! -d "${target_repo}/objects" ]; then
    echo "target OSTree repo is missing objects: ${target_repo}" >&2
    exit 1
fi

ostree --repo="${target_repo}" pull-local \
    --untrusted \
    --disable-verify-bindings \
    "${source_repo}" \
    "${layer_ref}"
ostree --repo="${target_repo}" summary --update

deployment_root="/mnt/sysimage/ostree/deploy/anatase/deploy"
shopt -s nullglob
origin_files=("${deployment_root}"/*.origin)
if [ "${#origin_files[@]}" -eq 0 ]; then
    deployment="$(ostree rev-parse --repo="${target_repo}" ostree/0/1/0)"
    origin_files=("${deployment_root}/${deployment}.0.origin")
fi

for origin_file in "${origin_files[@]}"; do
    install -d -m 0755 "$(dirname "${origin_file}")"
    python3 - "${origin_file}" <<'PY'
import configparser
import sys

origin_file = sys.argv[1]
target_image_ref = "ostree-unverified-registry:i.anatase.org/anatase:stable"

config = configparser.ConfigParser(interpolation=None)
config.optionxform = str
config.read(origin_file)

if not config.has_section("origin"):
    config.add_section("origin")

for key in ("refspec", "baserefspec"):
    config.remove_option("origin", key)
config.set("origin", "container-image-reference", target_image_ref)

with open(origin_file, "w") as f:
    config.write(f)
PY
done
%end

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
