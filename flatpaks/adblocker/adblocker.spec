%global extension_id lffaaenmikbaifpipgfdhhpgpneakaea
%global appstream_id org.anatase.Browser.Adblocker

Name:           anatase-browser-adblocker
Version:        xxxxxx
Release:        1%{?dist}
Summary:        Anatase Browser adblocker extension
License:        GPL-3.0-or-later
URL:            https://github.com/gorhill/uBlock
Source0:        uBlock-source.tar.gz
Source1:        rulesets-%{version}.tar.gz
Source2:        adblocker.pem
Source3:        adblocker.svg
Source4:        adblocker_off.svg
Source5:        %{appstream_id}.metainfo.xml
Patch0:         overrides.patch

# This is the private key used to sign the extension.
#
# A consideration was made about whether this should be private or public.
# The private key controls the extension ID chrome uses to identify it.
# It is also used to verify provenance during updates via the normal chromium
# update path. IE, this key is required and can be used to silently update
# the extension using the normal chromium updater.
#
# If this extension was distributed normally, it would have an update url
# attached to %{extension_id}.json (or the inner manifest) and every few
# hours chromium would check it for updates. If there was one, the key
# would be used to verify the update was valid.
#
# However, it is not distributed normally. This extension is provided by
# the anatase flatpak remote and merged into the flatpak itself under a
# special folder. Chromium silently installs any extensions in that folder
# during launch with permissions (however, if the key changed we would not
# be able to update the same extension; we would be able to force uninstall
# and replace it). Without an update url, chrome will never attempt to
# update it outside the flatpak channel.
#
# Therefore, an attacker with this key could create a malicious extension,
# but they could not "force update" this extension without compromising
# either the flatpak remote or the system. In the case they had this access,
# they could also just use a different extension ID to install their
# malicious extension, which would be much easier, or do other nefarious
# things with this access.
#
# Therefore, from a security perspective, this key being public is not a concern.
#
# Trying to keep it private, however, would be a huge pain. Chrome does not
# support signing via smartcards. It expects the pem private key directly.
# It is possible to sign via a third party compressor that is modified to
# call out to a key service. However, in this case Ludos would need to be
# extended to have a signing engine for internal packages, and this
# extension would only build in CI. So if you wanted to build an anatase
# image locally, it would break, or install duplicate adblockers. 
BuildArch:      noarch
BuildRequires:  bash
BuildRequires:  chromium
BuildRequires:  coreutils
BuildRequires:  jq
BuildRequires:  libappstream-glib
BuildRequires:  librsvg2-tools
BuildRequires:  nodejs
BuildRequires:  openssl
BuildRequires:  tar
BuildRequires:  zip

%description
Anatase Browser adblocker extension, built from uBO Lite source.

%prep
%autosetup -N -n uBlock-source

if [ -s "%{PATCH0}" ]; then
    %autopatch -p1
fi

tar -xzf %{SOURCE1}

%build

#
# Preprocess block
# It's from tools/make-mv3.sh, but we do not vendor that repo
# (it is just build scripts and deploy cruft, so we need to sync manually)

platform="chromium"
manifest_dir="chromium"
ubol_dir="$PWD/dist/build/AnataseAdblocker.$platform"

rm -rf "$ubol_dir"
mkdir -p "$ubol_dir"
ubol_dir="$(cd "$ubol_dir" && pwd)"

mkdir -p "$ubol_dir"/css/fonts
mkdir -p "$ubol_dir"/js/offscreen
mkdir -p "$ubol_dir"/img
mkdir -p "$ubol_dir"/lib

cp -R src/css/fonts/Inter "$ubol_dir"/css/fonts/
cp src/css/themes/default.css "$ubol_dir"/css/
cp src/css/common.css "$ubol_dir"/css/
cp src/css/dashboard-common.css "$ubol_dir"/css/
cp src/css/fa-icons.css "$ubol_dir"/css/

cp src/js/arglist-parser.js "$ubol_dir"/js/
cp src/js/dom.js "$ubol_dir"/js/
cp src/js/fa-icons.js "$ubol_dir"/js/
cp src/js/i18n.js "$ubol_dir"/js/
cp src/js/jsonpath.js "$ubol_dir"/js/
cp src/js/redirect-resources.js "$ubol_dir"/js/
cp src/js/regex-analyzer.js "$ubol_dir"/js/offscreen/
cp -R src/js/resources "$ubol_dir"/js/
cp src/js/static-filtering-parser.js "$ubol_dir"/js/
cp src/js/urlskip.js "$ubol_dir"/js/
cp src/lib/punycode.js "$ubol_dir"/js/
cp -R src/lib/regexanalyzer "$ubol_dir"/lib/
cp -R src/img/flags-of-the-world "$ubol_dir"/img
cp LICENSE.txt "$ubol_dir"/

cp platform/mv3/"$manifest_dir"/manifest.json "$ubol_dir"/
cp platform/mv3/extension/*.html "$ubol_dir"/
cp platform/mv3/extension/*.json "$ubol_dir"/
cp platform/mv3/extension/css/* "$ubol_dir"/css/
cp -R platform/mv3/extension/js/* "$ubol_dir"/js/
cp platform/mv3/"$platform"/ext-compat.js "$ubol_dir"/js/ 2>/dev/null || :
cp platform/mv3/"$platform"/ext-offscreen.js "$ubol_dir"/js/ 2>/dev/null || :
cp platform/mv3/"$platform"/css-api.js "$ubol_dir"/js/scripting/ 2>/dev/null || :
cp platform/mv3/"$platform"/css-user.js "$ubol_dir"/js/scripting/ 2>/dev/null || :
cp platform/mv3/extension/img/* "$ubol_dir"/img/
cp platform/mv3/"$platform"/img/* "$ubol_dir"/img/ 2>/dev/null || :
install -m0644 %{SOURCE3} "$ubol_dir/img/ublock.svg"
for size in 16 32 64 128 512; do
    rsvg-convert \
        -w "$size" \
        -h "$size" \
        -o "$ubol_dir/img/icon_${size}.png" \
        %{SOURCE3}
    rsvg-convert \
        -w "$size" \
        -h "$size" \
        -o "$ubol_dir/img/icon_${size}_off.png" \
        %{SOURCE4}
done
cp -R platform/mv3/extension/_locales "$ubol_dir"/
cp platform/mv3/README.md "$ubol_dir"/

mkdir -p "$ubol_dir"/lib/codemirror
cp platform/mv3/extension/lib/codemirror/* \
    "$ubol_dir"/lib/codemirror/ 2>/dev/null || :
cp platform/mv3/extension/lib/codemirror/codemirror-ubol/dist/cm6.bundle.ubol.min.js \
    "$ubol_dir"/lib/codemirror/
cp platform/mv3/extension/lib/codemirror/codemirror.LICENSE \
    "$ubol_dir"/lib/codemirror/
cp platform/mv3/extension/lib/codemirror/codemirror-ubol/LICENSE \
    "$ubol_dir"/lib/codemirror/codemirror-quickstart.LICENSE
mkdir -p "$ubol_dir"/lib/csstree
cp src/lib/csstree/* "$ubol_dir"/lib/csstree/
cp platform/mv3/extension/lib/s14e-serializer/s14e-serializer.js \
    "$ubol_dir"/lib/

ruleset_cache="$PWD/dist/build/mv3-data"
rm -rf "$ruleset_cache"
mkdir -p "$ruleset_cache"
cp rulesets/* "$ruleset_cache"/

ubol_build_dir="$PWD/dist/build/mv3-nodejs"
rm -rf "$ubol_build_dir"
mkdir -p "$ubol_build_dir"
./tools/make-nodejs.sh "$ubol_build_dir"
cp platform/mv3/*.json "$ubol_build_dir"/
cp platform/mv3/*.js "$ubol_build_dir"/
cp platform/mv3/*.mjs "$ubol_build_dir"/
cp platform/mv3/extension/js/utils.js "$ubol_build_dir"/js/
cp -R src/lib/regexanalyzer "$ubol_build_dir"/js/
cp -R src/js/resources "$ubol_build_dir"/js/
cp -R platform/mv3/scriptlets "$ubol_build_dir"/
cp -R platform/mv3/extension/js/offscreen "$ubol_build_dir"/js/
cp src/js/regex-analyzer.js "$ubol_build_dir"/js/offscreen/
mkdir -p "$ubol_build_dir"/web_accessible_resources
cp src/web_accessible_resources/* "$ubol_build_dir"/web_accessible_resources/
cp -R platform/mv3/"$platform" "$ubol_build_dir"/

(
    cd "$ubol_build_dir"
    node --no-warnings make-rulesets.js output="$ubol_dir" platform="$platform"
)
rm -rf "$ubol_build_dir"

rm -rf "$ubol_dir/rulesets/debug"

%install
key_file="$PWD/adblocker.pem"
install -m0644 %{SOURCE2} "$key_file"

chromium-browser \
    --no-sandbox \
    --disable-gpu \
    --user-data-dir="$PWD/chromium-pack-profile" \
    --pack-extension="$PWD/dist/build/AnataseAdblocker.chromium" \
    --pack-extension-key="$key_file"

install -Dm0644 \
    "$PWD/dist/build/AnataseAdblocker.chromium.crx" \
    "%{buildroot}/app/extensions/%{extension_id}/AnataseAdblocker.crx"

install -dm0755 "%{buildroot}/app/extensions"
extension_version="$(jq -r .version "$PWD/dist/build/AnataseAdblocker.chromium/manifest.json")"
cat > "%{buildroot}/app/extensions/%{extension_id}.json" <<EOF
{
  "external_crx": "/app/chromium/extensions/extensions/%{extension_id}/AnataseAdblocker.crx",
  "external_version": "$extension_version"
}
EOF

install -dm0755 "%{buildroot}/app/policies/managed"
cat > "%{buildroot}/app/policies/managed/anatase-adblocker.json" <<EOF
{
  "ExtensionSettings": {
    "%{extension_id}": {
      "toolbar_pin": "default_pinned"
    }
  }
}
EOF

install -dm0755 "%{buildroot}%{_metainfodir}"
sed "s/@VERSION@/%{version}/g" "%{SOURCE5}" \
    > "%{buildroot}%{_metainfodir}/%{appstream_id}.metainfo.xml"

for size in 64 128; do
    install -dm0755 "%{buildroot}%{_datadir}/icons/hicolor/${size}x${size}/apps"
    rsvg-convert \
        -w "$size" \
        -h "$size" \
        -o "%{buildroot}%{_datadir}/icons/hicolor/${size}x${size}/apps/%{appstream_id}.png" \
        %{SOURCE3}
done

%check
appstream-util validate-relax --nonet \
    "%{buildroot}%{_metainfodir}/%{appstream_id}.metainfo.xml"

%files
%license LICENSE.txt
/app/extensions
/app/policies
%{_datadir}/icons/hicolor/*/apps/org.anatase.Browser.Adblocker.png
%{_metainfodir}/org.anatase.Browser.Adblocker.metainfo.xml
