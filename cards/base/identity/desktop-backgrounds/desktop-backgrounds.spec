%global wallpaper_id Anatase
%global render_resolution 3840x2160
%global resolutions 1024x600 1024x768 1080x1920 1152x720 1152x864 1200x900 1280x1024 1280x720 1280x768 1280x800 1280x960 1366x768 1440x1080 1440x2960 1440x900 1600x1200 1600x1280 1680x1050 1920x1080 1920x1200 1920x1280 1920x1440 2048x1536 2160x1440 2304x1440 2560x1440 2560x1600 2960x1440 3000x2000 3200x1800 3440x1440 3840x2160 5120x2880 640x480 800x480 800x600

Name:           desktop-backgrounds
Version:        44.0.0
Release:        %autorelease
Summary:        Anatase desktop backgrounds

License:        LicenseRef-Anatase-Logos
Source0:        palette-day
Source1:        palette-night
Source10:       anatase-formation.svg
Source11:       anatase-crystal.svg
Source12:       anatase-strata.svg

BuildArch:      noarch
BuildRequires:  libjxl-utils
BuildRequires:  librsvg2-tools
BuildRequires:  libxml2

%description
The desktop-backgrounds package contains artwork intended to be used as
desktop background images.


%package        gnome
Summary:        The default Anatase wallpaper for GNOME
Requires:       %{name} = %{version}-%{release}
Requires:       gsettings-desktop-schemas >= 2.91.92
Provides:       system-backgrounds-gnome = %{version}-%{release}

%description    gnome
The desktop-backgrounds-gnome package sets the default background in GNOME.


%package        kde
Summary:        The default Anatase wallpaper for KDE Plasma
Requires:       %{name} = %{version}-%{release}
Provides:       system-backgrounds-kde = %{version}-%{release}

%description    kde
The desktop-backgrounds-kde package sets the default background in KDE Plasma.


%prep


%build
set -eu

generated=%{_builddir}/%{name}-generated
rm -rf "${generated}"
mkdir -p "${generated}"/svg "${generated}"/png "${generated}"/jxl

apply_palette() {
  palette=$1
  source_svg=$2
  output_svg=$3

  cp -p "${source_svg}" "${output_svg}"
  while IFS='=' read -r key value; do
    case "${key}" in
      ""|\#*) continue ;;
    esac
    sed -i "s|@${key}@|${value}|g" "${output_svg}"
  done < "${palette}"

  if grep -Eq '@[A-Z0-9_]+@' "${output_svg}"; then
    echo "Unresolved palette token in ${output_svg}" >&2
    grep -nE '@[A-Z0-9_]+@' "${output_svg}" >&2
    exit 1
  fi
  xmllint --noout "${output_svg}"
}

render_jxl() {
  source_svg=$1
  output_jxl=$2
  resolution=$3
  width=${resolution%x*}
  height=${resolution#*x}
  output_png="${generated}/png/$(basename "${output_jxl}" .jxl).png"

  mkdir -p "$(dirname "${output_jxl}")"
  rsvg-convert -w "${width}" -h "${height}" -o "${output_png}" "${source_svg}"
  cjxl "${output_png}" "${output_jxl}" --quality=90 --effort=7 --quiet
  rm -f "${output_png}"
}

render_design() {
  name=$1
  source_svg=$2

  day_svg="${generated}/svg/${name}-day.svg"
  night_svg="${generated}/svg/${name}-night.svg"

  apply_palette %{SOURCE0} "${source_svg}" "${day_svg}"
  apply_palette %{SOURCE1} "${source_svg}" "${night_svg}"

  render_jxl "${day_svg}" "${generated}/jxl/${name}/day/%{render_resolution}.jxl" "%{render_resolution}"
  render_jxl "${night_svg}" "${generated}/jxl/${name}/night/%{render_resolution}.jxl" "%{render_resolution}"
}

render_design formation %{SOURCE10}
render_design crystal %{SOURCE11}
render_design strata %{SOURCE12}


%install
set -eu

generated=%{_builddir}/%{name}-generated
background_dir=%{buildroot}%{_datadir}/backgrounds/anatase/default
wallpaper_root=%{buildroot}%{_datadir}/wallpapers

mkdir -p "${background_dir}"
install -m 0644 -p "${generated}/jxl/formation/day/%{render_resolution}.jxl" \
  "${background_dir}/anatase-01-day.jxl"
install -m 0644 -p "${generated}/jxl/formation/night/%{render_resolution}.jxl" \
  "${background_dir}/anatase-01-night.jxl"
cat > "${background_dir}/anatase.xml" <<'EOF'
<background>
  <starttime>
    <year>2026</year>
    <month>04</month>
    <day>14</day>
    <hour>8</hour>
    <minute>00</minute>
    <second>00</second>
  </starttime>
  <static>
    <duration>36000.0</duration>
    <file>/usr/share/backgrounds/anatase/default/anatase-01-day.jxl</file>
  </static>
  <transition type="overlay">
    <duration>7200.0</duration>
    <from>/usr/share/backgrounds/anatase/default/anatase-01-day.jxl</from>
    <to>/usr/share/backgrounds/anatase/default/anatase-01-night.jxl</to>
  </transition>
  <static>
    <duration>36000.0</duration>
    <file>/usr/share/backgrounds/anatase/default/anatase-01-night.jxl</file>
  </static>
  <transition type="overlay">
    <duration>7200.0</duration>
    <from>/usr/share/backgrounds/anatase/default/anatase-01-night.jxl</from>
    <to>/usr/share/backgrounds/anatase/default/anatase-01-day.jxl</to>
  </transition>
</background>
EOF

mkdir -p %{buildroot}%{_datadir}/backgrounds/images
pushd %{buildroot}%{_datadir}/backgrounds
  ln -s anatase/default/anatase-01-day.jxl default.jxl
  ln -s anatase/default/anatase-01-night.jxl default-dark.jxl
popd
pushd %{buildroot}%{_datadir}/backgrounds/images
  ln -s ../anatase/default/anatase-01-day.jxl default.jxl
  ln -s ../anatase/default/anatase-01-night.jxl default-dark.jxl
popd

mkdir -p %{buildroot}%{_datadir}/glib-2.0/schemas
cat > %{buildroot}%{_datadir}/glib-2.0/schemas/10_org.gnome.desktop.background.anatase.gschema.override <<'EOF'
[org.gnome.desktop.background]
picture-uri='file:///usr/share/backgrounds/anatase/default/anatase-01-day.jxl'
picture-uri-dark='file:///usr/share/backgrounds/anatase/default/anatase-01-night.jxl'
EOF
cat > %{buildroot}%{_datadir}/glib-2.0/schemas/10_org.gnome.desktop.screensaver.anatase.gschema.override <<'EOF'
[org.gnome.desktop.screensaver]
picture-uri='file:///usr/share/backgrounds/anatase/default/anatase-01-day.jxl'
picture-uri-dark='file:///usr/share/backgrounds/anatase/default/anatase-01-night.jxl'
EOF

install_wallpaper() {
  design=$1
  id=$2
  name=$3
  wallpaper_dir="${wallpaper_root}/${id}"

  mkdir -p "${wallpaper_dir}/contents/images" "${wallpaper_dir}/contents/images_dark"
  for resolution in %{resolutions}; do
    if [ "${resolution}" = "%{render_resolution}" ]; then
      install -m 0644 -p "${generated}/jxl/${design}/day/${resolution}.jxl" \
        "${wallpaper_dir}/contents/images/${resolution}.jxl"
      install -m 0644 -p "${generated}/jxl/${design}/night/${resolution}.jxl" \
        "${wallpaper_dir}/contents/images_dark/${resolution}.jxl"
    else
      ln -s %{render_resolution}.jxl "${wallpaper_dir}/contents/images/${resolution}.jxl"
      ln -s %{render_resolution}.jxl "${wallpaper_dir}/contents/images_dark/${resolution}.jxl"
    fi
  done

  cat > "${wallpaper_dir}/metadata.json" <<EOF
{
    "KPlugin": {
        "Authors": [
            {
                "Name": "Anatase"
            }
        ],
        "Id": "${id}",
        "License": "LicenseRef-Anatase-Logos",
        "Name": "${name}"
    }
}
EOF
}

install_wallpaper formation %{wallpaper_id} "Anatase"
install_wallpaper crystal Anatase_Crystal "Anatase Crystal"
install_wallpaper strata Anatase_Strata "Anatase Strata"

pushd "${wallpaper_root}"
  ln -s %{wallpaper_id} Default
popd


%files
%dir %{_datadir}/backgrounds
%dir %{_datadir}/backgrounds/anatase
%dir %{_datadir}/backgrounds/anatase/default
%{_datadir}/backgrounds/anatase/default/*.jxl
%{_datadir}/backgrounds/anatase/default/anatase.xml
%dir %{_datadir}/backgrounds/images
%{_datadir}/backgrounds/images/default*.jxl
%{_datadir}/backgrounds/default*.jxl

%files gnome
%{_datadir}/glib-2.0/schemas/10_org.gnome.desktop.background.anatase.gschema.override
%{_datadir}/glib-2.0/schemas/10_org.gnome.desktop.screensaver.anatase.gschema.override

%files kde
%dir %{_datadir}/wallpapers
%{_datadir}/wallpapers/%{wallpaper_id}
%{_datadir}/wallpapers/Anatase_Crystal
%{_datadir}/wallpapers/Anatase_Strata
%{_datadir}/wallpapers/Default

%changelog
%autochangelog
