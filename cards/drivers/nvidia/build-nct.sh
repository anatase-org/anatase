#!/bin/bash

set -eoux pipefail

ARCH=$(uname -m)
FEDORA_VERSION=${FEDORA_VERSION:-${releasever:-43}}

rm -rf build/NVT/centos8/$ARCH
mkdir -p build/NVT/centos8/$ARCH

export DOCKER="podman"
export PATH="$(pwd):$PATH"

# Fix urls
sed -i 's|https://storage.googleapis.com/golang/go|https://dl.google.com/go/go|g' \
    $(grep -rl 'https://storage.googleapis.com/golang/go' ./nvidia-container-toolkit) \
    || true

LIB_VERSION=$(sed -n 's/^LIB_VERSION := //p' \
    ./nvidia-container-toolkit/third_party/libnvidia-container/versions.mk | head -n1)

DIST_DIR="$(pwd)/build/NVT" \
    make -C ./nvidia-container-toolkit/third_party/libnvidia-container LIB_VERSION=$LIB_VERSION centos8-$ARCH
LIB_NAME="nct" DIST_DIR="$(pwd)/build/NVT" \
    make -C ./nvidia-container-toolkit LIB_TAG="" DOCKER=podman centos8-$ARCH
rm -rf ./build/RPMS/f$FEDORA_VERSION/nvt-$ARCH
mkdir -p ./build/RPMS/f$FEDORA_VERSION/nvt-$ARCH
mv build/NVT/centos8/$ARCH/*.rpm ./build/RPMS/f$FEDORA_VERSION/nvt-$ARCH
