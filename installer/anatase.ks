# Kickstart defaults for the interactive Anatase installer.

# Define our storage shape
reqpart --add-boot
part btrfs.01 --size=1024 --grow
btrfs none --label=anatase btrfs.01
btrfs / --subvol --name=root LABEL=anatase
btrfs /var --subvol --name=var LABEL=anatase
btrfs /var/home --subvol --name=home LABEL=anatase

ostreesetup --osname="anatase" --remote="anatase" --url="file:///ostree/repo" --ref="master" --nogpg
