#!/bin/bash

set -eoux pipefail

ARCH=$(uname -m)
FEDORA_VERSION=${FEDORA_VERSION:-${releasever:-43}}

rm -rf build/NVT/centos8/$ARCH
mkdir -p build/NVT/centos8/$ARCH

export DOCKER="podman"
export PATH="$(pwd):$PATH"

# Nested Podman cannot configure bridge networking because /proc/sys is
# read-only inside the outer image build. The packaging containers only build
# and extract artifacts, so reuse the outer build container's network.
cat > containers.conf <<'EOF'
[containers]
netns = "host"
EOF
export CONTAINERS_CONF="$(pwd)/containers.conf"

# Upstream mostly honors DOCKER, but a few packaging rules still call docker
# directly. Keep the source tree untouched and provide a local compatibility
# shim in PATH.
cat > docker <<'EOF'
#!/bin/sh
mkdir -p /cache/podman/root /cache/podman/runroot
exec podman \
    --root /cache/podman/root \
    --runroot /cache/podman/runroot \
    "$@"
EOF
chmod +x docker

# Fix urls
sed -i 's|https://storage.googleapis.com/golang/go|https://dl.google.com/go/go|g' \
    $(grep -rl 'https://storage.googleapis.com/golang/go' ./nvidia-container-toolkit) \
    || true

LIB_VERSION=$(sed -n 's/^LIB_VERSION := //p' \
    ./nvidia-container-toolkit/versions.mk | head -n1)

DIST_DIR="$(pwd)/build/NVT" \
    make -C ./nvidia-container-toolkit/third_party/libnvidia-container \
    REVISION=$REVISION LIB_VERSION=$LIB_VERSION centos8-$ARCH
LIB_NAME="nct" DIST_DIR="$(pwd)/build/NVT" \
    make -C ./nvidia-container-toolkit \
    REVISION=$REVISION GIT_COMMIT=$REVISION LIB_TAG="" DOCKER=podman centos8-$ARCH
rm -rf ./build/RPMS/f$FEDORA_VERSION/nvt-$ARCH
mkdir -p ./build/RPMS/f$FEDORA_VERSION/nvt-$ARCH
mv build/NVT/centos8/$ARCH/*.rpm ./build/RPMS/f$FEDORA_VERSION/nvt-$ARCH

# Hand binary RPMs back to Ludos. Source RPMs are intentionally ignored.
if [ -d /rpms ]; then
    find "build/RPMS/f${FEDORA_VERSION}/nvt-$ARCH" -type f \
        \( -name "nvidia-container-toolkit-[0-9]*.rpm" \
        -o -name "nvidia-container-toolkit-base-[0-9]*.rpm" \
        -o -name "libnvidia-container1-[0-9]*.rpm" \
        -o -name "libnvidia-container-tools-[0-9]*.rpm" \) \
        -exec cp -t /rpms {} +
fi
