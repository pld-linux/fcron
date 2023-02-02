# TODO
# - use libbsd-devel? (bitstring at least?)
Summary:	A periodical command scheduler which aims at replacing Vixie Cron
Summary(pl.UTF-8):	Serwer okresowego uruchamiania poleceń zastępujący Vixie Crona
Name:		fcron
Version:	3.1.2
Release:	10
License:	GPL v2+
Group:		Daemons
Source0:	http://fcron.free.fr/archives/%{name}-%{version}.src.tar.gz
# Source0-md5:	36bf213e15f3a480f2274f8e46cced0a
Source1:	%{name}.init
Source3:	cron.sysconfig
Source4:	%{name}.crontab
Source5:	%{name}.pam
Source6:	%{name}.conf
Source7:	%{name}tab.pam
Source8:	%{name}.systab
Patch0:		%{name}-sendmail.patch
Patch1:		%{name}-Makefile.patch
Patch2:		%{name}-accept_readable_fcron.conf.patch
URL:		http://fcron.free.fr/
# configure tests -x (check can be removed, just like sendmail)
BuildRequires:	/bin/vi
BuildRequires:	autoconf
BuildRequires:	automake
BuildRequires:	libselinux-devel
BuildRequires:	pam-devel
BuildRequires:	rpmbuild(macros) >= 1.268
Requires(post):	fileutils
Requires(post,preun):	/sbin/chkconfig
Requires(postun):	/usr/sbin/groupdel
Requires(pre):	/bin/id
Requires(pre):	/usr/bin/getgid
Requires(pre):	/usr/sbin/groupadd
Requires(pre):	/usr/sbin/useradd
Requires:	/bin/run-parts
Requires:	psmisc >= 20.1
Requires:	rc-scripts
Provides:	crondaemon
Provides:	cronjobs
Provides:	crontabs = 1.7
Provides:	group(crontab)
Obsoletes:	crondaemon
Obsoletes:	cronjobs
Obsoletes:	crontabs
Conflicts:	sysklogd < 1.5.1-2
Conflicts:	syslog-ng < 3.6.4-3
Conflicts:	rsyslog < 5.10.1-4
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%description
Fcron is a periodical command scheduler which aims at replacing Vixie
Cron, so it implements most of its functionalities. But fcron does not
assume that your system is running neither all the time nor regularly:
you can, for instance, tell fcron to execute tasks every x hours y
minutes of system up time or to do a job only once in a specified
interval of time. You can also set a nice value to a job, run it
depending on the system load average and much more !

%description -l pl.UTF-8
Fcron jest serwerem okresowego uruchamiania poleceń mającym za cel
zastąpienie Vixie Crona, posiadającym zaimplementowane większość
spośród jego funkcji. Jednakże fcron nie zakłada, że system działa
cały czas, ani że jest uruchamiany regularnie: można, na przykład,
kazać fcronowi uruchamiać zadanie co każde x godzin y minut od
uruchomienia systemu lub wykonywać zadanie dokładnie raz w podanym
okresie czasu. Umożliwia również ustawianie wartości nice dla zadania,
uruchamianie go w zależności od obciążenia systemu i dużo więcej.

%prep
%setup -q
%patch0 -p1
%patch1 -p1
%patch2 -p0

%build
%{__aclocal}
%{__autoconf}
%configure \
	--with-sendmail=/usr/sbin/sendmail \
	--with-sysfcrontab=systab \
	--with-spooldir=%{_var}/spool/cron \
	--with-run-non-privileged=no \
	--with-boot-install=no \
	--with-fcrondyn=yes \
	--with-username=crontab \
	--with-groupname=crontab \
	--with-pam=yes \
	--with-selinux=yes \
	--with-boot-install=no \
	--with-editor=/bin/vi

%{__make} \
	OPTION="%{rpmcflags}"

echo "#!/bin/sh" > script/user-group

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT{/var/{log,spool/cron},%{_mandir}} \
	$RPM_BUILD_ROOT/etc/{rc.d/init.d,logrotate.d,sysconfig} \
	$RPM_BUILD_ROOT%{_sysconfdir}/{cron,cron.{d,hourly,daily,weekly,monthly},pam.d}

%{__make} install-staged \
	DESTDIR=$RPM_BUILD_ROOT \
	ROOTNAME=$(id -u) \
	ROOTGROUP=$(id -g) \
	USERNAME=$(id -u) \
	GROUPNAME=$(id -g)

#fix premission for rpmbuild
chmod +rw $RPM_BUILD_ROOT%{_prefix}/*bin/*

ln -sf %{_bindir}/fcrontab $RPM_BUILD_ROOT%{_bindir}/crontab
mv -f $RPM_BUILD_ROOT%{_sbindir}/fcron $RPM_BUILD_ROOT%{_sbindir}/crond

install %{SOURCE1} $RPM_BUILD_ROOT/etc/rc.d/init.d/crond
install %{SOURCE3} $RPM_BUILD_ROOT/etc/sysconfig/cron
install %{SOURCE4} $RPM_BUILD_ROOT/etc/cron.d/crontab
install %{SOURCE5} $RPM_BUILD_ROOT/etc/pam.d/fcron
install %{SOURCE6} $RPM_BUILD_ROOT%{_sysconfdir}/fcron.conf
install %{SOURCE7} $RPM_BUILD_ROOT/etc/pam.d/fcrontab
install %{SOURCE8} $RPM_BUILD_ROOT/etc/cron.hourly/fcron.systab

cat > $RPM_BUILD_ROOT%{_sysconfdir}/cron/cron.allow << 'EOF'
# cron.allow	This file describes the names of the users which are
#		allowed to use the local cron daemon
root
EOF

cat > $RPM_BUILD_ROOT%{_sysconfdir}/cron/cron.deny << 'EOF'
# cron.deny	This file describes the names of the users which are
#		NOT allowed to use the local cron daemon
EOF

%{__rm} -r $RPM_BUILD_ROOT%{_docdir}/%{name}-%{version}

# conflicts with libbsd-devel-0.7.0-2.x86_64
%{__rm} $RPM_BUILD_ROOT/usr/share/man/man3/bitstring.3*

%clean
rm -rf $RPM_BUILD_ROOT

%pre
%groupadd -g 117 -r -f crontab
%useradd -u 134 -r -d /var/spool/cron -s /bin/false -c "crontab User" -g crontab crontab

%post
if [ "$1" = "1" ]; then
	if [ -d /var/spool/cron ]; then
		FIND=`find /var/spool/cron -type f`
		for FILE in $FIND; do
			mv -f $FILE $FILE.orig
			USER=`basename $FILE`
			chown crontab:crontab $FILE.orig
			chmod 640 $FILE.orig
			(test ! -z "$USER" && fcrontab -u $USER -z) > /dev/null 2>&1
		done
		if [ -f /var/spool/cron/root.orig ]; then
			chmod 600 /var/spool/cron/root.orig
			chown root:root /var/spool/cron/root.orig
		fi
	fi
fi

if [ "$1" = "2" ]; then
	FIND=`find /var/spool/cron -name \*.orig`
	for FILE in $FIND; do
		BASENAME=`basename $FILE`
		USER=`echo "$BASENAME"| sed 's/.orig//'`
		[ ! -z "$USER" ] && fcrontab -u $USER -z > /dev/null 2>&1
	done
fi

/sbin/chkconfig --add crond
%service crond restart "Cron Daemon"

%preun
if [ "$1" = "0" ]; then
	%service crond stop
	/sbin/chkconfig --del crond

	rm -f /var/spool/cron/systab*

	FIND=`find /var/spool/cron -name '*.orig'`
	for FILE in $FIND; do
		BASENAME=`basename $FILE`
		USER="${BASENAME%.orig}"
		mv -f $FILE /var/spool/cron/$USER >/dev/null 2>&1
		chown $USER:crontab /var/spool/cron/$USER >/dev/null 2>&1
		chmod 600 /var/spool/cron/$USER >/dev/null 2>&1
	done
	rm -f /var/spool/cron/rm.*
	rm -f /var/spool/cron/fcrontab.sig
	rm -f /var/spool/cron/new.*
fi

%postun
if [ "$1" = "0" ]; then
	%userremove crontab
	%groupremove crontab
fi

%triggerun -- hc-cron,vixie-cron,cronie
# Prevent preun from crond from working
chmod a-x /etc/rc.d/init.d/crond

%triggerpostun -- hc-cron,vixie-cron,cronie
# Restore what triggerun removed
chmod 754 /etc/rc.d/init.d/crond
# reinstall crond init.d links, which could be different
/sbin/chkconfig --del crond
/sbin/chkconfig --add crond

%files
%defattr(644,root,root,755)
%doc doc/en/HTML doc/en/txt/{faq.txt,changes.txt,readme.txt,thanks.txt,todo.txt}
%attr(750,root,crontab) %dir %{_sysconfdir}/cron*
%attr(750,root,root) %{_sysconfdir}/cron.hourly/%{name}.systab
%attr(640,root,crontab) %config(noreplace) /etc/cron.d/crontab
%attr(640,root,crontab) %config(noreplace,missingok) %verify(not md5 mtime size) %{_sysconfdir}/cron/cron.allow
%attr(640,root,crontab) %config(noreplace,missingok) %verify(not md5 mtime size) %{_sysconfdir}/cron/cron.deny
%attr(640,root,root) %config(noreplace) %verify(not md5 mtime size) /etc/sysconfig/cron
%attr(644,root,crontab) %config(noreplace) %verify(not md5 mtime size) /etc/pam.d/fcron
%attr(644,root,crontab) %config(noreplace) %verify(not md5 mtime size) /etc/pam.d/fcrontab
%attr(754,root,root) /etc/rc.d/init.d/crond
%config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/fcron.allow
%config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/fcron.deny
%attr(640,root,crontab) %config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/fcron.conf
%attr(755,root,root) %{_sbindir}/crond
%attr(6111,crontab,crontab) %{_bindir}/fcrontab
%attr(6111,crontab,crontab) %{_bindir}/crontab
%attr(4711,root,root) %{_bindir}/fcronsighup
%attr(6111,crontab,crontab) %{_bindir}/fcrondyn
%{_mandir}/man1/fcrondyn.1*
%{_mandir}/man1/fcrontab.1*
%{_mandir}/man5/fcron.conf.5*
%{_mandir}/man5/fcrontab.5*
%{_mandir}/man8/fcron.8*
%lang(fr) %{_mandir}/fr/man1/fcrondyn.1*
%lang(fr) %{_mandir}/fr/man1/fcrontab.1*
%lang(fr) %{_mandir}/fr/man5/fcron.conf.5*
%lang(fr) %{_mandir}/fr/man5/fcrontab.5*
%lang(fr) %{_mandir}/fr/man8/fcron.8*
%attr(1730,root,crontab) /var/spool/cron
