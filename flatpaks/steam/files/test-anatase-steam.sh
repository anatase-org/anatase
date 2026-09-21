#!/bin/bash
set -euo pipefail

launcher="${ANATASE_STEAM:-files/anatase-steam}"
test_root=$(mktemp -d)
trap 'rm -rf -- "$test_root"' EXIT

# Run the launcher's real setup code without starting Steam or its helpers.
sed '/^# Skip OOTB/,$d' "$launcher" > "$test_root/setup"
cat > "$test_root/run-setup" <<'EOF'
#!/bin/bash
source "$ANATASE_TEST_SETUP"
printf '%s\n' "$XDG_CONFIG_HOME" "$XDG_DATA_HOME" \
    "$ANATASE_STEAM_SANDBOX_DATA_HOME" > "$ANATASE_TEST_OUTPUT"
EOF
chmod +x "$test_root/run-setup"

# The old fallback asks flatpak-spawn for the host environment.
mkdir -p "$test_root/bin"
cat > "$test_root/bin/flatpak-spawn" <<'EOF'
#!/bin/sh
[ "$1" = --host ] || exit 1
shift
exec env -u XDG_DATA_HOME "$@"
EOF
chmod +x "$test_root/bin/flatpak-spawn"

home="$test_root/permission-home"
private_config="$home/.var/app/org.anatase.Steam/config"
private_data="$home/.var/app/org.anatase.Steam/data"
host_config="$test_root/host-config"
host_data="$test_root/host-data"
mkdir -p "$private_config/StardewValley" "$private_data" \
    "$host_config/StardewValley" "$host_data"
printf 'new private save\n' > "$private_config/StardewValley/save"
printf 'existing host save\n' > "$host_config/StardewValley/save"
touch "$private_data/.anatase-config-home-migrated"
cat > "$test_root/permission-info" <<'EOF'
[Context]
features=host-xdg-dirs;
filesystems=home;
EOF

ANATASE_TEST_SETUP="$test_root/setup" \
ANATASE_TEST_OUTPUT="$test_root/permission-output" \
FLATPAK_INFO="$test_root/permission-info" \
HOME="$home" XDG_CONFIG_HOME="$host_config" XDG_DATA_HOME="$host_data" \
PATH="$test_root/bin:$PATH" "$test_root/run-setup"
printf '%s\n' "$host_config" "$host_data" "$private_data" > "$test_root/expected"
diff -u "$test_root/expected" "$test_root/permission-output"
test -e "$private_data/.anatase-host-xdg-config-migrated"
test "$(cat "$host_config/StardewValley/save")" = 'existing host save'
test "$(cat "$host_config/StardewValley.bak/save")" = 'new private save'

# The new marker prevents duplicate conflict backups on later launches.
ANATASE_TEST_SETUP="$test_root/setup" \
ANATASE_TEST_OUTPUT="$test_root/permission-output" \
FLATPAK_INFO="$test_root/permission-info" \
HOME="$home" XDG_CONFIG_HOME="$host_config" XDG_DATA_HOME="$host_data" \
PATH="$test_root/bin:$PATH" "$test_root/run-setup"
test ! -e "$host_config/StardewValley.bak.1"

home="$test_root/fallback-home"
private_config="$home/.var/app/org.anatase.Steam/config"
private_data="$home/.var/app/org.anatase.Steam/data"
mkdir -p "$private_config/StardewValley" "$private_data"
printf 'private save\n' > "$private_config/StardewValley/save"
cat > "$test_root/fallback-info" <<'EOF'
[Context]
features=!host-xdg-dirs;
filesystems=~/.steam:create;xdg-data/Steam:create;home;
EOF

ANATASE_TEST_SETUP="$test_root/setup" \
ANATASE_TEST_OUTPUT="$test_root/fallback-output" \
FLATPAK_INFO="$test_root/fallback-info" \
HOME="$home" XDG_CONFIG_HOME="$private_config" XDG_DATA_HOME="$private_data" \
PATH="$test_root/bin:$PATH" "$test_root/run-setup"
printf '%s\n' "$home/.config" "$home/.local/share" "$private_data" > "$test_root/expected"
diff -u "$test_root/expected" "$test_root/fallback-output"
test ! -e "$home/.config/StardewValley"
test "$(cat "$private_config/StardewValley/save")" = 'private save'
test ! -e "$private_data/.anatase-config-home-migrated"
test ! -e "$private_data/.anatase-host-xdg-config-migrated"

# Granting the permission later is the only step that migrates the save.
ANATASE_TEST_SETUP="$test_root/setup" \
ANATASE_TEST_OUTPUT="$test_root/permission-after-fallback-output" \
FLATPAK_INFO="$test_root/permission-info" \
HOME="$home" XDG_CONFIG_HOME="$home/.config" XDG_DATA_HOME="$home/.local/share" \
PATH="$test_root/bin:$PATH" "$test_root/run-setup"
test "$(cat "$home/.config/StardewValley/save")" = 'private save'
test -e "$private_data/.anatase-host-xdg-config-migrated"
