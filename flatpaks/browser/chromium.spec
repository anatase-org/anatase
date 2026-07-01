# macro for el10 minor version
%if 0%{?rhel} == 10
%global rhel_minor_version %(echo %{dist} | sed -n 's/.*el10_\\([0-9]\\+\\).*/\\1/p')
%endif

%define _lto_cflags %{nil}
%global _default_patch_fuzz 2

# enable|disable system build flags
%global system_build_flags 0

%global numjobs %{_smp_build_ncpus}

# official builds have less debugging and go faster... but we have to shut some things off.
%global official_build 1

# enable|disble use_custom_libcxx
%global use_custom_libcxx 0
%if 0%{?rhel}
# no libcxx in el
%global use_custom_libcxx 1
%endif

# enable|disble bootstrap
%global bootstrap 0
# workaround for old gn on el9, it causes build error: unknown function filter_labels_include()
%if 0%{?rhel} == 9
%global bootstrap 1
%endif

# Fancy build status, so we at least know, where we are..
# %1 where
# %2 what
%global build_target() \
	export NINJA_STATUS="[%2:%f/%t] " ; \
	ninja -j %{numjobs} -C '%1' '%2'

# enable|disable chrome_management_service
%global build_chrome_management_service 1
%if 0%{?flatpak}
%global build_chrome_management_service 0
%endif

# enable|disable chromedriver
%global build_chromedriver 1
%if 0%{?flatpak}
%global build_chromedriver 0
%endif

# enable|disable headless client build
%global build_headless 1
%if 0%{?flatpak}
%global build_headless 0
%endif

# set nodejs_version
%global nodejs_version v22.22.0
%ifarch x86_64
%global nodejs_arch x64
%endif
%ifarch aarch64
%global nodejs_arch arm64
%endif

# enable gtk4 for fedora and el>9
%global gtk_version 4
%if 0%{?rhel} == 9
%global gtk_version 3
%endif

%if 0%{?rhel} == 8
%global chromium_pybin /usr/bin/python3.9
%else
%global chromium_pybin %{__python3}
%endif

# va-api only supported in rhel >= 9 and fedora
%global use_vaapi 1

# v4l2_codec only enable for fedora aarch64
%global use_v4l2_codec 0

# libva is too old on el8
%if 0%{?rhel} == 8
%global use_vaapi 0
%endif

# enable v4l2 and disable vaapi for aarch64 platform
%ifarch aarch64
%if 0%{?fedora} >= 36
%global use_vaapi 0
%global use_v4l2_codec 1
%endif
%endif

# Workaround for https://bugzilla.redhat.com/show_bug.cgi?id=2239523
# Disable BTI until this is fixed upstream.
%global disable_bti 0
%ifarch aarch64
%if 0%{?fedora}
%global optflags %(echo %{optflags} | sed 's/-mbranch-protection=standard /-mbranch-protection=pac-ret /')
%global disable_bti 1
%endif
%endif

# Disabled because of Google, starting with Chromium 88.
%global userestrictedapikeys 0

# We can still use the api key though. For now.
%global useapikey 1

# Link against noopenh264 for WebRTC H.264 support.
%global noopenh264 1

# Leave this alone, please.
%global chromebuilddir out/Release
%global headlessbuilddir out/Headless
%global remotingbuilddir out/Remoting

# enable|disable debuginfo
%global enable_debug 1
# disable debuginfo due to a bug in debugedit on el7
# error: canonicalization unexpectedly shrank by one character
# https://bugzilla.redhat.com/show_bug.cgi?id=304121
%if ! %{enable_debug}
%global debug_package %{nil}
%global debug_level 0
%else
%global debug_level 1
# workaround for the error empty file debugsource
%undefine _debugsource_packages
%endif

%global chromium_menu_name Anatase Browser
%global chromium_path %{_libdir}/chromium-browser
%global crd_path %{_libdir}/chrome-remote-desktop

# We don't want any libs in these directories to generate Provides
# Requires is trickier.

# To generate this list, go into %%{buildroot}%%{chromium_path} and run
# for i in `find . -name "*.so" | sort`; do NAME=`basename -s .so $i`; printf "$NAME|"; done
# for RHEL7, append libfontconfig to the end
# make sure there is not a trailing | at the end of the list
# We always filter provides. We only filter Requires when building shared.
%global __provides_exclude_from ^(%{chromium_path}/.*\\.so|%{chromium_path}/.*\\.so.*)$
%global __requires_exclude ^(%{chromium_path}/.*\\.so|%{chromium_path}/.*\\.so.*)$

# enable|disable control flow integrity support
%global cfi 0
%ifarch x86_64 aarch64
%global cfi 1
%endif

# enable qt backend
%global enable_qt 1
%if %{enable_qt}
%if 0%{?rhel} > 9 || 0%{?fedora} > 39
%global use_qt6 1
%global use_qt5 1
%else
%global use_qt6 0
%global use_qt5 1
%endif
%else
%global use_qt6 0
%global use_qt5 0
%endif

# bundle re2, jsoncpp, woff2 - build errors with use_custom_libcxx=true
%global bundlere2 1
%global bundlejsoncpp 1
%global bundlewoff2 1
%global bundlelibaom 1
%global bundlelibavif 1
%global bundlesnappy 1
%global bundlezstd 1
%global bundleicu 1
%global bundledav1d 1
%global bundlelibwebp 1
%global bundlecrc32c 1
%global bundleharfbuzz 1
%global bundlelibpng 1
%global bundlelibjpeg 1
%global bundlefreetype 1
%global bundlelibdrm 1
%global bundlefontconfig 1
%global bundleffmpegfree 1
%global bundlehighway 1
# openjpeg2, need to update to 2.5.x
%global bundlelibopenjpeg2 1
%global bundlelibtiff 1
# libxml2, need to update to 2.14.x for bz#2368923
%global bundlelibxml 1
%global bundlepylibs 0
%global bundlelibxslt 1
%global bundleflac 1
%global bundledoubleconversion 1
%global bundlelibXNVCtrl 1
%global bundlelibusbx 1
%global bundlelibsecret 1
%global bundlelcms2 1
%global bundlesimdutf 1

# workaround for build error
# disable bundleminizip for Fedora > 39 due to switch to minizip-ng
# disable bundleminizip for epel and Fedora39 due to old minizip version
%global bundleminizip 1

### From 2013 until early 2021, Google permitted distribution builds of
### Chromium to access Google APIs that added significant features to
### Chromium including, but not limited to, Sync and geolocation.
### As of March 15, 2021, any Chromium builds which pass client_id and/or
### client_secret during build will prevent end-users from signing into their
### Google account.

### With Chromium 88, I have removed the calls to "google_default_client_id"
### and "google_default_client_secret" to comply with their changes.

### Honestly, at this point, you might be better off looking for a different
### FOSS browser.

### Google API keys (see http://www.chromium.org/developers/how-tos/api-keys)
### Note: These are for Fedora use ONLY.
### For your own distribution, please get your own set of keys.
### http://lists.debian.org/debian-legal/2013/11/msg00006.html
%if %{useapikey}
%global api_key AIzaSyDUIXvzVrt5OkVsgXhQ6NFfvWlA44by-aw
%else
%global api_key %nil
%endif

%if %{userestrictedapikeys}
%global default_client_id 449907151817.apps.googleusercontent.com
%global default_client_secret miEreAep8nuvTdvLums6qyLK
%global chromoting_client_id 449907151817-8vnlfih032ni8c4jjps9int9t86k546t.apps.googleusercontent.com 
%else
%global default_client_id %nil
%global default_client_secret %nil
%global chromoting_client_id %nil
%endif

Name:	chromium
Version: 149.0.7827.200
Release: 1%{?dist}
Summary: A WebKit (Blink) powered web browser that Google doesn't want you to use
Url: http://www.chromium.org/Home
License: BSD-3-Clause AND LGPL-2.1-or-later AND Apache-2.0 AND IJG AND MIT AND GPL-2.0-or-later AND ISC AND OpenSSL AND (MPL-1.1 OR GPL-2.0-only OR LGPL-2.0-only)

# Use /etc/chromium for initial_prefs
Patch1: chromium-115-initial_prefs-etc-path.patch

# debian patches
# disable font-test 
Patch20: chromium-disable-font-tests.patch
# don't download binary blob
Patch21: chromium-123-screen-ai-service.patch

# Fix link error when building with system libcxx
Patch22: chromium-131-fix-qt-ui.patch

# disable enterprise_companion_integration_tests due to Unresolved dependencies
Patch31: chromium-145-disable-enterprise_companion_integration_tests.patch

# patch for Failed NodeJS version check
Patch92: chromium-138-checkversion-nodejs.patch

# fix build error
Patch93: chromium-141-csss_style_sheet.patch

# revert the patch to fix the build error: "ld.lld: error: undefined symbol: __sanitizer_set_death_callback"
Patch94: chromium-148-v8-sanitize-build-error.patch

# FTBFS - error: cannot find attribute `sanitize` in this scope
#    --> ../../third_party/crabbyavif/src/src/capi/io.rs:210:41
#     |
# 210 |     #[cfg_attr(feature = "disable_cfi", sanitize(cfi = "off"))]
Patch96: chromium-142-crabbyavif-ftbfs-old-rust.patch

# add correct path for Qt6Gui header and libs
Patch150: chromium-124-qt6.patch

# fix FTBFS caused by missing include file on aarch64/ppc64le
Patch300: chromium-145-swiftshader-missing-include.patch

# Fix rhbz#2387446, FTBFS with rust-1.89.0
Patch310: chromium-139-rust-FTBFS-suppress-warnings.patch

# enable fstack-protector-strong
Patch311: chromium-123-fstack-protector-strong.patch

# error with old rustc
Patch315: chromium-145-rustc-ftbfs.patch

# llvm <= 22
# clang++: error: unknown argument: '-fno-lifetime-dse'
Patch316: chromium-149-clang++-unknown-argument.patch

Patch318: memory-allocator-dcheck-assert-fix.patch

# compile swiftshader against llvm-16.0
Patch319: chromium-143-swiftshader-llvm-16.0.patch

# Fix build error on fedora aarch64
Patch320: chromium-149-aarch64-log-error.patch

# Workaround for https://bugzilla.redhat.com/show_bug.cgi?id=2239523
# https://bugs.chromium.org/p/chromium/issues/detail?id=1145581#c60
# Disable BTI until this is fixed upstream.
Patch352: chromium-117-workaround_for_crash_on_BTI_capable_system.patch

# workaround for build error on aarch64
Patch353: chromium-127-aarch64-duplicate-case-value.patch

# fix build error: no member named 'hardware_destructive_interference_size' in namespace 'std'
Patch355: chromium-130-hardware_destructive_interference_size.patch

# fix build error:
# ../../build/modules/linux-x64/module.modulemap:11:12: error: header '../../linux/debian_bullseye_amd64-sysroot/usr/include/alloca.h' not found
Patch356: chromium-141-use_libcxx_modules.patch

# error: no matching member function for call to 'Append'
Patch357: chromium-134-type-mismatch-error.patch

# set clang_lib path
Patch358: chromium-144-rust-clanglib.patch

# fix FTBFS with rustc 1.95
Patch359: chromium-148-rust-1.95-bytemuck-ftbfs.patch

# flatpak sandbox patches from
# https://github.com/flathub/org.chromium.Chromium/tree/master/patches/chromium
Patch500: flatpak-Add-initial-sandbox-support.patch
Patch501: flatpak-Adjust-paths-for-the-sandbox.patch

# Patches from ungoogle chromium, https://github.com/ungoogled-software/ungoogled-chromium
# remove rollup binary, build with wasm-rollup 
Patch520: build-with-wasm-rollup.patch
Patch521: disable-ai.patch
Patch522: chromium-149-anatase-branding.patch

# Upstream patches
# Fix auto dark mode
Patch600: chromium-148-Add-luminance-ratio-feature-for-dark-mode-image-classification.patch
Patch601: chromium-148-Prefix-dark-mode-decision-tree-threshold-constants-with-kFeature.patch
Patch602: chromium-148-Add-saturation-feature-for-dark-mode-image-classification.patch
Patch603: chromium-148-Add-AutoDarkModeSkipImages-flag-to-bypass-image-dark-mode.patch
Patch604: chromium-148-Add-chromatic-pixels-feature-based-on-muted-hue-colors-for-dark-mode.patch
Patch605: chromium-149-Make-dark-mode-apply-filter-to-images-irrespective-of-layout-zoom.patch
Patch606: chromium-149-use-64px-css-pixels-absolute-threshold-for-dark-image-classification.patch

Source0: https://commondatastorage.googleapis.com/chromium-browser-official/chromium-%{version}-lite.tar.xz
Source2: chromium.conf
Source3: chromium-browser.sh
Source4: chromium-browser.desktop
# GNOME stuff
Source9: chromium-browser.xml
Source10: chromium-browser.appdata.xml
Source11: master_preferences

Source12: https://nodejs.org/dist/%{nodejs_version}/node-%{nodejs_version}-linux-%{nodejs_arch}.tar.xz
# Disable AI Mode settings
Source14: disable-ai.json
Source15: chromium-browser-24.png
Source16: chromium-browser-48.png
Source17: chromium-browser-64.png
Source18: chromium-browser-128.png
Source19: chromium-browser-256.png
Source20: chromium-browser-16.png
Source21: chromium-browser-32.png
Source22: browser.svg

BuildRequires: clang
BuildRequires: clang-tools-extra
BuildRequires: llvm
BuildRequires: lld

%if ! %{use_custom_libcxx}
BuildRequires: libcxx-devel
%endif

%if 0%{?rhel} && 0%{?rhel} <= 9
BuildRequires: gcc-toolset-14-libatomic-devel
%endif

BuildRequires: rustc
BuildRequires: rustfmt
BuildRequires: bindgen-cli

BuildRequires:	alsa-lib-devel
BuildRequires:	atk-devel
BuildRequires:	bison
BuildRequires:	cups-devel
BuildRequires:	dbus-devel
BuildRequires:	desktop-file-utils
BuildRequires:	expat-devel
BuildRequires:	flex
BuildRequires:	fontconfig-devel
BuildRequires:	glib2-devel
BuildRequires:	glibc-devel
BuildRequires:	gperf

%if %{use_qt5}
BuildRequires: pkgconfig(Qt5Core)
BuildRequires: pkgconfig(Qt5Widgets)
%endif

%if %{use_qt6}
BuildRequires: pkgconfig(Qt6Core)
BuildRequires: pkgconfig(Qt6Widgets)
%endif

BuildRequires: compiler-rt

BuildRequires: libatomic
BuildRequires:	libcap-devel
BuildRequires:	libcurl-devel

BuildRequires:	libgcrypt-devel
BuildRequires:	libudev-devel
BuildRequires:	libuuid-devel

%if 0%{?fedora} >= 37 || 0%{?rhel} > 9
BuildRequires:	libusb-compat-0.1-devel
%else
BuildRequires:	libusb-devel
%endif

BuildRequires:	libutempter-devel
BuildRequires:	libXdamage-devel
BuildRequires:	libXtst-devel
BuildRequires:	xcb-proto
BuildRequires:	mesa-libgbm-devel

%if ! %{bootstrap}
BuildRequires: gn
%endif

BuildRequires:	nss-devel >= 3.26
BuildRequires:	pciutils-devel
BuildRequires:	pulseaudio-libs-devel

# For screen sharing on Wayland
# pipewire is old on el8, chromium needs new version, disable it temporary
%if 0%{?fedora} || 0%{?rhel} > 8
BuildRequires:	pipewire-devel
%endif

# for /usr/bin/appstream-util
BuildRequires: libappstream-glib

%if %{bootstrap}
# gn needs these
BuildRequires: libstdc++-static
%endif

BuildRequires:	bzip2-devel
BuildRequires:	dbus-glib-devel
BuildRequires:	libffi-devel
# For eu-strip
BuildRequires:	elfutils
BuildRequires:	elfutils-libelf-devel

# One of the python scripts invokes git to look for a hash. So helpful.
BuildRequires:	git-core
BuildRequires:	hwdata
BuildRequires:	kernel-headers
BuildRequires:	which

BuildRequires:	libudev-devel

%if %{use_vaapi}
BuildRequires:	libva-devel
%endif

BuildRequires:	libxshmfence-devel

# Same here, it seems.
# BuildRequires: libyuv-devel
BuildRequires:	mesa-libGL-devel

BuildRequires: %{chromium_pybin}
%if %{gtk_version} == 4
BuildRequires: pkgconfig(gtk4)
BuildRequires: pkgconfig(xcursor)
BuildRequires: pkgconfig(xi)
BuildRequires: pkgconfig(xrender)
BuildRequires: pkgconfig(xscrnsaver)
BuildRequires: pkgconfig(xshmfence)
BuildRequires: pkgconfig(xt)
BuildRequires: pkgconfig(xtst)
BuildRequires: pkgconfig(x11)
BuildRequires: pkgconfig(xcb-dri3)
BuildRequires: pkgconfig(xcb-proto)
Requires: gtk4
%else
BuildRequires: pkgconfig(gtk+-3.0)
# GTK modules it expects to find for some reason.
Requires: libcanberra-gtk3%{_isa}
%endif

# Build deps of Chromium proper which are often transitively pulled in by toolkits (GTK, Qt),
# but are still required without them.
BuildRequires: pkgconfig(atspi-2)
BuildRequires: pkgconfig(atk-bridge-2.0)
BuildRequires: pkgconfig(pangocairo)
BuildRequires: pkgconfig(xkbcommon)
BuildRequires: pkgconfig(xcomposite)
BuildRequires: pkgconfig(xrandr)
BuildRequires: wayland-devel

%if ! %{bundlepylibs}
%if 0%{?fedora} || 0%{?rhel} >= 8
BuildRequires: python3-jinja2
%else
BuildRequires: python-jinja2
%endif
%endif

BuildRequires: speech-dispatcher-devel
BuildRequires: zlib-devel

%if 0%{?noopenh264}
BuildRequires: pkgconfig(openh264)
%endif

# remote desktop needs this
BuildRequires:	pam-devel
BuildRequires:	systemd

# using the built from source version on aarch64
BuildRequires: ninja-build

# Yes, java is needed as well..
%if %{build_headless}
BuildRequires:	java-openjdk-headless
%endif

BuildRequires: libevdev-devel

# esbuild is needed
BuildRequires: golang-github-evanw-esbuild

# There is a hardcoded check for nss 3.26 in the chromium code (crypto/nss_util.cc)
Requires: nss%{_isa} >= 3.26
Requires: nss-mdns%{_isa}

%if 0%{?fedora} && %{undefined flatpak}
# This enables support for u2f tokens
Requires: u2f-hidraw-policy
%endif

Requires: chromium-common%{_isa} = %{version}-%{release}

ExclusiveArch: x86_64 aarch64

# Bundled bits (I'm sure I've missed some)
Provides: bundled(bintrees) = 1.0.1
# This is a fork of openssl.
Provides: bundled(boringssl)
Provides: bundled(brotli) = 222564a95d9ab58865a096b8d9f7324ea5f2e03e
%if %{bundlesimdutf} 
Provides: bundled(simdutf) = 7.0.0
%endif
Provides: bundled(bspatch) = 465265d0d473d107b76e74d969199eaf2cdc8750
Provides: bundled(colorama) = 0.4.6
Provides: bundled(crashpad) = 8f131016b21d986c38ca4a0f091403dbb822d636
Provides: bundled(expat) = 2.7.1
Provides: bundled(fdmlibm) = c512d6173f33c6b8301d3fba9384edc9fc1f9e45

# Don't get too excited. MPEG and other legally problematic stuff is stripped out.
%if %{bundleffmpegfree}
Provides: bundled(ffmpeg) = 7.1.git
%endif

%if %{bundlelibaom}
Provides: bundled(libaom) = 3.12.1
%endif

%if %{bundlefontconfig}
Provides: bundled(fontconfig) = 8cf0ce700a8abe0d97ace4bf7efc7f9534b729ba
%endif

%if %{bundlefreetype}
Provides: bundled(freetype) = 2.13.3.230.ge07e56c7f
%endif

%if %{bundleharfbuzz}
Provides: bundled(harfbuzz) = 11.0.0.97
%endif

Provides: bundled(hunspell) = 6d7d19f

%if %{bundleicu}
Provides: bundled(icu) = 74.2
%endif

Provides: bundled(leveldb) = 1.23
Provides: bundled(libaddressinput) = 2610f7b104

%if %{bundlelibdrm}
Provides: bundled(libdrm) = 2.4.122
%endif

Provides: bundled(libjingle) = 5493b8a59deb16cf0481e24707a0ed72d19047dc

%if %{bundlelibjpeg}
Provides: bundled(libjpeg-turbo) = 3.1.0
%endif

Provides: bundled(libphonenumber) = 140dfeb81b753388e8a672900fb7a971e9a0d362

%if %{bundlelibpng}
Provides: bundled(libpng) = 1.6.43
%endif

Provides: bundled(libsrtp) = fd08747fa6800b321d53e15feb34da12dc697dee

%if %{bundlelibusbx}
Provides: bundled(libusbx) = 1.0.17
%endif

Provides: bundled(libvpx) = 1.6.0

%if %{bundlelibwebp}
Provides: bundled(libwebp) = 0.6.0
%endif

%if %{bundlelibxml}
Provides: bundled(libxml) = 2.14.2
%endif

%if %{bundlelibXNVCtrl}
Provides: bundled(libXNVCtrl) = 302.17
%endif
Provides: bundled(libyuv) = 1909
Provides: bundled(lzma) = 24.09

Provides: bundled(opus) = 55513e81

Provides: bundled(ots) = 8d70cffebbfa58f67a5c3ed0e9bc84dccdbc5bc0
Provides: bundled(protobuf) = 3.0.0.beta.3
Provides: bundled(qcms) = 4

%if %{bundlere2}
Provides: bundled(re2)
%endif

Provides: bundled(sfntly) = 04740d2600193b14aa3ef24cd9fbb3d5996b9f77
Provides: bundled(skia)
Provides: bundled(SMHasher) = 0
Provides: bundled(snappy) = 1.1.4.head
Provides: bundled(speech-dispatcher) = 0.7.1
Provides: bundled(sqlite) = 3.17patched
Provides: bundled(superfasthash) = 0
Provides: bundled(talloc) = 2.0.1
Provides: bundled(usrsctp) = 0
Provides: bundled(v8) = 5.9.211.31
Provides: bundled(webrtc) = 90usrsctp
Provides: bundled(woff2) = 445f541996fe8376f3976d35692fd2b9a6eedf2d
Provides: bundled(xdg-mime)
Provides: bundled(xdg-user-dirs)
# Provides: bundled(zlib) = 1.2.11

%if %{undefined flatpak}
# For selinux scriptlet
Requires(post): /usr/sbin/semanage
Requires(post): /usr/sbin/restorecon
%endif

%description
Chromium is an open-source web browser, powered by WebKit (Blink).

%package common
Summary: Files needed for both the headless_shell and full Chromium

%description common
%{summary}.

%package -n chromedriver
Summary: WebDriver for Google Chrome/Chromium
Requires: chromium-common%{_isa} = %{version}-%{release}

%description -n chromedriver
WebDriver is an open source tool for automated testing of webapps across many
browsers. It provides capabilities for navigating to web pages, user input,
JavaScript execution, and more. ChromeDriver is a standalone server which
implements WebDriver's wire protocol for Chromium. It is being developed by
members of the Chromium and WebDriver teams.

%package headless
Summary:	A minimal headless shell built from Chromium
Requires: chromium-common%{_isa} = %{version}-%{release}

%description headless
A minimal headless client built from Chromium. headless_shell is built
without support for alsa, cups, dbus, gconf, gio, kerberos, pulseaudio, or 
udev.

%package qt5-ui
Summary: Qt5 UI built from Chromium
Requires: chromium%{_isa} = %{version}-%{release}

%description qt5-ui
Qt5 UI for chromium.

%package qt6-ui
Summary: Qt6 UI built from Chromium
Requires: chromium%{_isa} = %{version}-%{release}

%description qt6-ui
Qt6 UI for chromium.

%prep
%setup -q -n chromium-%{version}

### Chromium Fedora Patches ###
%patch -P1 -p1 -b .etc

%patch -P20 -p1 -b .disable-font-test
%patch -P21 -p1 -b .screen-ai-service
%if ! %{use_custom_libcxx}
%patch -P22 -p1 -b .fix-qt-ui
%endif

%patch -P31 -p1 -b .disable-enterprise_companion_integration_tests

%patch -P92 -p1 -b .nodejs-checkversion
%patch -P93 -p1 -b .ftbfs-csss_style_sheet
%patch -P94 -p1 -R -b .v8-sanitize-build-error
%patch -P96 -p1 -b .crabbyavif-ftbfs-old-rust

%patch -P150 -p1 -b .qt6

%patch -P300 -p1 -b .swiftshader-missing-include

%patch -P315 -p1 -b .rustc-ftbfs
%patch -P310 -p1 -b .rust-FTBFS-suppress-warnings
%patch -P311 -p1 -b .fstack-protector-strong

%patch -P316 -p1 -b .clang++-unknown-argument

%patch -P318 -p1 -b .memory-allocator-dcheck-assert-fix
%patch -P319 -p1 -b .swiftshader-llvm-16.0

%ifarch aarch64 && 0%{?fedora}
%patch -P320 -p1 -b .aarch64-log-error
%endif

%if %{disable_bti}
%patch -P352 -p1 -b .workaround_for_crash_on_BTI_capable_system
%endif

%ifarch aarch64 && (0%{?fedora} > 40 || 0%{?rhel} > 10)
%patch -P353 -p1 -b .duplicate-case-value
%endif

%patch -P355 -p1 -b .hardware_destructive_interference_size

%patch -P356 -p1 -b .disable_use_libcxx_modules

%patch -P357 -p1 -b .type-mismatch-error

%patch -P358 -p1 -b .rust-clang_lib

%if  0%{?fedora} > 41 || (0%{?rhel} == 10 && 0%{?rhel_minor_version} > 2)
%patch -P359 -p1 -b .ftbfs-with-rustc-1.95
%endif

%if 0%{?flatpak}
%patch -P500 -p1 -b .flatpak-initial-sandbox
%patch -P501 -p1 -b .flatpak-sandbox-paths
%endif

%patch -P520 -p1 -b .build-with-wasm-rollup
%patch -P521 -p1 -b .disable-ai
%patch -P522 -p1 -b .anatase-branding

# Upstream patches
# improve auto dark image inversion logic
%patch -P600 -p1 -b .Add-luminance-ratio-feature-for-dark-mode-image-classification
%patch -P601 -p1 -b .Prefix-dark-mode-decision-tree-threshold-constants-with-kFeature
%patch -P602 -p1 -b .Add-saturation-feature-for-dark-mode-image-classification
%patch -P603 -p1 -b .Add-AutoDarkModeSkipImages-flag-to-bypass-image-dark-mode
%patch -P604 -p1 -b .Add-chromatic-pixels-feature-based-on-muted-hue-colors-for-dark-mode
%patch -P605 -p1 -b .Make-dark-mode-apply-filter-to-images-irrespective-of-layout-zoom
%patch -P606 -p1 -b .chromium-149-use-64px-css-pixels-absolute-threshold-for-dark-image-classification

# Replace Chromium's bundled product logos used by chrome:// pages.
cp -a %{SOURCE20} chrome/app/theme/chromium/product_logo_16.png
cp -a %{SOURCE15} chrome/app/theme/chromium/product_logo_24.png
cp -a %{SOURCE21} chrome/app/theme/chromium/product_logo_32.png
cp -a %{SOURCE16} chrome/app/theme/chromium/product_logo_48.png
cp -a %{SOURCE17} chrome/app/theme/chromium/product_logo_64.png
cp -a %{SOURCE18} chrome/app/theme/chromium/product_logo_128.png
cp -a %{SOURCE19} chrome/app/theme/chromium/product_logo_256.png
cp -a %{SOURCE22} chrome/app/theme/chromium/product_logo.svg
cp -a %{SOURCE20} chrome/app/theme/chromium/linux/product_logo_16.png
cp -a %{SOURCE15} chrome/app/theme/chromium/linux/product_logo_24.png
cp -a %{SOURCE17} chrome/app/theme/chromium/linux/product_logo_64.png
cp -a %{SOURCE18} chrome/app/theme/chromium/linux/product_logo_128.png
cp -a %{SOURCE19} chrome/app/theme/chromium/linux/product_logo_256.png

# Change shebang in all relevant files in this directory and all subdirectories
# See `man find` for how the `-exec command {} +` syntax works
find -type f \( -iname "*.py" \) -exec sed -i '1s=^#! */usr/bin/\(python\|env python\)[23]\?=#!%{chromium_pybin}=' {} +

tar xf %{SOURCE12}

# Add correct path for nodejs binary
mkdir -p third_party/node/linux/node-linux-x64/bin
ln -sfn ../../../../../node-%{nodejs_version}-linux-%{nodejs_arch}/bin/node third_party/node/linux/node-linux-x64/bin/node

# Add correct path for esbuild binary
mkdir -p third_party/devtools-frontend/src/third_party/esbuild
ln -sfn $(which esbuild) third_party/devtools-frontend/src/third_party/esbuild/esbuild

# Remove bundle gn and replace it with a system gn or bootstrap gn as it is x86_64 and causes
# FTBFS on other arch like aarch64/ppc64le
mkdir -p buildtools/linux64/
%if %{bootstrap}
ln -sf ../../%{chromebuilddir}/gn buildtools/linux64/gn 
%else
ln -sf $(which gn) buildtools/linux64/gn
%endif

# Remove bundle gperf and replace it with system gperf
mkdir -p third_party/gperf/cipd/bin
ln -fs $(which gperf) third_party/gperf/cipd/bin/gperf

# Remove bundle rustc and replace it with system rustc
mkdir -p third_party/rust-toolchain/bin/
ln -fs $(which rustc) third_party/rust-toolchain/bin/rustc

%if %{bundlelibusbx}
# no hackity hack hack
%else
# hackity hack hack
rm -rf third_party/libusb/src/libusb/libusb.h
# we _shouldn't need to do this, but it looks like we do.
cp -a $(pkg-config --variable=includedir libusb-1.0)/libusb-1.0/libusb.h third_party/libusb/src/libusb/libusb.h
%endif

# Fix hardcoded path in remoting code
sed -i 's|/opt/google/chrome-remote-desktop|%{crd_path}|g' remoting/host/setup/daemon_controller_delegate_linux_single_process.cc

# bz#2265957, add correct platform
sed -i "s/Linux x86_64/Linux %{_arch}/" components/embedder_support/user_agent_utils.cc

%if ! %{bundlesimdutf}
ln -sf %{_includedir}/simdutf.h third_party/simdutf/simdutf.h
%endif

%build

# reduce warnings
FLAGS=' -Wno-deprecated-declarations -Wno-unknown-warning-option -Wno-unused-command-line-argument'
FLAGS+=' -Wno-unused-but-set-variable -Wno-unused-result -Wno-unused-function -Wno-unused-variable'
FLAGS+=' -Wno-unused-const-variable -Wno-unneeded-internal-declaration -Wno-unknown-attributes -Wno-unknown-pragmas'

%if %{system_build_flags}
CFLAGS=${CFLAGS/-fexceptions}
CFLAGS=${CFLAGS/-Wp,-D_GLIBCXX_ASSERTIONS}
CFLAGS="$CFLAGS $FLAGS"
CXXFLAGS="$CFLAGS"
%else
# override system build flags
CFLAGS="$FLAGS"
CXXFLAGS="$FLAGS"
%endif

%ifarch ppc64le
CXXFLAGS+=' -faltivec-src-compat=mixed -Wno-deprecated-altivec-src-compat'
%endif

%if ! %{use_custom_libcxx}
LDFLAGS="${LDFLAGS} -stdlib=libc++"
CXXFLAGS="${CXXFLAGS} -stdlib=libc++"
%endif

export CC=clang
export CXX=clang++
export AR=llvm-ar
export NM=llvm-nm
export READELF=llvm-readelf
export CFLAGS
export CXXFLAGS
export LDFLAGS

# need for error: the option `Z` is only accepted on the nightly compiler
export RUSTC_BOOTSTRAP=1

# set rustc version
# Fix error: multiple input filenames provided, caused by rustc_wrapper
rustc_version="$(rustc -V | cut -d' ' -f-2 | sed 's/ /-/')"
# set rust bindgen root
rust_bindgen_root="$(which bindgen | sed 's#/s\?bin/.*##')"
rust_sysroot_absolute="$(rustc --print sysroot)"

# set clang version
clang_version="$(clang --version | sed -n 's/clang version //p' | cut -d. -f1)"
%if 0%{?fedora} > 41 || 0%{?rhel} > 9
clang_base_path="$(PATH=/usr/bin:/usr/sbin which clang | sed 's#/bin/.*##')"
%else
clang_base_path="$(clang --version | grep InstalledDir | cut -d' ' -f2 | sed 's#/bin##')"
%endif

# Core defines are flags that are true for both the browser and headless.
CHROMIUM_CORE_GN_DEFINES=""
# using system toolchain
CHROMIUM_CORE_GN_DEFINES+=' custom_toolchain="//build/toolchain/linux/unbundle:default"'
CHROMIUM_CORE_GN_DEFINES+=' host_toolchain="//build/toolchain/linux/unbundle:default"'
%if ! %{use_custom_libcxx}
CHROMIUM_BROWSER_GN_DEFINES+=' use_custom_libcxx=false'
%endif
CHROMIUM_CORE_GN_DEFINES+=' is_debug=false dcheck_always_on=false dcheck_is_configurable=false'
CHROMIUM_CORE_GN_DEFINES+=' enable_enterprise_companion=false'
CHROMIUM_CORE_GN_DEFINES+=' system_libdir="%{_lib}"'

%if %{official_build}
CHROMIUM_CORE_GN_DEFINES+=' is_official_build=true'
sed -i 's|OFFICIAL_BUILD|GOOGLE_CHROME_BUILD|g' tools/generate_shim_headers/generate_shim_headers.py
%endif

CHROMIUM_CORE_GN_DEFINES+=' chrome_pgo_phase=0'

%if ! %{cfi}
CHROMIUM_CORE_GN_DEFINES+=' is_cfi=false use_thin_lto=false'
%endif

%if %{useapikey}
CHROMIUM_CORE_GN_DEFINES+=' google_api_key="%{api_key}"'
%endif

%if %{userestrictedapikeys}
CHROMIUM_CORE_GN_DEFINES+=' google_default_client_id="%{default_client_id}"'
CHROMIUM_CORE_GN_DEFINES+=' google_default_client_secret="%{default_client_secret}"'
%endif

CHROMIUM_CORE_GN_DEFINES+=' is_clang=true'
CHROMIUM_CORE_GN_DEFINES+=" clang_base_path=\"$clang_base_path\""
CHROMIUM_CORE_GN_DEFINES+=" clang_version=$clang_version"
CHROMIUM_CORE_GN_DEFINES+=' clang_use_chrome_plugins=false'
CHROMIUM_CORE_GN_DEFINES+=' use_lld=true'

# enable system rust
CHROMIUM_CORE_GN_DEFINES+=" rust_sysroot_absolute=\"$rust_sysroot_absolute\""
CHROMIUM_CORE_GN_DEFINES+=" rust_bindgen_root=\"$rust_bindgen_root\""
CHROMIUM_CORE_GN_DEFINES+=" rustc_version=\"$rustc_version\""

CHROMIUM_CORE_GN_DEFINES+=' use_sysroot=false'

%ifarch aarch64
CHROMIUM_CORE_GN_DEFINES+=' target_cpu="arm64"'
%endif

%ifarch ppc64le
CHROMIUM_CORE_GN_DEFINES+=' target_cpu="ppc64"'
%endif

CHROMIUM_CORE_GN_DEFINES+=' icu_use_data_file=true'
CHROMIUM_CORE_GN_DEFINES+=' target_os="linux"'
CHROMIUM_CORE_GN_DEFINES+=' current_os="linux"'
CHROMIUM_CORE_GN_DEFINES+=' treat_warnings_as_errors=false'
CHROMIUM_CORE_GN_DEFINES+=' enable_iterator_debugging=false'
CHROMIUM_CORE_GN_DEFINES+=' enable_vr=false'
CHROMIUM_CORE_GN_DEFINES+=' build_dawn_tests=false enable_perfetto_unittests=false'
CHROMIUM_CORE_GN_DEFINES+=' disable_fieldtrial_testing_config=true'
CHROMIUM_CORE_GN_DEFINES+=' symbol_level=0 blink_symbol_level=0 v8_symbol_level=0'
CHROMIUM_CORE_GN_DEFINES+=' angle_has_histograms=false'
CHROMIUM_CORE_GN_DEFINES+=' use_system_libffi=true'
# drop unrar
CHROMIUM_CORE_GN_DEFINES+=' safe_browsing_use_unrar=false'
CHROMIUM_CORE_GN_DEFINES+=' v8_enable_backtrace=true'
# disable devtools buildle
CHROMIUM_CORE_GN_DEFINES+=' devtools_bundle=false'

if [ -n "${CCACHE_DIR:-}" ]; then
	CHROMIUM_CORE_GN_DEFINES+=' cc_wrapper="ccache"'
fi

export CHROMIUM_CORE_GN_DEFINES

# browser gn defines
CHROMIUM_BROWSER_GN_DEFINES=""

# Use Chromium's bundled ffmpeg inside the Flatpak.
CHROMIUM_BROWSER_GN_DEFINES+=' ffmpeg_branding="Chrome" proprietary_codecs=true is_component_ffmpeg=false enable_ffmpeg_video_decoders=true media_use_ffmpeg=true'
%if 0%{?noopenh264}
CHROMIUM_BROWSER_GN_DEFINES+=' media_use_openh264=true'
CHROMIUM_BROWSER_GN_DEFINES+=' rtc_use_h264=true'
%else
CHROMIUM_BROWSER_GN_DEFINES+=' media_use_openh264=false'
CHROMIUM_BROWSER_GN_DEFINES+=' rtc_use_h264=false'
%endif
CHROMIUM_BROWSER_GN_DEFINES+=' use_kerberos=true'
# Workaround for FTBFS, error: no member named 'bPsnrY' in 'Source_Picture_s'
CHROMIUM_BROWSER_GN_DEFINES+=' rtc_video_psnr=false'

%if %{use_qt5}
CHROMIUM_BROWSER_GN_DEFINES+=" use_qt5=true moc_qt5_path=\"$(%{_qt5_qmake} -query QT_HOST_BINS)\""
%else
CHROMIUM_BROWSER_GN_DEFINES+=' use_qt5=false'
%endif

%if %{use_qt6}
CHROMIUM_BROWSER_GN_DEFINES+=" use_qt6=true moc_qt6_path=\"$(%{_qt6_qmake} -query QT_HOST_LIBEXECS)\""
%else
CHROMIUM_BROWSER_GN_DEFINES+=' use_qt6=false'
%endif
CHROMIUM_BROWSER_GN_DEFINES+=' use_gtk=true gtk_version=%{gtk_version}'

CHROMIUM_BROWSER_GN_DEFINES+=' use_gio=true use_pulseaudio=true'
CHROMIUM_BROWSER_GN_DEFINES+=' enable_hangout_services_extension=true'
CHROMIUM_BROWSER_GN_DEFINES+=' enable_widevine=true'
CHROMIUM_BROWSER_GN_DEFINES+=' enable_library_cdms=true'

%if %{use_vaapi}
CHROMIUM_BROWSER_GN_DEFINES+=' use_vaapi=true'
%else
CHROMIUM_BROWSER_GN_DEFINES+=' use_vaapi=false'
%endif

%if %{use_v4l2_codec} 
CHROMIUM_BROWSER_GN_DEFINES+=' use_v4l2_codec=true'
%endif

%if 0%{?fedora} || 0%{?rhel} > 8
CHROMIUM_BROWSER_GN_DEFINES+=' rtc_use_pipewire=true rtc_link_pipewire=true'
%else
CHROMIUM_BROWSER_GN_DEFINES+=' rtc_use_pipewire=false rtc_link_pipewire=false'
%endif

export CHROMIUM_BROWSER_GN_DEFINES

%if 0%{?noopenh264}
build/linux/unbundle/replace_gn_files.py --system-libraries openh264
%endif

# headless gn defines
CHROMIUM_HEADLESS_GN_DEFINES=""
CHROMIUM_HEADLESS_GN_DEFINES+=' use_ozone=true ozone_auto_platforms=false ozone_platform="headless" ozone_platform_headless=true'
CHROMIUM_HEADLESS_GN_DEFINES+=' angle_enable_vulkan=true angle_enable_swiftshader=true headless_use_embedded_resources=false'
CHROMIUM_HEADLESS_GN_DEFINES+=' headless_use_prefs=false headless_use_policy=false'
CHROMIUM_HEADLESS_GN_DEFINES+=' v8_use_external_startup_data=false enable_print_preview=false enable_remoting=false'
CHROMIUM_HEADLESS_GN_DEFINES+=' use_alsa=false use_bluez=false use_cups=false use_dbus=false use_gio=false use_kerberos=false'
CHROMIUM_HEADLESS_GN_DEFINES+=' use_libpci=false use_pulseaudio=false use_udev=false rtc_use_pipewire=false'
CHROMIUM_HEADLESS_GN_DEFINES+=' v8_enable_lazy_source_positions=false use_glib=false use_gtk=false use_pangocairo=false'
CHROMIUM_HEADLESS_GN_DEFINES+=' use_qt5=false use_qt6=false is_component_build=false enable_ffmpeg_video_decoders=false media_use_ffmpeg=false'
CHROMIUM_HEADLESS_GN_DEFINES+=' media_use_libvpx=false proprietary_codecs=false'
export CHROMIUM_HEADLESS_GN_DEFINES

# Check that there is no system 'google' module, shadowing bundled ones:
if python3 -c 'import google ; print google.__path__' 2> /dev/null ; then \
    echo "Python 3 'google' module is defined, this will shadow modules of this build"; \
    exit 1 ; \
fi

%if %{bootstrap}
tools/gn/bootstrap/bootstrap.py --gn-gen-args="$CHROMIUM_CORE_GN_DEFINES $CHROMIUM_BROWSER_GN_DEFINES"
%else
mkdir -p %{chromebuilddir} && cp -a $(which gn) %{chromebuilddir}/
%endif

%{chromebuilddir}/gn --script-executable=%{chromium_pybin} gen --args="$CHROMIUM_CORE_GN_DEFINES $CHROMIUM_BROWSER_GN_DEFINES" %{chromebuilddir}

%build_target %{chromebuilddir} chrome

%build_target %{chromebuilddir} chrome_sandbox

%if %{build_chromedriver}
%build_target %{chromebuilddir} chromedriver
%endif

%if %{build_headless}
%build_target %{chromebuilddir} headless_shell
%endif

%if %{build_chrome_management_service}
%build_target %{chromebuilddir} chrome_management_service
%endif

%install
rm -rf %{buildroot}

mkdir -p %{buildroot}%{_bindir} \
         %{buildroot}%{chromium_path}/locales \
         %{buildroot}%{_sysconfdir}/%{name}

# install system wide chromium config
cp -a %{SOURCE2} %{buildroot}%{_sysconfdir}/%{name}/%{name}.conf
cp -a %{SOURCE3} %{buildroot}%{chromium_path}/chromium-browser.sh

%if ! %{use_vaapi}
# remove vaapi flags
echo "# system wide chromium flags" > %{buildroot}%{_sysconfdir}/%{name}/%{name}.conf
%endif

sed -i "s|@@EXTRA_FLAGS@@||g" %{buildroot}%{chromium_path}/chromium-browser.sh

ln -s ../..%{chromium_path}/chromium-browser.sh %{buildroot}%{_bindir}/chromium-browser
mkdir -p %{buildroot}%{_mandir}/man1/

pushd %{chromebuilddir}
%if %{bundleicu}
	cp -a icudtl.dat %{buildroot}%{chromium_path}
%endif
	cp -a chrom*.pak resources.pak %{buildroot}%{chromium_path}
	cp -a locales/*.pak %{buildroot}%{chromium_path}/locales/
	cp -a MEIPreload/ PrivacySandboxAttestationsPreloaded/ %{buildroot}%{chromium_path}/
%if %{build_chrome_management_service}
	cp -a chrome_management_service %{buildroot}%{chromium_path}/chrome-management-service
%endif
	%ifarch x86_64 aarch64 ppc64le
		cp -a libvk_swiftshader.so %{buildroot}%{chromium_path}
		cp -a libvulkan.so.1 %{buildroot}%{chromium_path}
		cp -a vk_swiftshader_icd.json %{buildroot}%{chromium_path}
	%endif
	cp -a chrome %{buildroot}%{chromium_path}/chromium-browser
	cp -a chrome_sandbox %{buildroot}%{chromium_path}/chrome-sandbox
	cp -a chrome_crashpad_handler %{buildroot}%{chromium_path}/chrome_crashpad_handler
	cp -a ../../chrome/app/resources/manpage.1.in %{buildroot}%{_mandir}/man1/chromium-browser.1
	sed -i "s|@@PACKAGE|chromium-browser|g" %{buildroot}%{_mandir}/man1/chromium-browser.1
	sed -i "s|@@MENUNAME|%{chromium_menu_name}|g" %{buildroot}%{_mandir}/man1/chromium-browser.1

	# V8 initial snapshots
	# https://code.google.com/p/chromium/issues/detail?id=421063
	cp -a v8_context_snapshot.bin %{buildroot}%{chromium_path}

	# This is ANGLE, not to be confused with the similarly named files under swiftshader/
	cp -a libEGL.so libGLESv2.so %{buildroot}%{chromium_path}

	%if %{use_qt5}
		cp -a libqt5_shim.so %{buildroot}%{chromium_path}
	%endif

	%if %{use_qt6}
		cp -a libqt6_shim.so %{buildroot}%{chromium_path}
	%endif

	%if %{build_chromedriver}
		# chromedriver
		cp -a chromedriver %{buildroot}%{chromium_path}/chromedriver
		ln -s ../..%{chromium_path}/chromedriver %{buildroot}%{_bindir}/chromedriver
	%endif

popd

%if %{build_headless}
	pushd %{chromebuilddir}
		cp -a *.pak headless_shell %{buildroot}%{chromium_path}
	popd
%endif

# need to strip binaries explicitly when debug is disable
%if ! %{enable_debug}
pushd %{buildroot}%{chromium_path}/
for f in *.so *.so.1 chrome_crashpad_handler chrome-sandbox chromium-browser headless_shell chromedriver ; do
   [ -f $f ] && strip $f
done
popd
%endif

# Add directories for policy management
mkdir -p %{buildroot}%{_sysconfdir}/chromium/policies/managed
mkdir -p %{buildroot}%{_sysconfdir}/chromium/policies/recommended

# disable AI
cp -a %{SOURCE14} %{buildroot}%{_sysconfdir}/chromium/policies/managed/

install -Dm0644 %{SOURCE20} %{buildroot}%{_datadir}/icons/hicolor/16x16/apps/chromium-browser.png
install -Dm0644 %{SOURCE15} %{buildroot}%{_datadir}/icons/hicolor/24x24/apps/chromium-browser.png
install -Dm0644 %{SOURCE21} %{buildroot}%{_datadir}/icons/hicolor/32x32/apps/chromium-browser.png
install -Dm0644 %{SOURCE16} %{buildroot}%{_datadir}/icons/hicolor/48x48/apps/chromium-browser.png
install -Dm0644 %{SOURCE17} %{buildroot}%{_datadir}/icons/hicolor/64x64/apps/chromium-browser.png
install -Dm0644 %{SOURCE18} %{buildroot}%{_datadir}/icons/hicolor/128x128/apps/chromium-browser.png
install -Dm0644 %{SOURCE19} %{buildroot}%{_datadir}/icons/hicolor/256x256/apps/chromium-browser.png

# Install the master_preferences file
install -m 0644 %{SOURCE11} %{buildroot}%{_sysconfdir}/%{name}/

mkdir -p %{buildroot}%{_datadir}/applications/
desktop-file-install --dir %{buildroot}%{_datadir}/applications %{SOURCE4}

install -D -m0644 %{SOURCE10} ${RPM_BUILD_ROOT}%{_datadir}/appdata/chromium-browser.appdata.xml
appstream-util validate-relax --nonet ${RPM_BUILD_ROOT}%{_datadir}/appdata/chromium-browser.appdata.xml

mkdir -p %{buildroot}%{_datadir}/gnome-control-center/default-apps/
cp -a %{SOURCE9} %{buildroot}%{_datadir}/gnome-control-center/default-apps/

%if %{undefined flatpak}
%post
# Set SELinux labels - semanage itself will adjust the lib directory naming
# But only do it when selinux is enabled, otherwise, it gets noisy.
if selinuxenabled; then
	semanage fcontext -a -t bin_t /usr/lib/chromium-browser &>/dev/null || :
	semanage fcontext -a -t bin_t /usr/lib/chromium-browser/chromium-browser.sh &>/dev/null || :
	semanage fcontext -a -t chrome_sandbox_exec_t /usr/lib/chrome-sandbox &>/dev/null || :
	restorecon -R -v %{chromium_path}/chromium-browser &>/dev/null || :
fi
%endif

%files
%doc AUTHORS
%license LICENSE
%dir %{_sysconfdir}/%{name}/policies/
%dir %{chromium_path}/MEIPreload/
%dir %{chromium_path}/PrivacySandboxAttestationsPreloaded/
%config(noreplace) %{_sysconfdir}/%{name}/chromium.conf
%config %{_sysconfdir}/%{name}/master_preferences
%config %{_sysconfdir}/%{name}/policies/managed/disable-ai.json
%{_bindir}/chromium-browser
%{chromium_path}/chrome_*.pak
%{chromium_path}/chrome_crashpad_handler
%{chromium_path}/resources.pak
%{chromium_path}/chromium-browser
%{chromium_path}/chromium-browser.sh
%if %{build_chrome_management_service}
%{chromium_path}/chrome-management-service
%endif
%{chromium_path}/MEIPreload/*
%{chromium_path}/PrivacySandboxAttestationsPreloaded/*
%{chromium_path}/chrome-sandbox
%{_mandir}/man1/chromium-browser.*
%{_datadir}/icons/hicolor/*/apps/chromium-browser.png
%{_datadir}/applications/*.desktop
%{_datadir}/appdata/*.appdata.xml
%{_datadir}/gnome-control-center/default-apps/chromium-browser.xml

%if %{use_qt5}
%files qt5-ui
%{chromium_path}/libqt5_shim.so
%endif

%if %{use_qt6}
%files qt6-ui
%{chromium_path}/libqt6_shim.so
%endif

%files common
%{chromium_path}/libvk_swiftshader.so*
%{chromium_path}/libvulkan.so*
%{chromium_path}/vk_swiftshader_icd.json
%{chromium_path}/libEGL.so*
%{chromium_path}/libGLESv2.so*
%{chromium_path}/*.bin
%if %{bundleicu}
%{chromium_path}/icudtl.dat
%endif
%dir %{chromium_path}/
%dir %{chromium_path}/locales/
%lang(af) %{chromium_path}/locales/af*.pak
%lang(am) %{chromium_path}/locales/am*.pak
%lang(ar) %{chromium_path}/locales/ar*.pak
%lang(bg) %{chromium_path}/locales/bg*.pak
%lang(bn) %{chromium_path}/locales/bn*.pak
%lang(ca) %{chromium_path}/locales/ca*.pak
%lang(cs) %{chromium_path}/locales/cs*.pak
%lang(da) %{chromium_path}/locales/da*.pak
%lang(de) %{chromium_path}/locales/de*.pak
%lang(el) %{chromium_path}/locales/el*.pak
%lang(en_GB) %{chromium_path}/locales/en-GB*.pak
# Chromium _ALWAYS_ needs en-US.pak as a fallback
# This means we cannot apply the lang code here.
# Otherwise, it is filtered out on install.
%{chromium_path}/locales/en-US*.pak
%lang(es) %{chromium_path}/locales/es*.pak
%lang(et) %{chromium_path}/locales/et*.pak
%lang(fa) %{chromium_path}/locales/fa*.pak
%lang(fi) %{chromium_path}/locales/fi{.pak,_*.pak}
%lang(fil) %{chromium_path}/locales/fil*.pak
%lang(fr) %{chromium_path}/locales/fr*.pak
%lang(gu) %{chromium_path}/locales/gu*.pak
%lang(he) %{chromium_path}/locales/he*.pak
%lang(hi) %{chromium_path}/locales/hi*.pak
%lang(hr) %{chromium_path}/locales/hr*.pak
%lang(hu) %{chromium_path}/locales/hu*.pak
%lang(id) %{chromium_path}/locales/id*.pak
%lang(it) %{chromium_path}/locales/it*.pak
%lang(ja) %{chromium_path}/locales/ja*.pak
%lang(kn) %{chromium_path}/locales/kn*.pak
%lang(ko) %{chromium_path}/locales/ko*.pak
%lang(lt) %{chromium_path}/locales/lt*.pak
%lang(lv) %{chromium_path}/locales/lv*.pak
%lang(ml) %{chromium_path}/locales/ml*.pak
%lang(mr) %{chromium_path}/locales/mr*.pak
%lang(ms) %{chromium_path}/locales/ms*.pak
%lang(nb) %{chromium_path}/locales/nb*.pak
%lang(nl) %{chromium_path}/locales/nl*.pak
%lang(pl) %{chromium_path}/locales/pl*.pak
%lang(pt_BR) %{chromium_path}/locales/pt-BR*.pak
%lang(pt_PT) %{chromium_path}/locales/pt-PT*.pak
%lang(ro) %{chromium_path}/locales/ro*.pak
%lang(ru) %{chromium_path}/locales/ru*.pak
%lang(sk) %{chromium_path}/locales/sk*.pak
%lang(sl) %{chromium_path}/locales/sl*.pak
%lang(sr) %{chromium_path}/locales/sr*.pak
%lang(sv) %{chromium_path}/locales/sv*.pak
%lang(sw) %{chromium_path}/locales/sw*.pak
%lang(ta) %{chromium_path}/locales/ta*.pak
%lang(te) %{chromium_path}/locales/te*.pak
%lang(th) %{chromium_path}/locales/th*.pak
%lang(tr) %{chromium_path}/locales/tr*.pak
%lang(uk) %{chromium_path}/locales/uk*.pak
%lang(ur) %{chromium_path}/locales/ur*.pak
%lang(vi) %{chromium_path}/locales/vi*.pak
%lang(zh_CN) %{chromium_path}/locales/zh-CN*.pak
%lang(zh_TW) %{chromium_path}/locales/zh-TW*.pak
# These are psuedolocales, not real ones.
# They only get generated when is_official_build=false
%if ! %{official_build}
%{chromium_path}/locales/ar-XB.pak
%{chromium_path}/locales/en-XA.pak
%endif

%if %{build_headless}
%files headless
%{chromium_path}/headless_shell
%{chromium_path}/headless_*.pak
%endif

%if %{build_chromedriver}
%files -n chromedriver
%doc AUTHORS
%license LICENSE
%{_bindir}/chromedriver
%{chromium_path}/chromedriver
%endif

%changelog
* Fri Jun 26 2026 Than Ngo <than@redhat.com> - 149.0.7827.200-1
- Update to 149.0.7827.200
   CVE-2026-13281: Integer overflow in Mojo
   CVE-2026-13282: Use after free in Payments
   CVE-2026-13283: Use after free in AdFilter

* Wed Jun 24 2026 Than Ngo <than@redhat.com> - 149.0.7827.196-1
- Update to 149.0.7827.196
  * CVE-2026-13028: Use after free in WebGL
  * CVE-2026-13032: Use after free in WebGL
  * CVE-2026-13033: Out of bounds read in Blink>InterestGroups
  * CVE-2026-13038: Use after free in Autofill
  * CVE-2026-13021: Inappropriate implementation in DeviceBoundSessionCredentials
  * CVE-2026-13022: Inappropriate implementation in Autofill
  * CVE-2026-13023: Uninitialized Use in GPU
  * CVE-2026-13024: Insufficient validation of untrusted input in Navigation
  * CVE-2026-13025: Insufficient validation of untrusted input in DevTools
  * CVE-2026-13026: Use after free in Digital Credentials
  * CVE-2026-13027: Use after free in FileSystem
  * CVE-2026-13029: Use after free in Web Authentication
  * CVE-2026-13030: Uninitialized Use in GPU
  * CVE-2026-13031: Use after free in Blink
  * CVE-2026-13034: Inappropriate implementation in Passwords
  * CVE-2026-13035: Use after free in Bluetooth
  * CVE-2026-13036: Use after free in Blink
  * CVE-2026-13037: Use after free in WebView
- Upstream patch, Make dark mode apply filter to images irrespective of layout zoom

* Wed Jun 17 2026 Than Ngo <than@redhat.com> - 149.0.7827.155-1
- Update to 149.0.7827.155
  * CVE-2026-12437: Use after free in WebShare
  * CVE-2026-12438: Inappropriate implementation in WebView
  * CVE-2026-12439: Use after free in Digital Credentials
  * CVE-2026-12440: Use after free in DigitalCredentials
  * CVE-2026-12441: Use after free in File Input
  * CVE-2026-12442: Use after free in Passwords
  * CVE-2026-12443: Use after free in Web Authentication
  * CVE-2026-12444: Out of bounds read in Chromoting
  * CVE-2026-12445: Use after free in Extensions
  * CVE-2026-12446: Insufficient data validation in Passwords
  * CVE-2026-12447: Heap buffer overflow in WebRTC
  * CVE-2026-12448: Inappropriate implementation in WebView
  * CVE-2026-12449: Use after free in Chromoting
  * CVE-2026-12450: Inappropriate implementation in Media
  * CVE-2026-12451: Use after free in DigitalCredentials
  * CVE-2026-12452: Use after free in Downloads
  * CVE-2026-12453: Insufficient validation of untrusted input in Input
  * CVE-2026-12454: Race in Safe Browsing
  * CVE-2026-12455: Use after free in Tab Strip
  * CVE-2026-12456: Insufficient validation of untrusted input in Extensions
  * CVE-2026-12457: Insufficient data validation in Extensions
  * CVE-2026-12458: Incorrect security UI in Passwords
  * CVE-2026-12459: Inappropriate implementation in Serial
  * CVE-2026-12460: Insufficient policy enforcement in File System Access
  * CVE-2026-12461: Out of bounds read in WebRTC
  * CVE-2026-12462: Use after free in Media
  * CVE-2026-12463: Inappropriate implementation in Views
  * CVE-2026-12464: Use after free in Browser
  * CVE-2026-12465: Insufficient validation of untrusted input in Metrics
  * CVE-2026-12466: Heap buffer overflow in WebRTC
  * CVE-2026-12467: Use after free in Extensions
  * CVE-2026-12468: Inappropriate implementation in Updater
  * CVE-2026-12469: Uninitialized Use in GPU

* Fri Jun 12 2026 Than Ngo <than@redhat.com> - 149.0.7827.114-1
- Update to 149.0.7827.114
  * CVE-2026-12007: Use after free  Core
  * CVE-2026-12008: Use after free  DigitalCredentials
  * CVE-2026-12009: Insufficient validation of untrusted input  Accessibility
  * CVE-2026-12010: Heap buffer overflow  GPU
  * CVE-2026-12011: Use after free  WebMIDI
  * CVE-2026-12012: Use after free  Network
  * CVE-2026-12013: Use after free  Media
  * CVE-2026-12014: Use after free  Cast
  * CVE-2026-12015: Use after free  Autofill
  * CVE-2026-12016: Insufficient validation of untrusted input  DevTools
  * CVE-2026-12017: Insufficient validation of untrusted input  Extensions
  * CVE-2026-12018: Inappropriate implementation  Mojo
  * CVE-2026-12019: Out of bounds write  Codecs
  * CVE-2026-12020: Use after free  Autofill
  * CVE-2026-12022: Race  Safe Browsing
  * CVE-2026-12023: Use after free  GPU
  * CVE-2026-12024: Insufficient policy enforcement  DevTools
  * CVE-2026-12025: Insufficient validation of untrusted input  Network
  * CVE-2026-12026: Out of bounds read  Video
  * CVE-2026-12027: Insufficient policy enforcement  Headless
  * CVE-2026-12028: Use after free  GPU
  * CVE-2026-12029: Use after free  Video
  * CVE-2026-12030: Heap buffer overflow  GPU
  * CVE-2026-12031: Inappropriate implementation  Views
  * CVE-2026-12032: Inappropriate implementation  Passwords
  * CVE-2026-12033: Out of bounds read  VideoCapture
  * CVE-2026-12034: Insufficient validation of untrusted input  Linux Toolkit Theming
  * CVE-2026-12035: Use after free  Views
- Disable AI Mode settings

* Tue Jun 09 2026 Than Ngo <than@redhat.com> - 149.0.7827.102-1
- Update to 149.0.7827.102
  * CVE-2026-11628: Use after free in Ozone
  * CVE-2026-11629: Use after free in Ozone
  * CVE-2026-11630: Use after free in File Input
  * CVE-2026-11631: Use after free in Aura
  * CVE-2026-11632: Use after free in TabStrip
  * CVE-2026-11633: Use after free in Bluetooth
  * CVE-2026-11634: Use after free in Gamepad
  * CVE-2026-11635: Use after free in Bluetooth
  * CVE-2026-11636: Use after free in Autofill
  * CVE-2026-11637: Use after free in Views
  * CVE-2026-11638: Use after free in Printing
  * CVE-2026-11639: Use after free in Compositing
  * CVE-2026-11640: Integer overflow in libyuv
  * CVE-2026-11641: Use after free in Bluetooth
  * CVE-2026-11642: Use after free in Web Apps
  * CVE-2026-11643: Use after free in Proxy
  * CVE-2026-11644: Use after free in Views
  * CVE-2026-11645: Out of bounds memory access in V8
  * CVE-2026-11646: Use after free in ViewTransitions
  * CVE-2026-11647: Use after free in Printing
  * CVE-2026-11648: Use after free in FullScreen
  * CVE-2026-11649: Use after free in V8
  * CVE-2026-11650: Use after free in V8
  * CVE-2026-11651: Use after free in Network
  * CVE-2026-11652: Use after free in Extensions
  * CVE-2026-11653: Insufficient validation of untrusted input in Extensions
  * CVE-2026-11654: Use after free in CameraCapture
  * CVE-2026-11655: Integer overflow in Media
  * CVE-2026-11656: Use after free in ServiceWorker
  * CVE-2026-11657: Use after free in Payments
  * CVE-2026-11658: Insufficient validation of untrusted input in Extensions
  * CVE-2026-11659: Insufficient validation of untrusted input in UI
  * CVE-2026-11660: Insufficient validation of untrusted input in New Tab Page
  * CVE-2026-11661: Use after free in Views
  * CVE-2026-11662: Type Confusion in Bindings
  * CVE-2026-11663: Use after free in Skia
  * CVE-2026-11664: Use after free in Payments
  * CVE-2026-11665: Out of bounds read in Dawn
  * CVE-2026-11666: Insufficient validation of untrusted input in Input
  * CVE-2026-11667: Out of bounds read in WebRTC
  * CVE-2026-11668: Uninitialized Use in Codecs
  * CVE-2026-11669: Integer overflow in Media
  * CVE-2026-11670: Use after free in PDF
  * CVE-2026-11671: Use after free in Navigation
  * CVE-2026-11672: Out of bounds write in GPU
  * CVE-2026-11673: Use after free in InterestGroups
  * CVE-2026-11674: Use after free in Guest View
  * CVE-2026-11675: Insufficient validation of untrusted input in Skia
  * CVE-2026-11676: Insufficient validation of untrusted input in Dawn
  * CVE-2026-11677: Race in Network
  * CVE-2026-11678: Integer overflow in libyuv
  * CVE-2026-11679: Use after free in Codecs
  * CVE-2026-11680: Use after free in Media
  * CVE-2026-11681: Use after free in Ozone
  * CVE-2026-11682: Insufficient validation of untrusted input in Views
  * CVE-2026-11683: Use after free in WebCodecs
  * CVE-2026-11684: Insufficient policy enforcement in Network
  * CVE-2026-11685: Insufficient data validation in MediaCapture
  * CVE-2026-11686: Insufficient validation of untrusted input in Dawn
  * CVE-2026-11687: Use after free in Dawn
  * CVE-2026-11688: Object lifecycle issue in SVG
  * CVE-2026-11689: Insufficient validation of untrusted input in Passwords
  * CVE-2026-11690: Out of bounds read and write in Media
  * CVE-2026-11691: Insufficient validation of untrusted input in New Tab Page
  * CVE-2026-11692: Use after free in Read Anything
  * CVE-2026-11693: Inappropriate implementation in Plugins
  * CVE-2026-11694: Use after free in ServiceWorker
  * CVE-2026-11695: Inappropriate implementation in Passwords
  * CVE-2026-11696: Uninitialized Use in Video
  * CVE-2026-11697: Insufficient validation of untrusted input in UI
  * CVE-2026-11698: Use after free in Bluetooth
  * CVE-2026-11699: Use after free in Bluetooth
  * CVE-2026-11700: Use after free in Tracing
  * CVE-2026-11701: Insufficient validation of untrusted input in Guest View
- Refresh ppc64le patches

* Fri Jun 05 2026 Than Ngo <than@redhat.com> - 149.0.7827.53-1
- Update to 149.0.7827.53
  * CVE-2026-10881: Out of bounds read and write in ANGLE
  * CVE-2026-10882: Use after free in Network
  * CVE-2026-10883: Out of bounds write in ANGLE
  * CVE-2026-10884: Use after free in Chromecast
  * CVE-2026-10885: Use after free in Chrome for iOS
  * CVE-2026-10886: Use after free in FileSystem
  * CVE-2026-10887: Use after free in Chromoting
  * CVE-2026-10888: Use after free in Cast Streaming
  * CVE-2026-10889: Out of bounds read in ANGLE
  * CVE-2026-10890: Use after free in Cast
  * CVE-2026-10891: Use after free in GFX
  * CVE-2026-10892: Out of bounds write in GPU
  * CVE-2026-10893: Use after free in Chromoting
  * CVE-2026-10894: Use after free in Printing
  * CVE-2026-10895: Use after free in Ozone
  * CVE-2026-10896: Use after free in Chrome for iOS
  * CVE-2026-10897: Out of bounds write in GPU
  * CVE-2026-10898: Stack buffer overflow in GPU
  * CVE-2026-10899: Use after free in Ozone
  * CVE-2026-10900: Use after free in Passwords
  * CVE-2026-10901: Use after free in Passwords
  * CVE-2026-10902: Use after free in Ozone
  * CVE-2026-10903: Use after free in WebRTC
  * CVE-2026-10904: Inappropriate implementation in V8
  * CVE-2026-10905: Use after free in Network
  * CVE-2026-10906: Use after free in WebAuthentication
  * CVE-2026-10907: Out of bounds write in ANGLE
  * CVE-2026-10908: Use after free in FullScreen
  * CVE-2026-10909: Use after free in Dawn
  * CVE-2026-10910: Type Confusion in V8
  * CVE-2026-10911: Insufficient validation of untrusted input in Media
  * CVE-2026-10912: Insufficient validation of untrusted input in Extensions
  * CVE-2026-10913: Use after free in ANGLE
  * CVE-2026-10914: Use after free in ANGLE
  * CVE-2026-10915: Use after free in Core
  * CVE-2026-10916: Insufficient validation of untrusted input in DevTools
  * CVE-2026-10917: Insufficient validation of untrusted input in Media
  * CVE-2026-10918: Use after free in Viz
  * CVE-2026-10919: Use after free in ANGLE
  * CVE-2026-10920: Insufficient validation of untrusted input in WebShare
  * CVE-2026-10921: Integer overflow in Dawn
  * CVE-2026-10922: Insufficient validation of untrusted input in DevTools
  * CVE-2026-10923: Use after free in WebAppInstalls
  * CVE-2026-10924: Integer overflow in Chromecast
  * CVE-2026-10925: Out of bounds write in Skia
  * CVE-2026-10926: Use after free in Cast
  * CVE-2026-10927: Out of bounds read in Dawn
  * CVE-2026-10928: Script injection in Headless
  * CVE-2026-10929: Heap buffer overflow in ANGLE
  * CVE-2026-10930: Out of bounds read in ANGLE
  * CVE-2026-10931: Use after free in FileSystem
  * CVE-2026-10932: Use after free in UI
  * CVE-2026-10933: Use after free in Audio
  * CVE-2026-10934: Use after free in Autofill
  * CVE-2026-10935: Inappropriate implementation in V8
  * CVE-2026-10936: Type Confusion in V8
  * CVE-2026-10937: Inappropriate implementation in Passwords
  * CVE-2026-10938: Insufficient validation of untrusted input in Input
  * CVE-2026-10939: Use after free in WebRTC
  * CVE-2026-10940: Race in Codecs
  * CVE-2026-10941: Out of bounds memory access in Skia
  * CVE-2026-10942: Insufficient validation of untrusted input in UI
  * CVE-2026-10943: Use after free in WebRTC
  * CVE-2026-10944: Insufficient policy enforcement in Autofill
  * CVE-2026-10945: Use after free in PDF
  * CVE-2026-10946: Heap buffer overflow in Media
  * CVE-2026-10947: Use after free in WebRTC
  * CVE-2026-10948: Use after free in WebRTC
  * CVE-2026-10949: Heap buffer overflow in Video
  * CVE-2026-10950: Insufficient policy enforcement in Autofill
  * CVE-2026-10951: Use after free in Autofill
  * CVE-2026-10952: Use after free in Chrome for iOS
  * CVE-2026-10953: Use after free in Core
  * CVE-2026-10954: Use after free in Actor
  * CVE-2026-10955: Type Confusion in ANGLE
  * CVE-2026-10956: Use after free in MimeHandlerView
  * CVE-2026-10957: Use after free in Glic
  * CVE-2026-10958: Use after free in Chrome for iOS
  * CVE-2026-10959: Use after free in Input
  * CVE-2026-10960: Uninitialized Use in Codecs
  * CVE-2026-10961: Use after free in Chrome for iOS
  * CVE-2026-10962: Type Confusion in Media
  * CVE-2026-10963: Integer overflow in V8
  * CVE-2026-10964: Integer overflow in V8
  * CVE-2026-10965: Integer overflow in DevTools
  * CVE-2026-10966: Insufficient validation of untrusted input in Codecs
  * CVE-2026-10967: Use after free in SurfaceCapture
  * CVE-2026-10968: Insufficient validation of untrusted input in Dawn
  * CVE-2026-10969: Insufficient validation of untrusted input in Extensions
  * CVE-2026-10970: Insufficient validation of untrusted input in InterestGroups
  * CVE-2026-10971: Insufficient validation of untrusted input in Printing
  * CVE-2026-10972: Use after free in Ozone
  * CVE-2026-10973: Uninitialized Use in Dawn
  * CVE-2026-10974: Insufficient validation of untrusted input in ANGLE
  * CVE-2026-10975: Use after free in WebRTC
  * CVE-2026-10976: Uninitialized Use in Dawn
  * CVE-2026-10977: Uninitialized Use in Skia
  * CVE-2026-10978: Use after free in Chromoting
  * CVE-2026-10979: Out of bounds read in ANGLE
  * CVE-2026-10980: Insufficient validation of untrusted input in DevTools
  * CVE-2026-10981: Insufficient validation of untrusted input in Codecs
  * CVE-2026-10982: Use after free in WebXR
  * CVE-2026-10983: Insufficient validation of untrusted input in Dawn
  * CVE-2026-10984: Inappropriate implementation in Accessibility
  * CVE-2026-10985: Out of bounds read in Skia
  * CVE-2026-10986: Integer overflow in Media
  * CVE-2026-10987: Integer overflow in V8
  * CVE-2026-10988: Use after free in Views
  * CVE-2026-10989: Inappropriate implementation in V8
  * CVE-2026-10990: Use after free in Glic
  * CVE-2026-10991: Use after free in V8
  * CVE-2026-10992: Insufficient data validation in Animation
  * CVE-2026-10993: Heap buffer overflow in Skia
  * CVE-2026-10994: Uninitialized Use in ANGLE
  * CVE-2026-10995: Heap buffer overflow in TabStrip
  * CVE-2026-10996: Inappropriate implementation in Workers
  * CVE-2026-10997: Insufficient policy enforcement in Extensions
  * CVE-2026-10998: Out of bounds read in Media
  * CVE-2026-10999: Out of bounds memory access in ANGLE
  * CVE-2026-11000: Use after free in Fonts
  * CVE-2026-11001: Incorrect security UI in Payments
  * CVE-2026-11002: Use after free in Autofill
  * CVE-2026-11003: Use after free in WebRTC
  * CVE-2026-11004: Out of bounds read in ANGLE
  * CVE-2026-11005: Out of bounds read in ANGLE
  * CVE-2026-11006: Out of bounds read in Dawn
  * CVE-2026-11007: Insufficient validation of untrusted input in WebView
  * CVE-2026-11008: Insufficient validation of untrusted input in WebAppInstalls
  * CVE-2026-11009: Use after free in USB
  * CVE-2026-11010: Use after free in WebShare
  * CVE-2026-11011: Insufficient policy enforcement in Password Manager
  * CVE-2026-11012: Use after free in Serial
  * CVE-2026-11013: Insufficient validation of untrusted input in Network
  * CVE-2026-11014: Insufficient policy enforcement in Extensions
  * CVE-2026-11015: Out of bounds read in WebGPU
  * CVE-2026-11016: Insufficient validation of untrusted input in Network
  * CVE-2026-11017: Inappropriate implementation in Link Preview
  * CVE-2026-11018: Insufficient policy enforcement in Actor
  * CVE-2026-11019: Inappropriate implementation in Payments
  * CVE-2026-11020: Inappropriate implementation in Extensions
  * CVE-2026-11021: Insufficient validation of untrusted input in GPU
  * CVE-2026-11022: Insufficient validation of untrusted input in DevTools
  * CVE-2026-11023: Insufficient validation of untrusted input in WebAppInstalls
  * CVE-2026-11024: Stack buffer overflow in Skia
  * CVE-2026-11025: Insufficient policy enforcement in Navigation
  * CVE-2026-11026: Insufficient policy enforcement in Extensions
  * CVE-2026-11027: Insufficient validation of untrusted input in Glic
  * CVE-2026-11028: Use after free in Media
  * CVE-2026-11029: Insufficient validation of untrusted input in Drag and Drop
  * CVE-2026-11030: Use after free in Network
  * CVE-2026-11031: Insufficient validation of untrusted input in Password Manager
  * CVE-2026-11032: Insufficient data validation in Password Manager
  * CVE-2026-11033: Uninitialized Use in WebML
  * CVE-2026-11034: Insufficient validation of untrusted input in Tab Group Sync
  * CVE-2026-11035: Insufficient validation of untrusted input in Custom Tabs
  * CVE-2026-11036: Inappropriate implementation in DOM
  * CVE-2026-11037: Out of bounds write in Codecs
  * CVE-2026-11038: Insufficient validation of untrusted input in Subresource Integrity
  * CVE-2026-11039: Uninitialized Use in Skia
  * CVE-2026-11040: Use after free in ANGLE
  * CVE-2026-11041: Insufficient validation of untrusted input in Media
  * CVE-2026-11042: Use after free in Views
  * CVE-2026-11043: Out of bounds write in ANGLE
  * CVE-2026-11044: Integer overflow in ANGLE
  * CVE-2026-11045: Insufficient validation of untrusted input in GPU
  * CVE-2026-11046: Insufficient validation of untrusted input in Media
  * CVE-2026-11047: Insufficient validation of untrusted input in Base
  * CVE-2026-11048: Inappropriate implementation in Extensions
  * CVE-2026-11049: Use after free in Password Manager
  * CVE-2026-11050: Use after free in V8
  * CVE-2026-11051: Out of bounds read in ANGLE
  * CVE-2026-11052: Type Confusion in GPU
  * CVE-2026-11053: VULNERABILITY in WebRTC
  * CVE-2026-11054: Use after free in WebRTC
  * CVE-2026-11055: Use after free in ANGLE
  * CVE-2026-11056: Insufficient validation of untrusted input in SiteIsolation
  * CVE-2026-11057: Uninitialized Use in Skia
  * CVE-2026-11058: Integer overflow in CredentialProvider
  * CVE-2026-11059: Use after free in Blink
  * CVE-2026-11060: Use after free in Media
  * CVE-2026-11061: Out of bounds read in ANGLE
  * CVE-2026-11062: Insufficient policy enforcement in Extensions
  * CVE-2026-11063: Insufficient validation of untrusted input in WebNN
  * CVE-2026-11064: Uninitialized Use in GPU
  * CVE-2026-11065: Use after free in ANGLE
  * CVE-2026-11066: Insufficient validation of untrusted input in ANGLE
  * CVE-2026-11067: Uninitialized Use in Dawn
  * CVE-2026-11068: Use after free in WebSockets
  * CVE-2026-11069: Insufficient validation of untrusted input in Cast
  * CVE-2026-11070: Insufficient validation of untrusted input in Chromoting
  * CVE-2026-11071: Use after free in Base
  * CVE-2026-11072: Use after free in WebView
  * CVE-2026-11073: Use after free in WebGL
  * CVE-2026-11074: Use after free in WebRTC
  * CVE-2026-11075: Out of bounds read in V8
  * CVE-2026-11076: Type Confusion in CSS
  * CVE-2026-11077: Out of bounds read in Dawn
  * CVE-2026-11078: Insufficient validation of untrusted input in FileSystem
  * CVE-2026-11079: Insufficient validation of untrusted input in Codecs
  * CVE-2026-11080: Use after free in WebView
  * CVE-2026-11081: Policy bypass in Canvas
  * CVE-2026-11082: Use after free in GPU
  * CVE-2026-11083: Inappropriate implementation in Password Manager
  * CVE-2026-11084: Inappropriate implementation in Password Manager
  * CVE-2026-11085: Integer overflow in GPU
  * CVE-2026-11086: Insufficient validation of untrusted input in Dawn
  * CVE-2026-11087: Uninitialized Use in ANGLE
  * CVE-2026-11088: Integer overflow in ANGLE
  * CVE-2026-11089: Uninitialized Use in Media
  * CVE-2026-11090: Uninitialized Use in ANGLE
  * CVE-2026-11091: Inappropriate implementation in Dawn
  * CVE-2026-11092: Insufficient policy enforcement in DevTools
  * CVE-2026-11093: Insufficient validation of untrusted input in Printing
  * CVE-2026-11094: Use after free in Codecs
  * CVE-2026-11095: Insufficient validation of untrusted input in Codecs
  * CVE-2026-11096: Out of bounds read in WebRTC
  * CVE-2026-11097: Inappropriate implementation in WebView
  * CVE-2026-11098: Insufficient validation of untrusted input in GPU
  * CVE-2026-11099: Vulnerability in Skia
  * CVE-2026-11100: Use after free in File Input
  * CVE-2026-11101: Uninitialized Use in Dawn
  * CVE-2026-11102: Inappropriate implementation in Isolated Web Apps
  * CVE-2026-11103: Inappropriate implementation in Installer
  * CVE-2026-11104: Uninitialized Use in ANGLE
  * CVE-2026-11105: Insufficient validation of untrusted input in WebUI
  * CVE-2026-11106: Inappropriate implementation in Media
  * CVE-2026-11107: Inappropriate implementation in Downloads
  * CVE-2026-11108: Inappropriate implementation in NFC
  * CVE-2026-11109: Uninitialized Use in ANGLE
  * CVE-2026-11110: Uninitialized Use in ANGLE
  * CVE-2026-11111: Out of bounds read in ANGLE
  * CVE-2026-11112: Insufficient validation of untrusted input in Chromoting
  * CVE-2026-11113: Insufficient validation of untrusted input in ANGLE
  * CVE-2026-11114: Use after free in Device Trust
  * CVE-2026-11115: Use after free in Updater
  * CVE-2026-11116: Use after free in Chromoting
  * CVE-2026-11117: Use after free in Views
  * CVE-2026-11118: Use after free in WebRTC
  * CVE-2026-11119: Insufficient validation of untrusted input in GPU
  * CVE-2026-11120: Insufficient validation of untrusted input in Enterprise Reporting
  * CVE-2026-11121: Insufficient validation of untrusted input in Skia
  * CVE-2026-11122: Inappropriate implementation in Keyboard
  * CVE-2026-11123: Uninitialized Use in ANGLE
  * CVE-2026-11124: Heap buffer overflow in Skia
  * CVE-2026-11125: Use after free in Compositing
  * CVE-2026-11126: Insufficient validation of untrusted input in DevTools
  * CVE-2026-11127: Inappropriate implementation in WebAPKs
  * CVE-2026-11128: Insufficient validation of untrusted input in Web Share
  * CVE-2026-11129: Inappropriate implementation in Extensions
  * CVE-2026-11130: Use after free in Media
  * CVE-2026-11131: Use after free in Autofill
  * CVE-2026-11132: Policy bypass in Paint
  * CVE-2026-11133: Insufficient policy enforcement in Paint
  * CVE-2026-11134: Insufficient data validation in Media
  * CVE-2026-11135: Insufficient policy enforcement in Autofill
  * CVE-2026-11136: Use after free in Canvas
  * CVE-2026-11137: Uninitialized Use in ANGLE
  * CVE-2026-11138: Uninitialized Use in ANGLE
  * CVE-2026-11139: Policy bypass in Paint
  * CVE-2026-11140: Insufficient validation of untrusted input in Chromecast
  * CVE-2026-11141: Uninitialized Use in Audio
  * CVE-2026-11142: Policy bypass in Paint
  * CVE-2026-11143: Heap buffer overflow in Extensions
  * CVE-2026-11144: Use after free in Media
  * CVE-2026-11145: Race in Geolocation
  * CVE-2026-11146: Insufficient validation of untrusted input in Chromoting
  * CVE-2026-11147: Use after free in WebML
  * CVE-2026-11148: Inappropriate implementation in Payments
  * CVE-2026-11149: Insufficient validation of untrusted input in Extensions
  * CVE-2026-11150: Inappropriate implementation in XML
  * CVE-2026-11151: Insufficient validation of untrusted input in Password Manager
  * CVE-2026-11152: Object lifecycle issue in Dawn
  * CVE-2026-11153: Side-channel information leakage in Forms
  * CVE-2026-11154: Use after free in Dawn
  * CVE-2026-11155: Insufficient policy enforcement in CSS
  * CVE-2026-11156: Inappropriate implementation in CSS
  * CVE-2026-11157: Script injection in Accessibility
  * CVE-2026-11158: Insufficient validation of untrusted input in Downloads
  * CVE-2026-11159: Uninitialized Use in Skia
  * CVE-2026-11160: Out of bounds read in Input
  * CVE-2026-11161: Insufficient data validation in DataTransfer
  * CVE-2026-11162: Insufficient policy enforcement in CSS
  * CVE-2026-11163: Use after free in Messages
  * CVE-2026-11164: Use after free in Blink
  * CVE-2026-11165: Use after free in WebMIDI
  * CVE-2026-11166: Inappropriate implementation in SVG
  * CVE-2026-11167: Inappropriate implementation in WebView
  * CVE-2026-11168: Insufficient policy enforcement in Extensions
  * CVE-2026-11169: Inappropriate implementation in XML
  * CVE-2026-11170: Inappropriate implementation in Chromoting
  * CVE-2026-11171: Integer overflow in Blink
  * CVE-2026-11172: Incorrect security UI in Contact Picker
  * CVE-2026-11173: Out of bounds write in V8
  * CVE-2026-11174: Insufficient policy enforcement in Site Isolation
  * CVE-2026-11175: Incorrect security UI in Messages
  * CVE-2026-11176: Inappropriate implementation in Media
  * CVE-2026-11177: Use after free in Omnibox
  * CVE-2026-11178: Policy bypass in WebView
  * CVE-2026-11179: Inappropriate implementation in ORB
  * CVE-2026-11180: Policy bypass in SVG
  * CVE-2026-11181: Inappropriate implementation in Media Session
  * CVE-2026-11182: Inappropriate implementation in SVG
  * CVE-2026-11183: Out of bounds read in GWP-ASan
  * CVE-2026-11184: Insufficient policy enforcement in Actor
  * CVE-2026-11185: Use after free in V8
  * CVE-2026-11186: Inappropriate implementation in CSS
  * CVE-2026-11187: Insufficient policy enforcement in Glic
  * CVE-2026-11188: Use after free in USB
  * CVE-2026-11189: Insufficient validation of untrusted input in DevTools
  * CVE-2026-11190: Insufficient policy enforcement in Extensions
  * CVE-2026-11191: Out of bounds memory access in ANGLE
  * CVE-2026-11192: Insufficient validation of untrusted input in Password Manager
  * CVE-2026-11193: Insufficient policy enforcement in Password Manager
  * CVE-2026-11194: Inappropriate implementation in Network
  * CVE-2026-11195: Inappropriate implementation in MHTML
  * CVE-2026-11196: Type Confusion in XML
  * CVE-2026-11197: Insufficient policy enforcement in Workers
  * CVE-2026-11198: Insufficient validation of untrusted input in Codecs
  * CVE-2026-11199: Insufficient validation of untrusted input in WebRTC
  * CVE-2026-11200: Inappropriate implementation in WebRTC
  * CVE-2026-11201: Use after free in ServiceWorker
  * CVE-2026-11202: Insufficient validation of untrusted input in Chrome for iOS
  * CVE-2026-11203: Policy bypass in GPU
  * CVE-2026-11204: Inappropriate implementation in Signin
  * CVE-2026-11205: Insufficient validation of untrusted input in Chrome for iOS
  * CVE-2026-11206: Policy bypass in ServiceWorker
  * CVE-2026-11207: Insufficient validation of untrusted input in Autofill
  * CVE-2026-11208: Use after free in Codecs
  * CVE-2026-11209: Insufficient policy enforcement in Passwords
  * CVE-2026-11210: Insufficient policy enforcement in Safe Browsing
  * CVE-2026-11211: Integer overflow in V8
  * CVE-2026-11212: Insufficient policy enforcement in DevTools
  * CVE-2026-11213: Insufficient validation of untrusted input in Reading Mode
  * CVE-2026-11214: Inappropriate implementation in Chrome for iOS
  * CVE-2026-11215: Inappropriate implementation in Cronet
  * CVE-2026-11216: Incorrect security UI in File Input
  * CVE-2026-11217: Insufficient policy enforcement in Fenced Frames
  * CVE-2026-11218: Inappropriate implementation in PlatformIntegration
  * CVE-2026-11219: Insufficient data validation in Navigation
  * CVE-2026-11220: Insufficient validation of untrusted input in Navigation
  * CVE-2026-11221: Insufficient validation of untrusted input in PointerLock
  * CVE-2026-11222: Incorrect security UI in Tab Strip
  * CVE-2026-11223: Insufficient validation of untrusted input in Network
  * CVE-2026-11224: Use after free in Chromoting
  * CVE-2026-11225: Incorrect security UI in WebUI
  * CVE-2026-11226: Insufficient policy enforcement in PreviewTab
  * CVE-2026-11227: Incorrect security UI in Tab Hover Cards
  * CVE-2026-11228: Incorrect security UI in File Input
  * CVE-2026-11229: Insufficient policy enforcement in Enterprise
  * CVE-2026-11230: Use after free in Extensions
  * CVE-2026-11231: Inappropriate implementation in Safe Browsing
  * CVE-2026-11232: Inappropriate implementation in TabGroups
  * CVE-2026-11233: Insufficient validation of untrusted input in FoldableAPIs
  * CVE-2026-11234: Insufficient policy enforcement in FoldableAPIs
  * CVE-2026-11235: Insufficient validation of untrusted input in Compositing
  * CVE-2026-11236: Insufficient policy enforcement in Web Bluetooth
  * CVE-2026-11237: Insufficient validation of untrusted input in Media
  * CVE-2026-11238: Inappropriate implementation in DevTools
  * CVE-2026-11239: Insufficient validation of untrusted input in Extensions
  * CVE-2026-11240: Insufficient validation of untrusted input in Loader
  * CVE-2026-11241: Insufficient validation of untrusted input in Cast
  * CVE-2026-11242: Insufficient validation of untrusted input in Plugins
  * CVE-2026-11243: Incorrect security UI in Downloads
  * CVE-2026-11244: Insufficient validation of untrusted input in WebAuthentication
  * CVE-2026-11245: Inappropriate implementation in Payments
  * CVE-2026-11246: Insufficient validation of untrusted input in IndexedDB
  * CVE-2026-11247: Insufficient policy enforcement in CustomTabs
  * CVE-2026-11248: Policy bypass in Google Lens
  * CVE-2026-11249: Use after free in Network
  * CVE-2026-11250: Inappropriate implementation in DevTools
  * CVE-2026-11251: Insufficient validation of untrusted input in Password Manager
  * CVE-2026-11252: Policy bypass in Content Settings
  * CVE-2026-11253: Race in Permissions
  * CVE-2026-11254: Inappropriate implementation in Permissions
  * CVE-2026-11255: Insufficient validation of untrusted input in Storage Access API
  * CVE-2026-11256: Out of bounds read in GPU
  * CVE-2026-11257: Inappropriate implementation in Browser
  * CVE-2026-11258: Inappropriate implementation in File System Access
  * CVE-2026-11259: Insufficient validation of untrusted input in Cast
  * CVE-2026-11260: Policy bypass in Permissions
  * CVE-2026-11261: Insufficient validation of untrusted input in PDF
  * CVE-2026-11262: Use after free in TabStrip
  * CVE-2026-11263: Insufficient policy enforcement in WebAuthentication
  * CVE-2026-11264: Policy bypass in Content Security Policy
  * CVE-2026-11265: Insufficient data validation in Autofill
  * CVE-2026-11266: Policy bypass in SafeBrowsing
  * CVE-2026-11267: Insufficient policy enforcement in Extensions
  * CVE-2026-11268: Uninitialized Use in ANGLE
  * CVE-2026-11269: Inappropriate implementation in Extensions
  * CVE-2026-11270: Inappropriate implementation in UI
  * CVE-2026-11271: Incorrect security UI in Passwords
  * CVE-2026-11272: Insufficient validation of untrusted input in Reading List
  * CVE-2026-11273: Insufficient validation of untrusted input in Omnibox
  * CVE-2026-11274: Inappropriate implementation in DOM Distiller
  * CVE-2026-11275: Insufficient policy enforcement in Page Info
  * CVE-2026-11276: Inappropriate implementation in Cast
  * CVE-2026-11277: Insufficient policy enforcement in Chrome for iOS
  * CVE-2026-11278: Inappropriate implementation in CustomTabs
  * CVE-2026-11279: Out of bounds read in DevTools
  * CVE-2026-11280: Insufficient validation of untrusted input in Signin
  * CVE-2026-11281: Integer overflow in Chromoting
  * CVE-2026-11282: Policy bypass in Sandbox
  * CVE-2026-11283: Policy bypass in Shortcuts
  * CVE-2026-11284: Side-channel information leakage in PerformanceAPIs
  * CVE-2026-11285: Insufficient policy enforcement in Chrome for iOS
  * CVE-2026-11286: Insufficient validation of untrusted input in Wallet
  * CVE-2026-11287: Insufficient validation of untrusted input in Navigation
  * CVE-2026-11288: Policy bypass in CSS
  * CVE-2026-11289: Side-channel information leakage in Paint
  * CVE-2026-11290: Integer overflow in WebView
  * CVE-2026-11291: Policy bypass in Android Autofill
  * CVE-2026-11292: Policy bypass in Blink
  * CVE-2026-11293: Use after free in Input
  * CVE-2026-11294: Inappropriate implementation in Passwords
  * CVE-2026-11295: Inappropriate implementation in WebView
  * CVE-2026-11296: Inappropriate implementation in ImageCapture
  * CVE-2026-11297: Insufficient validation of untrusted input in Reader Mode
  * CVE-2026-11298: Insufficient policy enforcement in Chrome for iOS
  * CVE-2026-11299: Out of bounds read in Fonts
  * CVE-2026-11300: Inappropriate implementation in Permissions
  * CVE-2026-11301: Out of bounds read in LiveCaption
  * CVE-2026-11302: Insufficient policy enforcement in Chrome for iOS
  * CVE-2026-11303: Use after free in PDFium
  * CVE-2026-11304: Use after free in PDFium
  * CVE-2026-11305: Use after free in PDFium
  * CVE-2026-11306: Use after free in PDFium
  * CVE-2026-11307: Use after free in PDFium
  * CVE-2026-11308: Inappropriate implementation in Extensions
  * CVE-2026-11309: Insufficient policy enforcement in History

* Fri May 29 2026 Than Ngo <than@redhat.com> - 148.0.7778.215-1
- Update to 148.0.7778.215
  * CVE-2026-9872: Out of bounds write in GPU
  * CVE-2026-9873: Use after free in Network
  * CVE-2026-9874: Use after free in Dawn
  * CVE-2026-9875: Out of bounds read in WebGL
  * CVE-2026-9876: Use after free in WebGL
  * CVE-2026-9877: Use after free in ANGLE
  * CVE-2026-9878: Use after free in ANGLE
  * CVE-2026-9879: Out of bounds write in ANGLE
  * CVE-2026-9880: Insufficient validation of untrusted input in WebGL
  * CVE-2026-9881: Use after free in Bluetooth
  * CVE-2026-9882: Integer overflow in ANGLE
  * CVE-2026-9883: Use after free in Base
  * CVE-2026-9884: Use after free in Browser
  * CVE-2026-9885: Insufficient validation of untrusted input in UI
  * CVE-2026-9886: Use after free in Base
  * CVE-2026-9887: Use after free in Proxy
  * CVE-2026-9888: Use after free in WebView
  * CVE-2026-9889: Out of bounds read and write in Dawn
  * CVE-2026-9890: Use after free in XR
  * CVE-2026-9891: Use after free in Extensions
  * CVE-2026-9892: Inappropriate implementation in Skia
  * CVE-2026-9893: Use after free in Skia
  * CVE-2026-9894: Use after free in GPU
  * CVE-2026-9895: Out of bounds read in GPU
  * CVE-2026-9896: Out of bounds write in V8
  * CVE-2026-9897: Use after free in DOM
  * CVE-2026-9898: Insufficient validation of untrusted input in GPU
  * CVE-2026-9899: Use after free in ANGLE
  * CVE-2026-9900: Out of bounds write in ANGLE
  * CVE-2026-9901: Use after free in ANGLE
  * CVE-2026-9902: Use after free in Accessibility
  * CVE-2026-9903: Insufficient validation of untrusted input in Site Isolation
  * CVE-2026-9904: Use after free in ANGLE
  * CVE-2026-9905: Use after free in Accessibility
  * CVE-2026-9906: Out of bounds write in GPU
  * CVE-2026-9907: Out of bounds read in Dawn
  * CVE-2026-9908: Out of bounds read in ANGLE
  * CVE-2026-9909: Integer overflow in Skia
  * CVE-2026-9910: Out of bounds memory access in ANGLE
  * CVE-2026-9911: Integer overflow in ANGLE
  * CVE-2026-9912: Inappropriate implementation in GPU
  * CVE-2026-9913: Inappropriate implementation in ANGLE
  * CVE-2026-9914: Insufficient validation of untrusted input in ANGLE
  * CVE-2026-9915: Heap buffer overflow in ANGLE
  * CVE-2026-9916: Out of bounds write in ANGLE
  * CVE-2026-9917: Uninitialized Use in WebGL
  * CVE-2026-9918: Inappropriate implementation in Tint
  * CVE-2026-9919: Out of bounds read in WebGL
  * CVE-2026-9920: Uninitialized Use in GPU
  * CVE-2026-9921: Uninitialized Use in WebGL
  * CVE-2026-9922: Use after free in GPU
  * CVE-2026-9923: Use after free in Skia
  * CVE-2026-9924: Heap buffer overflow in ANGLE
  * CVE-2026-9925: Use after free in ANGLE
  * CVE-2026-9926: Heap buffer overflow in ANGLE
  * CVE-2026-9927: Use after free in ANGLE
  * CVE-2026-9928: Out of bounds read in ANGLE
  * CVE-2026-9929: Inappropriate implementation in WebGL
  * CVE-2026-9930: Out of bounds write in Dawn
  * CVE-2026-9931: Use after free in GPU
  * CVE-2026-9932: Use after free in ANGLE
  * CVE-2026-9933: Use after free in Input
  * CVE-2026-9934: Use after free in Aura
  * CVE-2026-9935: Uninitialized Use in ANGLE
  * CVE-2026-9936: Use after free in GFX
  * CVE-2026-9937: Use after free in UI
  * CVE-2026-9938: Inappropriate implementation in V8
  * CVE-2026-9939: Heap buffer overflow in WebCodecs
  * CVE-2026-9940: Heap buffer overflow in ANGLE
  * CVE-2026-9941: Use after free in ANGLE
  * CVE-2026-9942: Uninitialized Use in ANGLE
  * CVE-2026-9943: Out of bounds read in WebGL
  * CVE-2026-9944: Uninitialized Use in ANGLE
  * CVE-2026-9945: Use after free in Media
  * CVE-2026-9946: Use after free in ANGLE
  * CVE-2026-9947: Use after free in XML
  * CVE-2026-9948: Use after free in Views
  * CVE-2026-9949: Use after free in Core
  * CVE-2026-9950: Insufficient validation of untrusted input in iOS
  * CVE-2026-9951: Use after free in UI
  * CVE-2026-9952: Use after free in WebAudio
  * CVE-2026-9953: Out of bounds read in ANGLE
  * CVE-2026-9954: Use after free in TabStrip
  * CVE-2026-9955: Inappropriate implementation in iOS
  * CVE-2026-9956: Use after free in iOS
  * CVE-2026-9957: Use after free in PDF
  * CVE-2026-9958: Use after free in PDFium
  * CVE-2026-9959: Race in WebRTC
  * CVE-2026-9960: Integer overflow in PDFium
  * CVE-2026-9961: Use after free in SurfaceCapture
  * CVE-2026-9962: Use after free in WebRTC
  * CVE-2026-9963: Uninitialized Use in iOS
  * CVE-2026-9964: Use after free in Bluetooth
  * CVE-2026-9965: Out of bounds write in ANGLE
  * CVE-2026-9966: Integer overflow in XML
  * CVE-2026-9967: Out of bounds write in GPU
  * CVE-2026-9968: Integer overflow in V8
  * CVE-2026-9969: Insufficient validation of untrusted input in ANGLE
  * CVE-2026-9970: Use after free in WebGL
  * CVE-2026-9971: Inappropriate implementation in iOS
  * CVE-2026-9972: Uninitialized Use in Gamepad
  * CVE-2026-9973: Out of bounds write in V8
  * CVE-2026-9974: Out of bounds write in GPU
  * CVE-2026-9975: Out of bounds read and write in ANGLE
  * CVE-2026-9976: Inappropriate implementation in USB
  * CVE-2026-9977: Insufficient validation of untrusted input in WebShare
  * CVE-2026-9978: Use after free in Glic
  * CVE-2026-9979: Insufficient validation of untrusted input in Input
  * CVE-2026-9980: Insufficient validation of untrusted input in Printing
  * CVE-2026-9981: Inappropriate implementation in Skia
  * CVE-2026-9982: Insufficient validation of untrusted input in ANGLE
  * CVE-2026-9983: Type Confusion in Skia
  * CVE-2026-9984: Use after free in UI
  * CVE-2026-9985: Insufficient validation of untrusted input in Media
  * CVE-2026-9986: Insufficient validation of untrusted input in OptimizationGuide
  * CVE-2026-9987: Insufficient validation of untrusted input in WebAppInstalls
  * CVE-2026-9988: Use after free in WebRTC
  * CVE-2026-9989: Inappropriate implementation in Media
  * CVE-2026-9990: Use after free in WebAppInstalls
  * CVE-2026-9991: Inappropriate implementation in Media
  * CVE-2026-9992: Use after free in Network
  * CVE-2026-9993: Use after free in Views
  * CVE-2026-9994: Use after free in Core
  * CVE-2026-9995: Use after free in WebXR
  * CVE-2026-9996: Out of bounds read in WebRTC
  * CVE-2026-9997: Use after free in Input
  * CVE-2026-9998: Integer overflow in Skia
  * CVE-2026-9999: Inappropriate implementation in ANGLE
  * CVE-2026-10000: Use after free in Passwords
  * CVE-2026-10001: Use after free in PerformanceManager
  * CVE-2026-10002: Use after free in PDFium
  * CVE-2026-10003: Use after free in Views
  * CVE-2026-10004: Insufficient validation of untrusted input in Passwords
  * CVE-2026-10005: Use after free in WebAppInstalls
  * CVE-2026-10006: Race in WebAudio
  * CVE-2026-10007: Use after free in SVG
  * CVE-2026-10008: Uninitialized Use in GPU
  * CVE-2026-10009: Integer overflow in Skia
  * CVE-2026-10010: Inappropriate implementation in Input
  * CVE-2026-10011: Inappropriate implementation in Skia
  * CVE-2026-10012: Use after free in Skia
  * CVE-2026-10013: Use after free in WebCodecs
  * CVE-2026-10014: Use after free in WebMIDI
  * CVE-2026-10015: Integer overflow in WTF
  * CVE-2026-10016: Use after free in DOM
  * CVE-2026-10017: Out of bounds read in Headless
  * CVE-2026-10018: Integer overflow in ANGLE
  * CVE-2026-10019: Integer overflow in ANGLE
  * CVE-2026-10020: Insufficient validation of untrusted input in Skia
  * CVE-2026-10021: Insufficient validation of untrusted input in USB
  * CVE-2026-10022: Type Confusion in V8

* Wed May 20 2026 Than Ngo <than@redhat.com> - 148.0.7778.178-1
- Update to 148.0.7778.178
  * CVE-2026-9111: Use after free in WebRTC
  * CVE-2026-9110: Inappropriate implementation in UI
  * CVE-2026-9112: Use after free in GPU
  * CVE-2026-9113: Out of bounds read in GPU
  * CVE-2026-9114: Use after free in QUIC
  * CVE-2026-9115: Insufficient policy enforcement in Service Worker
  * CVE-2026-9116: Insufficient policy enforcement in ServiceWorker
  * CVE-2026-9117: Type Confusion in GFX
  * CVE-2026-9118: Use after free in XR
  * CVE-2026-9119: Heap buffer overflow in WebRTC
  * CVE-2026-9120: Use after free in WebRTC
  * CVE-2026-9126: Use after free in DOM
  * CVE-2026-9121: Out of bounds read in GPU
  * CVE-2026-9122: Out of bounds read in GPU
  * CVE-2026-9123: Heap buffer overflow in Chromecast
  * CVE-2026-9124: Insufficient validation of untrusted input in Input
- Backport upstream patches to improve auto dark image inversion logic
- Update default chromium browser config

* Fri May 15 2026 Than Ngo <than@redhat.com> - 148.0.7778.167-1
- Update to 148.0.7778.167
   * CVE-2026-8509: Heap buffer overflow in WebML
   * CVE-2026-8510: Integer overflow in Skia
   * CVE-2026-8511: Use after free in UI
   * CVE-2026-8512: Use after free in FileSystem
   * CVE-2026-8513: Use after free in Input
   * CVE-2026-8514: Use after free in Aura
   * CVE-2026-8515: Use after free in HID
   * CVE-2026-8516: Insufficient validation of untrusted input in DataTransfer
   * CVE-2026-8517: Object lifecycle issue in WebShare
   * CVE-2026-8518: Use after free in Blink
   * CVE-2026-8519: Integer overflow in ANGLE
   * CVE-2026-8520: Race in Payments
   * CVE-2026-8521: Use after free in Tab Groups
   * CVE-2026-8522: Use after free in Downloads
   * CVE-2026-8523: Use after free in Mojo
   * CVE-2026-8558: Out of bounds write in Fonts
   * CVE-2026-8524: Out of bounds write in WebAudio
   * CVE-2026-8525: Heap buffer overflow in ANGLE
   * CVE-2026-8526: Out of bounds write in WebRTC
   * CVE-2026-8527: Insufficient validation of untrusted input in Downloads
   * CVE-2026-8528: Insufficient validation of untrusted input in SiteIsolation
   * CVE-2026-8529: Heap buffer overflow in Codecs
   * CVE-2026-8530: Use after free in Network
   * CVE-2026-8531: Heap buffer overflow in WebML
   * CVE-2026-8532: Integer overflow in XML
   * CVE-2026-8533: Use after free in Accessibility
   * CVE-2026-8534: Integer overflow in GPU
   * CVE-2026-8535: Out of bounds read in Media
   * CVE-2026-8536: Insufficient validation of untrusted input in ReadingMode
   * CVE-2026-8537: Insufficient policy enforcement in ViewTransitions
   * CVE-2026-8538: Insufficient validation of untrusted input in GPU
   * CVE-2026-8539: Script injection in SanitizerAPI
   * CVE-2026-8540: Type Confusion in V8
   * CVE-2026-8541: Out of bounds read in UI
   * CVE-2026-8542: Use after free in Core
   * CVE-2026-8543: Out of bounds read in FileSystem
   * CVE-2026-8544: Use after free in Media
   * CVE-2026-8545: Object corruption in Compositing
   * CVE-2026-8546: Out of bounds read in GPU
   * CVE-2026-8547: Insufficient policy enforcement in Passwords
   * CVE-2026-8548: Out of bounds write in Media
   * CVE-2026-8549: Use after free in Media
   * CVE-2026-8550: Use after free in Google Lens
   * CVE-2026-8551: Use after free in Downloads
   * CVE-2026-8552: Heap buffer overflow in GPU
   * CVE-2026-8553: Use after free in GPU
   * CVE-2026-8554: Type Confusion in ANGLE
   * CVE-2026-8555: Use after free in GTK
   * CVE-2026-8556: Inappropriate implementation in ANGLE
   * CVE-2026-8557: Use after free in Accessibility
   * CVE-2026-8559: Integer overflow in Internationalization
   * CVE-2026-8560: Heap buffer overflow in SwiftShader
   * CVE-2026-8561: Incorrect security UI in Fullscreen
   * CVE-2026-8562: Side-channel information leakage in Navigation
   * CVE-2026-8563: Insufficient policy enforcement in IFrame Sandbox
   * CVE-2026-8564: Incorrect security UI in Downloads
   * CVE-2026-8565: Inappropriate implementation in Downloads
   * CVE-2026-8566: Insufficient policy enforcement in Payments
   * CVE-2026-8567: Integer overflow in ANGLE
   * CVE-2026-8568: Insufficient policy enforcement in AI
   * CVE-2026-8569: Out of bounds write in Codecs
   * CVE-2026-8570: Type Confusion in V8
   * CVE-2026-8571: Insufficient policy enforcement in GPU
   * CVE-2026-8572: Insufficient policy enforcement in Network
   * CVE-2026-8573: Integer overflow in Codecs
   * CVE-2026-8574: Use after free in Core
   * CVE-2026-8575: Use after free in UI
   * CVE-2026-8576: Inappropriate implementation in CORS
   * CVE-2026-8577: Integer overflow in Fonts
   * CVE-2026-8578: Out of bounds read in GPU
   * CVE-2026-8579: Insufficient validation of untrusted input in Skia
   * CVE-2026-8580: Use after free in Mojo
   * CVE-2026-8581: Use after free in GPU
   * CVE-2026-8582: Object lifecycle issue in Dawn
   * CVE-2026-8583: Insufficient policy enforcement in WebXR
   * CVE-2026-8584: Inappropriate implementation in Views
   * CVE-2026-8585: Inappropriate implementation in Media
   * CVE-2026-8586: Inappropriate implementation in Chromoting
   * CVE-2026-8587: Use after free in Extensions

* Wed May 06 2026 Than Ngo <than@redhat.com> - 148.0.7778.96-1
- Update to 148.0.7778.96
   * CVE-2026-7896: Integer overflow in Blink
   * CVE-2026-7897: Use after free in Mobile
   * CVE-2026-7898: Use after free in Chromoting
   * CVE-2026-7899: Out of bounds read and write in V8
   * CVE-2026-7900: Heap buffer overflow in ANGLE
   * CVE-2026-7901: Use after free in ANGLE
   * CVE-2026-7902: Out of bounds memory access in V8
   * CVE-2026-7903: Integer overflow in ANGLE
   * CVE-2026-7904: Out of bounds read in Fonts
   * CVE-2026-7905: Insufficient validation of untrusted input in Media
   * CVE-2026-7906: Use after free in SVG
   * CVE-2026-7907: Use after free in DOM
   * CVE-2026-7908: Use after free in Fullscreen
   * CVE-2026-7909: Inappropriate implementation in ServiceWorker
   * CVE-2026-7910: Use after free in Views
   * CVE-2026-7911: Use after free in Aura
   * CVE-2026-7912: Integer overflow in GPU
   * CVE-2026-7913: Insufficient policy enforcement in DevTools
   * CVE-2026-7914: Type Confusion in Accessibility
   * CVE-2026-7915: Insufficient data validation in DevTools
   * CVE-2026-7916: Insufficient data validation in InterestGroups
   * CVE-2026-7917: Use after free in Fullscreen
   * CVE-2026-7918: Use after free in GPU
   * CVE-2026-7919: Use after free in Aura
   * CVE-2026-7920: Use after free in Skia
   * CVE-2026-7921: Use after free in Passwords
   * CVE-2026-7922: Use after free in ServiceWorker
   * CVE-2026-7923: Out of bounds write in Skia
   * CVE-2026-7924: Uninitialized Use in Dawn
   * CVE-2026-7925: Use after free in Chromoting
   * CVE-2026-7926: Use after free in PresentationAPI
   * CVE-2026-7927: Type Confusion in Runtime
   * CVE-2026-7928: Use after free in WebRTC
   * CVE-2026-7929: Use after free in MediaRecording
   * CVE-2026-7930: Insufficient validation of untrusted input in Cookies
   * CVE-2026-7931: Insufficient validation of untrusted input in iOS
   * CVE-2026-7932: Insufficient policy enforcement in Downloads
   * CVE-2026-7933: Out of bounds read in WebCodecs
   * CVE-2026-7934: Insufficient validation of untrusted input in Popup Blocker
   * CVE-2026-7935: Inappropriate implementation in Speech
   * CVE-2026-7936: Object lifecycle issue in V8
   * CVE-2026-7937: Insufficient policy enforcement in DevTools
   * CVE-2026-7938: Use after free in CSS
   * CVE-2026-7939: Inappropriate implementation in SanitizerAPI
   * CVE-2026-7940: Use after free in V8
   * CVE-2026-7941: Insufficient validation of untrusted input in Mobile
   * CVE-2026-7942: Integer overflow in ANGLE
   * CVE-2026-7943: Insufficient validation of untrusted input in ANGLE
   * CVE-2026-7944: Insufficient validation of untrusted input in Persistent Cache
   * CVE-2026-7945: Insufficient validation of untrusted input in COOP
   * CVE-2026-7946: Insufficient policy enforcement in WebUI
   * CVE-2026-7947: Insufficient validation of untrusted input in Network
   * CVE-2026-7948: Race in Chromoting
   * CVE-2026-7949: Out of bounds read in Skia
   * CVE-2026-7950: Out of bounds read and write in GFX
   * CVE-2026-7951: Out of bounds write in WebRTC
   * CVE-2026-7952: Insufficient policy enforcement in Extensions
   * CVE-2026-7953: Insufficient validation of untrusted input in Omnibox
   * CVE-2026-7954: Race in Shared Storage
   * CVE-2026-7955: Uninitialized Use in GPU
   * CVE-2026-7956: Use after free in Navigation
   * CVE-2026-7957: Out of bounds write in Media
   * CVE-2026-7958: Inappropriate implementation in ServiceWorker
   * CVE-2026-7959: Inappropriate implementation in Navigation
   * CVE-2026-7960: Race in Speech
   * CVE-2026-7961: Insufficient validation of untrusted input in Permissions
   * CVE-2026-7962: Insufficient policy enforcement in DirectSockets
   * CVE-2026-7963: Inappropriate implementation in ServiceWorker
   * CVE-2026-7964: Insufficient validation of untrusted input in FileSystem
   * CVE-2026-7965: Insufficient validation of untrusted input in DevTools
   * CVE-2026-7966: Insufficient validation of untrusted input in SiteIsolation
   * CVE-2026-7967: Insufficient validation of untrusted input in Navigation
   * CVE-2026-7968: Insufficient validation of untrusted input in CORS
   * CVE-2026-7969: Integer overflow in Network
   * CVE-2026-7970: Use after free in TopChrome
   * CVE-2026-7971: Inappropriate implementation in ORB
   * CVE-2026-7972: Uninitialized Use in GPU
   * CVE-2026-7973: Integer overflow in Dawn
   * CVE-2026-7974: Use after free in Blink
   * CVE-2026-7975: Use after free in DevTools
   * CVE-2026-7976: Use after free in Views
   * CVE-2026-7977: Inappropriate implementation in Canvas
   * CVE-2026-7978: Inappropriate implementation in Companion
   * CVE-2026-7979: Inappropriate implementation in Media
   * CVE-2026-7980: Use after free in WebAudio
   * CVE-2026-7981: Out of bounds read in Codecs
   * CVE-2026-7982: Uninitialized Use in WebCodecs
   * CVE-2026-7983: Out of bounds read in Dawn
   * CVE-2026-7984: Use after free in ReadingMode
   * CVE-2026-7985: Use after free in GPU
   * CVE-2026-7986: Insufficient policy enforcement in Autofill
   * CVE-2026-7987: Use after free in WebRTC
   * CVE-2026-7988: Type Confusion in WebRTC
   * CVE-2026-7989: Insufficient data validation in DataTransfer
   * CVE-2026-7990: Insufficient validation of untrusted input in Updater
   * CVE-2026-7991: Use after free in UI
   * CVE-2026-7992: Insufficient validation of untrusted input in UI
   * CVE-2026-7993: Insufficient validation of untrusted input in Payments
   * CVE-2026-7994: Inappropriate implementation in Chromoting
   * CVE-2026-7995: Out of bounds read in AdFilter
   * CVE-2026-7996: Insufficient validation of untrusted input in SSL
   * CVE-2026-7997: Insufficient validation of untrusted input in Updater
   * CVE-2026-7998: Insufficient validation of untrusted input in Dialog
   * CVE-2026-7999: Inappropriate implementation in V8
   * CVE-2026-8000: Insufficient validation of untrusted input in ChromeDriver
   * CVE-2026-8001: Use after free in Printing
   * CVE-2026-8002: Use after free in Audio
   * CVE-2026-8003: Insufficient validation of untrusted input in TabGroups
   * CVE-2026-8004: Insufficient policy enforcement in DevTools
   * CVE-2026-8005: Insufficient validation of untrusted input in Cast
   * CVE-2026-8006: Insufficient policy enforcement in DevTools
   * CVE-2026-8007: Insufficient validation of untrusted input in Cast
   * CVE-2026-8008: Inappropriate implementation in DevTools
   * CVE-2026-8009: Inappropriate implementation in Cast
   * CVE-2026-8010: Insufficient validation of untrusted input in SiteIsolation
   * CVE-2026-8011: Insufficient policy enforcement in Search
   * CVE-2026-8012: Inappropriate implementation in MHTML
   * CVE-2026-8013: Insufficient validation of untrusted input in FedCM
   * CVE-2026-8014: Inappropriate implementation in Preload
   * CVE-2026-8015: Inappropriate implementation in Media
   * CVE-2026-8016: Use after free in WebRTC
   * CVE-2026-8017: Side-channel information leakage in Media
   * CVE-2026-8018: Insufficient policy enforcement in DevTools
   * CVE-2026-8019: Insufficient policy enforcement in WebApp
   * CVE-2026-8020: Uninitialized Use in GPU
   * CVE-2026-8021: Script injection in UI
   * CVE-2026-8022: Inappropriate implementation in MHTML
- Remove old remoting-no-tests patch
- Remove fix_GL_native_pixmap_import_support_reset_in_GpuInit patch
- Fix build error causing by sanitizer defines in GN
- Refresh rust-enable-unstable_feature patch
- Fix build error with system rust compiler
- Fix build error causing by new clang++ options which are not supported yet
- Fix build error causing by harfbuzz library rename

* Wed Apr 29 2026 Than Ngo <than@redhat.com> - 147.0.7727.137-1
- Update to 147.0.7727.137
   * Critical CVE-2026-7363: Use after free in Canvas
   * Critical CVE-2026-7361: Use after free in iOS
   * Critical CVE-2026-7344: Use after free in Accessibility
   * Critical CVE-2026-7343: Use after free in Views
   * High CVE-2026-7333: Use after free in GPU
   * High CVE-2026-7360: Insufficient validation of untrusted input in Compositing
   * High CVE-2026-7359: Use after free in ANGLE
   * High CVE-2026-7358: Use after free in Animation
   * High CVE-2026-7334: Use after free in Views
   * High CVE-2026-7357: Use after free in GPU
   * High CVE-2026-7356: Use after free in Navigation
   * High CVE-2026-7354: Out of bounds read and write in Angle
   * High CVE-2026-7353: Heap buffer overflow in Skia
   * High CVE-2026-7352: Use after free in Media
   * High CVE-2026-7351: Race in MHTML
   * High CVE-2026-7350: Use after free in WebMIDI
   * High CVE-2026-7349: Use after free in Cast
   * High CVE-2026-7348: Use after free in Codecs
   * High CVE-2026-7335: Use after free in media
   * High CVE-2026-7336: Use after free in WebRTC
   * High CVE-2026-7337: Type Confusion in V8
   * High CVE-2026-7347: Use after free in Chromoting
   * High CVE-2026-7346: Inappropriate implementation in Tint
   * High CVE-2026-7345: Insufficient validation of untrusted input in Feedback
   * High CVE-2026-7338: Use after free in Cast
   * High CVE-2026-7342: Use after free in WebView
   * High CVE-2026-7341: Use after free in WebRTC
   * Medium CVE-2026-7339: Heap buffer overflow in WebRTC
   * Medium CVE-2026-7340: Integer overflow in ANGLE
   * Medium CVE-2026-7355: Use after free in Media

* Sun Apr 26 2026 Than Ngo <than@redhat.com> - 147.0.7727.116-2
- Fix FTBFS with rust 1.95
- Backport the upstream fix GL native pixmap import support reset in GpuInit

* Thu Apr 23 2026 Than Ngo <than@redhat.com> - 147.0.7727.116-1
- Update to 147.0.7727.116
  * High CVE-2026-6919: Use after free in DevTools
  * High CVE-2026-6920: Out of bounds read in GPU
  * Medium CVE-2026-6921: Race in GPU
- Fix rhbz#2458171, unexpanded macros in manpage

* Wed Apr 15 2026 Than Ngo <than@redhat.com> - 147.0.7727.101-1
- Update to 147.0.7727.101
  * Critical CVE-2026-6296: Heap buffer overflow in ANGLE
  * Critical CVE-2026-6297: Use after free in Proxy
  * Critical CVE-2026-6298: Heap buffer overflow in Skia
  * Critical CVE-2026-6299: Use after free in Prerender
  * Critical CVE-2026-6358: Use after free in XR
  * High CVE-2026-6359: Use after free in Video
  * High CVE-2026-6300: Use after free in CSS
  * High CVE-2026-6301: Type Confusion in Turbofan
  * High CVE-2026-6302: Use after free in Video
  * High CVE-2026-6303: Use after free in Codecs
  * High CVE-2026-6304: Use after free in Graphite
  * High CVE-2026-6305: Heap buffer overflow in PDFium
  * High CVE-2026-6306: Heap buffer overflow in PDFium
  * High CVE-2026-6307: Type Confusion in Turbofan
  * High CVE-2026-6308: Out of bounds read in Media
  * High CVE-2026-6309: Use after free in Viz
  * High CVE-2026-6360: Use after free in FileSystem
  * High CVE-2026-6310: Use after free in Dawn
  * High CVE-2026-6311: Uninitialized Use in Accessibility
  * High CVE-2026-6312: Insufficient policy enforcement in Passwords
  * High CVE-2026-6313: Insufficient policy enforcement in CORS
  * High CVE-2026-6314: Out of bounds write in GPU
  * High CVE-2026-6315: Use after free in Permissions
  * High CVE-2026-6316: Use after free in Forms
  * High CVE-2026-6361: Heap buffer overflow in PDFium
  * High CVE-2026-6362: Use after free in Codecs
  * High CVE-2026-6317: Use after free in Cast
  * Medium CVE-2026-6363: Type Confusion in V8
  * Medium CVE-2026-6318: Use after free in Codecs
  * Medium CVE-2026-6319: Use after free in Payments
  * Medium CVE-2026-6364: Out of bounds read in Skia

* Thu Apr 09 2026 Than Ngo <than@redhat.com> - 147.0.7727.55-1
- Update to 147.0.7727.55
  * Critical CVE-2026-5858: Heap buffer overflow in WebML
  * Critical CVE-2026-5859: Integer overflow in WebML
  * High CVE-2026-5860: Use after free in WebRTC
  * High CVE-2026-5861: Use after free in V8
  * High CVE-2026-5862: Inappropriate implementation in V8
  * High CVE-2026-5863: Inappropriate implementation in V8
  * High CVE-2026-5864: Heap buffer overflow in WebAudio
  * High CVE-2026-5865: Type Confusion in V8
  * High CVE-2026-5866: Use after free in Media
  * High CVE-2026-5867: Heap buffer overflow in WebML
  * High CVE-2026-5868: Heap buffer overflow in ANGLE
  * High CVE-2026-5869: Heap buffer overflow in WebML
  * High CVE-2026-5870: Integer overflow in Skia
  * High CVE-2026-5871: Type Confusion in V8
  * High CVE-2026-5872: Use after free in Blink
  * High CVE-2026-5873: Out of bounds read and write in V8
  * Medium CVE-2026-5874: Use after free in PrivateAI
  * Medium CVE-2026-5875: Policy bypass in Blink
  * Medium CVE-2026-5876: Side-channel information leakage in Navigation
  * Medium CVE-2026-5877: Use after free in Navigation
  * Medium CVE-2026-5878: Incorrect security UI in Blink
  * Medium CVE-2026-5879: Insufficient validation of untrusted input in ANGLE
  * Medium CVE-2026-5880: Incorrect security UI in browser UI
  * Medium CVE-2026-5881: Policy bypass in LocalNetworkAccess
  * Medium CVE-2026-5882: Incorrect security UI in Fullscreen
  * Medium CVE-2026-5883: Use after free in Media
  * Medium CVE-2026-5884: Insufficient validation of untrusted input in Media
  * Medium CVE-2026-5885: Insufficient validation of untrusted input in WebML
  * Medium CVE-2026-5886: Out of bounds read in WebAudio
  * Medium CVE-2026-5887: Insufficient validation of untrusted input in Downloads
  * Medium CVE-2026-5888: Uninitialized Use in WebCodecs
  * Medium CVE-2026-5889: Cryptographic Flaw in PDFium
  * Medium CVE-2026-5890: Race in WebCodecs
  * Medium CVE-2026-5891: Insufficient policy enforcement in browser UI
  * Medium CVE-2026-5892: Insufficient policy enforcement in PWAs
  * Medium CVE-2026-5893: Race in V8
  * Low CVE-2026-5894: Inappropriate implementation in PDF
  * Low CVE-2026-5895: Incorrect security UI in Omnibox
  * Low CVE-2026-5896: Policy bypass in Audio
  * Low CVE-2026-5897: Incorrect security UI in Downloads
  * Low CVE-2026-5898: Incorrect security UI in Omnibox
  * Low CVE-2026-5899: Incorrect security UI in History Navigation
  * Low CVE-2026-5900: Policy bypass in Downloads
  * Low CVE-2026-5901: Policy bypass in DevTools
  * Low CVE-2026-5902: Race in Media
  * Low CVE-2026-5903: Policy bypass in IFrameSandbox
  * Low CVE-2026-5904: Use after free in V8
  * Low CVE-2026-5905: Incorrect security UI in Permissions
  * Low CVE-2026-5906: Incorrect security UI in Omnibox
  * Low CVE-2026-5907: Insufficient data validation in Media
  * Low CVE-2026-5908: Integer overflow in Media
  * Low CVE-2026-5909: Integer overflow in Media
  * Low CVE-2026-5910: Integer overflow in Media
  * Low CVE-2026-5911: Policy bypass in ServiceWorkers
  * Low CVE-2026-5912: Integer overflow in WebRTC
  * Low CVE-2026-5913: Out of bounds read in Blink
  * Low CVE-2026-5914: Type Confusion in CSS
  * Low CVE-2026-5915: Insufficient validation of untrusted input in WebML
  * Low CVE-2026-5918: Inappropriate implementation in Navigation
  * Low CVE-2026-5919: Insufficient validation of untrusted input in WebSockets

* Wed Apr 01 2026 Than Ngo <than@redhat.com> - 146.0.7680.177-1
- Update to 146.0.7680.177
  * High CVE-2026-5273: Use after free in CSS
  * High CVE-2026-5272: Heap buffer overflow in GPU
  * High CVE-2026-5274: Integer overflow in Codecs
  * High CVE-2026-5275: Heap buffer overflow in ANGLE
  * High CVE-2026-5276: Insufficient policy enforcement in WebUSB
  * High CVE-2026-5277: Integer overflow in ANGLE
  * High CVE-2026-5278: Use after free in Web MIDI
  * High CVE-2026-5279: Object corruption in V8
  * High CVE-2026-5280: Use after free in WebCodecs
  * High CVE-2026-5281: Use after free in Dawn
  * High CVE-2026-5282: Out of bounds read in WebCodecs
  * High CVE-2026-5283: Inappropriate implementation in ANGLE
  * High CVE-2026-5284: Use after free in Dawn
  * High CVE-2026-5285: Use after free in WebGL
  * High CVE-2026-5286: Use after free in Dawn
  * High CVE-2026-5287: Use after free in PDF
  * High CVE-2026-5288: Use after free in WebView
  * High CVE-2026-5289: Use after free in Navigation
  * High CVE-2026-5290: Use after free in Compositing
  * Medium CVE-2026-5291: Inappropriate implementation in WebGL
  * Medium CVE-2026-5292: Out of bounds read in WebCodecs

* Tue Mar 24 2026 Than Ngo <than@redhat.com> - 146.0.7680.164-1
- Update to 146.0.7680.164
  * High CVE-2026-4673: Heap buffer overflow in WebAudio
  * High CVE-2026-4674: Out of bounds read in CSS
  * High CVE-2026-4675: Heap buffer overflow in WebGL
  * High CVE-2026-4676: Use after free in Dawn
  * High CVE-2026-4677: Out of bounds read in WebAudio
  * High CVE-2026-4678: Use after free in WebGPU
  * High CVE-2026-4679: Integer overflow in Fonts
  * High CVE-2026-4680: Use after free in FedCM

* Fri Mar 20 2026 Than Ngo <than@redhat.com> - 146.0.7680.153-1
- Update to 146.0.7680.153
  * CVE-2026-4439: Out of bounds memory access in WebGL
  * CVE-2026-4440: Out of bounds read and write in WebGL
  * CVE-2026-4441: Use after free in Base
  * CVE-2026-4442: Heap buffer overflow in CSS
  * CVE-2026-4443: Heap buffer overflow in WebAudio
  * CVE-2026-4444: Stack buffer overflow in WebRTC
  * CVE-2026-4445: Use after free in WebRTC
  * CVE-2026-4446: Use after free in WebRTC
  * CVE-2026-4447: Inappropriate implementation in V8
  * CVE-2026-4448: Heap buffer overflow in ANGLE
  * CVE-2026-4449: Use after free in Blink
  * CVE-2026-4450: Out of bounds write in V8
  * CVE-2026-4451: Insufficient validation of untrusted input in Navigation
  * CVE-2026-4452: Integer overflow in ANGLE
  * CVE-2026-4453: Integer overflow in Dawn
  * CVE-2026-4454: Use after free in Network
  * CVE-2026-4455: Heap buffer overflow in PDFium
  * CVE-2026-4456: Use after free in Digital Credentials API
  * CVE-2026-4457: Type Confusion in V8
  * CVE-2026-4458: Use after free in Extensions
  * CVE-2026-4459: Out of bounds read and write in WebAudio
  * CVE-2026-4460: Out of bounds read in Skia
  * CVE-2026-4461: Inappropriate implementation in V8
  * CVE-2026-4462: Out of bounds read in Blink
  * CVE-2026-4463: Heap buffer overflow in WebRTC
  * CVE-2026-4464: Integer overflow in ANGLE

* Sat Mar 14 2026 Than Ngo <than@redhat.com> - 146.0.7680.80-1
- Update to 146.0.7680.80
  * CVE-2026-3909: Out of bounds write in Skia

* Fri Mar 13 2026 Than Ngo <than@redhat.com> - 146.0.7680.75-1
- Update to 146.0.7680.75
  * CVE-2026-3910: Inappropriate implementation in V8

* Thu Mar 12 2026 Than Ngo <than@redhat.com> - 146.0.7680.71-1
- Update to 146.0.7680.71
  * CVE-2026-3913: Heap buffer overflow in WebML
  * CVE-2026-3914: Integer overflow in WebML
  * CVE-2026-3915: Heap buffer overflow in WebML
  * CVE-2026-3916: Out of bounds read in Web Speech
  * CVE-2026-3917: Use after free in Agents
  * CVE-2026-3918: Use after free in WebMCP
  * CVE-2026-3919: Use after free in Extensions
  * CVE-2026-3920: Out of bounds memory access in WebML
  * CVE-2026-3921: Use after free in TextEncoding
  * CVE-2026-3922: Use after free in MediaStream
  * CVE-2026-3923: Use after free in WebMIDI
  * CVE-2026-3924: Use after free in WindowDialog
  * CVE-2026-3925: Incorrect security UI in LookalikeChecks
  * CVE-2026-3926: Out of bounds read in V8
  * CVE-2026-3927: Incorrect security UI in PictureInPicture
  * CVE-2026-3928: Insufficient policy enforcement in Extensions
  * CVE-2026-3929: Side-channel information leakage in ResourceTiming
  * CVE-2026-3930: Unsafe navigation in Navigation
  * CVE-2026-3931: Heap buffer overflow in Skia
  * CVE-2026-3932: Insufficient policy enforcement in PDF
  * CVE-2026-3934: Insufficient policy enforcement in ChromeDriver
  * CVE-2026-3935: Incorrect security UI in WebAppInstalls
  * CVE-2026-3936: Use after free in WebView
  * CVE-2026-3937: Incorrect security UI in Downloads
  * CVE-2026-3938: Insufficient policy enforcement in Clipboard
  * CVE-2026-3939: Insufficient policy enforcement in PDF
  * CVE-2026-3940: Insufficient policy enforcement in DevTools
  * CVE-2026-3941: Insufficient policy enforcement in DevTools
  * CVE-2026-3942: Incorrect security UI in PictureInPicture

* Fri Mar 06 2026 Than Ngo <than@redhat.com> - 145.0.7632.159-1
- Update to 145.0.7632.159
  * CVE-2026-3536: Integer overflow in ANGLE
  * CVE-2026-3537: Object lifecycle issue in PowerVR
  * CVE-2026-3538: Integer overflow in Skia
  * CVE-2026-3539: Object lifecycle issue in DevTools
  * CVE-2026-3540: Inappropriate implementation in WebAudio
  * CVE-2026-3541: Inappropriate implementation in CSS
  * CVE-2026-3542: Inappropriate implementation in WebAssembly
  * CVE-2026-3543: Inappropriate implementation in V8
  * CVE-2026-3544: Heap buffer overflow in WebCodecs
  * CVE-2026-3545: Insufficient data validation in Navigation

* Tue Feb 24 2026 Than Ngo <than@redhat.com> - 145.0.7632.116-1
- Update to 145.0.7632.116
  * CVE-2026-3061: Out of bounds read in Media
  * CVE-2026-3062: Out of bounds read and write in Tint
  * CVE-2026-3063: Inappropriate implementation in DevTools

* Mon Feb 23 2026 Than Ngo <than@redhat.com> - 145.0.7632.109-1
- Update to 145.0.7632.109
  * CVE-2026-2648: Heap buffer overflow in PDFium
  * CVE-2026-2649: Integer overflow in V8
  * CVE-2026-2650: Heap buffer overflow in Media

* Sat Feb 14 2026 Than Ngo <than@redhat.com> - 145.0.7632.75-1
- Update to 145.0.7632.75
   * CVE-2026-2441: Use after free in CSS

* Thu Feb 12 2026 Than Ngo <than@redhat.com> - 145.0.7632.45-1
- Update to 145.0.7632.45
  * CVE-2026-2313: Use after free in CSS
  * CVE-2026-2314: Heap buffer overflow in Codecs
  * CVE-2026-2315: Inappropriate implementation in WebGPU
  * CVE-2026-2316: Insufficient policy enforcement in Frames
  * CVE-2026-2317: Inappropriate implementation in Animation
  * CVE-2026-2318: Inappropriate implementation in PictureInPicture
  * CVE-2026-2319: Race in DevTools
  * CVE-2026-2320: Inappropriate implementation in File input
  * CVE-2026-2321: Use after free in Ozone
  * CVE-2026-2322: Inappropriate implementation in File input
  * CVE-2026-2323: Inappropriate implementation in Downloads

* Thu Feb 05 2026 Than Ngo <than@redhat.com> - 144.0.7559.132-1
- Update to 144.0.7559.132
  * CVE-2026-1861: Heap buffer overflow in libvpx
  * CVE-2026-1862: Type Confusion in V8
- Add BR on esbuild
- Disable devtool bundle
- Update scripts for downloading the source

* Wed Jan 28 2026 Than Ngo <than@redhat.com> - 144.0.7559.109-1
- Update to 144.0.7559.109
  * CVE-2026-1504: Inappropriate implementation in Background Fetch API

* Wed Jan 21 2026 Than Ngo <than@redhat.com> - 144.0.7559.96-1
- Update to 144.0.7559.96
  * CVE-2026-1220: Race in V8

* Fri Jan 16 2026 Fedora Release Engineering <releng@fedoraproject.org> - 144.0.7559.59-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_44_Mass_Rebuild

* Fri Jan 16 2026 Fedora Release Engineering <releng@fedoraproject.org> - 144.0.7559.59-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_44_Mass_Rebuild

* Wed Jan 14 2026 Than Ngo <than@redhat.com> - 144.0.7559.59-1
- Update to 144.0.7559.59
  * CVE-2026-0899: Out of bounds memory access in V8
  * CVE-2026-0900: Inappropriate implementation in V8
  * CVE-2026-0901: Inappropriate implementation in Blink
  * CVE-2026-0902: Inappropriate implementation in V8
  * CVE-2026-0903: Insufficient validation of untrusted input in Downloads
  * CVE-2026-0904: Incorrect security UI in Digital Credentials
  * CVE-2026-0905: Insufficient policy enforcement in Network
  * CVE-2026-0906: Incorrect security UI
  * CVE-2026-0907: Incorrect security UI in Split View
  * CVE-2026-0908: Use after free in ANGLE

* Wed Jan 07 2026 Than Ngo <than@redhat.com> - 143.0.7499.192-1
- Update to 143.0.7499.192
  * High CVE-2026-0628: Insufficient policy enforcement in WebView tag
- Fix rhbz#2425338, Enable control flow integrity support for x86_64/aarch64
- Enable build for epel10.1

* Sat Dec 20 2025 Than Ngo <than@redhat.com> - 143.0.7499.169-1
- Update to 143.0.7499.169

* Wed Dec 17 2025 Than Ngo <than@redhat.com> - 143.0.7499.146-1
- Update to 143.0.7499.146
  * High CVE-2025-14765: Use after free in WebGPU
  * High CVE-2025-14766: Out of bounds read and write in V8
- Force dark mode when auto dark mode web content is on
- Remove omnibox-next-Improve-cutout-mouse-handling-for-Wayla patch, as it's merged

* Thu Dec 11 2025 Than Ngo <than@redhat.com> - 143.0.7499.109-2
- Enable gtk4 by default

* Thu Dec 11 2025 Than Ngo <than@redhat.com> - 143.0.7499.109-1
- Update to 143.0.7499.109
  * High: Under coordination
  * Medium CVE-2025-14372: Use after free in Password Manager
  * Medium CVE-2025-14373: Inappropriate implementation in Toolbar
- Workaround problem of auto dark mode inverting images and making them unreadable

* Tue Dec 09 2025 LuK1337 <priv.luk@gmail.com> - 143.0.7499.40-2
- Backport Wayland Omnibox bug fix from upstream

* Tue Dec 02 2025 Than Ngo <than@redhat.com> - 143.0.7499.40-1
- Update to 143.0.7499.40
  * High CVE-2025-13630: Type Confusion in V8
  * High CVE-2025-13631: Inappropriate implementation in Google Updater
  * High CVE-2025-13632: Inappropriate implementation in DevTools
  * High CVE-2025-13633: Use after free in Digital Credentials
  * Medium CVE-2025-13634: Inappropriate implementation in Downloads
  * Medium CVE-2025-13720: Bad cast in Loader
  * Medium CVE-2025-13721: Race in v8
  * Low CVE-2025-13635: Inappropriate implementation in Downloads
  * Low CVE-2025-13636: Inappropriate implementation in Split View
  * Low CVE-2025-13637: Inappropriate implementation in Downloads
  * Low CVE-2025-13638: Use after free in Media Stream
  * Low CVE-2025-13639: Inappropriate implementation in WebRTC
  * Low CVE-2025-13640: Inappropriate implementation in Passwords

* Mon Dec 01 2025 LuK1337 <priv.luk@gmail.com> - 142.0.7444.175-5
- Backport one more Wayland DnD bug fix from upstream

* Mon Nov 24 2025 Than Ngo <than@redhat.com> - 142.0.7444.175-4
- Enable system libcxx
- Fix link error when building with system libcxx
- Apply memory-allocator-dcheck-assert-fix for aarch64

* Thu Nov 20 2025 LuK1337 <priv.luk@gmail.com> - 142.0.7444.175-3
- Backport Wayland DnD bug fix from upstream

* Wed Nov 19 2025 Than Ngo <than@redhat.com> - 142.0.7444.175-2
- Fix typos in chromium.conf

* Tue Nov 18 2025 Than Ngo <than@redhat.com> - 142.0.7444.175-1
- Update to 142.0.7444.175
  * High CVE-2025-13223: Type Confusion in V8
  * High CVE-2025-13224: Type Confusion in V8

* Sat Nov 15 2025 LuK1337 <priv.luk@gmail.com> - 142.0.7444.162-2
- Disable LensOverlay feature by default

* Thu Nov 13 2025 Mamoru TASAKA <mtasaka@fedoraproject.org> - 142.0.7444.162-2
- Rebuild for ffmpeg 8 again

* Wed Nov 12 2025 Than Ngo <than@redhat.com> - 142.0.7444.162-1
- Update to 142.0.7444.162
  * High CVE-2025-13042: Inappropriate implementation in V8

* Tue Nov 11 2025 Dominik Mierzejewski <dominik@greysector.net> - 142.0.7444.134-2
- Rebuilt for FFmpeg 8

* Thu Nov 06 2025 Than Ngo <than@redhat.com> - 142.0.7444.134-1
- Update to 142.0.7444.134
  * High CVE-2025-12725: Out of bounds write in WebGPU
  * High CVE-2025-12726: Inappropriate implementation in Views
  * High CVE-2025-12727: Inappropriate implementation in V8
  * Medium CVE-2025-12728: Inappropriate implementation in Omnibox
  * Medium CVE-2025-12729: Inappropriate implementation in Omnibox

* Wed Nov 05 2025 Dominik Mierzejewski <dominik@greysector.net> - 142.0.7444.59-2
- Rebuilt for FFmpeg 8

* Thu Oct 30 2025 Than Ngo <than@redhat.com> - 142.0.7444.59-1
- Update to 142.0.7444.59
  * High CVE-2025-12428: Type Confusion in V8
  * High CVE-2025-12429: Inappropriate implementation in V8
  * High CVE-2025-12430: Object lifecycle issue in Media
  * High CVE-2025-12431: Inappropriate implementation in Extensions
  * High CVE-2025-12432: Race in V8
  * High CVE-2025-12433: Inappropriate implementation in V8
  * High CVE-2025-12036: Inappropriate implementation in V8
  * Medium CVE-2025-12434: Race in Storage
  * Medium CVE-2025-12435: Incorrect security UI in Omnibox
  * Medium CVE-2025-12436: Policy bypass in Extensions
  * Medium CVE-2025-12437: Use after free in PageInfo
  * Medium CVE-2025-12438: Use after free in Ozone
  * Medium CVE-2025-12439: Inappropriate implementation in App-Bound Encryption
  * Low CVE-2025-12440: Inappropriate implementation in Autofill
  * Medium CVE-2025-12441: Out of bounds read in V8
  * Medium CVE-2025-12443: Out of bounds read in WebXR
  * Low CVE-2025-12444: Incorrect security UI in Fullscreen UI
  * Low CVE-2025-12445: Policy bypass in Extensions
  * Low CVE-2025-12446: Incorrect security UI in SplitView
  * Low CVE-2025-12447: Incorrect security UI in Omnibox
  * Refreshed ppc64le patches
  * Refreshed system-brotli patch
  * Refreshed clang++-unknown-argument patch
  * Refreshed split-threshold-for-reg-with-hint patch
  * Fixed some FTBFS caused by missing header files
  * Fixed FTBFS caused by old rust compiler
  * Fixed FTBFS caused by new glibc-2.42 in Rawhide
  * Fixed FTBFS caused by old python-3.9.x in EL8/9
  * Dropped obsoleted chromium-141-el9-ffmpeg-5.x-duration.patch for old ffmpeg on EL9

* Wed Oct 22 2025 Than Ngo <than@redhat.com> - 141.0.7390.122-1
- Update to 141.0.7390.122
  * High CVE-2025-12036 chromium: Inappropriate implementation in V8

* Wed Oct 15 2025 Than Ngo <than@redhat.com> - 141.0.7390.107-1
- Update 141.0.7390.107
  * High CVE-2025-11756: Use after free in Safe Browsing

* Sun Oct 12 2025 Than Ngo <than@redhat.com> - 141.0.7390.76-1
- Update to 141.0.7390.76

* Wed Oct 08 2025 Than Ngo <than@redhat.com> - 141.0.7390.65-1
- Update to 141.0.7390.65
  * High CVE-2025-11458: Heap buffer overflow in Sync
  * High CVE-2025-11460: Use after free in Storage
  * Medium CVE-2025-11211: Out of bounds read in WebCodecs

* Fri Oct 03 2025 Tom Stellard <tstellar@redhat.com> - 141.0.7390.54-2
- Fix build with clang-22

* Thu Oct 02 2025 Than Ngo <than@redhat.com> - 141.0.7390.54-1
- Update to 141.0.7390.54
  * High CVE-2025-11205: Heap buffer overflow in WebGPU
  * High CVE-2025-11206: Heap buffer overflow in Video
  * Medium CVE-2025-11207: Side-channel information leakage in Storage
  * Medium CVE-2025-11208: Inappropriate implementation in Media
  * Medium CVE-2025-11209: Inappropriate implementation in Omnibox
  * Medium CVE-2025-11210: Side-channel information leakage in Tab
  * Medium CVE-2025-11211: Out of bounds read in Media
  * Medium CVE-2025-11212: Inappropriate implementation in Media
  * Medium CVE-2025-11213: Inappropriate implementation in Omnibox
  * Medium CVE-2025-11215: Off by one error in V8
  * Low CVE-2025-11216: Inappropriate implementation in Storage
  * Low CVE-2025-11219: Use after free in V8

* Wed Sep 24 2025 Than Ngo <than@redhat.com> - 140.0.7339.207-1
- Update to 140.0.7339.207
  * CVE-2025-10890: Side-channel information leakage in V8
  * CVE-2025-10891: Integer overflow in V8
  * CVE-2025-10892: Integer overflow in V8


* Wed Sep 17 2025 Than Ngo <than@redhat.com> - 140.0.7339.185-1
- Update to 140.0.7339.185
  * CVE-2025-10585: Type Confusion in V8
  * CVE-2025-10500: Use after free in Dawn
  * CVE-2025-10501: Use after free in WebRTC
  * CVE-2025-10502: Heap buffer overflow in ANGLE

* Thu Sep 11 2025 Than Ngo <than@redhat.com> - 140.0.7339.127-1
- Update to 140.0.7339.127
  * CVE-2025-10200: Use after free in Serviceworker
  * CVE-2025-10201: Inappropriate implementation in Mojo

* Wed Sep 03 2025 Than Ngo <than@redhat.com> - 140.0.7339.80-1
- Update to 140.0.7339.80
  * CVE-2025-9864: Use after free in V8
  * CVE-2025-9865: Inappropriate implementation in Toolbar
  * CVE-2025-9866: Inappropriate implementation in Extensions
    CVE-2025-9867: Inappropriate implementation in Downloads

* Thu Aug 28 2025 Than Ngo <than@redhat.com> - 139.0.7258.154-1
- Update to 139.0.7258.154
  * CVE-2025-9478: Use after free in ANGLE

* Fri Aug 22 2025 Than Ngo <than@redhat.com> - 139.0.7258.138-1
- Updated to 139.0.7258.138
  * CVE-2025-9132: Out of bounds write in V8

* Wed Aug 20 2025 Dominik Mierzejewski <dominik@greysector.net> - 139.0.7258.127-2
- Drop unused yasm build dependency
  see https://fedoraproject.org/wiki/Changes/DeprecateYASM

* Wed Aug 13 2025 Than Ngo <than@redhat.com> - 139.0.7258.127-1
- Updated to 139.0.7258.127
  * CVE-2025-8879: Heap buffer overflow in libaom
  * CVE-2025-8880: Race in V8
  * CVE-2025-8901: Out of bounds write in ANGLE
  * CVE-2025-8881: Inappropriate implementation in File Picker
  * CVE-2025-8882: Use after free in Aura

* Tue Aug 05 2025 Than Ngo <than@redhat.com> - 139.0.7258.66-1
- Updated to 139.0.7258.66
  * CVE-2025-8576: Use after free in Extensions
  * CVE-2025-8578: Use after free in Cast
  * CVE-2025-8579: Inappropriate implementation in Gemini Live in Chrome
  * CVE-2025-8580: Inappropriate implementation in Filesystems
  * CVE-2025-8581: Inappropriate implementation in Extensions
  * CVE-2025-8582: Insufficient validation of untrusted input in DOM
  * CVE-2025-8583: Inappropriate implementation in Permissions

* Mon Aug 04 2025 Tom Stellard <tstellar@redhat.com> - 138.0.7204.183-2
- Backport fix for build failure with clang-21

* Wed Jul 30 2025 Than Ngo <than@redhat.com> - 138.0.7204.183-1
- Update to 138.0.7204.183
  * CVE-2025-8292: Use after free in Media Stream

* Wed Jul 23 2025 Fedora Release Engineering <releng@fedoraproject.org> - 138.0.7204.168-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_43_Mass_Rebuild

* Wed Jul 23 2025 Than Ngo <than@redhat.com> - 138.0.7204.168-1
- Update to 138.0.7204.168
  * CVE-2025-8010: Type Confusion in V8
  * CVE-2025-8011: Type Confusion in V8

* Wed Jul 16 2025 Than Ngo <than@redhat.com> - 138.0.7204.157-1
- Update to 138.0.7204.157
  * CVE-2025-7656: Integer overflow in V8
  * CVE-2025-7657: Use after free in WebRTC
  * CVE-2025-6558: Incorrect validation of untrusted input in ANGLE and GPU

* Fri Jul 11 2025 Tom Stellard <tstellar@redhat.com> -138.0.7204.100-2
- Update rust-clanglib patch for clang 21

* Wed Jul 09 2025 Than Ngo <than@redhat.com> - 138.0.7204.100-1
- Update to 138.0.7204.100

* Tue Jul 01 2025 Than Ngo <than@redhat.com> - 138.0.7204.92-1
- Update to 138.0.7204.92
  * High CVE-2025-6554: Type Confusion in V8 

* Tue Jun 24 2025 Than Ngo <than@redhat.com> - 138.0.7204.49-1
- Update to 138.0.7204.49
  * CVE-2025-6555: Use after free in Animation
  * CVE-2025-6556: Insufficient policy enforcement in Loader
  * CVE-2025-6557: Insufficient data validation in DevTools

* Wed Jun 18 2025 Than Ngo <than@redhat.com> - 137.0.7151.119-1
- Update to 137.0.7151.119
  * CVE-2025-6191: Integer overflow in V8
  * CVE-2025-6192: Use after free in Profiler

* Wed Jun 11 2025 Than Ngo <than@redhat.com> - 137.0.7151.103-1
- Update to 137.0.7151.103
  * CVE-2025-5958: Use after free in Media
  * CVE-2025-5959: Type Confusion in V8
- Provide correct version for bundle librarires
- Fix rhbz#2368923, Chromium crash

* Tue Jun 03 2025 Than Ngo <than@redhat.com> - 137.0.7151.68-1
- Update to 137.0.7151.68
  * CVE-2025-5419: Out of bounds read and write in V8
  * CVE-2025-5068: Use after free in Blink

* Tue May 27 2025 Than Ngo <than@redhat.com> - 137.0.7151.55-1
- Update to 137.0.7151.55
  * CVE-2025-5063: Use after free in Compositing
  * CVE-2025-5280: Out of bounds write in V8
  * CVE-2025-5064: Inappropriate implementation in Background Fetch API
  * CVE-2025-5065: Inappropriate implementation in FileSystemAccess API
  * CVE-2025-5066: Inappropriate implementation in Messages
  * CVE-2025-5281: Inappropriate implementation in BFCache
  * CVE-2025-5283: Use after free in libvpx
  * CVE-2025-5067: Inappropriate implementation in Tab Strip
- Fix FTBFS caused by simdutf and pdfium-png_decoder
- Remove chromium-135-gperf.patch and chromium-135-add-cfi-suppressions-for-pipewire-functions.patch, merged by upstream
- Refresh ppc64le patches
- Enable system simdutf for F43

* Tue May 27 2025 Jitka Plesnikova <jplesnik@redhat.com> - 136.0.7103.113-2
- Rebuilt for flac 1.5.0

* Wed May 14 2025 Than Ngo <than@redhat.com> - 136.0.7103.113-1
- Update to 136.0.7103.113
  * CVE-2025-4664: Insufficient policy enforcement in Loader
  * CVE-2025-4609: Incorrect handle provided in unspecified circumstances in Mojo

* Wed May 07 2025 Than Ngo <than@redhat.com> - 136.0.7103.92-1
- Update to 136.0.7103.92
  * CVE-2025-4372: Use after free in WebAudio

* Tue Apr 29 2025 Than Ngo <than@redhat.com> - 136.0.7103.59-1
- Update to 136.0.7103.59
  * CVE-2025-4096: Heap buffer overflow in HTML
  * CVE-2025-4050: Out of bounds memory access in DevTools
  * CVE-2025-4051: Insufficient data validation in DevTools
  * CVE-2025-4052: Inappropriate implementation in DevTools

* Thu Apr 24 2025 Than Ngo <than@redhat.com> - 136.0.7103.48-1
- Update to 136.0.7103.48

* Wed Apr 23 2025 Than Ngo <than@redhat.com> - 135.0.7049.114-1
- Update to 135.0.7049.114

* Wed Apr 16 2025 Than Ngo <than@redhat.com> - 135.0.7049.95-1
- Update to 135.0.7049.95
  * CVE-2025-3619: Heap buffer overflow in Codecs
  * CVE-2025-3620: Use after free in USB

* Wed Apr 09 2025 Than Ngo <than@redhat.com> - 135.0.7049.84-1
- Update to 135.0.7049.84
  * CVE-2025-3066: Use after free in Site Isolation

* Wed Apr 02 2025 Jan Grulich <jgrulich@redhat.com> - 135.0.7049.52-2
- Add CFI suppressions for inline PipeWire functions

* Tue Apr 01 2025 Than Ngo <than@redhat.com> - 135.0.7049.52-1
- Update to 135.0.7049.52

* Fri Mar 28 2025 Than Ngo <than@redhat.com> - 135.0.7049.41-1
- Update to 135.0.7049.41

* Mon Mar 24 2025 Than Ngo <than@redhat.com> - 134.0.6998.165-1
- Update to 134.0.6998.165
- Fixed rhbz#2354377 - Enable ppc64le support for el10

* Thu Mar 20 2025 Than Ngo <than@redhat.com> -  134.0.6998.117-1
- Update to 134.0.6998.117
  * Critical CVE-2025-2476: Use after free in Lens

* Mon Mar 17 2025 Than Ngo <than@redhat.com> -  134.0.6998.88-4
- Fixed rhbz#2352698, rebuild for noopenh264 2.6.0

* Fri Mar 14 2025 Than Ngo <than@redhat.com> -  134.0.6998.88-3
- Fixed build errors on ppc64le

* Thu Mar 13 2025 Fabio Valentini <decathorpe@gmail.com> - 134.0.6998.88-2
- Rebuild for noopenh264 2.6.0

* Tue Mar 11 2025 Than Ngo <than@redhat.com> -  134.0.6998.88-1
- Update to 134.0.6998.88
  * High CVE-2025-1920: Type Confusion in V8
  * High CVE-2025-2135: Type Confusion in V8
  * High CVE-TBD: Out of bounds write in GPU
  * Medium CVE-2025-2136: Use after free in Inspector
  * Medium CVE-2025-2137: Out of bounds read in V8

* Wed Mar 05 2025 Than Ngo <than@redhat.com> -  134.0.6998.35-1
- Update to 134.0.6998.35
  * CVE-2025-1914: Out of bounds read in V8
  * CVE-2025-1915: Improper Limitation of a Pathname to a Restricted Directory in DevTools
  * CVE-2025-1916: Use after free in Profiles
  * CVE-2025-1917: Inappropriate Implementation in Browser UI
  * CVE-2025-1918: Out of bounds read in PDFium
  * CVE-2025-1919: Out of bounds read in Media
  * CVE-2025-1921: Inappropriate Implementation in Media Stream
  * CVE-2025-1922: Inappropriate Implementation in Selection
  * CVE-2025-1923: Inappropriate Implementation in Permission Prompts

* Wed Feb 26 2025 Than Ngo <than@redhat.com> - 133.0.6943.141-1
- Update to 133.0.6943.141

* Wed Feb 19 2025 Than Ngo <than@redhat.com> - 133.0.6943.126-1
- Update to 133.0.6943.126
  * CVE-2025-0999: Heap buffer overflow in V8
  * CVE-2025-1426: Heap buffer overflow in GPU
  * CVE-2025-1006: Use after free in Network

* Thu Feb 13 2025 Than Ngo <than@redhat.com> - 133.0.6943.98-1
- Update to 133.0.6943.98
  * CVE-2025-0995: Use after free in V8
  * CVE-2025-0996: Inappropriate implementation in Browser UI
  * CVE-2025-0997: Use after free in Navigation
  * CVE-2025-0998: Out of bounds memory access in V8

* Tue Feb 04 2025 Than Ngo <than@redhat.com> - 133.0.6943.53-1
- Update to 133.0.6943.53
  * CVE-2025-0444: Use after free in Skia
  * CVE-2025-0445: Use after free in V8
  * CVE-2025-0451: Inappropriate implementation in Extensions API

* Wed Jan 29 2025 Than Ngo <than@redhat.com> - 132.0.6834.159-1
- Updated to 132.0.6834.159
  * Medium CVE-2025-0762: Use after free in DevTools

* Thu Jan 23 2025 Than Ngo <than@redhat.com> - 132.0.6834.110-1
- Update to 132.0.6834.110
  * High CVE-2025-0611: Object corruption in V8
  * High CVE-2025-0612: Out of bounds memory access in V8

* Thu Jan 16 2025 Fedora Release Engineering <releng@fedoraproject.org> - 132.0.6834.83-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_42_Mass_Rebuild

* Wed Jan 15 2025 Than Ngo <than@redhat.com> - 132.0.6834.83-1
- Update to 132.0.6834.83
  * High CVE-2025-0434: Out of bounds memory access in V8
  * High CVE-2025-0435: Inappropriate implementation in Navigation
  * High CVE-2025-0436: Integer overflow in Skia
  * High CVE-2025-0437: Out of bounds read in Metrics
  * High CVE-2025-0438: Stack buffer overflow in Tracing
  * Medium CVE-2025-0439: Race in Frames
  * Medium CVE-2025-0440: Inappropriate implementation in Fullscreen
  * Medium CVE-2025-0441: Inappropriate implementation in Fenced
  * Medium CVE-2025-0442: Inappropriate implementation in Payments
  * Medium CVE-2025-0443: Insufficient data validation in Extensions
  * Low CVE-2025-0446: Inappropriate implementation in Extensions
  * Low CVE-2025-0447: Inappropriate implementation in Navigation
  * Low CVE-2025-0448: Inappropriate implementation in Compositing

* Wed Jan 08 2025 Than Ngo <than@redhat.com> - 131.0.6778.264-1
- Update to 131.0.6778.264
  * High CVE-2025-0291: Type Confusion in V8

* Thu Dec 19 2024 Than Ngo <than@redhat.com> - 131.0.6778.204-1
- Update to 131.0.6778.204
  * High CVE-2024-12692: Type Confusion in V8
  * High CVE-2024-12693: Out of bounds memory access in V8
  * High CVE-2024-12694: Use after free in Compositing
  * High CVE-2024-12695: Out of bounds write in V8

* Wed Dec 11 2024 Than Ngo <than@redhat.com> - 131.0.6778.139-1
- Update to 131.0.6778.139
  * High CVE-2024-12381: Type Confusion in V8
  * High CVE-2024-12382: Use after free in Translate

* Wed Dec 04 2024 Than Ngo <than@redhat.com> - 131.0.6778.108-1
- Update to 131.0.6778.108
  * High CVE-2024-12053: Type Confusion in V8

* Sat Nov 23 2024 Than Ngo <than@redhat.com> - 131.0.6778.85-2
- Enable qt-ui
- Workaround for random crash

* Wed Nov 20 2024 Than Ngo <than@redhat.com> - 131.0.6778.85-1
- Update to 131.0.6778.85
  * High CVE-2024-11395: Type Confusion in V8

* Tue Nov 12 2024 Than Ngo <than@redhat.com> - 131.0.6778.69-1
- Update to 131.0.6778.69
  * High CVE-2024-11110: Inappropriate implementation in Blink
  * Medium CVE-2024-11111: Inappropriate implementation in Autofill
  * Medium CVE-2024-11112: Use after free in Media
  * Medium CVE-2024-11113: Use after free in Accessibility
  * Medium CVE-2024-11114: Inappropriate implementation in Views
  * Medium CVE-2024-11115: Insufficient policy enforcement in Navigation
  * Medium CVE-2024-11116: Inappropriate implementation in Paint
  * Low CVE-2024-11117: Inappropriate implementation in FileSystem

* Sun Nov 10 2024 Than Ngo <than@redhat.com> - 130.0.6723.116-1
- Update to 130.0.6723.116
  * High CVE-2024-10826: Use after free in Family Experience
  * High CVE-2024-10827: Use after free in Serial

* Wed Oct 30 2024 Than Ngo <than@redhat.com> - 130.0.6723.91-1
- Update to 130.0.6723.91
  * Critical CVE-2024-10487: Out of bounds write in Dawn
  * High CVE-2024-10488: Use after free in WebRTC

* Sat Oct 26 2024 Than Ngo <than@redhat.com> - 130.0.6723.69-1
- Update to 130.0.6723.69
  * High CVE-2024-10229: Inappropriate implementation in Extensions
  * High CVE-2024-10230: Type Confusion in V8
  * High CVE-2024-10231: Type Confusion in V8

* Mon Oct 21 2024 Than Ngo <than@redhat.com> - 130.0.6723.58-2
- Add missing pthread stack size for ppc64 (openpower-patches)

* Wed Oct 16 2024 Than Ngo <than@redhat.com> - 130.0.6723.58-1
- update to 130.0.6723.58
  * High CVE-2024-9954: Use after free in AI
  * Medium CVE-2024-9955: Use after free in Web Authentication
  * Medium CVE-2024-9956: Inappropriate implementation in Web Authentication
  * Medium CVE-2024-9957: Use after free in UI
  * Medium CVE-2024-9958: Inappropriate implementation in PictureInPicture
  * Medium CVE-2024-9959: Use after free in DevTools
  * Medium CVE-2024-9960: Use after free in Dawn
  * Medium CVE-2024-9961: Use after free in Parcel Tracking
  * Medium CVE-2024-9962: Inappropriate implementation in Permissions
  * Medium CVE-2024-9963: Insufficient data validation in Downloads
  * Low CVE-2024-9964: Inappropriate implementation in Payments
  * Low CVE-2024-9965: Insufficient data validation in DevTools
  * Low CVE-2024-9966: Inappropriate implementation in Navigations

* Wed Oct 09 2024 Than Ngo <than@redhat.com> - 129.0.6668.100-1
- update to 129.0.6668.100
  * CVE-2024-9602: Type Confusion in V8
  * CVE-2024-9603: Type Confusion in V8

* Wed Oct 02 2024 Than Ngo <than@redhat.com> - 129.0.6668.89-1
- update to 129.0.6668.89
  * High CVE -2024-7025: Integer overflow in Layout
  * High CVE-2024-9369: Insufficient data validation in Mojo
  * High CVE-2024-9370: Inappropriate implementation in V8

* Mon Sep 30 2024 Than Ngo <than@redhat.com> - 129.0.6668.70-3
- add clang-19 support

* Fri Sep 27 2024 Dominik Mierzejewski <dominik@greysector.net> - 129.0.6668.70-2
- Rebuilt for FFmpeg 7

* Wed Sep 25 2024 Than Ngo <than@redhat.com> - 129.0.6668.70-1
- update to 129.0.6668.70
  * High CVE-2024-9120: Use after free in Dawn
  * High CVE-2024-9121: Inappropriate implementation in V8
  * High CVE-2024-9122: Type Confusion in V8
  * High CVE-2024-9123: Integer overflow in Skia

* Thu Sep 19 2024 Than Ngo <than@redhat.com> - 129.0.6668.58-2
- clean up

* Tue Sep 17 2024 Than Ngo <than@redhat.com> - 129.0.6668.58-1
- update to 129.0.6668.58
  * High CVE-2024-8904: Type Confusion in V8
  * Medium CVE-2024-8905: Inappropriate implementation in V8
  * Medium CVE-2024-8906: Incorrect security UI in Downloads
  * Medium CVE-2024-8907: Insufficient data validation in Omnibox
  * Low CVE-2024-8908: Inappropriate implementation in Autofill
  * Low CVE-2024-8909: Inappropriate implementation in UI

* Wed Sep 11 2024 Than Ngo <than@redhat.com> - 128.0.6613.137-1
- update to 128.0.6613.137
  * High CVE-2024-8636: Heap buffer overflow in Skia
  * High CVE-2024-8637: Use after free in Media Router
  * High CVE-2024-8638: Type Confusion in V8
  * High CVE-2024-8639: Use after free in Autofill

* Thu Sep 05 2024 Than Ngo <than@redhat.com> - 128.0.6613.119-1
- update to 128.0.6613.119
  * High CVE-2024-8362: Use after free in WebAudio
  * High CVE-2024-7970: Out of bounds write in V8

* Wed Aug 07 2024 Than Ngo <than@redhat.com> - 127.0.6533.99-1
- update to 127.0.6533.99
  * Critical CVE-2024-7532: Out of bounds memory access in ANGLE
  * High CVE-2024-7533: Use after free in Sharing
  * High CVE-2024-7550: Type Confusion in V8
  * High CVE-2024-7534: Heap buffer overflow in Layout
  * High CVE-2024-7535: Inappropriate implementation in V8
  * High CVE-2024-7536: Use after free in WebAudio

* Tue Aug 06 2024 Than Ngo <than@redhat.com> - 127.0.6533.88-3
- fix rhbz#2294773 - Allow enabling vulkan on ozone wayland for AMD vaapi
- add ppc64le patch to fix runtime assertion trap on ppc64el systems
- refresh ppc64le patch to work around broken 64k allocator code on arm64

* Thu Aug 01 2024 Than Ngo <than@redhat.com> - 127.0.6533.88-2
- remove old patch that seems to be the cause of a crash
  when the user set user.max_user_namespaces to 0

* Wed Jul 31 2024 Than Ngo <than@redhat.com> - 127.0.6533.88-1
- update to 127.0.6533.88

* Wed Jul 24 2024 Than Ngo <than@redhat.com> - 127.0.6533.72-1
- update to 127.0.6533.72
	* CVE-2024-6988: Use after free in Downloads
	* CVE-2024-6989: Use after free in Loader
	* CVE-2024-6991: Use after free in Dawn
	* CVE-2024-6992: Out of bounds memory access in ANGLE
	* CVE-2024-6993: Inappropriate implementation in Canvas
	* CVE-2024-6994: Heap buffer overflow in Layout
	* CVE-2024-6995: Inappropriate implementation in Fullscreen
	* CVE-2024-6996: Race in Frames
	* CVE-2024-6997: Use after free in Tabs
	* CVE-2024-6998: Use after free in User Education
	* CVE-2024-6999: Inappropriate implementation in FedCM
	* CVE-2024-7000: Use after free in CSS. Reported by Anonymous
	* CVE-2024-7001: Inappropriate implementation in HTML
	* CVE-2024-7003: Inappropriate implementation in FedCM
	* CVE-2024-7004: Insufficient validation of untrusted input in Safe Browsing
	* CVE-2024-7005: Insufficient validation of untrusted input in Safe

* Sat Jul 20 2024 Than Ngo <than@redhat.com> - 126.0.6478.182-2
- fix condition for is_cfi/use_thin_lto on aarch64/ppc64le
- update powerpc patches

* Tue Jul 16 2024 Than Ngo <than@redhat.com> - 126.0.6478.182-1
- update to 126.0.6478.182
  * High CVE-2024-6772: Inappropriate implementation in V8
  * High CVE-2024-6773: Type Confusion in V8
  * High CVE-2024-6774: Use after free in Screen Capture
  * High CVE-2024-6775: Use after free in Media Stream
  * High CVE-2024-6776: Use after free in Audio
  * High CVE-2024-6777: Use after free in Navigation
  * High CVE-2024-6778: Race in DevTools
  * High CVE-2024-6779: Out of bounds memory access in V8

* Sun Jul 07 2024 Than Ngo <than@redhat.com> - 126.0.6478.126-2
- fixed rhbz#2293202, chromium Wayland UI regression

* Tue Jun 25 2024 Than Ngo <than@redhat.com> - 126.0.6478.126-1
- update to 126.0.6478.126
  * High CVE-2024-6290: Use after free in Dawn
  * High CVE-2024-6291: Use after free in Swiftshader
  * High CVE-2024-6292: Use after free in Dawn
  * High CVE-2024-6293: Use after free in Dawn 

* Wed Jun 19 2024 Than Ngo <than@redhat.com> - 126.0.6478.114-1
- update to 126.0.6478.114
  * High CVE-2024-6100: Type Confusion in V8
  * High CVE-2024-6101: Inappropriate implementation in WebAssembly
  * High CVE-2024-6102: Out of bounds memory access in Dawn
  * High CVE-2024-6103: Use after free in Dawn

* Wed Jun 12 2024 Than Ngo <than@redhat.com> - 126.0.6478.55-1
- update to 126.0.6478.55
  * High CVE-2024-5830: Type Confusion in V8
  * High CVE-2024-5831: Use after free in Dawn
  * High CVE-2024-5832: Use after free in Dawn
  * High CVE-2024-5833: Type Confusion in V8
  * High CVE-2024-5834: Inappropriate implementation in Dawn
  * High CVE-2024-5835: Heap buffer overflow in Tab Groups
  * High CVE-2024-5836: Inappropriate Implementation in DevTools
  * High CVE-2024-5837: Type Confusion in V8
  * High CVE-2024-5838: Type Confusion in V8
  * Medium CVE-2024-5839: Inappropriate Implementation in Memory Allocator
  * Medium CVE-2024-5840: Policy Bypass in CORS
  * Medium CVE-2024-5841: Use after free in V8
  * Medium CVE-2024-5842: Use after free in Browser UI
  * Medium CVE-2024-5843: Inappropriate implementation in Downloads
  * Medium CVE-2024-5844: Heap buffer overflow in Tab Strip
  * Medium CVE-2024-5845: Use after free in Audio
  * Medium CVE-2024-5846: Use after free in PDFium
  * Medium CVE-2024-5847: Use after free in PDFium

* Fri May 31 2024 Than Ngo <than@redhat.com> - 125.0.6422.141-1
- update to 125.0.6422.141
  * High CVE-2024-5493: Heap buffer overflow in WebRTC
  * High CVE-2024-5494: Use after free in Dawn
  * High CVE-2024-5495: Use after free in Dawn
  * High CVE-2024-5496: Use after free in Media Session
  * High CVE-2024-5497: Out of bounds memory access in Keyboard Inputs
  * High CVE-2024-5498: Use after free in Presentation API
  * High CVE-2024-5499: Out of bounds write in Streams API
- fixed rhbz#2264332 - Chromium is unable to send/receive video on MS Teams
- cleanup chromium.conf

* Wed May 29 2024 Than Ngo <than@redhat.com> - 125.0.6422.112-3
- build against noopenh264

* Tue May 28 2024 Than Ngo <than@redhat.com> - 125.0.6422.112-2
- Workaround for build error on pp64le

* Sun May 26 2024 Than Ngo <than@redhat.com> - 125.0.6422.112-1
- update to 125.0.6422.112
  * High CVE-2024-5274: Type Confusion in V8

* Wed May 22 2024 Than Ngo <than@redhat.com> - 125.0.6422.76-1
- fix bz#2282246, update to 125.0.6422.76
  * High CVE-2024-5157: Use after free in Scheduling
  * High CVE-2024-5158: Type Confusion in V8
  * High CVE-2024-5159: Heap buffer overflow in ANGLE
  * High CVE-2024-5160: Heap buffer overflow in Dawn
- cleanup

* Mon May 20 2024 Than Ngo <than@redhat.com> - 125.0.6422.60-3
- remove unneeded BRs
- workarounds for el7 build

* Sun May 19 2024 Than Ngo <than@redhat.com> - 125.0.6422.60-2
- fix build errors on el7

* Thu May 16 2024 Than Ngo <than@redhat.com> - 125.0.6422.60-1
- update to 125.0.6422.60
  * High CVE-2024-4947: Type Confusion in V8
  * High CVE-2024-4948: Use after free in Dawn
  * Medium CVE-2024-4949: Use after free in V8
  * Low CVE-2024-4950: Inappropriate implementation in Downloads

* Sun May 12 2024 Than Ngo <than@redhat.com> - 125.0.6422.41-1
- update to 125.0.6422.41

* Sat May 11 2024 Than Ngo <than@redhat.com> - 124.0.6367.201-2
- include headless_command_resources.pak for headless_shell

* Fri May 10 2024 Than Ngo <than@redhat.com> - 124.0.6367.201-1
- update to 124.0.6367.201
  * High CVE-2024-4671: Use after free in Visuals

* Wed May 08 2024 Than Ngo <than@redhat.com> - 124.0.6367.155-1
- update to 124.0.6367.155
  * High CVE-2024-4558: Use after free in ANGLE
  * High CVE-2024-4559: Heap buffer overflow in WebAudio

* Sun May 05 2024 Than Ngo <than@redhat.com> - 124.0.6367.118-2
- fixed build errors on el8
- refreshed clean_ffmpeg.sh
- added missing files for bundle ffmpeg

* Wed May 01 2024 Than Ngo <than@redhat.com> - 124.0.6367.118-1
- update to 124.0.6367.118
  * High CVE-2024-4331: Use after free in Picture In Picture
  * High CVE-2024-4368: Use after free in Dawn
- use system highway

* Sat Apr 27 2024 Than Ngo <than@redhat.com> - 124.0.6367.91-1
- update to 124.0.6367.91
- fixed bz#2277228 - chromium wrapper causes library issues (symbol lookup error)
- use system dav1d

* Wed Apr 24 2024 Than Ngo <than@redhat.com> - 124.0.6367.78-1
- update to 124.0.6367.78
  * Critical CVE-2024-4058: Type Confusion in ANGLE
  * High CVE-2024-4059: Out of bounds read in V8 API
  * High CVE-2024-4060: Use after free in Dawn

* Sat Apr 20 2024 Than Ngo <than@redhat.com> - 124.0.6367.60-2
- fix waylang regression

* Tue Apr 16 2024 Than Ngo <than@redhat.com> - 124.0.6367.60-1
- update to 124.0.6367.60

* Thu Apr 11 2024 Than Ngo <than@redhat.com> - 123.0.6312.122-1
- update to 123.0.6312.122
  * High CVE-2024-3157: Out of bounds write in Compositing
  * High CVE-2024-3516: Heap buffer overflow in ANGLE
  * High CVE-2024-3515: Use after free in Dawn

* Wed Apr 03 2024 Than Ngo <than@redhat.com> - 123.0.6312.105-1
- update to 123.0.6312.105
  * High CVE-2024-3156: Inappropriate implementation in V8
  * High CVE-2024-3158: Use after free in Bookmarks
  * High CVE-2024-3159: Out of bounds memory access in V8

* Wed Mar 27 2024 Than Ngo <than@redhat.com> - 123.0.6312.86-2
- update to 123.0.6312.86
  * Critical CVE-2024-2883: Use after free in ANGLE
  * High CVE-2024-2885: Use after free in Daw
  * High CVE-2024-2886: Use after free in WebCodecs
  * High CVE-2024-2887: Type Confusion in WebAssembly

* Sat Mar 23 2024 Than Ngo <than@redhat.com> - 123.0.6312.58-2
- fixed bz#2269768 - enable build ppc64le package for F40
- fixed bz#2270321 - VAAPI flags in chromium.conf are out of date
- fixed bz#2271183 - disable screen ai service

* Wed Mar 20 2024 Than Ngo <than@redhat.com> - 123.0.6312.58-1
- update to 123.0.6312.58
   * High CVE-2024-2625: Object lifecycle issue in V8
   * Medium CVE-2024-2626: Out of bounds read in Swiftshader
   * Medium CVE-2024-2627: Use after free in Canvas
   * Medium CVE-2024-2628: Inappropriate implementation in Downloads
   * Medium CVE-2024-2629: Incorrect security UI in iOS
   * Medium CVE-2024-2630: Inappropriate implementation in iOS
   * Low CVE-2024-2631: Inappropriate implementation in iOS

* Fri Mar 15 2024 Than Ngo <than@redhat.com> - 123.0.6312.46-1
- update to 123.0.6312.46

* Wed Mar 13 2024 Than Ngo <than@redhat.com> - 122.0.6261.128-1
- upstream security release 122.0.6261.128
   * High CVE-2024-2400: Use after free in Performance Manager

* Mon Mar 11 2024 Than Ngo <than@redhat.com> - 122.0.6261.111-2
- enable ppc64le build

* Wed Mar 06 2024 Than Ngo <than@redhat.com> - 122.0.6261.111-1
- upstream security release 122.0.6261.111
   * High CVE-2024-2173: Out of bounds memory access in V8
   * High CVE-2024-2174: Inappropriate implementation in V8
   * High CVE-2024-2176: Use after free in FedCM

* Sat Mar 02 2024 Jiri Vanek <jvanek@redhat.com> - 122.0.6261.94-2
- Rebuilt for java-21-openjdk as system jdk

* Wed Feb 28 2024 Than Ngo <than@redhat.com> - 122.0.6261.94-1
- upstream security release 122.0.6261.94
  * High : Type Confusion in V8
- fixed bz#2265957, added correct platform in chromium use agent

* Tue Feb 27 2024 Łukasz Wojniłowicz <lukasz.wojnilowicz@gmail.com> - 122.0.6261.69-3
- Make building of chromedriver optional

* Tue Feb 27 2024 Jiri Vanek <jvanek@redhat.com> - 122.0.6261.69-2
- Rebuilt for java-21-openjdk as system jdk

* Fri Feb 23 2024 Than Ngo <than@redhat.com> - 122.0.6261.69-1
- update to 122.0.6261.69
- fix build error on el8
- bz#2265039, built with -fwrapv for improved memory safety
- bz#2265043, built with -ftrivial-auto-var-init=zero for improved security and preditability

* Wed Feb 21 2024 Than Ngo <than@redhat.com> - 122.0.6261.57-1
- update to 122.0.6261.57
   * High CVE-2024-1669: Out of bounds memory access in Blink
   * High CVE-2024-1670: Use after free in Mojo
   * Medium CVE-2024-1671: Inappropriate implementation in Site Isolation
   * Medium CVE-2024-1672: Inappropriate implementation in Content Security Policy
   * Medium CVE-2024-1673: Use after free in Accessibility
   * Medium CVE-2024-1674: Inappropriate implementation in Navigation
   * Medium CVE-2024-1675: Insufficient policy enforcement in Download
   * Low CVE-2024-1676: Inappropriate implementation in Navigation.

* Sun Feb 18 2024 Than Ngo <than@redhat.com> - 122.0.6261.39-1
- update to 122.0.6261.39

* Wed Feb 14 2024 Than Ngo <than@redhat.com> - 121.0.6167.184-1
- update to 121.0.6167.184

* Wed Feb 07 2024 Than Ngo <than@redhat.com> - 121.0.6167.160-1
- update to 121.0.6167.160
  * High CVE-2024-1284: Use after free in Mojo
  * High CVE-2024-1283: Heap buffer overflow in Skia

* Thu Feb 01 2024 Than Ngo <than@redhat.com> - 121.0.6167.139-2
- Support for 64K pages on Linux/AArch64

* Wed Jan 31 2024 Than Ngo <than@redhat.com> - 121.0.6167.139-1
- update to 121.0.6167.139
  * High CVE-2024-1060: Use after free in Canvas
  * High CVE-2024-1059: Use after free in WebRTC
  * High CVE-2024-1077: Use after free in Network

* Wed Jan 24 2024 Than Ngo <than@redhat.com> - 121.0.6167.85-1
- update to 121.0.6167.85
  * High CVE-2024-0807: Use after free in WebAudio
  * High CVE-2024-0812: Inappropriate implementation in Accessibility
  * High CVE-2024-0808: Integer underflow in WebUI
  * Medium CVE-2024-0810: Insufficient policy enforcement in DevTools
  * Medium CVE-2024-0814: Incorrect security UI in Payments
  * Medium CVE-2024-0813: Use after free in Reading Mode
  * Medium CVE-2024-0806: Use after free in Passwords
  * Medium CVE-2024-0805: Inappropriate implementation in Downloads
  * Medium CVE-2024-0804: Insufficient policy enforcement in iOS Security UI
  * Low CVE-2024-0811: Inappropriate implementation in Extensions API
  * Low CVE-2024-0809: Inappropriate implementation in Autofill

* Tue Jan 23 2024 Than Ngo <than@redhat.com> - 121.0.6167.71-1
- update to 121.0.6167.71

* Tue Jan 23 2024 Fedora Release Engineering <releng@fedoraproject.org> - 120.0.6099.224-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_40_Mass_Rebuild

* Tue Jan 16 2024 Than Ngo <than@redhat.com> - 120.0.6099.224-1
- update to 120.0.6099.224
  * High CVE-2024-0517: Out of bounds write in V8
  * High CVE-2024-0518: Type Confusion in V8
  * High CVE-2024-0519: Out of bounds memory access in V8

* Wed Jan 10 2024 Than Ngo <than@redhat.com> - 120.0.6099.216-1
- update to 120.0.6099.216
  * High CVE-2024-0333: Insufficient data validation in Extensions

* Thu Jan 04 2024 Than Ngo <than@redhat.com> - 120.0.6099.199-1
- new gn update, drop workaround for broken gn on epel 8/9
- update to 120.0.6099.199
   * CVE-2024-0222: Use after free in ANGLE
   * CVE-2024-0223: Heap buffer overflow in ANGLE
   * CVE-2024-0224: Use after free in WebAudio
   * CVE-2024-0225: Use after free in WebGPU

* Thu Dec 21 2023 Than Ngo <than@redhat.com> - 120.0.6099.129-1
- update to 120.0.6099.129
  * High CVE-2023-7024: Heap buffer overflow in WebRTC

* Wed Dec 13 2023 Than Ngo <than@redhat.com> - 120.0.6099.109-1
- update to 120.0.6099.109
   * High CVE-2023-6702: Type Confusion in V8
   * High CVE-2023-6703: Use after free in Blink
   * High CVE-2023-6704: Use after free in libavif
   * High CVE-2023-6705: Use after free in WebRTC
   * High CVE-2023-6706: Use after free in FedCM
   * Medium CVE-2023-6707: Use after free in CSS

* Fri Dec 08 2023 Than Ngo <than@redhat.com> - 120.0.6099.71-1
- update to 120.0.6099.71

* Wed Dec 06 2023 Than Ngo <than@redhat.com> - 120.0.6099.62-2
- drop unsupported ldflag which caused build failure

* Tue Dec 05 2023 Than Ngo <than@redhat.com> - 120.0.6099.62-1
- update to 120.0.6099.62
- fixed bz#2252874, built with control flow integrity (CFI) support

* Sat Dec 02 2023 Than Ngo <than@redhat.com> - 120.0.6099.56-1
- update to 120.0.6099.56 
- enable qt6 UI backend

* Sat Dec 02 2023 Than Ngo <than@redhat.com> - 119.0.6045.199-2
- fixed bz#2242271, built with bundleminizip in fedora > 39
- fixed bz#2251884, built with fstack-protector-strong for improved security

* Wed Nov 29 2023 Than Ngo <than@redhat.com> - 119.0.6045.199-1
- update to 119.0.6045.199

* Sun Nov 19 2023 Than Ngo <than@redhat.com> - 119.0.6045.159-2
- fix ffmpeg conflicts

* Wed Nov 15 2023 Than Ngo <than@redhat.com> - 119.0.6045.159-1
- update to 119.0.6045.159, upstream security release
   High CVE-2023-5997, use after free in Garbage Collection
   High CVE-2023-6112, use after free in Navigation
- add Requires/Conflicts for ABI break in fmpeg-free 6.0.1
- drop first_dts patch, reintroduce first_dts patch in ffmpeg-free-6.0.1
- fixed python3 syntaxWarning: invalid escape sequenc
- skip clang's patches for epel8 that now gets clang-16 update

* Mon Nov 13 2023 Than Ngo <than@redhat.com> - 119.0.6045.123-2
- fixed bz#2240127, Some h.264 mp4s do not play 

* Wed Nov 08 2023 Than Ngo <than@redhat.com> - 119.0.6045.123-1
- update to 119.0.6045.123, include following security fixes:
  high CVE-2023-5996: Use after free in WebAudio

* Tue Nov 07 2023 Than Ngo <than@redhat.com> - 119.0.6045.105-2
- enable debuginfo

* Wed Nov 01 2023 Than Ngo <than@redhat.com> - 119.0.6045.105-1
- update to 119.0.6045.105

* Fri Oct 27 2023 Than Ngo <than@redhat.com> - 119.0.6045.59-1
- update 119.0.6045.59

* Wed Oct 25 2023 Than Ngo <than@redhat.com> - 118.0.5993.117-1
- update to 118.0.5993.117

* Wed Oct 18 2023 Than Ngo <than@redhat.com> - 118.0.5993.88-1
- update to 118.0.5993.88
- cleanup the package dependencies

* Mon Oct 16 2023 Than Ngo <than@redhat.com> - 118.0.5993.70-2
- fix tab crash with SIGTRAP when using system ffmpeg

* Wed Oct 11 2023 Than Ngo <than@redhat.com> - 118.0.5993.70-1
- update to 118.0.5993.70
    - CVE-2023-5218: Use after free in Site Isolation.
    - CVE-2023-5487: Inappropriate implementation in Fullscreen.
    - CVE-2023-5484: Inappropriate implementation in Navigation.
    - CVE-2023-5475: Inappropriate implementation in DevTools.
    - CVE-2023-5483: Inappropriate implementation in Intents.
    - CVE-2023-5481: Inappropriate implementation in Downloads.
    - CVE-2023-5476: Use after free in Blink History.
    - CVE-2023-5474: Heap buffer overflow in PDF.
    - CVE-2023-5479: Inappropriate implementation in Extensions API.
    - CVE-2023-5485: Inappropriate implementation in Autofill.
    - CVE-2023-5478: Inappropriate implementation in Autofill.
    - CVE-2023-5477: Inappropriate implementation in Installer.
    - CVE-2023-5486: Inappropriate implementation in Input.
    - CVE-2023-5473: Use after free in Cast.

* Sat Oct 07 2023 Than Ngo <than@redhat.com> - 118.0.5993.54-1
- update to 118.0.5993.54
- drop use_gnome_keyring as it's removed by upstream

* Thu Oct 05 2023 Than Ngo <than@redhat.com> - 117.0.5938.149-1
- update to 117.0.5938.149
- fix CVE-2023-5346: Type Confusion in V8

* Fri Sep 29 2023 Than Ngo <than@redhat.com> - 117.0.5938.132-2
- add workaround for the crash on BTI capable system 

* Thu Sep 28 2023 Than Ngo <than@redhat.com> - 117.0.5938.132-1
- update to 117.0.5938.132
- CVE-2023-5217, heap buffer overflow in vp8 encoding in libvpx.
- CVE-2023-5186, use after free in Passwords.
- CVE-2023-5187, use after free in Extensions.
￼	
* Sat Sep 23 2023 Than Ngo <than@redhat.com> - 117.0.5938.92-2
- backport upstream patch to fix memory leak

* Fri Sep 22 2023 Than Ngo <than@redhat.com> - 117.0.5938.92-1
- update to 117.0.5938.92

* Sun Sep 17 2023 Than Ngo <than@redhat.com> - 117.0.5938.88-1
- update to 117.0.5938.88

* Wed Sep 13 2023 Than Ngo <than@redhat.com> - 117.0.5938.62-1
- update to 117.0.5938.62

* Tue Sep 12 2023 Than Ngo <than@redhat.com> - 116.0.5845.187-1
- update to 116.0.5845.187

* Fri Sep 08 2023 Than Ngo <than@redhat.com> - 116.0.5845.179-1
- update to 116.0.5845.179

* Tue Aug 15 2023 Than Ngo <than@redhat.com> - 116.0.5845.96-1
- update to 116.0.5845.96 

* Wed Aug 09 2023 Than Ngo <than@redhat.com> - 115.0.5790.170-2
- set use_all_cpus=1 for aarch64

* Thu Aug 03 2023 Than Ngo <than@redhat.com> - 115.0.5790.170-1
- update to 115.0.5790.170

* Wed Jul 26 2023 Than Ngo <than@redhat.com> - 115.0.5790.110-1
- update to 115.0.5790.110

* Sat Jul 22 2023 Than Ngo <than@redhat.com> - 115.0.5790.102-1
- update to 115.0.5790.102

* Tue Jul 18 2023 Than Ngo <than@redhat.com> - 115.0.5790.98-1
- update to 115.0.5790.98

* Tue Jun 27 2023 Than Ngo <than@redhat.com> - 114.0.5735.198-1
- update to 114.0.5735.198

* Wed Jun 14 2023 Than Ngo <than@redhat.com> - 114.0.5735.133-1
- update to 114.0.5735.133 
- Enable AllowQt feature flag
- Fix Qt deps
- Fix Qt logical scale factor

* Wed Jun 07 2023 Than Ngo <than@redhat.com> - 114.0.5735.106-1
- update to 114.0.5735.106

* Sun May 28 2023 Than Ngo <than@redhat.com> - 114.0.5735.45-1
- update to 114.0.5735.45
- add qt6 linuxui backend
- backport: handle scale factor changes
- backport: fix font double_scaling

* Wed May 17 2023 Than Ngo <than@redhat.com> - 113.0.5672.126-1
- drop clang workaround for el8
- update to 113.0.5672.126

* Tue May 09 2023 Than Ngo <than@redhat.com> - 113.0.5672.92-1
- update to 113.0.5672.92

* Wed May 03 2023 Than Ngo <than@redhat.com> - 113.0.5672.63-1
- update to 113.0.5672.63

* Sun Apr 23 2023 Than Ngo <than@redhat.com> - 112.0.5615.165-2
- make --use-gl=egl default for x11/wayland
- enable WebUIDarkMode

* Thu Apr 20 2023 Than Ngo <than@redhat.com> - 112.0.5615.165-1
- update to 112.0.5615.165

* Mon Apr 17 2023 Than Ngo <than@redhat.com> - 112.0.5615.121-2
- fix vaapi issue on xwayland
- fix the build order, chrome_feed_response_metadata.pb.h file not found
- fix compiler flags and typo

* Sat Apr 15 2023 Than Ngo <than@redhat.com> - 112.0.5615.121-1
- update to 112.0.5615.121

* Wed Apr 05 2023 Than Ngo <than@redhat.com> - 112.0.5615.49-1
- update to 112.0.5615.49
- fix #2184142, Small fonts in menus

* Tue Mar 28 2023 Than Ngo <than@redhat.com> - 111.0.5563.146-1
- update to 111.0.5563.146

* Sat Mar 25 2023 Neal Gompa <ngompa@fedoraproject.org> - 111.0.5563.110-2
- Fix ffmpeg note in README.fedora

* Wed Mar 22 2023 Than Ngo <than@redhat.com> - 111.0.5563.110-1
- update to 111.0.5563.110

* Sun Mar 12 2023 Neal Gompa <ngompa@fedoraproject.org> - 111.0.5563.64-2
- Rebuild for ffmpeg 6.0

* Tue Mar 07 2023 Than Ngo <than@redhat.com> - 111.0.5563.64-1
- update to 111.0.5563.64

* Mon Mar 06 2023 Than Ngo <than@redhat.com> - 111.0.5563.50-1
- update to 111.0.5563.50
- system freetype on fedora > 36

* Thu Feb 23 2023 Than Ngo <than@redhat.com> - 110.0.5481.177-1
- update to 110.0.5481.177
- workaround for crash on aarch64, rhel8

* Wed Feb 22 2023 Jan Grulich <jgrulich@redhat.com> - 110.0.5481.100-3
- Enable PipeWire screen sharing on RHEL8+

* Tue Feb 21 2023 Than Ngo <than@redhat.com> - 110.0.5481.100-2
- fixed bz#2036205, failed to load GLES library

* Fri Feb 17 2023 Than Ngo <than@redhat.com> - 110.0.5481.100-1
- update to 110.0.5481.100

* Thu Feb 16 2023 Than Ngo <than@redhat.com> - 110.0.5481.77-2
- fix #2071126, enable support V4L2 stateless decoders for aarch64 plattform
- fix prefers-color-scheme
- drop snapshot_blob.bin, replace snapshot_blob.bin with v8_context_snapshot.bin
- move headless_lib*.pak to headless subpackage

* Wed Feb 08 2023 Than Ngo <than@redhat.com> - 110.0.5481.77-1
- update to 110.0.5481.77

* Sat Feb 04 2023 Than Ngo <than@redhat.com> - 110.0.5481.61-1
- update to 110.0.5481.61

* Thu Feb 02 2023 Jan Grulich <jgrulich@redhat.com> - 109.0.5414.119-2
- Use ffmpeg decoders for h264 support

* Wed Jan 25 2023 Than Ngo <than@redhat.com> - 109.0.5414.119-1
- update to 109.0.5414.119

* Sun Jan 22 2023 Than Ngo <than@redhat.com> - 109.0.5414.74-4
- clean up

* Wed Jan 18 2023 Fedora Release Engineering <releng@fedoraproject.org> - 109.0.5414.74-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_38_Mass_Rebuild

* Sun Jan 15 2023 Than Ngo <than@redhat.com> - 109.0.5414.74-2
- conditionalize system_build_flags
- cleaned up gn defines
- add BR on python3-importlib-metadata
- set correct toolchain gcc|clang
- fix FTBFS with gcc13

* Wed Jan 11 2023 Than Ngo <than@redhat.com> - 109.0.5414.74-1
- update to 109.0.5414.74

* Tue Jan 10 2023 Than Ngo <than@redhat.com> - 108.0.5359.124-5
- enable qt backend for el >= 9 and fedora >= 35
- drop i686
- conditional BR on java-1.8.0-openjdk-headless

* Sun Jan 08 2023 Than Ngo <than@redhat.com> - 108.0.5359.124-4
- vaapi support for wayland

* Wed Jan 04 2023 Than Ngo <than@redhat.com> - 108.0.5359.124-3
- build with system ffmpeg-free and system libaom
- fix widewine extension issue
- vaapi, disable UseChromeOSDirectVideoDecoder
- workaround for linking issue in clang <= 14

* Sun Jan  1 2023 Tom Callaway <spot@fedoraproject.org> - 108.0.5359.124-2
- turn headless back on (chrome-remote-desktop will stay off, probably forever)

* Wed Dec 28 2022 Than Ngo <than@redhat.com> - 108.0.5359.124-1
- update to 108.0.5359.124
- switch to clang

* Tue Nov 29 2022 Than Ngo <than@redhat.com> - 107.0.5304.121-1
- update to 107.0.5304.121

* Fri Nov 11 2022 Than Ngo <than@redhat.com> - 107.0.5304.110-1
- update to 107.0.5304.110

* Fri Sep 23 2022 Tom Callaway <spot@fedoraproject.org> - 105.0.5195.125-2
- apply upstream fix for wayland menu misplacement bug

* Mon Sep 19 2022 Tom Callaway <spot@fedoraproject.org> - 105.0.5195.125-1
- update to 105.0.5195.125

* Thu Sep  1 2022 Tom Callaway <spot@fedoraproject.org> - 105.0.5195.52-1
- update to 105.0.5195.52

* Thu Aug 18 2022 Tom Callaway <spot@fedoraproject.org> - 104.0.5112.101-1
- update to 104.0.5112.101

* Wed Jul 20 2022 Fedora Release Engineering <releng@fedoraproject.org> - 103.0.5060.114-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_37_Mass_Rebuild

* Wed Jul 13 2022 Tom Callaway <spot@fedoraproject.org> - 103.0.5060.114-1
- update to 103.0.5060.114

* Wed Jun 22 2022 Tom Callaway <spot@fedoraproject.org> - 103.0.5060.53-1
- update to 103.0.5060.53

* Thu Jun 16 2022 Tom Callaway <spot@fedoraproject.org> - 102.0.5005.115-2
- fix minizip Requires for EL9

* Fri Jun 10 2022 Tom Callaway <spot@fedoraproject.org> - 102.0.5005.115-1
- update to 102.0.5005.115

* Fri Jun  3 2022 Tom Callaway <spot@fedoraproject.org> - 102.0.5005.61-1
- update to 102.0.5005.61

* Wed Apr 27 2022 Tom Callaway <spot@fedoraproject.org> - 101.0.4951.41-1
- update to 101.0.4951.41

* Thu Apr 21 2022 Tom Callaway <spot@fedoraproject.org> - 100.0.4896.127-1
- update to 100.0.4896.127

* Tue Apr  5 2022 Tom Callaway <spot@fedoraproject.org> - 100.0.4896.75-1
- update to 100.0.4896.75

* Sat Apr  2 2022 Tom Callaway <spot@fedoraproject.org> - 100.0.4896.60-1
- update to 100.0.4896.60

* Sun Mar 27 2022 Tom Callaway <spot@fedoraproject.org> - 99.0.4844.84-1
- update to 99.0.4844.84
- package up libremoting_core.so* for chrome-remote-desktop
- strip all the .so files (and binaries)

* Sat Mar 19 2022 Tom Callaway <spot@fedoraproject.org> - 99.0.4844.74-1
- update to 99.0.4844.74

* Sat Mar  5 2022 Tom Callaway <spot@fedoraproject.org> - 99.0.4844.5-1
- update to 99.0.4844.5

* Fri Feb 25 2022 Tom Callaway <spot@fedoraproject.org> - 98.0.4758.102-1
- update to 98.0.4758.102
- fix build issue with subzero and gcc12

* Tue Feb  8 2022 Tom Callaway <spot@fedoraproject.org> - 98.0.4758.80-1
- update to 98.0.4758.80

* Sat Feb 05 2022 Jiri Vanek <jvanek@redhat.com> - 96.0.4664.110-9
- Rebuilt for java-17-openjdk as system jdk

* Wed Jan 19 2022 Fedora Release Engineering <releng@fedoraproject.org> - 96.0.4664.110-8
- Rebuilt for https://fedoraproject.org/wiki/Fedora_36_Mass_Rebuild

* Wed Jan  5 2022 Tom Callaway <spot@fedoraproject.org> - 96.0.4664.110-7
- i hate regex. trying again

* Tue Jan  4 2022 Tom Callaway <spot@fedoraproject.org> - 96.0.4664.110-6
- always filter provides, was previously inside conditional for shared builds

* Mon Jan  3 2022 Tom Callaway <spot@fedoraproject.org> - 96.0.4664.110-5
- fix provides filtering to be more inclusive (and work properly)

* Thu Dec 30 2021 Tom Callaway <spot@fedoraproject.org> - 96.0.4664.110-4
- package up more swiftshader/angle stuff
- move swiftshader files to -common so headless can use them

* Mon Dec 27 2021 Tom Callaway <spot@fedoraproject.org> - 96.0.4664.110-3
- have chromium-browser.sh check for wayland env vars and if found, set ozone flags appropriately
  Thanks to Neal Gompa for the nudge

* Mon Dec 20 2021 Tom Callaway <spot@fedoraproject.org> - 96.0.4664.110-2
- enable WebRTCPipeWireCapturer by default

* Thu Dec 16 2021 Tom Callaway <spot@fedoraproject.org> - 96.0.4664.110-1
- update to 96.0.4664.110

* Fri Nov 19 2021 Tom Callaway <spot@fedoraproject.org> - 96.0.4664.45-1
- update to 96.0.4664.45

* Fri Nov 12 2021 Tom Callaway <spot@fedoraproject.org> - 95.0.4638.69-1
- update to 95.0.4638.69

* Fri Oct  8 2021 Tom Callaway <spot@fedoraproject.org> - 94.0.4606.81-1
- update to 94.0.4606.81

* Wed Oct  6 2021 Tom Callaway <spot@fedoraproject.org> - 94.0.4606.71-2
- add official_build flag
- apply upstream patch to handle nullptr correctly in PartitionGetSizeEstimate()

* Tue Oct  5 2021 Tom Callaway <spot@fedoraproject.org> - 94.0.4606.71-1
- update to 94.0.4606.71

* Fri Sep 24 2021 Tom Callaway <spot@fedoraproject.org> - 94.0.4606.61-1
- update to 94.0.4606.61

* Thu Sep 23 2021 Tom Callaway <spot@fedoraproject.org> - 94.0.4606.54-1
- update to 94.0.4606.54

* Mon Sep 20 2021 Tom Callaway <spot@fedoraproject.org> - 93.0.4577.82-2
- add fix for harfbuzz v3 (thanks to Jan Beich @ FreeBSD)

* Thu Sep 16 2021 Tom Callaway <spot@fedoraproject.org> - 93.0.4577.82-1
- update to 93.0.4577.82

* Thu Sep  2 2021 Tom Callaway <spot@fedoraproject.org> - 93.0.4577.63-1
- update to 93.0.4577.63

* Mon Aug 30 2021 Tom Callaway <spot@fedoraproject.org> - 92.0.4515.159-2
- disable userfaultd code in epel8
- include crashpad_handler (it works a lot better when it doesn't immediately crash because of this missing file)

* Tue Aug 17 2021 Tom Callaway <spot@fedoraproject.org> - 92.0.4515.159-1
- update to 92.0.4515.159

* Mon Aug 16 2021 Tom Callaway <spot@fedoraproject.org> - 92.0.4515.131-1
- update to 92.0.4515.131
- apply upstream fix for clone3 crash

* Mon Jul 26 2021 Tom Callaway <spot@fedoraproject.org> - 92.0.4515.107-1
- update to 92.0.4515.107
- drop python2 deps (finally)

* Wed Jul 21 2021 Fedora Release Engineering <releng@fedoraproject.org> - 91.0.4472.164-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_35_Mass_Rebuild

* Fri Jul 16 2021 Tom Callaway <spot@fedoraproject.org> - 91.0.4472.164-1
- update to 91.0.4472.164

* Tue Jul  6 2021 Tom Callaway <spot@fedoraproject.org> - 91.0.4472.114-2
- fix ThemeService crash (thanks OpenSUSE)

* Wed Jun 23 2021 Tom Callaway <spot@fedoraproject.org> - 91.0.4472.114-1
- update to 91.0.4472.114

* Tue Jun  1 2021 Tom Callaway <spot@fedoraproject.org> - 91.0.4472.77-1
- update to 91.0.4472.77

* Tue May 18 2021 Tom Callaway <spot@fedoraproject.org> - 90.0.4430.212-1
- update to 90.0.4430.212

* Tue Apr 27 2021 Tom Callaway <spot@fedoraproject.org> - 90.0.4430.93-1
- update to 90.0.4430.93

* Wed Apr 21 2021 Tom Callaway <spot@fedoraproject.org> - 90.0.4430.85-1
- update to 90.0.4430.85

* Fri Apr 16 2021 Tom Callaway <spot@fedoraproject.org> - 90.0.4430.72-1
- update to 90.0.4430.72

* Wed Apr 14 2021 Tom Callaway <spot@fedoraproject.org> - 89.0.4389.128-1
- update to 89.0.4389.128

* Wed Mar 31 2021 Jonathan Wakely <jwakely@redhat.com> - 89.0.4389.90-5
- Rebuilt for removed libstdc++ symbols (#1937698)

* Mon Mar 29 2021 Tom Callaway <spot@fedoraproject.org> - 89.0.4389.90-4
- fix libva compile in rawhide

* Thu Mar 25 2021 Tom Callaway <spot@fedoraproject.org> - 89.0.4389.90-3
- apply upstream fix for newer system libva

* Wed Mar 24 2021 Tom Callaway <spot@fedoraproject.org> - 89.0.4389.90-2
- fix crashes with components/cast_*

* Thu Mar 18 2021 Tom Callaway <spot@fedoraproject.org> - 89.0.4389.90-1
- update to 89.0.4389.90
- disable auto-download of widevine binary only blob

* Mon Mar 15 2021 Tom Callaway <spot@fedoraproject.org> - 89.0.4389.82-2
- add support for futex_time64

* Mon Mar  8 2021 Tom Callaway <spot@fedoraproject.org> - 89.0.4389.82-1
- update to 89.0.4389.82

* Thu Mar  4 2021 Tom Callaway <spot@fedoraproject.org> - 89.0.4389.72-1
- update to 89.0.4389.72

* Tue Mar 02 2021 Zbigniew Jędrzejewski-Szmek <zbyszek@in.waw.pl> - 88.0.4324.182-3
- Rebuilt for updated systemd-rpm-macros
  See https://pagure.io/fesco/issue/2583.

* Thu Feb 25 2021 Tom Callaway <spot@fedoraproject.org> - 88.0.4234.182-2
- fix swiftshader symbols in libEGL/libGLESv2 with gcc

* Wed Feb 17 2021 Tom Callaway <spot@fedoraproject.org> - 88.0.4234.182-1
- update to 88.0.4234.182

* Fri Feb  5 2021 Tom Callaway <spot@fedoraproject.org> - 88.0.4234.150-1
- update to 88.0.4234.150

* Tue Feb  2 2021 Tom Callaway <spot@fedoraproject.org> - 88.0.4234.146-1
- update to 88.0.4234.146

* Tue Feb  2 2021 Tom Callaway <spot@fedoraproject.org> - 88.0.4234.96-4
- turn on the API key (just the API key, not the client_id or client_secret)

* Tue Jan 26 2021 Fedora Release Engineering <releng@fedoraproject.org> - 88.0.4324.96-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_34_Mass_Rebuild

* Mon Jan 25 2021 Tom Callaway <spot@fedoraproject.org> - 88.0.4324.96-2
- apply fix from Kevin Kofler for new glibc fstat sandbox handling

* Wed Jan 20 2021 Tom Callaway <spot@fedoraproject.org> - 88.0.4324.96-1
- 88 goes from beta to stable
- disable use of api keys (Google shut off API access)

* Wed Jan 13 2021 Tom Callaway <spot@fedoraproject.org>
- update to 87.0.4280.141

* Wed Dec 30 2020 Tom Callaway <spot@fedoraproject.org> - 88.0.4324.50-1
- update to 88.0.4324.50
- drop patches 74 & 75 (applied upstream)

* Thu Dec 17 2020 Tom Callaway <spot@fedoraproject.org>
- add two patches for missing headers to build with gcc 11

* Thu Dec  3 2020 Tom Callaway <spot@fedoraproject.org> - 88.0.4324.27-1
- dev release to prepare for next stable

* Thu Dec  3 2020 Tom Callaway <spot@fedoraproject.org> - 87.0.4280.88-1
- update to 87.0.4280.88

* Wed Nov 18 2020 Tom Callaway <spot@fedoraproject.org> - 87.0.4280.66-1
- update to 87.0.4280.66

* Thu Nov 12 2020 Jeff Law <law@fedoraproject.org> - 86.0.4240.198-1
- Fix missing #inclues for gcc-11
- Fix bogus volatile caught by gcc-11

* Thu Nov 12 2020 Tom Callaway <spot@fedoraproject.org> - 86.0.4240.198-1
- update to 86.0.4240.198

* Tue Nov 10 2020 Tom Callaway <spot@fedoraproject.org> - 86.0.4240.193-1
- update to 86.0.4240.193

* Wed Nov  4 2020 Tom Callaway <spot@fedoraproject.org> - 86.0.4240.183-1
- update to 86.0.4240.183

* Mon Nov  2 2020 Tom Callaway <spot@fedoraproject.org> - 86.0.4240.111-2
- fix conditional typo that was causing console logging to be turned on

* Wed Oct 21 2020 Tom Callaway <spot@fedoraproject.org> - 86.0.4240.111-1
- update to 86.0.4240.111

* Tue Oct 20 2020 Tom Callaway <spot@fedoraproject.org> - 86.0.4240.75-2
- use bundled zlib/minizip on el7 (thanks Red Hat. :P)

* Wed Oct 14 2020 Tom Callaway <spot@fedoraproject.org> - 86.0.4240.75-1
- update to 86.0.4240.75

* Mon Sep 28 2020 Tom Callaway <spot@fedoraproject.org> - 85.0.4183.121-2
- rebuild for libevent

* Mon Sep 21 2020 Tom Callaway <spot@fedoraproject.org> - 85.0.4183.121-1
- update to 85.0.4183.121
- apply upstream fix for networking issue with CookieMonster

* Tue Sep  8 2020 Tom Callaway <spot@fedoraproject.org> - 85.0.4183.102-1
- update to 85.0.4183.102
- install ANGLE so files (libEGL.so, libGLESv2.so)

* Wed Aug 26 2020 Tom Callaway <spot@fedoraproject.org> - 85.0.4183.83-1
- update to 85.0.4183.83

* Thu Aug 20 2020 Tom Callaway <spot@fedoraproject.org> - 84.0.4147.135-1
- update to 84.0.4147.135
- conditionalize build_clear_key_cdm
- disable build_clear_key_cdm on F33+ aarch64 until binutils bug is fixed
- properly install libclearkeycdm.so everywhere else (whoops)

* Mon Aug 17 2020 Tom Callaway <spot@fedoraproject.org> - 84.0.4147.125-2
- force fix_textrels fix in ffmpeg for i686 (even without lld)

* Mon Aug 10 2020 Tom Callaway <spot@fedoraproject.org> - 84.0.4147.125-1
- update to 84.0.4147.125

* Sat Aug 01 2020 Fedora Release Engineering <releng@fedoraproject.org> - 84.0.4147.105-2
- Second attempt - Rebuilt for
  https://fedoraproject.org/wiki/Fedora_33_Mass_Rebuild

* Fri Jul 31 2020 Tom Callaway <spot@fedoraproject.org> - 84.0.4147.105-1
- update to 84.0.4147.105

* Mon Jul 27 2020 Fedora Release Engineering <releng@fedoraproject.org> - 84.0.4147.89-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_33_Mass_Rebuild

* Wed Jul 15 2020 Tom Callaway <spot@fedoraproject.org> - 84.0.4147.89-1
- update to 84.0.4147.89

* Sat Jun 27 2020 Tom Callaway <spot@fedoraproject.org> - 83.0.4103.116-3
- only set ozone on headless
- enable use_kerberos

* Tue Jun 23 2020 Tom Callaway <spot@fedoraproject.org> - 83.0.4103.116-2
- do not force ozone into x11

* Tue Jun 23 2020 Tom Callaway <spot@fedoraproject.org> - 83.0.4103.116-1
- update to 83.0.4103.116

* Thu Jun 18 2020 Tom Callaway <spot@fedoraproject.org> - 83.0.4103.106-1
- update to 83.0.4103.106
- remove duplicate ServiceWorker fix
- add fix to work around gcc bug on aarch64
- disable python byte compiling (we do not need it)

* Tue Jun 16 2020 Tom Callaway <spot@fedoraproject.org> - 83.0.4103.97-5
- add ServiceWorker fix

* Mon Jun 15 2020 Tom Callaway <spot@fedoraproject.org> - 83.0.4103.97-4
- use old cups handling on epel7
- fix skia attribute overrides with gcc

* Wed Jun 10 2020 Tom Callaway <spot@fedoraproject.org> - 83.0.4103.97-3
- fix issue on epel7 where linux/kcmp.h does not exist

* Mon Jun  8 2020 Tom Callaway <spot@fedoraproject.org> - 83.0.4103.97-2
- more fixes from gentoo

* Sun Jun  7 2020 Tom Callaway <spot@fedoraproject.org> - 83.0.4103.97-1
- update to 83.0.4103.97

* Tue Jun  2 2020 Tom Callaway <spot@fedoraproject.org> - 83.0.4103.61-1
- update to 83.0.4103.61
- conditionalize and disable remoting

* Thu May  7 2020 Tom Callaway <spot@fedoraproject.org> - 81.0.4044.138-1
- update to 81.0.4044.138

* Tue May  5 2020 Tom Callaway <spot@fedoraproject.org> - 81.0.4044.129-1
- update to 81.0.4044.129

* Thu Apr 23 2020 Tom Callaway <spot@fedoraproject.org> - 81.0.4044.122-1
- update to 81.0.4044.122

* Tue Apr 21 2020 Tom Callaway <spot@fedoraproject.org> - 81.0.4044.113-2
- add explicit Requires: chromium-common

* Thu Apr 16 2020 Tom Callaway <spot@fedoraproject.org> - 81.0.4044.113-1
- update to 81.0.4044.113

* Mon Apr 13 2020 Tom Callaway <spot@fedoraproject.org> - 81.0.4044.92-1
- update to 81.0.4044.92
- squelch the selinux output in the post scriptlet
- add Provides/Obsoletes in case we're build with shared set to 0
- add ulimit -n 4096 (needed for static builds, probably not harmful for shared builds either)
- do static build

* Sat Apr  4 2020 Tom Callaway <spot@fedoraproject.org> - 80.0.3987.163-1
- update to 80.0.3987.163

* Wed Apr  1 2020 Tom Callaway <spot@fedoraproject.org> - 80.0.3987.162-1
- update to 80.0.3987.162

* Wed Mar 18 2020 Tom Callaway <spot@fedoraproject.org> - 80.0.3987.149-1
- update to 80.0.3987.149

* Thu Feb 27 2020 Tom Callaway <spot@fedoraproject.org> - 80.0.3987.132-1
- update to 80.0.3987.132
- disable C++17 changes (this means f32+ will no longer build, but it segfaulted immediately)

* Thu Feb 27 2020 Tom Callaway <spot@fedoraproject.org> - 80.0.3987.122-1
- update to 80.0.3987.122

* Mon Feb 17 2020 Tom Callaway <spot@fedoraproject.org> - 80.0.3987.106-1
- update to 80.0.3987.106

* Wed Feb  5 2020 Tom Callaway <spot@fedoraproject.org> - 80.0.3987.87-1
- update to 80.0.3987.87

* Tue Jan 28 2020 Fedora Release Engineering <releng@fedoraproject.org> - 79.0.3945.130-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_32_Mass_Rebuild

* Fri Jan 17 2020 Tom Callaway <spot@fedoraproject.org> - 79.0.3945.130-1
- update to 79.0.3945.130

* Thu Jan  9 2020 Tom Callaway <spot@fedoraproject.org> - 79.0.3945.117-1
- update to 79.0.3945.117

* Tue Dec 17 2019 Tom Callaway <spot@fedoraproject.org> - 79.0.3945.88-1
- update to 79.0.3945.88

* Tue Dec 10 2019 Tom Callaway <spot@fedoraproject.org> - 79.0.3945.79-1
- update to 79.0.3945.79

* Wed Dec  4 2019 Tom Callaway <spot@fedoraproject.org> - 79.0.3945.56-2
- fix lib provides filtering

* Tue Dec  3 2019 Tom Callaway <spot@fedoraproject.org> - 79.0.3945.56-1
- update to current beta (rawhide only)
- switch to upstream patch for clock_nanosleep fix

* Mon Nov 25 2019 Tom Callaway <spot@fedoraproject.org> - 78.0.3904.108-1
- update to 78.0.3904.108

* Sun Nov 17 2019 Tom Callaway <spot@fedoraproject.org> - 78.0.3904.97-2
- allow clock_nanosleep through seccomp (bz #1773289)

* Thu Nov  7 2019 Tom Callaway <spot@fedoraproject.org> - 78.0.3904.97-1
- update to 78.0.3904.97

* Fri Nov  1 2019 Tom Callaway <spot@fedoraproject.org> - 78.0.3904.87-1
- update to 78.0.3904.87
- apply most of the freeworld changes in PR 23/24/25

* Wed Oct 23 2019 Tom Callaway <spot@fedoraproject.org> - 78.0.3904.80-1
- update to 78.0.3904.80

* Wed Oct 16 2019 Tom Callaway <spot@fedoraproject.org> - 77.0.3865.120-4
- upstream fix for zlib symbol exports with gcc

* Wed Oct 16 2019 Tom Callaway <spot@fedoraproject.org> - 77.0.3865.120-3
- silence outdated build noise (bz1745745)

* Tue Oct 15 2019 Tom Callaway <spot@fedoraproject.org> - 77.0.3865.120-2
- fix node handling for EPEL-8

* Mon Oct 14 2019 Tomas Popela <tpopela@redhat.com> - 77.0.3865.120-1
- Update to 77.0.3865.120

* Thu Oct 10 2019 Tom Callaway <spot@fedoraproject.org> - 77.0.3865.90-4
- enable aarch64 for EPEL-8

* Wed Oct  9 2019 Tom Callaway <spot@fedoraproject.org> - 77.0.3865.90-3
- spec cleanups and changes to make EPEL8 try to build

* Mon Sep 23 2019 Tomas Popela <tpopela@redhat.com> - 77.0.3865.90-2
- Fix the icon
- Remove quite a few of downstream patches
- Fix the crashes by backporting an upstream bug
- Resolves: rhbz#1754179

* Thu Sep 19 2019 Tomas Popela <tpopela@redhat.com> - 77.0.3865.90-1
- Update to 77.0.3865.90

* Mon Sep 16 2019 Tomas Popela <tpopela@redhat.com> - 77.0.3865.75-2
- Update the list of private libraries

* Fri Sep 13 2019 Tomas Popela <tpopela@redhat.com> - 77.0.3865.75-1
- Update to 77.0.3865.75

* Tue Sep 03 2019 Tomas Popela <tpopela@redhat.com> - 76.0.3809.132-2
- Backport patch to fix certificate transparency

* Tue Aug 27 2019 Tomas Popela <tpopela@redhat.com> - 76.0.3809.132-1
- Update to 76.0.3809.132

* Tue Aug 13 2019 Tomas Popela <tpopela@redhat.com> - 76.0.3809.100-1
- Update to 76.0.3809.100

* Wed Jul 24 2019 Fedora Release Engineering <releng@fedoraproject.org> - 75.0.3770.100-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_31_Mass_Rebuild

* Tue Jul  2 2019 Tom Callaway <spot@fedoraproject.org> - 75.0.3770.100-3
- apply upstream fix to resolve issue where it is dangerous to post a
  task with a RenderProcessHost pointer because the RenderProcessHost
  can go away before the task is run (causing a segfault).

* Tue Jun 25 2019 Tom Callaway <spot@fedoraproject.org> - 75.0.3770.100-2
- fix v8 compile with gcc

* Thu Jun 20 2019 Tom Callaway <spot@fedoraproject.org> - 75.0.3770.100-1
- update to 75.0.3770.100

* Fri Jun 14 2019 Tom Callaway <spot@fedoraproject.org> - 75.0.3770.90-1
- update to 75.0.3770.90

* Wed Jun  5 2019 Tom Callaway <spot@fedoraproject.org> - 75.0.3770.80-1
- update to 75.0.3770.80
- disable vaapi (via conditional), too broken

* Fri May 31 2019 Tom Callaway <spot@fedoraproject.org> - 74.0.3729.169-1
- update to 74.0.3729.169

* Thu Apr 11 2019 Tom Callaway <spot@fedoraproject.org> - 73.0.3683.103-1
- update to 73.0.3683.103
- add CLONE_VFORK logic to seccomp filter for linux to handle glibc 2.29 change

* Wed Mar 27 2019 Tom Callaway <spot@fedoraproject.org> - 73.0.3683.86-2
- remove lang macro from en-US.pak* because Chromium crashes if it is not present
  (bz1692660)

* Fri Mar 22 2019 Tom Callaway <spot@fedoraproject.org> - 73.0.3683.86-1
- update to 73.0.3683.86

* Tue Mar 19 2019 Tom Callaway <spot@fedoraproject.org> - 73.0.3683.75-2
- do not include pyproto/protoc files in package

* Tue Mar 12 2019 Tom Callaway <spot@fedoraproject.org> - 73.0.3683.75-1
- update to 73.0.3683.75

* Sat Mar  9 2019 Tom Callaway <spot@fedoraproject.org> - 72.0.3626.121-1
- update to 72.0.3626.121

* Tue Feb 26 2019 Tom Callaway <spot@fedoraproject.org> - 71.0.3578.98-5
- rebuild for libva api change

* Thu Jan 31 2019 Fedora Release Engineering <releng@fedoraproject.org> - 71.0.3578.98-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_30_Mass_Rebuild

* Mon Jan 21 2019 Tom Callaway <spot@fedoraproject.org> - 71.0.3578.98-3
- rebuild with widevine fix

* Tue Jan  8 2019 Tom Callaway <spot@fedoraproject.org> - 71.0.3578.98-2
- drop rsp clobber, which breaks gcc9 (thanks to Jeff Law)

* Fri Dec 14 2018 Tom Callaway <spot@fedoraproject.org> - 71.0.3578.98-1
- update to 71.0.3578.98

* Tue Nov 27 2018 Tom Callaway <spot@fedoraproject.org> - 70.0.3538.110-2
- enable vaapi support (thanks to Akarshan Biswas for doing the hard work here)

* Mon Nov 26 2018 Tom Callaway <spot@fedoraproject.org> - 70.0.3538.110-1
- update to .110

* Wed Nov  7 2018 Tom Callaway <spot@fedoraproject.org> - 70.0.3538.77-4
- fix library requires filtering

* Tue Nov  6 2018 Tom Callaway <spot@fedoraproject.org> - 70.0.3538.77-3
- fix build with harfbuzz2 in rawhide

* Mon Nov  5 2018 Tom Callaway <spot@fedoraproject.org> - 70.0.3538.77-2
- drop jumbo_file_merge_limit to 8 to (hopefully) avoid OOMs on aarch64

* Fri Nov  2 2018 Tom Callaway <spot@fedoraproject.org> - 70.0.3538.77-1
- .77 came out while I was working on this. :/

* Fri Nov  2 2018 Tom Callaway <spot@fedoraproject.org> - 70.0.3538.67-1
- update to 70

* Tue Oct 16 2018 Tom Callaway <spot@fedoraproject.org> - 69.0.3497.100-2
- do not play with fonts on freeworld builds

* Thu Oct  4 2018 Tom Callaway <spot@fedoraproject.org> - 69.0.3497.100-1
- update to 69.0.3497.100

* Wed Sep 12 2018 Tom Callaway <spot@fedoraproject.org> - 69.0.3497.92-1
- update to 69.0.3497.92

* Wed Sep  5 2018 Tom Callaway <spot@fedoraproject.org> - 69.0.3497.81-1
- update to 69.0.3497.81

* Tue Aug 28 2018 Patrik Novotný <panovotn@redhat.com> - 68.0.3440.106-4
- change requires to minizip-compat(-devel), rhbz#1609830, rhbz#1615381

* Sun Aug 19 2018 Tom Callaway <spot@fedoraproject.org> - 68.0.3440.106-3
- fix library filters

* Fri Aug 17 2018 Tom Callaway <spot@fedoraproject.org> - 68.0.3440.106-2
- fix error with defaulting on redeclaration

* Thu Aug  9 2018 Tom Callaway <spot@fedoraproject.org> - 68.0.3440.106-1
- update to 68.0.3440.106

* Wed Aug  8 2018 Tom Callaway <spot@fedoraproject.org> - 68.0.3440.84-1
- update to 68.0.3440.84

* Mon Jul 30 2018 Tom Callaway <spot@fedoraproject.org> - 68.0.3440.75-1
- update to 68.0.3440.75

* Thu Jul 12 2018 Fedora Release Engineering <releng@fedoraproject.org> - 67.0.3396.99-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_29_Mass_Rebuild

* Mon Jul  9 2018 Tom Callaway <spot@fedoraproject.org> 67.0.3396.99-1
- update to 67.0.3396.99

* Mon Jun 25 2018 Tom Callaway <spot@fedoraproject.org> 67.0.3396.87-2
- add "Fedora" to the user agent string

* Tue Jun 19 2018 Tom Callaway <spot@fedoraproject.org> 67.0.3396.87-1
- update to 67.0.3396.87

* Thu Jun  7 2018 Tom Callaway <spot@fedoraproject.org> 67.0.3396.79-1
- update to 67.0.3396.79

* Wed Jun  6 2018 Tom Callaway <spot@fedoraproject.org> 67.0.3396.62-2
- work around bug in RHEL7 python exec

* Wed May 30 2018 Tom Callaway <spot@fedoraproject.org> 67.0.3396.62-1
- 67 releases of chromium on the wall...

* Tue May 29 2018 Tom Callaway <spot@fedoraproject.org> 66.0.3359.181-3
- also filter out fontconfig on epel7

* Wed May 23 2018 Tom Callaway <spot@fedoraproject.org> 66.0.3359.181-2
- fix missing files

* Mon May 21 2018 Tom Callaway <spot@fedoraproject.org> 66.0.3359.181-1
- update to 66.0.3359.181

* Tue May 15 2018 Tom Callaway <spot@fedoraproject.org> 66.0.3359.170-2
- only x86_64 i686 have swiftshader
- fix gcc8 alignof issue on i686

* Mon May 14 2018 Tom Callaway <spot@fedoraproject.org> 66.0.3359.170-1
- update to 66.0.3359.170
- include swiftshader files

* Tue May  1 2018 Tom Callaway <spot@fedoraproject.org> 66.0.3359.139-1
- update to 66.0.3359.139

* Wed Apr 18 2018 Tom Callaway <spot@fedoraproject.org> 66.0.3359.117-1
- update to 66.0.3359.117

* Tue Apr 17 2018 Tom Callaway <spot@fedoraproject.org> 65.0.3325.181-3
- use system fontconfig (except on epel7)

* Wed Apr  4 2018 Tom Callaway <spot@fedoraproject.org> 65.0.3325.181-2
- add explicit dependency on minizip (bz 1534282)

* Wed Mar 28 2018 Tom Callaway <spot@fedoraproject.org>
- check that there is no system 'google' module, shadowing bundled ones
- conditionalize api keys (on by default)

* Wed Mar 21 2018 Tom Callaway <spot@fedoraproject.org> 65.0.3325.181-1
- update to 65.0.3325.181

* Mon Mar 19 2018 Tom Callaway <spot@fedoraproject.org> 65.0.3325.162-3
- use bundled libdrm on epel7

* Fri Mar 16 2018 Tom Callaway <spot@fedoraproject.org> 65.0.3325.162-2
- disable StartupNotify in chromium-browser.desktop (not in google-chrome desktop file)
  (bz1545241)
- use bundled freetype on epel7

* Wed Mar 14 2018 Tom Callaway <spot@fedoraproject.org> 65.0.3325.162-1
- update to 65.0.3325.162

* Wed Mar  7 2018 Tom Callaway <spot@fedoraproject.org> 65.0.3325.146-1
- update to 65.0.3325.146

* Mon Mar  5 2018 Tom Callaway <spot@fedoraproject.org> 64.0.3282.186-1
- update to 64.0.3282.186

* Fri Feb 16 2018 Tom Callaway <spot@fedoraproject.org> 64.0.3282.167-1
- update to 64.0.3282.167
- include workaround for gcc8 bug in gn
- disable unnecessary aarch64 glibc symbol change

* Fri Feb  2 2018 Tom Callaway <spot@fedoraproject.org> 64.0.3282.140-1
- update to 64.0.3282.140

* Thu Feb  1 2018 Tom Callaway <spot@fedoraproject.org> 64.0.3282.119-2
- include user-session binary in chrome-remote-desktop subpackage

* Thu Jan 25 2018 Tom Callaway <spot@fedoraproject.org> 64.0.3282.119-1
- update to 64.0.3282.119

* Fri Dec 15 2017 Tomas Popela <tpopela@redhat.com> 63.0.3239.108-1
- Update to 63.0.3239.108

* Thu Dec  7 2017 Tom Callaway <spot@fedoraproject.org> 63.0.3239.84-1
- update to 63.0.3239.84

* Wed Nov  8 2017 Tom Callaway <spot@fedoraproject.org> 62.0.3202.89-1
- update to 62.0.3202.89

* Fri Oct 27 2017 Tom Callaway <spot@fedoraproject.org> 62.0.3202.75-1
- update to 62.0.3202.75
- use devtoolset-7-toolchain to build on epel7

* Tue Oct 24 2017 Tom Callaway <spot@fedoraproject.org> 62.0.3202.62-1.1
- do not attempt std=c++14 on epel7

* Wed Oct 18 2017 Tom Callaway <spot@fedoraproject.org> 62.0.3202.62-1
- update to 62.0.3202.62

* Fri Sep 22 2017 Tom Callaway <spot@fedoraproject.org> 61.0.3163.100-1
- update to 61.0.3163.100
- lots of epel7 specific fixes
- use bundled libpng on epel7

* Wed Sep  6 2017 Tom Callaway <spot@fedoraproject.org> 61.0.3163.79-1
- update to 61.0.3163.79

* Mon Aug 28 2017 Tom Callaway <spot@fedoraproject.org> 60.0.3112.113-2
- disable aarch64 on rhel7, missing libatomic.so for some reason

* Wed Aug 23 2017 Tom Callaway <spot@fedoraproject.org> 60.0.3112.113-1
- fix ffmpeg clean script to not delete aarch64 file
- update to 60.0.3112.113

* Wed Aug 23 2017 Tom Callaway <spot@fedoraproject.org> 60.0.3112.101-3
- apply aarch64 fixes from Ryan Blakely <rblakely@redhat.com>

* Thu Aug 17 2017 Tom Callaway <spot@fedoraproject.org> 60.0.3112.101-2
- fix dep issue with chrome-remote-desktop on el7

* Wed Aug 16 2017 Tom Callaway <spot@fedoraproject.org> 60.0.3112.101-1
- update to 60.0.3112.101
- apply upstream fix for cameras which report zero resolution formats
  (bz1465357)

* Mon Aug 14 2017 Tom Callaway <spot@fedoraproject.org> 60.0.3112.90-3
- apply more workarounds to coax code to build with epel7 gcc

* Wed Aug  9 2017 Tom Callaway <spot@fedoraproject.org> 60.0.3112.90-2
- apply post 60 code commit to get code building on epel7

* Fri Aug  4 2017 Tom Callaway <spot@fedoraproject.org> 60.0.3112.90-1
- update to 60.0.3112.90

* Wed Aug 02 2017 Fedora Release Engineering <releng@fedoraproject.org> - 59.0.3071.115-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Binutils_Mass_Rebuild

* Mon Jul 31 2017 Tom Callaway <spot@fedoraproject.org> 60.0.3112.78-1
- update to 60.0.3112.78

* Wed Jul 26 2017 Fedora Release Engineering <releng@fedoraproject.org> - 59.0.3071.115-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Fri Jul 21 2017 Tom Callaway <spot@fedoraproject.org> 59.0.3071.115-4
- put common files in -common subpackage
- build headless_shell for -headless subpackage

* Fri Jul 21 2017 Tom Callaway <spot@fedoraproject.org> 59.0.3071.115-3
- use posttrans to ensure that old libs are gone before trying to make alternative symlinks

* Thu Jul 13 2017 Tom Callaway <spot@fedoraproject.org> 59.0.3071.115-2
- fix scriptlets

* Wed Jul 12 2017 Tom Callaway <spot@fedoraproject.org> 59.0.3071.115-1
- 59.0.3071.115
- conditionalize spec so it can be easily used to make -libs-media-freeworld

* Wed Jun 28 2017 Dominik Mierzejewski <dominik@greysector.net> 59.0.3071.109-6
- use alternatives for widevine stub and media libs to allow third-party
  packages to replace them without conflicts

* Mon Jun 26 2017 Tom Callaway <spot@fedoraproject.org> 59.0.3071.109-5
- fix path in pretrans scriptlet

* Fri Jun 23 2017 Tom Callaway <spot@fedoraproject.org> 59.0.3071.109-4
- copy files into /etc/opt/chrome/native-messaging-hosts instead of making symlinks
  this results in duplicate copies of the same files, but eh. making rpm happy.

* Fri Jun 23 2017 Tom Callaway <spot@fedoraproject.org> 59.0.3071.109-3
- use pretrans scriptlet to remove symlink on /etc/opt/chrome/native-messaging-hosts
  (it is now a directory)

* Thu Jun 22 2017 Tom Callaway <spot@fedoraproject.org> 59.0.3071.109-2
- fix duplication between chrome-remote-desktop and chromium

* Thu Jun 22 2017 Tom Callaway <spot@fedoraproject.org> 59.0.3071.109-1
- update to .109
- fix native-messaging-hosts dir to be a true dir instead of a symlink

* Fri Jun 16 2017 Tom Callaway <spot@fedoraproject.org> 59.0.3071.104-1
- update to .104

* Fri Jun 16 2017 Tom Callaway <spot@fedoraproject.org> 59.0.3071.86-4
- actually fix mp3 playback support

* Tue Jun 13 2017 Tom Callaway <spot@fedoraproject.org> 59.0.3071.86-3
- fix filtering

* Mon Jun 12 2017 Tom Callaway <spot@fedoraproject.org> 59.0.3071.86-2
- pnacl/nacl now needs llvm to build the bootstrap lib

* Mon Jun 12 2017 Tom Callaway <spot@fedoraproject.org> 59.0.3071.86-1
- update to 59.0.3071.86
- include smaller logo files

* Tue May 16 2017 Tom Callaway <spot@fedoraproject.org> 58.0.3029.110-2
- strip provides/requires on libsensors

* Mon May 15 2017 Tom Callaway <spot@fedoraproject.org> 58.0.3029.110-1
- update to 58.0.3029.110

* Mon May  8 2017 Tom Callaway <spot@fedoraproject.org> 58.0.3029.96-1
- update to 58.0.3029.96

* Fri Apr 21 2017 Tom Callaway <spot@fedoraproject.org> 58.0.3029.81-1
- update to 58.0.3029.81

* Thu Mar 30 2017 Tom Callaway <spot@fedoraproject.org> 57.0.2987.133-1
- update to 57.0.2987.133

* Sun Mar 26 2017 Tom Callaway <spot@fedoraproject.org> 57.0.2987.110-4
- copy compat stdatomic.h in for RHEL. Re-enable mp3 enablement.
- fix issue in gtk_ui.cc revealed by RHEL build

* Sun Mar 26 2017 Tom Callaway <spot@fedoraproject.org> 57.0.2987.110-3
- fix mp3 enablement
- disable mp3 enablement on RHEL (compiler too old)

* Tue Mar 21 2017 Tom Callaway <spot@fedoraproject.org> 57.0.2987.110-2
- fix privlibs

* Mon Mar 20 2017 Tom Callaway <spot@fedoraproject.org> 57.0.2987.110-1
- update to 57.0.2987.110

* Tue Mar 14 2017 Tom Callaway <spot@fedoraproject.org> 57.0.2987.98-1
- update to 57.0.2987.98

* Sun Mar  5 2017 Tom Callaway <spot@fedoraproject.org> 56.0.2924.87-8
- enable mp3 support

* Sat Mar  4 2017 Tom Callaway <spot@fedoraproject.org> 56.0.2924.87-7
- fix desktop file to have "new window" and "new private window" actions

* Tue Feb 28 2017 Tom Callaway <spot@fedoraproject.org> 56.0.2924.87-6
- fix issue with gcc7 compile in v8 (thanks to Ben Noordhuis)

* Fri Feb 24 2017 Tom Callaway <spot@fedoraproject.org> 56.0.2924.87-5
- versioning sync build on rawhide

* Fri Feb 24 2017 Tom Callaway <spot@fedoraproject.org> 56.0.2924.87-4.1
- fix issue with unique_ptr move on return with old gcc

* Tue Feb 21 2017 Tom Callaway <spot@fedoraproject.org> 56.0.2924.87-4
- disable debuginfo

* Mon Feb 13 2017 Tom Callaway <spot@fedoraproject.org> 56.0.2924.87-3
- fix compilation issue
- build third_party/WebKit with -fpermissive
- use bundled jinja everywhere

* Fri Feb 10 2017 Tom Callaway <spot@fedoraproject.org> 56.0.2924.87-2
- add BR: gtk3-devel

* Fri Feb 10 2017 Tom Callaway <spot@fedoraproject.org> 56.0.2924.87-1
- update to 56.0.2924.87

* Fri Feb 10 2017 Fedora Release Engineering <releng@fedoraproject.org> - 55.0.2883.87-2.1
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Tue Dec 13 2016 Tom Callaway <spot@fedoraproject.org> 55.0.2883.87-1.1
- use bundled jinja2 on RHEL (or Fedora older than 23)
- fix rvalue issue in remoting code

* Tue Dec 13 2016 Tom Callaway <spot@fedoraproject.org> 55.0.2883.87-1
- update to 55.0.2883.87

* Mon Dec 12 2016 Tom Callaway <spot@fedoraproject.org> 55.0.2883.75-1
- update to 55.0.2883.75

* Fri Dec  2 2016 Tom Callaway <spot@fedoraproject.org> 54.0.2840.100-1
- update to 54.0.2840.100

* Fri Nov  4 2016 Tom Callaway <spot@fedoraproject.org> 54.0.2840.90-3
- when use_aura is on, chrome/browser needs to link to ui/snapshot

* Wed Nov  2 2016 Tom Callaway <spot@fedoraproject.org> 54.0.2840.90-2
- export setOpaque in cc_blink

* Wed Nov  2 2016 Tom Callaway <spot@fedoraproject.org> 54.0.2840.90-1
- update to 54.0.2840.90
- undo ld manipulation for i686, just use -g1 there

* Tue Nov  1 2016 Tom Callaway <spot@fedoraproject.org> 54.0.2840.71-2
- disable debugging

* Wed Oct 26 2016 Tom Callaway <spot@fedoraproject.org> 54.0.2840.71-1
- update to 54.0.2840.71

* Wed Oct 26 2016 Tom Callaway <spot@fedoraproject.org> 54.0.2840.59-2
- fix deps

* Thu Oct 13 2016 Tom Callaway <spot@fedoraproject.org> 54.0.2840.59-1
- 54.0.2840.59
- use bundled opus, libevent

* Fri Sep 30 2016 Tom Callaway <spot@fedoraproject.org> 53.0.2785.143-1
- 53.0.2785.143

* Tue Sep 20 2016 Tom Callaway <spot@fedoraproject.org> 53.0.2785.116-1
- 53.0.2785.116

* Wed Sep 14 2016 Tom Callaway <spot@fedoraproject.org> 53.0.2785.113-1
- 53.0.2785.113

* Thu Sep  8 2016 Tom Callaway <spot@fedoraproject.org> 53.0.2785.101-1
- 53.0.2785.101
- happy star trek day. live long and prosper.

* Wed Sep  7 2016 Tom Callaway <spot@fedoraproject.org> 53.0.2785.92-1
- add basic framework for gn tooling (disabled because it doesn't work yet)
- update to 53.0.2785.92
- fix HOME environment issue in chrome-remote-desktop service file

* Mon Aug 29 2016 Tom Callaway <spot@fedoraproject.org> 52.0.2743.116-11
- conditionalize Requires: u2f-hidraw-policy so that it is only used on Fedora
- use bundled harfbuzz on EL7

* Thu Aug 18 2016 Tom Callaway <spot@fedoraproject.org> 52.0.2743.116-10
- disable gtk3 because it breaks lots of things
- re-enable hidpi setting

* Tue Aug 16 2016 Tom Callaway <spot@fedoraproject.org> 52.0.2743.116-9
- filter out Requires/Provides for chromium-only libs and plugins

* Tue Aug 16 2016 Tom Callaway <spot@fedoraproject.org> 52.0.2743.116-8
- fix path on Requires(post) line for semanage

* Mon Aug 15 2016 Tom Callaway <spot@fedoraproject.org> 52.0.2743.116-7
- add Requires(post) items for selinux scriptlets

* Mon Aug 15 2016 Tom Callaway <spot@fedoraproject.org> 52.0.2743.116-6
- disable the "hidpi" setting
- unset MADV_FREE if set (should get F25+ working again)

* Fri Aug 12 2016 Tom Callaway <spot@fedoraproject.org> 52.0.2743.116-5
- do not package libwidevinecdm*.so, they are just empty shells
  instead, to enable widevine, get these files from Google Chrome

* Fri Aug 12 2016 Tom Callaway <spot@fedoraproject.org> 52.0.2743.116-4
- add "freeworld" conditional for testing netflix/widevine

* Fri Aug 12 2016 Tom Callaway <spot@fedoraproject.org> 52.0.2743.116-3
- move PepperFlash directory out of the nacl conditional (thanks to churchyard)
- fix widevine (thanks to David Vásquez and UnitedRPMS)

* Wed Aug 10 2016 Tom Callaway <spot@fedoraproject.org> 52.0.2743.116-2
- include clearkeycdm and widevinecdm files in libs-media

* Mon Aug  8 2016 Tom Callaway <spot@fedoraproject.org> 52.0.2743.116-1
- update to 52.0.2743.116

* Thu Aug  4 2016 Tom Callaway <spot@fedoraproject.org> 52.0.2743.82-13
- change libs split to "libs-media", as that actually works.
- add PepperFlash directory (nothing in it though, sorry)

* Wed Aug  3 2016 Tom Callaway <spot@fedoraproject.org> 52.0.2743.82-12
- split out libs package beyond ffmpeg, into libs and libs-content
- fix libusbx conditional for el7 to not nuke libusb headers
- disable speech-dispatcher header prefix setting if not fedora (el7)

* Wed Aug  3 2016 Tom Callaway <spot@fedoraproject.org> 52.0.2743.82-11
- split out chromium-libs-ffmpeg so it can be easily replaced
- conditionalize opus and libusbx for el7

* Wed Aug  3 2016 Tom Callaway <spot@fedoraproject.org> 52.0.2743.82-10
- Add ICU Text Codec aliases (from openSUSE via Russian Fedora)
- Use PIE in the Linux sandbox (from openSUSE via Russian Fedora)
- Enable ARM CPU detection for webrtc (from archlinux via Russian Fedora)
- Do not force -m32 in icu compile on ARM (from archlinux via Russian Fedora)
- Enable gtk3 support (via conditional)
- Enable fpic on linux
- Enable hidpi
- Force aura on
- Enable touch_ui
- Add chromedriver subpackage (from Russian Fedora)
- Set default master_preferences location to /etc/chromium
- Add master_preferences file as config file
- Improve chromium-browser.desktop (from Russian Fedora)

* Thu Jul 28 2016 Tom Callaway <spot@fedoraproject.org> 52.0.2743.82-9
- fix conditional to disable verbose logging output unless beta/dev

* Thu Jul 28 2016 Tom Callaway <spot@fedoraproject.org> 52.0.2743.82-8
- disable nacl/pnacl for Fedora 23 (and older)

* Thu Jul 28 2016 Tom Callaway <spot@fedoraproject.org> 52.0.2743.82-7
- fix post scriptlet so that selinux stuff only happens when selinux is enabled

* Thu Jul 28 2016 Richard Hughes <richard@hughsie.com> 52.0.2743.82-6
- Add an AppData file so that Chromium appears in the software center

* Wed Jul 27 2016 Tom Callaway <spot@fedoraproject.org> 52.0.2743.82-5
- enable nacl/pnacl (chromium-native_client has landed in Fedora)
- fix chromium-browser.sh to report Fedora build target properly

* Wed Jul 27 2016 Tom Callaway <spot@fedoraproject.org> 52.0.2743.82-4
- compile with -fno-delete-null-pointer-checks (fixes v8 crashes, nacl/pnacl)
- turn nacl/pnacl off until chromium-native_client lands in Fedora

* Tue Jul 26 2016 Tom Callaway <spot@fedoraproject.org> 52.0.2743.82-3
- turn nacl back on for x86_64

* Thu Jul 21 2016 Tom Callaway <spot@fedoraproject.org> 52.0.2743.82-2
- fix cups 2.2 support
- try to enable widevine compatibility (you still need to get the binary .so files from chrome)

* Thu Jul 21 2016 Tom Callaway <spot@fedoraproject.org> 52.0.2743.82-1
- update to 52.0.2743.82
- handle locales properly
- cleanup spec

* Tue Jul 19 2016 Tom Callaway <spot@fedoraproject.org> 52.0.2743.75-1
- update to 52.0.2743.75

* Wed Jul 6 2016 Tom Callaway <spot@fedoraproject.org> 52.0.2743.60-1
- bump to 52.0.2743.60, disable nacl for now

* Mon May 9 2016 Tom Callaway <spot@fedoraproject.org> 52.0.2723.2-1
- force to dev to see if it works better on F24+

* Wed May 4 2016 Tom Callaway <spot@fedoraproject.org> 50.0.2661.94-6
- apply upstream fix for https://bugs.chromium.org/p/chromium/issues/detail?id=604534

* Tue May 3 2016 Tom Callaway <spot@fedoraproject.org> 50.0.2661.94-5
- use bundled re2 (conditionalize it)

* Tue May 3 2016 Tom Callaway <spot@fedoraproject.org> 50.0.2661.94-4
- disable asan (it never quite built)
- do not preserve re2 bundled tree, causes header/library mismatch

* Mon May 2 2016 Tom Callaway <spot@fedoraproject.org> 50.0.2661.94-3
- enable AddressSanize (ASan) for debugging

* Sat Apr 30 2016 Tom Callaway <spot@fedoraproject.org> 50.0.2661.94-2
- use bundled icu always. *sigh*

* Fri Apr 29 2016 Tom Callaway <spot@fedoraproject.org> 50.0.2661.94-1
- update to 50.0.2661.94

* Wed Apr 27 2016 Tom Callaway <spot@fedoraproject.org> 50.0.2661.86-1
- update to 50.0.2661.86

* Thu Mar 17 2016 Tom Callaway <spot@fedoraproject.org> 49.0.2623.87-4
- protect third_party/woff2

* Thu Mar 17 2016 Tom Callaway <spot@fedoraproject.org> 49.0.2623.87-3
- add BuildRequires: libffi-devel

* Thu Mar 17 2016 Tom Callaway <spot@fedoraproject.org> 49.0.2623.87-2
- explicitly disable sysroot

* Thu Mar 17 2016 Tom Callaway <spot@fedoraproject.org> 49.0.2623.87-1
- update to 49.0.2623.87

* Mon Feb 29 2016 Tom Callaway <spot@fedoraproject.org> 48.0.2564.116-3
- Happy Leap Day!
- add Requires: u2f-hidraw-policy for u2f token support
- add Requires: xorg-x11-server-Xvfb for chrome-remote-desktop

* Fri Feb 26 2016 Tom Callaway <spot@fedoraproject.org> 48.0.2564.116-2
- fix icu BR

* Wed Feb 24 2016 Tom Callaway <spot@fedoraproject.org> 48.0.2564.116-1
- Update to 48.0.2564.116
- conditionalize icu properly
- fix libusbx handling (bz1270324)

* Wed Feb 17 2016 Tom Callaway <spot@fedoraproject.org> 48.0.2564.103-2
- fixes for gcc6

* Mon Feb  8 2016 Tom Callaway <spot@fedoraproject.org> 48.0.2564.103-1
- update to 48.0.2564.103
- use bundled libsrtp (because upstream has coded themselves into an ugly corner)

* Fri Jan 22 2016 Tom Callaway <spot@fedoraproject.org> 48.0.2564.82-1
- update to 48.0.2564.82

* Fri Jan 15 2016 Tom Callaway <spot@fedoraproject.org> 47.0.2526.111-1
- update to 47.0.2526.111

* Thu Jan 07 2016 Tomas Popela <tpopela@redhat.com> 47.0.2526.106-2
- compare hashes when downloading the tarballs
- Google started to include the Debian sysroots in tarballs - remove them while
  processing the tarball
- add a way to not use the system display server for tests instead of Xvfb
- update the depot_tools checkout to get some GN fixes
- use the remove_bundled_libraries script
- update the clean_ffmpeg script to print errors when some files that we are
  processing are missing
- update the clean_ffmpeg script to operate on tarball's toplevel folder
- don't show comments as removed tests in get_linux_tests_names script
- rework the process_ffmpeg_gyp script (also rename it to
  get_free_ffmpeg_source_files) to use the GN files insted of GYP (but we still
  didn't switched to GN build)

* Wed Dec 16 2015 Tom Callaway <spot@fedoraproject.org> 47.0.2526.106-1
- update to 47.0.2526.106

* Tue Dec 15 2015 Tom Callaway <spot@fedoraproject.org> 47.0.2526.80-4
- entirely patch out the broken fd counter from the nacl loader code
  killing it with fire would be better, but then chromium is on fire
  and that somehow makes it worse.

* Mon Dec 14 2015 Tom Callaway <spot@fedoraproject.org> 47.0.2526.80-3
- revert nacl fd patch (now we see 6 fds! 6 LIGHTS!)

* Fri Dec 11 2015 Tom Callaway <spot@fedoraproject.org> 47.0.2526.80-2
- build everything shared, but when we do shared builds, make -libs subpackage
- make chrome-remote-desktop dep on -libs subpackage in shared builds

* Wed Dec  9 2015 Tom Callaway <spot@fedoraproject.org> 47.0.2526.80-1
- update to 47.0.2526.80
- only build ffmpeg shared, not any other libs
  this is because if we build the other libs shared, then our
  chrome-remote-desktop build deps on those libs and we do not want that

* Tue Dec  8 2015 Tom Callaway <spot@fedoraproject.org> 47.0.2526.73-2
- The nacl loader claims it sees 7 fds open ALL THE TIME, and fails
  So, we tell it that it is supposed to see 7.
  I suspect building with shared objects is causing this disconnect.

* Wed Dec  2 2015 Tom Callaway <spot@fedoraproject.org> 47.0.2526.73-1
- update to 47.0.2526.73
- rework chrome-remote-desktop subpackage to work for google-chrome and chromium

* Wed Dec  2 2015 Tomas Popela <tpopela@redhat.com> 47.0.2526.69-1
- Update to 47.0.2526.69

* Tue Dec  1 2015 Tom Callaway <spot@fedoraproject.org> 46.0.2490.86-4
- still more remote desktop changes

* Mon Nov 30 2015 Tom Callaway <spot@fedoraproject.org> 46.0.2490.86-3
- lots of remote desktop cleanups

* Thu Nov 12 2015 Tom Callaway <spot@fedoraproject.org> 46.0.2490.86-2
- re-enable Requires/BuildRequires for libusbx
- add remote-desktop subpackage

* Wed Nov 11 2015 Tomas Popela <tpopela@redhat.com> 46.0.2490.86-1
- update to 46.0.2490.86
- clean the SPEC file
- add support for policies: https://www.chromium.org/administrators/linux-quick-start
- replace exec_mem_t SELinux label with bin_t - see rhbz#1281437
- refresh scripts that are used for processing the original tarball

* Fri Oct 30 2015 Tom Callaway <spot@fedoraproject.org> 46.0.2490.80-5
- tls_edit is a nacl thing. who knew?

* Thu Oct 29 2015 Tom Callaway <spot@fedoraproject.org> 46.0.2490.80-4
- more nacl fixups for i686 case

* Thu Oct 29 2015 Tom Callaway <spot@fedoraproject.org> 46.0.2490.80-3
- conditionalize nacl/nonacl, disable nacl on i686, build for i686

* Mon Oct 26 2015 Tom Callaway <spot@fedoraproject.org> 46.0.2490.80-2
- conditionalize shared bits (enable by default)

* Fri Oct 23 2015 Tom Callaway <spot@fedoraproject.org> 46.0.2490.80-1
- update to 46.0.2490.80

* Thu Oct 15 2015 Tom Callaway <spot@fedoraproject.org> 46.0.2490.71-1
- update to 46.0.2490.71

* Thu Oct 15 2015 Tom Callaway <spot@fedoraproject.org> 45.0.2454.101-2
- fix icu handling for f21 and older

* Mon Oct  5 2015 Tom Callaway <spot@fedoraproject.org> 45.0.2454.101-1
- update to 45.0.2454.101

* Thu Jun 11 2015 Tom Callaway <spot@fedoraproject.org> 43.0.2357.124-1
- update to 43.0.2357.124

* Tue Jun  2 2015 Tom Callaway <spot@fedoraproject.org> 43.0.2357.81-1
- update to 43.0.2357.81

* Thu Feb 26 2015 Tom Callaway <spot@fedoraproject.org> 40.0.2214.115-1
- update to 40.0.2214.115

* Thu Feb 19 2015 Tom Callaway <spot@fedoraproject.org> 40.0.2214.111-1
- update to 40.0.2214.111

* Mon Feb  2 2015 Tom Callaway <spot@fedoraproject.org> 40.0.2214.94-1
- update to 40.0.2214.94

* Tue Jan 27 2015 Tom Callaway <spot@fedoraproject.org> 40.0.2214.93-1
- update to 40.0.2214.93

* Sat Jan 24 2015 Tom Callaway <spot@fedoraproject.org> 40.0.2214.91-1
- update to 40.0.2214.91

* Wed Jan 21 2015 Tom Callaway <spot@fedoraproject.org> 39.0.2171.95-3
- use bundled icu on Fedora < 21, we need 5.2

* Tue Jan  6 2015 Tom Callaway <spot@fedoraproject.org> 39.0.2171.95-2
- rebase off Tomas's spec file for Fedora

* Fri Dec 12 2014 Tomas Popela <tpopela@redhat.com> 39.0.2171.95-1
- Update to 39.0.2171.95
- Resolves: rhbz#1173448

* Wed Nov 26 2014 Tomas Popela <tpopela@redhat.com> 39.0.2171.71-1
- Update to 39.0.2171.71
- Resolves: rhbz#1168128

* Wed Nov 19 2014 Tomas Popela <tpopela@redhat.com> 39.0.2171.65-2
- Revert the chrome-sandbox rename to chrome_sandbox
- Resolves: rhbz#1165653

* Wed Nov 19 2014 Tomas Popela <tpopela@redhat.com> 39.0.2171.65-1
- Update to 39.0.2171.65
- Use Red Hat Developer Toolset for compilation
- Set additional SELinux labels
- Add more unit tests
- Resolves: rhbz#1165653

* Fri Nov 14 2014 Tomas Popela <tpopela@redhat.com> 38.0.2125.122-1
- Update to 38.0.2125.122
- Resolves: rhbz#1164116

* Wed Oct 29 2014 Tomas Popela <tpopela@redhat.com> 38.0.2125.111-1
- Update to 38.0.2125.111
- Resolves: rhbz#1158347

* Fri Oct 24 2014 Tomas Popela <tpopela@redhat.com> 38.0.2125.104-2
- Fix the situation when the return key (and keys from numpad) does not work
  in HTML elements with input
- Resolves: rhbz#1153988
- Dynamically determine the presence of the PepperFlash plugin
- Resolves: rhbz#1154118

* Thu Oct 16 2014 Tomas Popela <tpopela@redhat.com> 38.0.2125.104-1
- Update to 38.0.2125.104
- Resolves: rhbz#1153012

* Thu Oct 09 2014 Tomas Popela <tpopela@redhat.com> 38.0.2125.101-2
- The boringssl is used for tests, without the possibility of using
  the system openssl instead. Remove the openssl and boringssl sources
  when not building the tests.
- Resolves: rhbz#1004948

* Wed Oct 08 2014 Tomas Popela <tpopela@redhat.com> 38.0.2125.101-1
- Update to 38.0.2125.101
- System openssl is used for tests, otherwise the bundled boringssl is used
- Don't build with clang
- Resolves: rhbz#1004948

* Wed Sep 10 2014 Tomas Popela <tpopela@redhat.com> 37.0.2062.120-1
- Update to 37.0.2062.120
- Resolves: rhbz#1004948

* Wed Aug 27 2014 Tomas Popela <tpopela@redhat.com> 37.0.2062.94-1
- Update to 37.0.2062.94
- Include the pdf viewer library

* Wed Aug 13 2014 Tomas Popela <tpopela@redhat.com> 36.0.1985.143-1
- Update to 36.0.1985.143
- Use system openssl instead of bundled one
- Resolves: rhbz#1004948

* Thu Jul 17 2014 Tomas Popela <tpopela@redhat.com> 36.0.1985.125-1
- Update to 36.0.1985.125
- Add libexif as BR
- Resolves: rhbz#1004948

* Wed Jun 11 2014 Tomas Popela <tpopela@redhat.com> 35.0.1916.153-1
- Update to 35.0.1916.153
- Resolves: rhbz#1004948

* Wed May 21 2014 Tomas Popela <tpopela@redhat.com> 35.0.1916.114-1
- Update to 35.0.1916.114
- Bundle python-argparse
- Resolves: rhbz#1004948

* Wed May 14 2014 Tomas Popela <tpopela@redhat.com> 34.0.1847.137-1
- Update to 34.0.1847.137
- Resolves: rhbz#1004948

* Mon May 5 2014 Tomas Popela <tpopela@redhat.com> 34.0.1847.132-1
- Update to 34.0.1847.132
- Bundle depot_tools and switch from make to ninja
- Remove PepperFlash
- Resolves: rhbz#1004948

* Mon Feb 3 2014 Tomas Popela <tpopela@redhat.com> 32.0.1700.102-1
- Update to 32.0.1700.102

* Thu Jan 16 2014 Tomas Popela <tpopela@redhat.com> 32.0.1700.77-1
- Update to 32.0.1700.77
- Properly kill Xvfb when tests fails
- Add libdrm as BR
- Add libcap as BR

* Tue Jan 7 2014 Tomas Popela <tpopela@redhat.com> 31.0.1650.67-2
- Minor changes in spec files and scripts
- Add Xvfb as BR for tests
- Add policycoreutils-python as Requires
- Compile unittests and run them in chech phase, but turn them off by default
  as many of them are failing in Brew

* Thu Dec 5 2013 Tomas Popela <tpopela@redhat.com> 31.0.1650.67-1
- Update to 31.0.1650.63

* Thu Nov 21 2013 Tomas Popela <tpopela@redhat.com> 31.0.1650.57-1
- Update to 31.0.1650.57

* Wed Nov 13 2013 Tomas Popela <tpopela@redhat.com> 31.0.1650.48-1
- Update to 31.0.1650.48
- Minimal supported RHEL6 version is now RHEL 6.5 due to GTK+

* Fri Oct 25 2013 Tomas Popela <tpopela@redhat.com> 30.0.1599.114-1
- Update to 30.0.1599.114
- Hide the infobar with warning that this version of OS is not supported
- Polished the chromium-latest.py

* Thu Oct 17 2013 Tomas Popela <tpopela@redhat.com> 30.0.1599.101-1
- Update to 30.0.1599.101
- Minor changes in scripts

* Wed Oct 2 2013 Tomas Popela <tpopela@redhat.com> 30.0.1599.66-1
- Update to 30.0.1599.66
- Automated the script for cleaning the proprietary sources from ffmpeg.

* Thu Sep 19 2013 Tomas Popela <tpopela@redhat.com> 29.0.1547.76-1
- Update to 29.0.1547.76
- Added script for removing the proprietary sources from ffmpeg. This script is called during cleaning phase of ./chromium-latest --rhel

* Mon Sep 16 2013 Tomas Popela <tpopela@redhat.com> 29.0.1547.65-2
- Compile with Dproprietary_codecs=0 and Dffmpeg_branding=Chromium to disable proprietary codecs (i.e. MP3)

* Mon Sep 9 2013 Tomas Popela <tpopela@redhat.com> 29.0.1547.65-1
- Initial version based on Tom Callaway's <spot@fedoraproject.org> work
