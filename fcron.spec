Summary:	A periodical command scheduler which aims at replacing Vixie Cron
Name:		fcron
Version:	2.9.4
Release:	1
License:	GPL
Group:		Daemons
Source0:	http://fcron.free.fr/%{name}-%{version}.src.tar.gz
# Source0-md5:	4bfcff1002a7231f374591511bacadb2
Source1:	%{name}.init
Source2:	cron.logrotate
Source3:	cron.sysconfig
Source4:	%{name}.crontab
Source5:	%{name}.pam
PreReq:		rc-scripts
Requires(pre):	/usr/bin/getgid
Requires(pre):	/usr/sbin/groupadd
Requires(post,preun):	/sbin/chkconfig
Requires(post):	fileutils
Requires(postun):	/usr/sbin/groupdel
Requires:	/bin/run-parts
Requires:	psmisc >= 20.1
Provides:	crontabs >= 1.7
Provides:	crondaemon
Obsoletes:	crontabs
Obsoletes:	crondaemon
Obsoletes:	hc-cron
BuildRequires:	pam-devel
BuildRequires:	libselinux-devel
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%description
Fcron is a periodical command scheduler which aims at replacing Vixie
Cron, so it implements most of its functionalities. But fcron does not
assume that your system is running neither all the time nor regularly
: you can, for instance, tell fcron to execute tasks every x hours y
minutes of system up time or to do a job only once in a specified
interval of time. You can also set a nice value to a job, run it
depending on the system load average and much more !

%prep
%setup -q

%build
%configure \
	--with-spooldir=%{_var}/spool/cron \
	--with-run-non-privileged=no \
	--with-boot-install=no \
	--with-fcrondyn=yes \
	--with-username=crontab \
	--with-groupname=crontab \
	--with-pam=yes \
	--with-selinux=yes
	
%{__make}

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT{/var/{log,spool/cron},%{_mandir}} \
	$RPM_BUILD_ROOT/etc/{rc.d/init.d,logrotate.d,sysconfig} \
	$RPM_BUILD_ROOT%{_sysconfdir}/{cron,cron.{d,hourly,daily,weekly,monthly},pam.d}

%{__make} install \
	DESTDIR=$RPM_BUILD_ROOT \
	DESTMAN=$RPM_BUILD_ROOT%{_mandir}

install %{SOURCE1} $RPM_BUILD_ROOT/etc/rc.d/init.d/crond
install %{SOURCE2} $RPM_BUILD_ROOT/etc/logrotate.d/cron
install %{SOURCE3} $RPM_BUILD_ROOT/etc/sysconfig/cron
install %{SOURCE4} $RPM_BUILD_ROOT/etc/cron.d/crontab
install %{SOURCE6} $RPM_BUILD_ROOT/etc/pam.d/cron

for a in fi fr id ja ko pl ; do
	if test -f $a/man1/crontab.1 ; then
		install -d $RPM_BUILD_ROOT%{_mandir}/$a/man1
		install $a/man1/crontab.1 $RPM_BUILD_ROOT%{_mandir}/$a/man1
	fi
	if test -f $a/man5/crontab.5 ; then
		install -d $RPM_BUILD_ROOT%{_mandir}/$a/man5
		install $a/man5/crontab.5 $RPM_BUILD_ROOT%{_mandir}/$a/man5
	fi
	if test -f $a/man8/cron.8 ; then
		install -d $RPM_BUILD_ROOT%{_mandir}/$a/man8
		install $a/man8/cron.8 $RPM_BUILD_ROOT%{_mandir}/$a/man8
		echo .so cron.8 > $RPM_BUILD_ROOT%{_mandir}/$a/man8/crond.8
	fi
done

touch $RPM_BUILD_ROOT/var/log/cron

cat > $RPM_BUILD_ROOT%{_sysconfdir}/cron/cron.allow << EOF
# cron.allow   This file describes the names of the users which are
#               allowed to use the local cron daemon
root
EOF

cat > $RPM_BUILD_ROOT%{_sysconfdir}/cron/cron.deny << EOF2
# cron.deny    This file describes the names of the users which are
#               NOT allowed to use the local cron daemon
EOF2

%clean
rm -rf $RPM_BUILD_ROOT

%pre
if [ -n "`/usr/bin/getgid crontab`" ]; then
	if [ "`/usr/bin/getgid crontab`" != "117" ]; then
		echo "Error: group crontab doesn't have gid=117. Correct this before installing cron." 1>&2
		exit 1
	fi
else
	echo "Adding group crontab GID=117."
	/usr/sbin/groupadd -g 117 -r -f crontab
fi

%post
/sbin/chkconfig --add crond
if [ -f /var/lock/subsys/crond ]; then
	/etc/rc.d/init.d/crond restart >&2
else
	echo "Run \"/etc/rc.d/init.d/crond start\" to start cron daemon."
fi
umask 027
touch /var/log/cron
chgrp crontab /var/log/cron
chmod 660 /var/log/cron

%preun
if [ "$1" = "0" ]; then
	if [ -f /var/lock/subsys/crond ]; then
		/etc/rc.d/init.d/crond stop >&2
	fi
	/sbin/chkconfig --del crond
fi

%postun
if [ "$1" = "0" ]; then
	echo "Removing group crontab."
	/usr/sbin/groupdel crontab
fi

%triggerpostun -- vixie-cron <= 3.0.1-85
for i in `/bin/ls /var/spool/cron 2>/dev/null`
do
	chown ${i} /var/spool/cron/${i} 2>/dev/null || :
done
/bin/chmod 660 /var/log/cron
/bin/chgrp crontab /var/log/cron
/bin/chmod 640 /etc/cron/cron.*
/bin/chgrp crontab /etc/cron/cron.*

%triggerpostun -- vixie-cron <= 3.0.1-73
if [ -f /etc/cron.d/cron.allow.rpmsave ]; then
	mv -f /etc/cron.d/cron.allow.rpmsave /etc/cron/cron.allow
fi
if [ -f /etc/cron.d/cron.allow ]; then
	mv -f /etc/cron.d/cron.allow /etc/cron/cron.allow
fi
if [ -f /etc/cron.d/cron.deny.rpmsave ]; then
	mv -f /etc/cron.d/cron.deny.rpmsave /etc/cron/cron.deny
fi
if [ -f /etc/cron.d/cron.deny ]; then
	mv -f /etc/cron.d/cron.deny /etc/cron/cron.deny
fi

%triggerpostun -- vixie-cron <= 3.0.1-70
if [ -f /etc/cron.allow ]; then
	mv -f /etc/cron.allow /etc/cron/cron.allow
fi
if [ -f /etc/cron.deny ]; then
	mv -f /etc/cron.deny /etc/cron/cron.deny
fi

%triggerpostun -- hc-cron
/sbin/chkconfig --del crond
/sbin/chkconfig --add crond

%triggerpostun -- hc-cron <= 0.14-12
for i in `/bin/ls /var/spool/cron 2>/dev/null`
do
	chown ${i} /var/spool/cron/${i} 2>/dev/null || :
done
/bin/chmod 660 /var/log/cron
/bin/chgrp crontab /var/log/cron
/bin/chmod 640 /etc/cron/cron.*
/bin/chgrp crontab /etc/cron/cron.*

%files
%defattr(644,root,root,755)
%doc CHANGES CONVERSION FEATURES MAIL README THANKS
%attr(0750,root,crontab) %dir %{_sysconfdir}/cron*
%attr(0644,root,crontab) %config(noreplace) /etc/cron.d/crontab
%attr(0640,root,crontab) %config(noreplace,missingok) %verify(not md5 mtime size) %{_sysconfdir}/cron/cron.allow
%attr(0640,root,crontab) %config(noreplace,missingok) %verify(not md5 mtime size) %{_sysconfdir}/cron/cron.deny
%attr(0640,root,root) %config(noreplace) %verify(not md5 mtime size) /etc/sysconfig/cron
%config(noreplace) %verify(not md5 size mtime) /etc/pam.d/cron
%attr(0754,root,root) /etc/rc.d/init.d/crond
%config /etc/logrotate.d/cron
%attr(0755,root,root) %{_sbindir}/crond
%attr(2755,root,crontab) %{_bindir}/crontab

%{_mandir}/man*/*
%lang(fi) %{_mandir}/fi/man*/*
%lang(fr) %{_mandir}/fr/man*/*
%lang(id) %{_mandir}/id/man*/*
%lang(ja) %{_mandir}/ja/man*/*
%lang(ko) %{_mandir}/ko/man*/*
%lang(pl) %{_mandir}/pl/man*/*

%attr(1730,root,crontab) /var/spool/cron
%attr(0660,root,crontab) %ghost /var/log/cron
