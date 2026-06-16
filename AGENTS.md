This repository contains the source code for Anatase, a bootc based distribution. Anatase is built using ludos, a python tool vendored in this repository under ./ludos and installed editable under venv/bin/ludos, with source code under ./ludos/src/ludos where changes are reflected instantly.

Ludos uses podman and so will you for running containers for testing. It builds an orchestrator image to run fedora commands, and it is available in user storage with the name orchestrator, it can be used for rpm / cargo commands.

You can use `ludos build anatase.yml` to build the distribution. When the user posts an error, the full transaction will be in ./logs/ludos.log (or ludos.log.N if another run rotated it).

Anatase uses the concept of manifests and cards to build images. ./anatase.yml is the manifest which specifies which cards to use, and e.g., ./cards/base/scx/card.yml is a build card for scx. It lists the runtime dependencies of the packages, the build dependencies that cannot be automatically infered, the specs locations, and how to update them.

Here are some other commands:
```bash
# Fork a spec so we can build it instead
ludos package fork \
    https://src.fedoraproject.org/rpms/xorg-x11-server-Xwayland \
    ./cards/gaming/xserver \
    --card ./cards/gaming/gamemode.yml

# For packages with override patches
# You can fill in the patch: field with the following:
# ludos patch init <card>:<path to spec or spec>
ludos patch init cards/gaming/gamemode.yml:xserver \
    https://gitlab.freedesktop.org/xorg/xserver --ref 'xwayland-${spec:Version}'

# You can checkout the current override patch with the current upstream patch hash
# under ./patchwork/xserver in branch ludos so you can commit changes to it
ludos patch checkout cards/gaming/gamemode.yml:xserver
# Then, to pull them back you can use, which will update the patch file
ludos patch apply cards/gaming/gamemode.yml:xserver

# Build the card itself after adding patches (.yml or /card.yml suffix is optional)
# and skip the image building, package resolution, and other cards
# skip the spec at the end to build all of the card specs
ludos build anatase.yml --card cards/gaming/gamemode:xserver
```