Name: cfitsio
Version: 4.6.3
Release: %autorelease
Summary: Library for manipulating FITS data files

License: CFITSIO
URL: https://heasarc.gsfc.nasa.gov/fitsio/
Source: https://heasarc.gsfc.nasa.gov/FTP/software/fitsio/c/cfitsio-%{version}.tar.gz
# Remove soname version check
Patch: cfitsio-noversioncheck.patch

BuildRequires: gcc-gfortran
BuildRequires: make
BuildRequires: zlib-devel
BuildRequires: bzip2-devel
BuildRequires: curl-devel

%description
CFITSIO is a library of C and FORTRAN subroutines for reading and writing 
data files in FITS (Flexible Image Transport System) data format. CFITSIO 
simplifies the task of writing software that deals with FITS files by 
providing an easy to use set of high-level routines that insulate the 
programmer from the internal complexities of the FITS file format. At the 
same time, CFITSIO provides many advanced features that have made it the 
most widely used FITS file programming interface in the astronomical 
community.

%package devel
Summary: Headers required when building programs against cfitsio
Requires: %{name} = %{version}-%{release}
Requires: pkgconfig

%description devel
Headers required when building a program against the cfitsio library.

%package static
Summary: Static cfitsio library

%description static
Static cfitsio library; avoid use if possible.

%package docs
Summary: Documentation for cfitsio
BuildArch:  noarch

%description docs
Stand-alone documentation for cfitsio.

%package utils
Summary: CFITSIO based utilities
Requires: %{name} = %{version}-%{release}
Provides: fpack{?_isa} = %{version}-%{release}
Obsoletes: fpack <= 4.5.0-1  
Provides: fitsverify{?_isa} = 4.22-5
Obsoletes: fitsverify <= 4.22-4

%description utils
This package contains utility programas provided by CFITSIO

%prep
%autosetup -p1

%build
%configure --enable-reentrant --with-bzip2 --includedir=%{_includedir}/%{name}
make %{?_smp_mflags}

%check
make testprog
LD_LIBRARY_PATH=. ./testprog > testprog.lis
cmp -s testprog.lis testprog.out
cmp -s testprog.fit testprog.std

%install
make DESTDIR=%{buildroot} install
#
rm %{buildroot}/%{_bindir}/cookbook
rm %{buildroot}/%{_bindir}/smem
rm %{buildroot}/%{_bindir}/speed

%ldconfig_scriptlets

%files
%doc README.md ChangeLog
%license licenses/License.txt
%{_libdir}/libcfitsio.so.10*

%files devel
%doc utilities/cookbook.*
%{_includedir}/%{name}
%{_libdir}/libcfitsio.so
%{_libdir}/pkgconfig/cfitsio.pc

%files static
%license licenses/License.txt
%{_libdir}/libcfitsio.a

%files docs
%doc docs/fitsio.pdf docs/cfitsio.pdf
%license licenses/License.txt

%files utils
%doc docs/fpackguide.pdf
%license licenses/License.txt
%{_bindir}/fitsverify
%{_bindir}/fitscopy
%{_bindir}/fpack
%{_bindir}/funpack
%{_bindir}/imcopy

%changelog
%autochangelog
