%bcond pstoedit 1
# used only in RDF; Soprano has not been updated since Qt4
%bcond marble 0
%bcond visio 1
%bcond wpd 1
%bcond okular 1

#global external_lilypond_fonts 1

Name:    calligra 
Version: 26.04.3
Release: 1%{?dist}
Summary: An integrated office suite

License: GPL-2.0-or-later AND GPL-3.0-or-later AND (GPL-2.0-only OR GPL-3.0-only) AND LGPL-2.0-only AND LGPL-2.1-only AND LGPL-2.0-or-later AND LGPL-2.1-or-later AND BSD-3-Clause AND BSD-2-Clause
URL:     https://calligra.org/
%global revision %(echo %{version} | cut -d. -f3)
%if %{revision} >= 50
%global stable unstable
%else
%global stable stable
%endif
Source0: https://download.kde.org/%{stable}/release-service/%{version}/src/calligra-%{version}.tar.xz

## upstream patches

## upstreamable patches

## downstream patches
Patch200: calligra-disable_products.patch

# https://fedoraproject.org/wiki/Changes/EncourageI686LeafRemoval
ExcludeArch: %{ix86}

BuildRequires: desktop-file-utils
BuildRequires: doxygen
BuildRequires: gcc-c++
BuildRequires: libappstream-glib

# kf6 deps
BuildRequires: extra-cmake-modules
BuildRequires: kf6-rpm-macros
BuildRequires: cmake(KF6Archive)
BuildRequires: cmake(KF6Completion)
BuildRequires: cmake(KF6Config)
BuildRequires: cmake(KF6ConfigWidgets)
BuildRequires: cmake(KF6CoreAddons)
BuildRequires: cmake(KF6Crash)
BuildRequires: cmake(KF6DocTools)
BuildRequires: cmake(KF6GuiAddons)
BuildRequires: cmake(KF6I18n)
BuildRequires: cmake(KF6IconThemes)
BuildRequires: cmake(KF6ItemViews)
BuildRequires: cmake(KF6JobWidgets)
BuildRequires: cmake(KF6KCMUtils)
BuildRequires: cmake(KF6KIO)
BuildRequires: cmake(KF6Notifications)
BuildRequires: cmake(KF6NotifyConfig)
BuildRequires: cmake(KF6Sonnet)
BuildRequires: cmake(KF6TextWidgets)
BuildRequires: cmake(KF6WidgetsAddons)
BuildRequires: cmake(KF6WindowSystem)
BuildRequires: cmake(KF6XmlGui)
BuildRequires: cmake(KF6DBusAddons)

# qt6 deps
BuildRequires: cmake(Qt6Core)
BuildRequires: cmake(Qt6Gui)
BuildRequires: cmake(Qt6Network)
BuildRequires: cmake(Qt6PrintSupport)
BuildRequires: cmake(Qt6Svg)
BuildRequires: cmake(Qt6Test)
BuildRequires: cmake(Qt6Widgets)
BuildRequires: cmake(Qt6Xml)
BuildRequires: cmake(Qt6Quick)
BuildRequires: cmake(Qt6QuickControls2)
BuildRequires: cmake(Qt6OpenGL)
BuildRequires: cmake(Qt6Sql)
%ifarch %{qt6_qtwebengine_arches}
BuildRequires: cmake(Qt6WebEngineWidgets)
%endif
BuildRequires: cmake(Qt6DBus)

# other required deps
BuildRequires: perl-interpreter
BuildRequires: zlib-devel
BuildRequires: cmake(Qt6Keychain)
BuildRequires: boost-devel

# optional deps
BuildRequires: cmake(Imath)
BuildRequires: pkgconfig(gsl)
BuildRequires: cmake(Phonon4Qt6)
#BuildRequires: cmake(KF6CalendarCore)
#BuildRequires: cmake(KF6Contacts)
#BuildRequires: cmake(KPim6Akonadi)
BuildRequires: cmake(KChart6)
BuildRequires: pkgconfig(eigen3)
BuildRequires: cmake(Qca-qt6)
%if %{with marble}
BuildRequires: cmake(Marble)
%endif
BuildRequires: pkgconfig(lcms2)
BuildRequires: pkgconfig(fontconfig)
BuildRequires: pkgconfig(shared-mime-info)
%if %{with wpd}
BuildRequires: pkgconfig(librevenge-0.0)
BuildRequires: pkgconfig(librevenge-stream-0.0)
BuildRequires: pkgconfig(libodfgen-0.1)
BuildRequires: pkgconfig(libwpd-0.10)
BuildRequires: pkgconfig(libwpg-0.3)
BuildRequires: pkgconfig(libwps-0.4)
%if %{with visio}
BuildRequires: pkgconfig(libvisio-0.1)
%endif
BuildRequires: pkgconfig(libetonyek-0.1)
%endif
BuildRequires: pkgconfig(poppler-qt6)
BuildRequires: pkgconfig(poppler)
BuildRequires: pkgconfig(libgit2)

# -- The following OPTIONAL packages have not been found:
# * Qt6QmlCompilerPlusPrivate
# * Cauchy, Cauchy's M2MML, a Matlab/Octave to MathML compiler, <https://bitbucket.org/cyrille/cauchy>
#   Required for the matlab/octave formula tool
# * OOoSDK

Requires:  %{name}-words%{?_isa} = %{version}-%{release}
Requires:  %{name}-sheets%{?_isa} = %{version}-%{release}
Requires:  %{name}-stage%{?_isa} = %{version}-%{release}
Requires:  %{name}-karbon%{?_isa} = %{version}-%{release}

%description
%{summary}.

%package data
Summary: Runtime support files for %{name}
%if %{undefined flatpak}
Requires: color-filesystem
%endif
%if 0%{?external_lilypond_fonts}
Requires: lilypond-emmentaler-fonts
%endif
Obsoletes: %{name}-core < 4
%if %{without okular}
Obsoletes: %{name}-okular-odpgenerator < %{version}-%{release}
Obsoletes: %{name}-okular-odtgenerator < %{version}-%{release}
%endif
BuildArch: noarch
%description data
%{summary}.

%package libs
Summary: Runtime libraries for %{name}
Requires: %{name}-data = %{version}-%{release}
%description libs
%{summary}.

%package l10n
Summary: Language files for calligra
# not *strictly* required, but helps ensure -l10n,-data, and other pkg versions match
Requires: %{name}-data = %{version}-%{release}
BuildArch: noarch
%description l10n
%{summary}.

%package  words
Summary:  An intuitive word processor application with desktop publishing features
Requires: %{name}-words-libs%{?_isa} = %{version}-%{release}
%description words
KWord is an intuitive word processor and desktop publisher application.
With it, you can create informative and attractive documents with
pleasure and ease.

%package  words-libs
Summary:  Runtime libraries for %{name}-words
Requires: %{name}-libs%{?_isa} = %{version}-%{release}
%description words-libs
%{summary}.

%package  sheets 
Summary:  A fully-featured spreadsheet application
Requires: %{name}-sheets-libs%{?_isa} = %{version}-%{release}
%description sheets 
Tables is a fully-featured calculation and spreadsheet tool.  Use it to
quickly create and calculate various business-related spreadsheets, such
as income and expenditure, employee working hours…

%package  sheets-libs
Summary:  Runtime libraries for %{name}-sheets
Requires: %{name}-libs%{?_isa} = %{version}-%{release}
%description sheets-libs
%{summary}.

%package  stage 
Summary:  A full-featured presentation program
Requires: %{name}-stage-libs%{?_isa} = %{version}-%{release}
%description stage 
Stage is a powerful and easy to use presentation application. You
can dazzle your audience with stunning slides containing images, videos,
animation and more.

%package  stage-libs
Summary:  Runtime libraries for %{name}-stage
Requires: %{name}-libs%{?_isa} = %{version}-%{release}
%description stage-libs
%{summary}.

%package  karbon
Summary:  A vector drawing application
Requires: %{name}-karbon-libs%{?_isa} = %{version}-%{release}
%if %{with pstoedit}
# for karbon eps import filter
BuildRequires: pstoedit
Requires: pstoedit
%endif
%description karbon
Karbon is a vector drawing application with an user interface that is
easy to use, highly customizable and extensible. That makes Karbon a
great application for users starting to explore the world of vector
graphics as well as for artists wanting to create breathtaking vector
art.

Whether you want to create clipart, logos, illustrations or photorealistic
vector images – look no further, Karbon is the tool for you!

%package  karbon-libs
Summary:  Runtime libraries for %{name}-karbon
Requires: %{name}-libs%{?_isa} = %{version}-%{release}
%description karbon-libs
%{summary}.

%if %{with okular}
%package  okular-odpgenerator
Summary:  OpenDocument presenter support for okular
BuildRequires: cmake(Okular6)
Requires: %{name}-stage-libs%{?_isa} = %{version}-%{release}
Requires: okular-part
Supplements: (%{name}-stage and okular)
%description okular-odpgenerator
%{summary}.

%package  okular-odtgenerator
Summary:  OpenDocument text support for okular
BuildRequires: cmake(Okular6)
Requires: %{name}-words-libs%{?_isa} = %{version}-%{release}
Requires: okular-part
Supplements: (%{name}-words and okular)
%description okular-odtgenerator
%{summary}.
%endif


%prep
%autosetup -p1


%build
%cmake_kf6 \
  -Wno-dev

%cmake_build


%install
%cmake_install

## unpackaged files
%if 0%{?external_lilypond_fonts}
rm -fv %{buildroot}%{_kf6_datadir}/calligra_shape_music/fonts/Emmentaler-14.ttf
%endif
rm -frv %{buildroot}%{_kf6_datadir}/locale/x-test/

%find_lang %{name} --all-name --with-html


%check
for appdata_file in %{buildroot}%{_kf6_metainfodir}/*.metainfo.xml ; do
appstream-util validate-relax --nonet ${appdata_file} ||:
done
for desktop_file in %{buildroot}%{_datadir}/applications/*.desktop ; do
desktop-file-validate ${desktop_file}  ||:
done


%files
%{_kf6_bindir}/calligraconverter
%{_kf6_bindir}/calligralauncher
%{_kf6_datadir}/applications/org.kde.calligra.desktop
%{_kf6_metainfodir}/org.kde.calligra.metainfo.xml

%files data
%doc AUTHORS README.md
%license COPYING*
%{_kf6_sysconfdir}/xdg/calligrasheetsrc
%{_kf6_sysconfdir}/xdg/calligrastagerc
%{_kf6_sysconfdir}/xdg/calligrawordsrc
%{_kf6_sysconfdir}/xdg/karbonrc
%{_datadir}/color/icc/calligra/
%{_kf6_datadir}/calligra/
%if ! 0%{?external_lilypond_fonts}
%{_kf6_datadir}/calligra_shape_music/fonts/Emmentaler-14.ttf
%endif
%{_kf6_datadir}/calligrasheets/
%{_kf6_datadir}/calligrastage/
%{_kf6_datadir}/calligrawords/
%{_kf6_datadir}/karbon/
%{_kf6_datadir}/config.kcfg/calligrasheets.kcfg
%{_kf6_datadir}/icons/hicolor/*/*/*
%{_kf6_datadir}/kxmlgui5/calligrasheets/
%{_kf6_datadir}/kxmlgui5/calligrastage/
%{_kf6_datadir}/kxmlgui5/calligrawords/
%{_kf6_datadir}/kxmlgui5/karbon/
%{_kf6_datadir}/mime/packages/calligra_svm.xml
%{_kf6_datadir}/mime/packages/wiki-format.xml

%files libs
%{_kf6_libdir}/libautocorrection.so*
%{_kf6_libdir}/libbasicflakes.so*
%{_kf6_libdir}/libflake.so*
%{_kf6_libdir}/libkoformula.so*
%{_kf6_libdir}/libkomain.so*
%{_kf6_libdir}/libkomsooxml.so*
%{_kf6_libdir}/libkoodf.so*
%{_kf6_libdir}/libkoodf2.so*
%{_kf6_libdir}/libkoodfreader.so*
%{_kf6_libdir}/libkopageapp.so*
%{_kf6_libdir}/libkoplugin.so*
%{_kf6_libdir}/libkostore.so*
%{_kf6_libdir}/libkotext.so*
%{_kf6_libdir}/libkotextlayout.so*
%{_kf6_libdir}/libkovectorimage.so*
%{_kf6_libdir}/libkowidgets.so*
%{_kf6_libdir}/libkowidgetutils.so*
%{_kf6_libdir}/libkowv2.so*
%{_kf6_libdir}/libkundo2.so*
%{_kf6_libdir}/libpigmentcms.so*
%{_kf6_libdir}/libRtfReader.so*
%dir %{_kf6_qtplugindir}/calligra/
%dir %{_kf6_qtplugindir}/calligra/colorspaces/
%{_kf6_qtplugindir}/calligra/colorspaces/kolcmsengine.so
%dir %{_kf6_qtplugindir}/calligra/dockers/
%{_kf6_qtplugindir}/calligra/dockers/calligra_docker_defaults.so
%{_kf6_qtplugindir}/calligra/dockers/calligra_docker_stencils.so
%dir %{_kf6_qtplugindir}/calligra/formatfilters/
%{_kf6_qtplugindir}/calligra/formatfilters/calligra_filter_eps2svgai.so
%{_kf6_qtplugindir}/calligra/formatfilters/calligra_filter_key2odp.so
%{_kf6_qtplugindir}/calligra/formatfilters/calligra_filter_kpr2odp.so
%{_kf6_qtplugindir}/calligra/formatfilters/calligra_filter_pdf2svg.so
%{_kf6_qtplugindir}/calligra/formatfilters/calligra_filter_vsdx2odg.so
%{_kf6_qtplugindir}/calligra/formatfilters/calligra_filter_wmf2svg.so
%{_kf6_qtplugindir}/calligra/formatfilters/calligra_filter_xfig2odg.so
%dir %{_kf6_qtplugindir}/calligra/pageapptools/
%{_kf6_qtplugindir}/calligra/pageapptools/kopabackgroundtool.so
%dir %{_kf6_qtplugindir}/calligra/parts/
%dir %{_kf6_qtplugindir}/calligra/shapefiltereffects/
%{_kf6_qtplugindir}/calligra/shapefiltereffects/calligra_filtereffects.so
%dir %{_kf6_qtplugindir}/calligra/shapes/
%ifarch %{qt6_qtwebengine_arches}
%{_kf6_qtplugindir}/calligra/shapes/braindump_shape_web.so
%endif
%{_kf6_qtplugindir}/calligra/shapes/calligra_shape_artistictext.so
%{_kf6_qtplugindir}/calligra/shapes/calligra_shape_chart.so
%{_kf6_qtplugindir}/calligra/shapes/calligra_shape_formula.so
%{_kf6_qtplugindir}/calligra/shapes/calligra_shape_music.so
%{_kf6_qtplugindir}/calligra/shapes/calligra_shape_paths.so
%{_kf6_qtplugindir}/calligra/shapes/calligra_shape_picture.so
%{_kf6_qtplugindir}/calligra/shapes/calligra_shape_plugin.so
%{_kf6_qtplugindir}/calligra/shapes/calligra_shape_text.so
%{_kf6_qtplugindir}/calligra/shapes/calligra_shape_threed.so
%{_kf6_qtplugindir}/calligra/shapes/calligra_shape_vector.so
%{_kf6_qtplugindir}/calligra/shapes/calligra_shape_video.so
%dir %{_kf6_qtplugindir}/calligra/textediting/
%{_kf6_qtplugindir}/calligra/textediting/calligra_textediting_autocorrect.so
%{_kf6_qtplugindir}/calligra/textediting/calligra_textediting_changecase.so
%{_kf6_qtplugindir}/calligra/textediting/calligra_textediting_spellcheck.so
%{_kf6_qtplugindir}/calligra/textediting/calligra_textediting_thesaurus.so
%dir %{_kf6_qtplugindir}/calligra/textinlineobjects/
%{_kf6_qtplugindir}/calligra/textinlineobjects/calligra_textinlineobject_variables.so
%dir %{_kf6_qtplugindir}/calligra/tools/
%{_kf6_qtplugindir}/calligra/tools/calligra_tool_basicflakes.so
%{_kf6_qtplugindir}/calligra/tools/calligra_tool_defaults.so
%{_kf6_plugindir}/propertiesdialog/calligradocinfopropspage.so
%{_kf6_plugindir}/thumbcreator/calligraimagethumbnail.so
%{_kf6_plugindir}/thumbcreator/calligrathumbnail.so

%files l10n -f %{name}.lang
# includes en/ docs, rename to -doc instead? -- rdieter
%{_kf6_datadir}/applications/calligra.desktop

%files sheets 
%{_kf6_bindir}/calligrasheets
%{_kf6_datadir}/applications/org.kde.calligra.sheets.desktop
%{_kf6_datadir}/kio/servicemenus/sheets_print.desktop
%{_kf6_datadir}/templates/.source/SpreadSheet.ods
%{_kf6_datadir}/templates/SpreadSheet.desktop
%{_kf6_metainfodir}/org.kde.calligra.sheets.metainfo.xml

%files sheets-libs
%{_libdir}/libcalligrasheetscore.so*
%{_libdir}/libcalligrasheetsengine.so*
%{_libdir}/libcalligrasheetspartlib.so*
%{_libdir}/libcalligrasheetsui.so*
%{_kf6_qtplugindir}/calligrasheets/
%{_kf6_qtplugindir}/calligra/parts/calligrasheetspart.so
%{_kf6_qtplugindir}/calligra/formatfilters/calligra_filter_applixspread2kspread.so
%{_kf6_qtplugindir}/calligra/formatfilters/calligra_filter_dbase2kspread.so
%{_kf6_qtplugindir}/calligra/formatfilters/calligra_filter_csv2sheets.so
%{_kf6_qtplugindir}/calligra/formatfilters/calligra_filter_gnumeric2sheets.so
%{_kf6_qtplugindir}/calligra/formatfilters/calligra_filter_kspread2tex.so
%{_kf6_qtplugindir}/calligra/formatfilters/calligra_filter_opencalc2sheets.so
%{_kf6_qtplugindir}/calligra/formatfilters/calligra_filter_qpro2sheets.so
%{_kf6_qtplugindir}/calligra/formatfilters/calligra_filter_sheets2csv.so
%{_kf6_qtplugindir}/calligra/formatfilters/calligra_filter_sheets2gnumeric.so
%{_kf6_qtplugindir}/calligra/formatfilters/calligra_filter_sheets2html.so
%{_kf6_qtplugindir}/calligra/formatfilters/calligra_filter_sheets2opencalc.so
%{_kf6_qtplugindir}/calligra/formatfilters/calligra_filter_xls2ods.so
%{_kf6_qtplugindir}/calligra/formatfilters/calligra_filter_xlsx2ods.so

%files stage 
#doc stage/AUTHORS stage/CHANGES
%{_bindir}/calligrastage
%{_kf6_datadir}/applications/org.kde.calligra.stage.desktop
%{_kf6_datadir}/kio/servicemenus/stage_print.desktop
%{_kf6_datadir}/templates/.source/Presentation.odp
%{_kf6_datadir}/templates/Presentation.desktop
%{_kf6_metainfodir}/org.kde.calligra.stage.metainfo.xml

%files stage-libs
%{_kf6_libdir}/libcalligrastageprivate.so*
%{_kf6_qtplugindir}/calligra/parts/calligrastagepart.so
%{_kf6_qtplugindir}/calligra/formatfilters/calligra_filter_ppt2odp.so
%{_kf6_qtplugindir}/calligra/formatfilters/calligra_filter_pptx2odp.so
%{_kf6_qtplugindir}/calligra/presentationeventactions/calligrastageeventactions.so
%{_kf6_qtplugindir}/calligra/textinlineobjects/kprvariables.so
%{_kf6_qtplugindir}/calligrastage/

%files karbon
%{_kf6_bindir}/karbon
%{_kf6_datadir}/applications/org.kde.calligra.karbon.desktop
%{_kf6_datadir}/kio/servicemenus/karbon_print.desktop
%{_kf6_datadir}/templates/.source/Illustration.odg
%{_kf6_datadir}/templates/Illustration.desktop
%{_kf6_metainfodir}/org.kde.calligra.karbon.metainfo.xml

%files karbon-libs
%{_kf6_libdir}/libkarboncommon.so*
%{_kf6_libdir}/libkarbonui.so*
%{_kf6_qtplugindir}/calligra/parts/karbonpart.so
%{_kf6_qtplugindir}/calligra/tools/karbon_tools.so
%{_kf6_qtplugindir}/karbon/
%{_kf6_qtplugindir}/calligra/formatfilters/calligra_filter_karbon1x2karbon.so
%{_kf6_qtplugindir}/calligra/formatfilters/calligra_filter_karbon2image.so
%{_kf6_qtplugindir}/calligra/formatfilters/calligra_filter_karbon2svg.so
%{_kf6_qtplugindir}/calligra/formatfilters/calligra_filter_karbon2wmf.so
%{_kf6_qtplugindir}/calligra/formatfilters/calligra_filter_pdf2odg.so
%{_kf6_qtplugindir}/calligra/formatfilters/calligra_filter_svg2karbon.so

%files words
%{_kf6_bindir}/calligrawords
%{_kf6_datadir}/applications/org.kde.calligra.words.desktop
%{_kf6_datadir}/applications/org.kde.calligrawords_ascii.desktop
%{_kf6_datadir}/kio/servicemenus/words_print.desktop
%{_kf6_datadir}/templates/.source/TextDocument.odt
%{_kf6_datadir}/templates/TextDocument.desktop
%{_kf6_metainfodir}/org.kde.calligra.words.metainfo.xml

%files words-libs
%{_kf6_libdir}/libwordsprivate.so*
%{_kf6_qtplugindir}/calligra/parts/calligrawordspart.so
%{_kf6_qtplugindir}/calligra/formatfilters/calligra_filter_applixword2odt.so
%{_kf6_qtplugindir}/calligra/formatfilters/calligra_filter_ascii2words.so
%{_kf6_qtplugindir}/calligra/formatfilters/calligra_filter_doc2odt.so
%{_kf6_qtplugindir}/calligra/formatfilters/calligra_filter_docx2odt.so
%{_kf6_qtplugindir}/calligra/formatfilters/calligra_filter_html2ods.so
%{_kf6_qtplugindir}/calligra/formatfilters/calligra_filter_odt2ascii.so
%{_kf6_qtplugindir}/calligra/formatfilters/calligra_filter_odt2docx.so
%{_kf6_qtplugindir}/calligra/formatfilters/calligra_filter_odt2epub2.so
%{_kf6_qtplugindir}/calligra/formatfilters/calligra_filter_odt2html.so
%{_kf6_qtplugindir}/calligra/formatfilters/calligra_filter_odt2mobi.so
%{_kf6_qtplugindir}/calligra/formatfilters/calligra_filter_odt2wiki.so
%{_kf6_qtplugindir}/calligra/formatfilters/calligra_filter_rtf2odt.so
%{_kf6_qtplugindir}/calligra/formatfilters/calligra_filter_wpd2odt.so
%{_kf6_qtplugindir}/calligra/formatfilters/calligra_filter_wpg2odg.so
%{_kf6_qtplugindir}/calligra/formatfilters/calligra_filter_wpg2svg.so
%{_kf6_qtplugindir}/calligra/formatfilters/calligra_filter_wps2odt.so

%if %{with okular}
%files okular-odpgenerator
%{_kf6_libdir}/libkookularGenerator_odp.so*
%{_kf6_qtplugindir}/okular_generators/okularGenerator_odp_calligra.so
%{_kf6_qtplugindir}/okular_generators/okularGenerator_powerpoint_calligra.so
%{_kf6_qtplugindir}/okular_generators/okularGenerator_pptx_calligra.so
%{_kf6_datadir}/applications/okularApplication_odp_calligra.desktop
%{_kf6_datadir}/applications/okularApplication_powerpoint_calligra.desktop
%{_kf6_datadir}/applications/okularApplication_pptx_calligra.desktop

%files okular-odtgenerator
%{_kf6_libdir}/libkookularGenerator_odt.so*
%{_kf6_qtplugindir}/okular_generators/okularGenerator_doc_calligra.so
%{_kf6_qtplugindir}/okular_generators/okularGenerator_docx_calligra.so
%{_kf6_qtplugindir}/okular_generators/okularGenerator_odt_calligra.so
%{_kf6_qtplugindir}/okular_generators/okularGenerator_powerpoint_calligra.so
%{_kf6_qtplugindir}/okular_generators/okularGenerator_rtf_calligra.so
%{_kf6_qtplugindir}/okular_generators/okularGenerator_wpd_calligra.so
%{_kf6_datadir}/applications/okularApplication_doc_calligra.desktop
%{_kf6_datadir}/applications/okularApplication_docx_calligra.desktop
%{_kf6_datadir}/applications/okularApplication_odt_calligra.desktop
%{_kf6_datadir}/applications/okularApplication_rtf_calligra.desktop
%{_kf6_datadir}/applications/okularApplication_wpd_calligra.desktop
%endif


%changelog
* Tue Jun 30 2026 Steve Cossette <farchord@gmail.com> - 26.04.3-1
- 26.04.3

* Fri Jun 12 2026 Yaakov Selkowitz <yselkowi@redhat.com> - 26.04.2-2
- Rebuilt for openssl 4.0

* Wed Jun 03 2026 Steve Cossette <farchord@gmail.com> - 26.04.2-1
- 26.04.2

* Sat May 30 2026 Richard Shaw <hobbes1069@gmail.com> - 26.04.1-2
- Rebuild for OpenColorIO 2.5.2.

* Wed May 06 2026 Steve Cossette <farchord@gmail.com> - 26.04.1-1
- 26.04.1

* Fri Apr 17 2026 Jan Grulich <jgrulich@redhat.com> - 26.04.0-3
- Rebuild (qt6)

* Tue Apr 14 2026 Steve Cossette <farchord@gmail.com> - 26.04.0-2
- Rebuild for openssl

* Sat Apr 11 2026 Steve Cossette <farchord@gmail.com> - 26.04.0-1
- 26.04.0

* Mon Mar 16 2026 Steve Cossette <farchord@gmail.com> - 26.03.80-1
- 26.03.80

* Sun Mar 08 2026 Steve Cossette <farchord@gmail.com> - 25.12.3-1
- 25.12.3

* Thu Feb 12 2026 Steve Cossette <farchord@gmail.com> - 25.12.2-2
- Full Stack Rebuild (kio abi break)

* Wed Feb 04 2026 Steve Cossette <farchord@gmail.com> - 25.12.2-1
- 25.12.2

* Mon Jan 19 2026 Steve Cossette <farchord@gmail.com> - 25.12.1-4
- Bump for poppler update

* Fri Jan 16 2026 Fedora Release Engineering <releng@fedoraproject.org> - 25.12.1-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_44_Mass_Rebuild

* Fri Jan 16 2026 Fedora Release Engineering <releng@fedoraproject.org> - 25.12.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_44_Mass_Rebuild

* Wed Jan 07 2026 farchord@gmail.com - 25.12.1-1
- 25.12.1

* Sat Dec 06 2025 Steve Cossette <farchord@gmail.com> - 25.12.0-1
- 25.12.0

* Fri Nov 28 2025 Steve Cossette <farchord@gmail.com> - 25.11.90-1
- 25.11.90

* Sat Nov 15 2025 Steve Cossette <farchord@gmail.com> - 25.11.80-1
- 25.11.80

* Tue Nov 04 2025 Steve Cossette <farchord@gmail.com> - 25.08.3-1
- 25.08.3

* Wed Oct 08 2025 Steve Cossette <farchord@gmail.com> - 25.08.2-1
- 25.08.2

* Sun Sep 21 2025 Steve Cossette <farchord@gmail.com> - 25.08.1-1
- 25.08.1

* Fri Aug 08 2025 Steve Cossette <farchord@gmail.com> - 25.08.0-1
- 25.08.0

* Fri Jul 25 2025 Steve Cossette <farchord@gmail.com> - 25.07.90-1
- 25.07.90

* Wed Jul 23 2025 Fedora Release Engineering <releng@fedoraproject.org> - 25.07.80-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_43_Mass_Rebuild

* Thu Jul 17 2025 Steve Cossette <farchord@gmail.com> - 25.07.80-2
- Rebuild for poppler update

* Fri Jul 11 2025 Steve Cossette <farchord@gmail.com> - 25.07.80-1
- 25.07.80

* Thu Jul 03 2025 Steve Cossette <farchord@gmail.com> - 25.04.3-1
- 25.04.3

* Wed Jun 04 2025 Steve Cossette <farchord@gmail.com> - 25.04.2-1
- 25.04.2

* Wed May 14 2025 Steve Cossette <farchord@gmail.com> - 25.04.1-1
- 25.04.1

* Sat Apr 12 2025 Steve Cossette <farchord@gmail.com> - 25.04.0-1
- 25.04.0

* Thu Mar 20 2025 Steve Cossette <farchord@gmail.com> - 25.03.80-1
- 25.03.80 (Beta)

* Tue Mar 04 2025 Steve Cossette <farchord@gmail.com> - 24.12.3-1
- 24.12.3

* Sun Feb 23 2025 Neal Gompa <ngompa@fedoraproject.org> - 24.12.2-4
- Rebuild for poppler 25.02.0 again

* Fri Feb 21 2025 Steve Cossette <farchord@gmail.com> - 24.12.2-3
- Rebuild for ppc64le enablement

* Mon Feb 10 2025 Steve Cossette <farchord@gmail.com> - 24.12.2-2
- Rebuild (for poppler 25.02.0)

* Wed Feb 05 2025 Steve Cossette <farchord@gmail.com> - 24.12.2-1
- 24.12.2

* Sun Feb 02 2025 Orion Poplawski <orion@nwra.com> - 24.12.1-3
- Rebuild with gsl 2.8

* Thu Jan 16 2025 Fedora Release Engineering <releng@fedoraproject.org> - 24.12.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_42_Mass_Rebuild

* Tue Jan 07 2025 Steve Cossette <farchord@gmail.com> - 24.12.1-1
- 24.12.1

* Sat Dec 07 2024 Marc Deop i Argemí <marcdeop@fedoraproject.org> - 24.12.0-1
- 24.12.0

* Fri Nov 29 2024 Marc Deop i Argemí <marcdeop@fedoraproject.org> - 24.11.90-1
- 24.11.90

* Fri Nov 15 2024 Marc Deop i Argemí <marcdeop@fedoraproject.org> - 24.11.80-1
- 24.11.80

* Tue Sep 03 2024 Yaakov Selkowitz <yselkowi@redhat.com> - 4.0.1-2
- Fix okular generator desktop files

* Mon Sep 02 2024 Yaakov Selkowitz <yselkowi@redhat.com> - 4.0.1-1
- 4.0.1

* Wed Aug 28 2024 Miroslav Suchý <msuchy@redhat.com> - 3.2.1-34
- convert license to SPDX

* Thu Aug 22 2024 Marek Kasik <mkasik@redhat.com> - 3.2.1-33
- Rebuild for poppler 24.08.0

* Wed Jul 17 2024 Fedora Release Engineering <releng@fedoraproject.org> - 3.2.1-32
- Rebuilt for https://fedoraproject.org/wiki/Fedora_41_Mass_Rebuild

* Thu Jun 13 2024 Robert-André Mauchin <zebob.m@gmail.com> - 3.2.1-31
- Rebuild for exiv2 0.28.2

* Thu Apr 25 2024 Benjamin A. Beasley <code@musicinmybrain.net> - 3.2.1-30
- Rebuilt for OpenColorIO 2.3.2

* Thu Feb 08 2024 Marek Kasik <mkasik@redhat.com> - 3.2.1-29
- Rebuild for poppler 24.02.0

* Mon Jan 29 2024 Benjamin A. Beasley <code@musicinmybrain.net> - 3.2.1-28
- Drop i686 support (leaf package)

* Tue Jan 23 2024 Fedora Release Engineering <releng@fedoraproject.org> - 3.2.1-27
- Rebuilt for https://fedoraproject.org/wiki/Fedora_40_Mass_Rebuild

* Fri Jan 19 2024 Fedora Release Engineering <releng@fedoraproject.org> - 3.2.1-26
- Rebuilt for https://fedoraproject.org/wiki/Fedora_40_Mass_Rebuild

* Mon Aug 07 2023 Marek Kasik <mkasik@redhat.com> - 3.2.1-25
- Rebuild for poppler 23.08.0

* Wed Jul 19 2023 Fedora Release Engineering <releng@fedoraproject.org> - 3.2.1-24
- Rebuilt for https://fedoraproject.org/wiki/Fedora_39_Mass_Rebuild

* Wed Apr 19 2023 Florian Weimer <fweimer@redhat.com> - 3.2.1-23
- Port to C99

* Mon Feb 06 2023 Marek Kasik <mkasik@redhat.com> - 3.2.1-22
- Rebuild for poppler-23.02.0
- Disable Okular support for now as it prevents to build Calligra currently

* Wed Jan 18 2023 Fedora Release Engineering <releng@fedoraproject.org> - 3.2.1-21
- Rebuilt for https://fedoraproject.org/wiki/Fedora_38_Mass_Rebuild

* Tue Aug 23 2022 Mamoru TASAKA <mtasaka@fedoraproject.org> - 3.2.1-20
- Rebuild for gsl-2.7.1

* Mon Aug 08 2022 Marek Kasik <mkasik@redhat.com> - 3.2.1-19
- Rebuild for poppler-22.08.0
- Backport necessary changes from upstream

* Wed Jul 20 2022 Fedora Release Engineering <releng@fedoraproject.org> - 3.2.1-18
- Rebuilt for https://fedoraproject.org/wiki/Fedora_37_Mass_Rebuild

* Tue May 24 2022 Rex Dieter <rdieter@fedoraproject.org> - 3.2.1-17
- rebuild (poppler)

* Wed Jan 19 2022 Fedora Release Engineering <releng@fedoraproject.org> - 3.2.1-16
- Rebuilt for https://fedoraproject.org/wiki/Fedora_36_Mass_Rebuild

* Tue Jan 18 2022 Marek Kasik <mkasik@redhat.com> - 3.2.1-15
- Rebuild for poppler-22.01.0
- Switch to C++17 because it is needed by poppler now

* Sun Nov 28 2021 Igor Raits <ignatenkobrain@fedoraproject.org> - 3.2.1-14
- Rebuild for libgit2 1.3.x

* Thu Aug 05 2021 Marek Kasik <mkasik@redhat.com> - 3.2.1-13
- Rebuild for poppler-21.08.0

* Sun Aug 01 2021 Rex Dieter <rdieter@fedoraproject.org> - 3.2.1-12
- pull in upstream 3.2 branch fixes

* Sun Aug 01 2021 Richard Shaw <hobbes1069@gmail.com> - 3.2.1-11
- Move to openexr2 compat package.

* Wed Jul 21 2021 Fedora Release Engineering <releng@fedoraproject.org> - 3.2.1-10
- Rebuilt for https://fedoraproject.org/wiki/Fedora_35_Mass_Rebuild

* Tue Jan 26 2021 Fedora Release Engineering <releng@fedoraproject.org> - 3.2.1-9
- Rebuilt for https://fedoraproject.org/wiki/Fedora_34_Mass_Rebuild

* Tue Jan 19 2021 Marek Kasik <mkasik@redhat.com> - 3.2.1-8
- Rebuild for poppler-21.01.0

* Fri Jan 01 2021 Richard Shaw <hobbes1069@gmail.com> - 3.2.1-7
- Rebuild for OpenEXR 2.5.3.

* Mon Dec 28 19:00:18 CET 2020 Igor Raits <ignatenkobrain@fedoraproject.org> - 3.2.1-6
- Rebuild for libgit2 1.1.x

* Wed Oct 14 2020 Jeff Law <law@redhat.com> - 3.2.1-5
- Add missing #includes for gcc-11

* Sat Aug 01 2020 Fedora Release Engineering <releng@fedoraproject.org> - 3.2.1-4
- Second attempt - Rebuilt for
  https://fedoraproject.org/wiki/Fedora_33_Mass_Rebuild

* Mon Jul 27 2020 Fedora Release Engineering <releng@fedoraproject.org> - 3.2.1-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_33_Mass_Rebuild

* Fri Jul 17 2020 Rex Dieter <rdieter@fedoraproject.org> - 3.2.1-2
- rebuild (poppler)

* Fri May 15 2020 Rex Dieter <rdieter@fedoraproject.org> - 3.2.1-1
- 3.2.1

* Fri Apr 24 2020 Rex Dieter <rdieter@fedoraproject.org> - 3.2.0-1
- 3.2.0

* Wed Apr 08 2020 Rex Dieter <rdieter@fedoraproject.org> - 3.1.90-1
- 3.1.90 (3.2 beta1)

* Tue Jan 28 2020 Fedora Release Engineering <releng@fedoraproject.org> - 3.1.0-19
- Rebuilt for https://fedoraproject.org/wiki/Fedora_32_Mass_Rebuild

* Fri Jan 17 2020 Marek Kasik <mkasik@redhat.com> - 3.1.0-18
- Rebuild for poppler-0.84.0

* Fri Aug 23 2019 Adam Williamson <awilliam@redhat.com> - 3.1.0-17
- Backport upstream fix for compile with Qt 5.13

* Tue Aug 20 2019 Susi Lehtola <jussilehtola@fedoraproject.org> - 3.1.0-16
- Rebuilt for GSL 2.6.

* Wed Jul 24 2019 Fedora Release Engineering <releng@fedoraproject.org> - 3.1.0-15
- Rebuilt for https://fedoraproject.org/wiki/Fedora_31_Mass_Rebuild

* Wed Apr 10 2019 Richard Shaw <hobbes1069@gmail.com> - 3.1.0-14
- Rebuild for OpenEXR 2.3.0.

* Thu Jan 31 2019 Fedora Release Engineering <releng@fedoraproject.org> - 3.1.0-13
- Rebuilt for https://fedoraproject.org/wiki/Fedora_30_Mass_Rebuild

* Fri Jan 25 2019 Marek Kasik <mkasik@redhat.com> - 3.1.0-12
- Rebuild for poppler-0.73.0

* Wed Dec 05 2018 Rex Dieter <rdieter@fedoraproject.org> - 3.1.0-11
- (re)enable stage (#1518400)

* Tue Aug 14 2018 Marek Kasik <mkasik@redhat.com> - 3.1.0-10
- Rebuild for poppler-0.67.0

* Thu Jul 12 2018 Fedora Release Engineering <releng@fedoraproject.org> - 3.1.0-9
- Rebuilt for https://fedoraproject.org/wiki/Fedora_29_Mass_Rebuild

* Thu Jun 28 2018 Rex Dieter <rdieter@fedoraproject.org> - 3.1.0-8
- Upstream Qt-5.11 fixes

* Sun Apr 08 2018 Rex Dieter <rdieter@fedoraproject.org> - 3.1.0-7
- rebuild (okular)

* Fri Apr 06 2018 Rex Dieter <rdieter@fedoraproject.org> - 3.1.0-6
- calligra-sheets package doesn't depend on calligra-sheets-libs (#1563177)
- use %%make_build %%ldconfig_scriptlets

* Fri Mar 23 2018 Marek Kasik <mkasik@redhat.com> - 3.1.0-5
- Rebuild for poppler-0.63.0

* Fri Mar 02 2018 Rex Dieter <rdieter@fedoraproject.org> - 3.1.0-4
- rebuild

* Wed Feb 14 2018 David Tardon <dtardon@redhat.com> - 3.1.0-3
- rebuild for poppler 0.62.0

* Wed Feb 07 2018 Fedora Release Engineering <releng@fedoraproject.org> - 3.1.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Sat Jan 27 2018 Rex Dieter <rdieter@fedoraproject.org> - 3.1.0-1
- calligra-3.1.0 (#1539266)

* Sun Jan 07 2018 Igor Gnatenko <ignatenkobrain@fedoraproject.org> - 3.0.90-3
- Remove obsolete scriptlets

* Sun Jan 07 2018 Rex Dieter <rdieter@fedoraproject.org> - 3.0.90-2
- fix -core/-libs to avoid dep on -stage

* Thu Jan 04 2018 Rex Dieter <rdieter@fedoraproject.org> - 3.0.90-1
- calligra-3.0.90
- drop calligra-plan (packaged separately)
- +kf5+kinit_requires as needed

* Fri Dec 29 2017 Rex Dieter <rdieter@fedoraproject.org> - 3.0.1-15
- rebuild (okular)

* Wed Dec 20 2017 Rex Dieter <rdieter@fedoraproject.org> - 3.0.1-14
- omit incompatible KF5AkonadiContacts/KF5CalendarCore components (for now)

* Fri Nov 17 2017 Rex Dieter <rdieter@fedoraproject.org> - 3.0.1-13
- use %%_kf5_metainfodir macro

* Wed Nov 08 2017 David Tardon <dtardon@redhat.com> - 3.0.1-13
- rebuild for poppler 0.61.0

* Fri Oct 06 2017 David Tardon <dtardon@redhat.com> - 3.0.1-12
- rebuild for poppler 0.60.1

* Wed Sep 13 2017 Rex Dieter <rdieter@fedoraproject.org> - 3.0.1-11
- rebuild (marble)

* Fri Sep 08 2017 David Tardon <dtardon@redhat.com> - 3.0.1-10
- rebuild for poppler 0.59.0

* Thu Aug 03 2017 David Tardon <dtardon@redhat.com> - 3.0.1-9
- rebuild for poppler 0.57.0

* Mon Jul 31 2017 Florian Weimer <fweimer@redhat.com> - 3.0.1-8
- Rebuild with binutils fix for ppc64le (#1475636)

* Tue Jul 25 2017 Rex Dieter <rdieter@fedoraproject.org> - 3.0.1-7
- rebuild (gsl)

* Wed Jul 12 2017 Rex Dieter <rdieter@fedoraproject.org> - 3.0.1-6
- drop empty -flow subpkg (#1470345)

* Mon Jun 26 2017 Rex Dieter <rdieter@fedoraproject.org> - 3.0.1-5
- -l10n subpkg

* Tue Jun 13 2017 Rex Dieter <rdieter@fedoraproject.org> - 3.0.1-4
- fix/move plugins to make apps independantly installable

* Tue Jun 13 2017 Rex Dieter <rdieter@fedoraproject.org> - 3.0.1-3
- main: drop Requires: -author
- Obsoletes: -braindump-libs

* Mon Jun 12 2017 Rex Dieter <rdieter@fedoraproject.org> - 3.0.1-2
- more Obsoletes: -author -reports-map-element -kexi-map-form-widget

* Tue Mar 28 2017 David Tardon <dtardon@redhat.com> - 2.9.11-20
- rebuild for poppler 0.53.0

* Fri Feb 10 2017 Fedora Release Engineering <releng@fedoraproject.org> - 2.9.11-19
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Thu Jan 12 2017 Rex Dieter <rdieter@fedoraproject.org> - 2.9.11-18
- drop okular support on f26+

* Wed Jan 11 2017 Rex Dieter <rdieter@fedoraproject.org> - 2.9.11-17
- -okular-*: (Build)Requires: s/okular/okular4/

* Wed Dec 28 2016 Rich Mattes <richmattes@gmail.com> - 2.9.11-16
- Rebuild for eigen3-3.3.1

* Sun Dec 18 2016 Rex Dieter <rdieter@fedoraproject.org> - 2.9.11-15
- Backport upstream plan-related fixes (#1382445,kde#359537)

* Sun Dec 18 2016 Rex Dieter <rdieter@fedoraproject.org> - 2.9.11-14
- filters/karbon/pdf: drop libjpeg/openjpeg overlinking
- make openjpeg build dep krita-only

* Fri Dec 16 2016 David Tardon <dtardon@redhat.com> - 2.9.11-13
- rebuild for poppler 0.50.0

* Thu Nov 24 2016 Orion Poplawski <orion@cora.nwra.com> - 2.9.11-12
- Rebuild for poppler 0.49.0

* Fri Oct 21 2016 Marek Kasik <mkasik@redhat.com> - 2.9.11-11
- Rebuild for poppler-0.48.0

* Sun Oct 09 2016 Rex Dieter <rdieter@fedoraproject.org> - 2.9.11-10
- omit krita on f25+, now packaged separately (#1376994)

* Thu Aug 25 2016 Rex Dieter <rdieter@fedoraproject.org> - 2.9.11-9
- fix typo in -kexi-driver-mysql (#1370037)

* Mon Jul 18 2016 Marek Kasik <mkasik@redhat.com> - 2.9.11-8
- Rebuild for poppler-0.45.0

* Tue May 31 2016 Rex Dieter <rdieter@fedoraproject.org> - 2.9.11-7
- calligra: allow >= krita versions, as future krita's will be released separately

* Tue May  3 2016 Marek Kasik <mkasik@redhat.com> - 2.9.11-6
- Rebuild for poppler-0.43.0

* Fri Apr 15 2016 David Tardon <dtardon@redhat.com> - 2.9.11-5
- rebuild for ICU 57.1

* Mon Feb 22 2016 Orion Poplawski <orion@cora.nwra.com> - 2.9.11-4
- Rebuild for gsl 2.1

* Tue Feb 09 2016 Rex Dieter <rdieter@fedoraproject.org> 2.9.11-3
- rebuild (okular)

* Tue Feb 09 2016 Rex Dieter <rdieter@fedoraproject.org> 2.9.11-2
- support kf5 ServiceMenus

* Wed Feb 03 2016 Rex Dieter <rdieter@fedoraproject.org> 2.9.11-1
- 2.9.11
- disable FTBFS krita gmic plugin on fc24+ (gcc6 internal compiler error)

* Wed Feb 03 2016 Fedora Release Engineering <releng@fedoraproject.org> - 2.9.10-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Tue Jan 26 2016 Rex Dieter <rdieter@fedoraproject.org> 2.9.10-4
- rebuild (boost)

* Fri Jan 22 2016 Marek Kasik <mkasik@redhat.com> - 2.9.10-3
- Rebuild for poppler-0.40.0

* Thu Jan 14 2016 Adam Jackson <ajax@redhat.com> - 2.9.10-2
- Rebuild for glew 1.13

* Wed Dec 09 2015 Rex Dieter <rdieter@fedoraproject.org> 2.9.10-1
- 2.9.10

* Fri Nov 06 2015 Rex Dieter <rdieter@fedoraproject.org> 2.9.9-1
- 2.9.9

* Wed Oct 28 2015 David Tardon <dtardon@redhat.com> - 2.9.8-3
- rebuild for ICU 56.1

* Fri Oct 16 2015 Rex Dieter <rdieter@fedoraproject.org> 2.9.8-2
- kexi-map-form-widget: drop hard-coded marble dep

* Tue Oct 13 2015 Rex Dieter <rdieter@fedoraproject.org> 2.9.8-1
- 2.9.8

* Sun Sep 20 2015 Rex Dieter <rdieter@fedoraproject.org> 2.9.7-2
- rebuild (marble)

* Thu Sep 03 2015 Rex Dieter <rdieter@fedoraproject.org> 2.9.7-1
- 2.9.7 (#1241726)

* Tue Sep 01 2015 Rex Dieter <rdieter@fedoraproject.org> 2.9.6-9
- rebuild (marble)

* Thu Aug 27 2015 Jonathan Wakely <jwakely@redhat.com> - 2.9.6-8
- Rebuilt for Boost 1.59

* Mon Aug 10 2015 Rex Dieter <rdieter@fedoraproject.org> 2.9.6-7
- (re)enable pstoedit support, bug #1183335 fixed

* Tue Aug 04 2015 Rex Dieter <rdieter@fedoraproject.org> 2.9.6-6
- kexi: Requires: kate-part (epel7)

* Wed Jul 29 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.9.6-5
- Rebuilt for https://fedoraproject.org/wiki/Changes/F23Boost159

* Tue Jul 28 2015 Rex Dieter <rdieter@fedoraproject.org> 2.9.6-4
- pull in minor/cosmetic upstream commits (version, .desktop validation)

* Wed Jul 22 2015 David Tardon <dtardon@redhat.com> - 2.9.6-3
- rebuild for Boost 1.58

* Wed Jul 22 2015 Marek Kasik <mkasik@redhat.com> 2.9.6-2
- Rebuild (poppler-0.34.0)

* Tue Jul 14 2015 Rex Dieter <rdieter@fedoraproject.org> 2.9.6-1
- 2.9.6 (#1241726)

* Wed Jun 24 2015 Rex Dieter <rdieter@fedoraproject.org> - 2.9.5-3
- rebuild (exiv2)

* Wed Jun 17 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.9.5-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Tue Jun 09 2015 Rex Dieter <rdieter@fedoraproject.org> 2.9.5-1
- 2.9.5 (#1228439), libwps-0.4 support f23+ only

* Sat Jun 06 2015 David Tardon <dtardon@redhat.com> - 2.9.4-5
- enable Apple Keynote import
- adapt to libwps 0.4

* Fri Jun  5 2015 Marek Kasik <mkasik@redhat.com> 2.9.4-4
- Rebuild (poppler-0.33.0)

* Fri May 22 2015 Rex Dieter <rdieter@fedoraproject.org> 2.9.4-3
- rebuild (libwps)

* Thu May 07 2015 Rex Dieter <rdieter@fedoraproject.org> 2.9.4-2
- -qtquick subpkg, -kexi: move kexirelationdesignshape here

* Thu May 07 2015 Rex Dieter <rdieter@fedoraproject.org> 2.9.4-1
- 2.9.4, BR: s/marble-devel/marble-widget-devel/

* Mon Apr 20 2015 Rex Dieter <rdieter@fedoraproject.org> 2.9.2-4
- kexi-libs: Requires: kate4-part (#1213229, kde#346373)

* Sun Apr 19 2015 Rex Dieter <rdieter@fedoraproject.org> 2.9.2-3
- rebuild (marble)

* Mon Apr 06 2015 Rex Dieter <rdieter@fedoraproject.org> 2.9.2-2
- backport "fix csv import" (kde#344718)

* Fri Apr 03 2015 Rex Dieter <rdieter@fedoraproject.org> 2.9.2-1
- 2.9.2

* Sun Mar 15 2015 Rex Dieter <rdieter@fedoraproject.org> 2.9.1-1
- calligra-2.9.1 (#1202153)

* Fri Mar 13 2015 Rex Dieter <rdieter@fedoraproject.org> 2.9.0-4
- -core: move kexirelationdesignshape plugin here (to match the .desktop file)

* Mon Mar 09 2015 Rex Dieter <rdieter@fedoraproject.org> 2.9.0-3
- rebuild (GraphicsMagick)

* Sun Mar 01 2015 Rex Dieter <rdieter@fedoraproject.org> 2.9.0-2
- rebuild

* Thu Feb 26 2015 Rex Dieter <rdieter@fedoraproject.org> 2.9.0-1
- 2.9.0

* Thu Feb 26 2015 Rex Dieter <rdieter@fedoraproject.org> 2.8.7-10
- rebuild (gcc5)

* Wed Feb 04 2015 Petr Machata <pmachata@redhat.com> - 2.8.7-9
- Bump for rebuild.

* Sun Feb 01 2015 Rex Dieter <rdieter@fedoraproject.org> 2.8.7-8
- don't own %%_datadir/appdata (#1188049)

* Tue Jan 27 2015 Petr Machata <pmachata@redhat.com> - 2.8.7-7
- Rebuild for boost 1.57.0

* Tue Jan 27 2015 Petr Machata <pmachata@redhat.com> - 2.8.7-6
- Rebuild for boost 1.57.0

* Fri Jan 23 2015 Marek Kasik <mkasik@redhat.com> 2.8.7-5
- Rebuild (poppler-0.30.0)

* Sun Jan 18 2015 Rex Dieter <rdieter@fedoraproject.org> 2.8.7-4
- kde-applications fixes
- disable pstoedit support on f22+ (#1183335)

* Sun Dec 21 2014 Rex Dieter <rdieter@fedoraproject.org> 2.8.7-3
- move libcalligradb to -libs, libkoreport now depends on it (#1176398)

* Wed Dec 10 2014 Rex Dieter <rdieter@fedoraproject.org> 2.8.7-2
- rebuild (marble)

* Fri Dec 05 2014 Rex Dieter <rdieter@fedoraproject.org> 2.8.7-1
- 2.8.7
- -core: +Requires: calligra-l10n

* Thu Nov 27 2014 Marek Kasik <mkasik@redhat.com> 2.8.6-3
- Rebuild (poppler-0.28.1)

* Wed Nov 26 2014 Rex Dieter <rdieter@fedoraproject.org> 2.8.6-2
- rebuild (openexr)

* Mon Sep 22 2014 Rex Dieter <rdieter@fedoraproject.org> 2.8.6-1
- 2.8.6

* Tue Aug 26 2014 David Tardon <dtardon@redhat.com> - 2.8.5-6
- rebuild for ICU 53.1

* Fri Aug 15 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.8.5-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Fri Aug 15 2014 Rex Dieter <rdieter@fedoraproject.org> 2.8.5-4
- rebuild (okular)

* Wed Aug 06 2014 Rex Dieter <rdieter@fedoraproject.org> 2.8.5-3
- rebuild (kde-4.13.97)

* Mon Jul 14 2014 Rex Dieter <rdieter@fedoraproject.org> 2.8.5-2
- rebuild (marble)

* Sun Jul 06 2014 Rex Dieter <rdieter@fedoraproject.org> 2.8.5-1
- 2.8.5

* Thu Jul 03 2014 Rex Dieter <rdieter@fedoraproject.org> 2.8.4-2
- optimize mimeinfo scriptlet

* Tue Jun 24 2014 Rex Dieter <rdieter@fedoraproject.org> 2.8.4-1
- 2.8.4

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.8.3-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Tue May 27 2014 David Tardon <dtardon@redhat.com> - 2.8.3-3
- switch to librevenge-based import libs

* Thu May 22 2014 Petr Machata <pmachata@redhat.com> - 2.8.3-2
- Rebuild for boost 1.55.0

* Thu May 15 2014 Rex Dieter <rdieter@fedoraproject.org> 2.8.3-1
- 2.8.3

* Tue May 13 2014 Marek Kasik <mkasik@redhat.com> 2.8.2-4
- Rebuild (poppler-0.26.0)

* Fri May 09 2014 Rex Dieter <rdieter@fedoraproject.org> 2.8.2-3
- fix dep on marble-part (no epoch)

* Wed May 07 2014 Rex Dieter <rdieter@fedoraproject.org> 2.8.2-2
- okular-odpgenerator: Requires: okular-part
- reports-map-element: Requires: marble-part

* Wed Apr 16 2014 Rex Dieter <rdieter@fedoraproject.org> 2.8.2-1
- 2.8.2

* Fri Apr 04 2014 Rex Dieter <rdieter@fedoraproject.org> 2.8.1-3
- rebuild (okular)

* Sat Mar 29 2014 Rex Dieter <rdieter@fedoraproject.org> 2.8.1-2
- respin tarball (omitting typo)

* Tue Mar 25 2014 Rex Dieter <rdieter@fedoraproject.org> 2.8.1-1
- 2.8.1

* Thu Mar 20 2014 Rex Dieter <rdieter@fedoraproject.org> 2.8.0-2
- rebuild (kde-4.13)

* Sun Mar 02 2014 Rex Dieter <rdieter@fedoraproject.org> 2.8.0-1
- 2.8.0

* Wed Feb 12 2014 Rex Dieter <rdieter@fedoraproject.org> 2.7.92-2
- rebuild (libicu)

* Sun Feb 09 2014 Rex Dieter <rdieter@fedoraproject.org> 2.7.92-1
- 2.7.92

* Mon Jan 13 2014 Rex Dieter <rdieter@fedoraproject.org> 2.7.91-1
- 2.7.91
- BR: +libodfgen-devel -OpenGTL-devel

* Mon Dec 16 2013 Rex Dieter <rdieter@fedoraproject.org> 2.7.90-3
- krita: fix handling of unversioned libkritasketchlib.so

* Sun Dec 15 2013 Rex Dieter <rdieter@fedoraproject.org> 2.7.90-2
- enable use of libpqxx-4.x

* Fri Dec 13 2013 Rex Dieter <rdieter@fedoraproject.org> 2.7.90-1
- 2.7.90

* Tue Dec 03 2013 Rex Dieter <rdieter@fedoraproject.org> - 2.7.5-2
- rebuild (exiv2)

* Wed Nov 27 2013 Rex Dieter <rdieter@fedoraproject.org> 2.7.5-1
- calligra-2.7.5

* Mon Nov 18 2013 Dave Airlie <airlied@redhat.com> - 2.7.4-3
- rebuilt for GLEW 1.10

* Sat Nov 16 2013 Rex Dieter <rdieter@fedoraproject.org> 2.7.4-2
- rebuild (kde-4.12)

* Sat Oct 12 2013 Rex Dieter <rdieter@fedoraproject.org> 2.7.4-1
- calligra-2.7.4

* Fri Sep 20 2013 Rex Dieter <rdieter@fedoraproject.org> 2.7.3-1
- calligra-2.7.3 (#951003)

* Sun Sep 08 2013 Rex Dieter <rdieter@fedoraproject.org> 2.7.2-3
- rebuild (openexr)

* Thu Sep 05 2013 Rex Dieter <rdieter@fedoraproject.org> 2.7.2-2
- rebuild (for libkdcraw-4.11.x)

* Fri Aug 23 2013 Rex Dieter <rdieter@fedoraproject.org> 2.7.2-1
- calligra-2.7.2 (#951003)

* Mon Aug 19 2013 Marek Kasik <mkasik@redhat.com> 2.7.1-2
- Rebuild (poppler-0.24.0)

* Wed Jul 31 2013 Rex Dieter <rdieter@fedoraproject.org> 2.7.1-1
- 2.7.1

* Tue Jul 30 2013 Petr Machata <pmachata@redhat.com> - 2.7.0-3
- Rebuild for boost 1.54.0

* Sat Jul 20 2013 Rex Dieter <rdieter@fedoraproject.org> 2.7.0-2
- fix arm FTBFS (qreal_double.patch courtesy of kubuntu)

* Fri Jul 19 2013 Rex Dieter <rdieter@fedoraproject.org> 2.7.0-1
- 2.7.0

* Sat Jun 29 2013 Rex Dieter <rdieter@fedoraproject.org> 2.6.92-1
- 2.6.92

* Mon Jun 24 2013 Marek Kasik <mkasik@redhat.com> 2.6.4-2
- Rebuild (poppler-0.22.5)

* Thu May 30 2013 Rex Dieter <rdieter@fedoraproject.org> 2.6.4-1
- 2.6.4 (#951003)

* Thu Apr 11 2013 Rex Dieter <rdieter@fedoraproject.org> 2.6.3-1
- 2.6.3

* Tue Mar 26 2013 Rex Dieter <rdieter@fedoraproject.org> 2.6.2-4
- explicitly omit bundled Arev fonts

* Sat Mar 23 2013 Rex Dieter <rdieter@fedoraproject.org> 2.6.2-3
- cannot display formulas (kde#317195)

* Mon Mar 18 2013 Rex Dieter <rdieter@fedoraproject.org> 2.6.2-2
- rebuild (OpenGTL)

* Mon Mar 11 2013 Rex Dieter <rdieter@fedoraproject.org> 2.6.2-1
- 2.6.2

* Sun Mar 10 2013 Rex Dieter <rdieter@fedoraproject.org> - 2.6.1-3
- rebuild (OpenEXR)

* Mon Mar 04 2013 Rex Dieter <rdieter@fedoraproject.org> 2.6.1-2.1
- rebuild (f18/marble)

* Tue Feb 19 2013 Rex Dieter <rdieter@fedoraproject.org> 2.6.1-2
- rebuild (OpenGTL/llvm)

* Mon Feb 18 2013 Rex Dieter <rdieter@fedoraproject.org> 2.6.1-1
- 2.6.1

* Mon Feb 04 2013 Rex Dieter <rdieter@fedoraproject.org> 2.6.0-1
- 2.6.0

* Sat Jan 26 2013 Rex Dieter <rdieter@fedoraproject.org> 2.5.93-4
- rebuild (icu)

* Fri Jan 18 2013 Adam Tkac <atkac redhat com> - 2.5.93-3
- rebuild due to "jpeg8-ABI" feature drop

* Fri Jan 18 2013 Marek Kasik <mkasik@redhat.com> 2.5.93-2
- Rebuild (poppler-0.22.0)

* Sat Jan 05 2013 Rex Dieter <rdieter@fedoraproject.org> 2.5.93-1
- 2.5.93

* Thu Dec 13 2012 Adam Jackson <ajax@redhat.com> - 2.5.92-3
- Rebuild for glew 1.9.0

* Tue Dec 04 2012 Rex Dieter <rdieter@fedoraproject.org> 2.5.92-2
- rebuild (marble)

* Wed Nov 28 2012 Rex Dieter <rdieter@fedoraproject.org> 2.5.92-1
- 2.5.92

* Wed Oct 24 2012 Rex Dieter <rdieter@fedoraproject.org> 2.5.91-1
- 2.5.91

* Mon Oct 08 2012 Rex Dieter <rdieter@fedoraproject.org> 2.5.3-1
- 2.5.3

* Sat Sep 08 2012 Rex Dieter <rdieter@fedoraproject.org> 2.5.2-1
- 2.5.2

* Wed Aug 29 2012 Rex Dieter <rdieter@fedoraproject.org> 2.5.1-1
- 2.5.1

* Sun Aug 26 2012 Rex Dieter <rdieter@fedoraproject.org> 2.5.0-3
- calligra is FTBFS on ARM, qreal = float (bug #851851)

* Tue Aug 07 2012 Rex Dieter <rdieter@fedoraproject.org> 2.5.0-2
- respin

* Sat Aug 04 2012 Rex Dieter <rdieter@fedoraproject.org> 2.5.0-1
- 2.5.0

* Fri Jul 27 2012 Rex Dieter <rdieter@fedoraproject.org> 2.4.92-4
- rebuild (glew)

* Thu Jul 19 2012 Dan Horák <dan[at]danny.cz> 2.4.92-3
- OpenGTL is missing on s390(x)

* Wed Jul 18 2012 Rex Dieter <rdieter@fedoraproject.org> 2.4.92-2
- BR: libvisio-devel

* Sat Jul 14 2012 Rex Dieter <rdieter@fedoraproject.org> 2.4.92-1
- calligra-2.4.92

* Mon Jul  2 2012 Marek Kasik <mkasik@redhat.com> - 2.4.91-3
- Rebuild (poppler-0.20.1)

* Sun Jun 17 2012 Rex Dieter <rdieter@fedoraproject.org> 2.4.91-2
- tarball respin

* Fri Jun 15 2012 Rex Dieter <rdieter@fedoraproject.org> 2.4.91-1
- calligra-2.4.91

* Wed Jun 06 2012 Rex Dieter <rdieter@fedoraproject.org> 2.4.90-2
- fix kexi-map-form-widget Requires/Obsoletes logic

* Tue May 29 2012 Jaroslav Reznik <jreznik@redhat.com> 2.4.90-1
- calligra-2.4.90

* Sat May 26 2012 Rex Dieter <rdieter@fedoraproject.org> 2.4.2-1
- calligra-2.4.2

* Wed May 16 2012 Marek Kasik <mkasik@redhat.com> - 2.4.1-4
- Rebuild (poppler-0.20.0)

* Mon May 07 2012 Rex Dieter <rdieter@fedoraproject.org> 2.4.1-3
- segfault when opening a new doc / new from template (#819371)

* Wed May 02 2012 Rex Dieter <rdieter@fedoraproject.org> - 2.4.1-2
- rebuild (exiv2)

* Sat Apr 21 2012 Rex Dieter <rdieter@fedoraproject.org> 2.4.1-1
- 2.4.1

* Fri Apr 20 2012 Rex Dieter <rdieter@fedoraproject.org> 2.4.0-4
- manifest file corrupted (#814643, kde#298134)

* Mon Apr 16 2012 Rex Dieter <rdieter@fedoraproject.org> 2.4.0-3
- -sheets: Provides: -tables

* Sun Apr 08 2012 Rex Dieter <rdieter@fedoraproject.org> 2.4.0-2
- -core/-libs: tighten subpkg deps

* Sat Apr 07 2012 Rex Dieter <rdieter@fedoraproject.org> 2.4.0-1
- 2.4.0
- Obsoletes: -map-shape (dropped since rc2)

* Sat Mar 17 2012 Rex Dieter <rdieter@fedoraproject.org> 2.3.92-1
- 2.3.92 (2.4rc2)
- rename -tables => -sheets

* Sat Mar 03 2012 Rex Dieter <rdieter@fedoraproject.org> 2.3.91-1
- 2.3.91 (2.4rc1)

* Sat Feb 11 2012 Rex Dieter <rdieter@fedoraproject.org> 2.3.87-4
- upstream krita_fitscreen patch (#788327)

* Wed Feb 08 2012 Rex Dieter <rdieter@fedoraproject.org> 2.3.87-3
- -braindump: move stateshape here

* Tue Jan 31 2012 Rex Dieter <rdieter@fedoraproject.org> 2.3.87-2
- -kexi: fix error in %%postun scriptlet

* Sat Jan 28 2012 Rex Dieter <rdieter@fedoraproject.org> 2.3.87-1
- 2.3.87

* Thu Jan 12 2012 Rex Dieter <rdieter@fedoraproject.org> 2.3.86-3
- %%build: -DBUILD_cstester:BOOL=OFF
- drop -filters

* Thu Jan 12 2012 Rex Dieter <rdieter@fedoraproject.org> 2.3.86-2
- rename kexi-driver-pgsql -> kexi-driver-postgresql
- kexi-driver-sybase subpkg
- kexi-map-form-widget, map-shape, reports-map-elemement subpkgs (with marble deps)

* Tue Jan 10 2012 Rex Dieter <rdieter@fedoraproject.org> 2.3.86-1
- 2.3.86
- License: +LGPLv2+
- drop Obsoletes: koffice-kivio

* Thu Aug 18 2011 Rex Dieter <rdieter@fedoraproject.org> 2.3.74-2
- fix Obsoletes: -kformula

* Mon Aug 15 2011 Rex Dieter <rdieter@fedoraproject.org> 2.3.74-1
- 2.3.74
- kformula dropped (upstream)

* Fri Jun 17 2011 Rex Dieter <rdieter@fedoraproject.org> 2.3.72-2
- fix URL
- Obsoletes: koffice < 3:2.3.70

* Thu Jun 16 2011 Rex Dieter <rdieter@fedoraproject.org> 2.3.72-1
- 2.3.72 (first try)

