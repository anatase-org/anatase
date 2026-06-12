#!/bin/bash

set -eoux pipefail

FEDORA_VERSION=${FEDORA_VERSION:-${releasever:-43}}
BUILD_ARM=${BUILD_ARM:-}
SKIP_TARBAL=${SKIP_TARBAL:-}
LEGACY=${LEGACY:-}

# Build only the requested architecture family, but keep x86 driver compat
# sources when building for x86_64.
if [ -n "$BUILD_ARM" ]; then
    ARCHES=("aarch64")
    DRV_ARCHES=("aarch64")
    SKIP_SOURCES="(i386|x86_64)"
else
    ARCHES=("x86_64")
    DRV_ARCHES=("i386" "x86_64")
    SKIP_SOURCES="aarch64"
fi

if [ -n "$LEGACY" ]; then
    prefix="nvidia-580/"
else
    prefix=""
fi

# Prefer the card-provided version, falling back to the packaged spec version.
SPEC_RELEASE=$(sed -n 's/^Version:[[:space:]]\+//p' ${prefix}nvidia-driver/nvidia-driver.spec)
export VERSION=${VERSION:-${version:-$SPEC_RELEASE}}

have_driver_tarballs() {
    local arch="$1"
    local driver_dir="${prefix}nvidia-driver"

    [ -f "$driver_dir/nvidia-kmod-common-${VERSION}.tar.xz" ] || return 1
    [ -f "$driver_dir/nvidia-driver-${VERSION}-${arch}.tar.xz" ] || return 1
    if [ "$arch" = "x86_64" ]; then
        [ -f "$driver_dir/nvidia-driver-${VERSION}-i386.tar.xz" ] || return 1
    fi
}

# The NVIDIA .run installer and generated source tarballs are large, so keep
# them in Ludos' per-card artifact cache between builds.
if [ -z "$SKIP_TARBAL" ]; then
    if [ -d /cache/artifacts ]; then
        find /cache/artifacts -maxdepth 1 -type f -name 'NVIDIA-*.run' \
            -exec cp -n -t ${prefix}nvidia-driver {} +
        find /cache/artifacts -maxdepth 1 -type f -name '*.tar.xz' \
            -exec cp -n -t ${prefix}nvidia-driver {} +
    fi
    if ! have_driver_tarballs "$(uname -m)"; then
        pushd ${prefix}nvidia-driver
        ARCHES="$(uname -m)" bash ./nvidia-generate-tarballs.sh
        popd
    fi
    if [ -d /cache/artifacts ]; then
        find ${prefix}nvidia-driver -maxdepth 1 -type f -name 'NVIDIA-*.run' \
            -exec cp -n -t /cache/artifacts {} +
        find ${prefix}nvidia-driver -maxdepth 1 -type f -name '*.tar.xz' \
            -exec cp -n -t /cache/artifacts {} +
    fi
fi

# Put generated specs in a separate tree so the source checkouts stay clean.
mkdir -p build/SPECS

# The kmod specs consume the driver-generated source tarballs.
cp -f ${prefix}nvidia-driver/nvidia-kmod-common*.tar.xz ${prefix}nvidia-kmod-common/

compile() {
    if [ -n "$LEGACY" ]; then
        target_dir="nvidia-580/$1"
        target_fn="nvidia-580-$1"
    else
        target_dir="$1"
        target_fn="$1"
    fi

    SPEC_TMP=build/SPECS/$target_fn-f${FEDORA_VERSION}/$1.spec
    mkdir -p $(dirname $SPEC_TMP)

    # Rewrite the version and drop sources for architectures not built here.
    cat $target_dir/$1.spec | \
        sed -E "s/^Version:[[:space:]]+.+$/Version: ${VERSION}/gim" | \
        sed -E "s/Source[0-9]+:[[:space:]].+$SKIP_SOURCES.tar.xz//gim" | \
        sed -E "/^Requires:[[:space:]]+nvidia-kmod = /d" \
        > $SPEC_TMP
    spectool -g -C $target_dir $SPEC_TMP
    
    if [ "$1" == "nvidia-driver" ]; then
        arches=("${DRV_ARCHES[@]}")
    else
        arches=("${ARCHES[@]}")
    fi

    for arch in "${arches[@]}"; do
        mkdir -p ./build/MOCK/$arch

        # Cache DNF RPM downloads outside mock's disposable buildroots.
        if [ -d /cache/dnf ]; then
            mkdir -p /cache/dnf/$arch
        fi

        # Mock reads user config from /root/.config/mock.cfg. Bind-mount the
        # shared DNF cache into each mock root so package downloads persist.
        if [ -d /cache/mock ]; then
            mkdir -p /cache/mock ./build/mock-config/$arch /root/.config
            cat > ./build/mock-config/$arch/mock.cfg <<EOF
config_opts['use_bootstrap'] = False
config_opts['basedir'] = '/workspace/build/MOCK'
config_opts['cache_topdir'] = '/cache/mock'
plugin_conf = config_opts.setdefault('plugin_conf', {})
plugin_conf['root_cache_enable'] = True
plugin_conf['package_state_enable'] = True
plugin_conf['bind_mount_enable'] = True
bind_mount_opts = plugin_conf.setdefault('bind_mount_opts', {})
bind_mount_dirs = bind_mount_opts.setdefault('dirs', [])
bind_mount_dirs.append(('/cache/dnf/$arch', '/var/cache/dnf/'))
config_opts['dnf_common_opts'] = [
    '--setopt=cachedir=/var/cache/dnf',
    '--setopt=system_cachedir=/var/cache/dnf',
    '--setopt=keepcache=True',
]
config_opts['dnf.conf'] = config_opts.get('dnf.conf', '') + '''
keepcache=True
cachedir=/var/cache/dnf
system_cachedir=/var/cache/dnf
'''
EOF
            cp ./build/mock-config/$arch/mock.cfg /root/.config/mock.cfg
        fi
        mock -r fedora-${FEDORA_VERSION}-${arch} --arch=$arch \
            --resultdir /workspace/build/RPMS/f${FEDORA_VERSION}/$target_fn-${arch} \
            --sources /workspace/$target_dir --spec /workspace/$SPEC_TMP --verbose
    done
}

compile nvidia-kmod-common
compile nvidia-settings
compile nvidia-modprobe
compile nvidia-persistenced
compile nvidia-driver

echo "$VERSION" > .driver-version

# Hand binary RPMs back to Ludos. Source RPMs are intentionally ignored.
if [ -d /rpms ]; then
    find "build/RPMS/f${FEDORA_VERSION}" -type f \
        \( -name "libnvidia-cfg-*.rpm" \
        -o -name "libnvidia-fbc-*.rpm" \
        -o -name "libnvidia-gpucomp-*.rpm" \
        -o -name "libnvidia-ml-*.rpm" \
        -o -name "nvidia-libXNVCtrl-[0-9]*.rpm" \
        -o -name "nvidia-settings-[0-9]*.rpm" \
        -o -name "nvidia-driver-*.rpm" \
        -o -name "nvidia-kmod-common-*.rpm" \
        -o -name "nvidia-modprobe-[0-9]*.rpm" \
        -o -name "nvidia-persistenced-[0-9]*.rpm" \
        -o -name "xorg-x11*.rpm" \) \
        ! -name "*.src.rpm" \
        ! -name "*debuginfo*.rpm" \
        ! -name "*debugsource*.rpm" \
        ! -name "*-devel-*.rpm" \
        -exec cp -t /rpms {} +
fi
