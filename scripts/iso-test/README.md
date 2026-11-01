# Local ISO acceptance test

From the repository root:

```sh
scripts/test_iso.sh /path/to/anatase.iso
scripts/test_iso.sh --arm /path/to/anatase-arm.iso
```

The test enrolls the ISO's signing key through MokManager, checks the live
KDE desktop and every bundled Flatpak, installs through Anaconda, completes
Plasma Setup, authenticates through Plasma Login, and repeats desktop checks
before and after another reboot. Btrfs checks use blocking read-only scrubs,
device error counters, and kernel logs. No additional applications are downloaded.

On Ubuntu, install the dependencies yourself:

```sh
sudo apt-get install python3 python3-pil tesseract-ocr tesseract-ocr-eng \
  qemu-system-x86 qemu-system-arm qemu-utils ovmf qemu-efi-aarch64
```

On Fedora, with QEMU and firmware already installed:

```sh
sudo dnf install python3-pillow tesseract tesseract-langpack-eng
```

OCR runs directly through the host's Tesseract installation.
It uses one OpenMP worker to share CI CPUs with QEMU. A slow OCR frame is
retried within the enclosing UI deadline, with its screenshot and timeout
record retained. Once the enrolled ISO reaches Linux's boot console, the
harness polls the guest agent without OCRing the boot messages.
The test never installs host packages automatically.
The guest needs its bundled QEMU Guest Agent, Python/Pillow, dbus-python,
pyatspi, and normal desktop/system tools; a missing capability fails explicitly.

Each run uses a private directory under `cache/iso-tests/` with a fresh sparse
40 GiB disk and Microsoft-enrolled firmware variables. Existing development
VM disks and variables are never reused. Allow at least 20 GiB free storage;
run directories must be on disk. Logs, screenshots, accessibility trees,
installer output, disk, firmware state, and `results.json` survive failure and
success. Exit status is zero only when all required checks pass.

Defaults are headless software graphics, 8 GiB RAM and four CPUs. The Virtio
display explicitly advertises 1280 × 800 through EDID (`xres=1280,yres=800`),
including with the GL override. GTK runs disable automatic zoom-to-fit so the
window requests the guest's native content size; window decorations and host
display scaling still apply. Set `QEMU_DISPLAY=gtk,zoom-to-fit=on` to opt into
scaling. Native guests use KVM when available; otherwise QEMU uses TCG and
reports it. ARM uses `neoverse-n1` under TCG to avoid the edk2 2025.11
firmware hang with `-cpu max`. ARM firmware runs without TrustZone (`secure=on`
would hang Ubuntu's AAVMF at EL3); UEFI Secure Boot uses the enrolled variable
store and is verified inside the guest. Both pflash and qemuvars firmware use
KVM when available. QEMU provides user-mode networking.

Use `scripts/test_iso.sh --help` for all overrides. Common examples:

```sh
QEMU_DISPLAY=gtk scripts/test_iso.sh ISO
QEMU_ACCEL=tcg VM_CPUS=4 ISO_TEST_BOOT_TIMEOUT=2400 scripts/test_iso.sh ISO
QEMU_OVMF_CODE=/path/to/code.fd QEMU_OVMF_VARS_TEMPLATE=/path/to/vars.fd \
  scripts/test_iso.sh ISO
```

`VM_MEMORY`, `VM_CPUS`, `VM_DISK_SIZE`, `QEMU_CPU`, `QEMU_MACHINE`, `QEMU_VGA`,
and the existing GL/Venus overrides are supported. `ISO_TEST_OUTPUT` changes
the artifact parent directory. `ISO_TEST_TIMEOUT`, `ISO_TEST_BOOT_TIMEOUT`,
`ISO_TEST_UI_TIMEOUT`, `ISO_TEST_INSTALL_TIMEOUT`, `ISO_TEST_APP_TIMEOUT`, and
`ISO_TEST_SCRUB_TIMEOUT` are bounded deadlines in seconds. Do not provide
`VM_DISK`, `VM_OVMF_VARS`, `VM_RESET_DISK`, or `SIMULATE_WINDOWS`.
UI/application defaults are 180/120 seconds with KVM and 600/600 seconds
with TCG; boot and installation deadlines also increase for TCG.

The live desktop authorizes a test-only QEMU Guest Agent service override through
`pkexec`. This gives diagnostics the access needed for accessibility and health
checks; SELinux remains enforcing and applications launch through the desktop
user's systemd manager with their normal sandbox permissions. The override is
also placed in the disposable installed deployment. Screenshots and private
artifacts contain a generated test account; treat the run directory accordingly.

Unknown applications/extensions or unavailable selectors fail rather than skip.
Application failures are recorded individually, and remaining applications are
still attempted. Runtime extensions are checked through their consuming browser.

Stage names, VM/acceleration status, and the final result print to stdout.
Detailed output is limited to failures: health failures print their errors and
unexpected crash summaries; successful check details and allowed crashes stay quiet. Other failed
stages/applications include short screen, journal error, and application/installer
log excerpts (20–30 lines each). QEMU/serial excerpts are shown when the guest
helper has not connected. Full diagnostics remain in the run directory and
Actions artifacts.

Coredumps normally fail health checks. The known SIGABRT from
`/usr/libexec/xdg-desktop-portal-kde` running as `plasmalogin` or `plasma-setup` is
allowed; its metadata and coredump details are saved in results. Exceptions are
centralized in `CRASH_EXCEPTIONS` at the top of `guest.py`.
Crashes of the same executable under the desktop user, or with another signal,
remain fatal.

Run protocol, failure-path, and reboot-boundary checks with:

```sh
python3 -m unittest discover -s scripts/iso-test -v
```

These checks supplement complete acceptance runs with real ISOs; they do not
replace them.

The `Build Anatase ISO` workflow tests both architectures after uploading each
ISO, so a failed test still leaves the ISO available for offline checks. Each
job first removes its build containers, images, volumes, and intermediate ISO
files while keeping `installer.iso`, then installs native Ubuntu dependencies.
Tests use `/usr/bin/python3`, headless software graphics, KVM where available,
and TCG otherwise. CI explicitly selects Ubuntu's Microsoft-enrolled OVMF/AAVMF
code and variables template for each architecture. Failures fail the job and
print diagnostics to its console.
JSON reports, logs, and screenshots are also retained as `iso-test-<channel>-<arch>`
artifacts for seven days; VM disks are excluded from uploads. The separate ARM
disk-image build is unchanged.
