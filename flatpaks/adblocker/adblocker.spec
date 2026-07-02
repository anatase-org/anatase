%global ublock_commit 94dea5fc98c8f8f2c3179b179f3f6e37af0b1ca2
%global codemirror_commit 30e88029af97777fc21a8b92044c2634612bddc9
%global serializer_commit 1f028eb315c14bb11f23f0ef6c4bf6c339d3b0b1
%global extension_id lffaaenmikbaifpipgfdhhpgpneakaea

Name:           anatase-browser-adblocker
Version:        2026.628.2035
Release:        1%{?dist}
Summary:        Anatase Browser adblocker extension
License:        GPL-3.0-or-later
URL:            https://github.com/uBlockOrigin/uBOL-home
Source0:        %{url}/archive/refs/tags/%{version}/uBOL-home-%{version}.tar.gz
Source1:        https://github.com/gorhill/uBlock/archive/%{ublock_commit}/uBlock-%{ublock_commit}.tar.gz
Source2:        https://github.com/gorhill/codemirror-ubol/archive/%{codemirror_commit}/codemirror-ubol-%{codemirror_commit}.tar.gz
Source3:        https://github.com/gorhill/s14e-serializer/archive/%{serializer_commit}/s14e-serializer-%{serializer_commit}.tar.gz
Source4:        adblocker.pem

BuildArch:      noarch
BuildRequires:  bash
BuildRequires:  chromium
BuildRequires:  coreutils
BuildRequires:  jq
BuildRequires:  nodejs
BuildRequires:  openssl
BuildRequires:  tar
BuildRequires:  zip

%description
Anatase Browser adblocker extension, built from uBO Lite source.

%prep
%autosetup -n uBOL-home-%{version}

rm -rf uBlock
mkdir -p uBlock
tar -xzf %{SOURCE1} --strip-components=1 -C uBlock

rm -rf uBlock/platform/mv3/extension/lib/codemirror/codemirror-ubol
mkdir -p uBlock/platform/mv3/extension/lib/codemirror/codemirror-ubol
tar -xzf %{SOURCE2} --strip-components=1 -C uBlock/platform/mv3/extension/lib/codemirror/codemirror-ubol

rm -rf uBlock/platform/mv3/extension/lib/s14e-serializer
mkdir -p uBlock/platform/mv3/extension/lib/s14e-serializer
tar -xzf %{SOURCE3} --strip-components=1 -C uBlock/platform/mv3/extension/lib/s14e-serializer

%build
cd uBlock
bash tools/make-mv3.sh chromium %{version}

%install
key_file="$PWD/adblocker.pem"
install -m0644 %{SOURCE4} "$key_file"

chromium-browser \
    --no-sandbox \
    --disable-gpu \
    --user-data-dir="$PWD/chromium-pack-profile" \
    --pack-extension="$PWD/uBlock/dist/build/uBOLite.chromium" \
    --pack-extension-key="$key_file"

install -Dm0644 \
    "$PWD/uBlock/dist/build/uBOLite.chromium.crx" \
    "%{buildroot}/app/extensions/%{extension_id}/uBOLite.crx"

install -dm0755 "%{buildroot}/app/extensions"
cat > "%{buildroot}/app/extensions/%{extension_id}.json" <<EOF
{
  "external_crx": "/app/chromium/extensions/extensions/%{extension_id}/uBOLite.crx",
  "external_version": "%{version}"
}
EOF

%files
%license uBlock/LICENSE.txt
/app/extensions
