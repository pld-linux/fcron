Summary:	A periodical command scheduler which aims at replacing Vixie Cron
Summary(pl):	Serwer okresowego uruchamiania poleceñ zastêpuj±cy Vixie Crona
Name:		fcron
Version:	2.9.5.1
Release:	1
License:	GPL
Group:		Daemons
Source0:	http://fcron.free.fr/archives/%{name}-%{version}.src.tar.gz
# Source0-md5:	bf39dcef6d0c452f167f5a31a1231e4e
Source1:	%{name}.init
Source2:	cron.logrotate
Source3:	cron.sysconfig
Source4:	%{name}.crontab
Source5:	%{name}.pam
Source6:	%{name}.conf
Source7:	fcrontab.pam	
Source8:	%{name}.systab
Patch0:		%{name}-mail_output_only_if_there_is_output.patch
URL:		http://fcron.free.fr/
BuildRequires:	libselinux-devel
BuildRequires:	pam-devel
BuildRequires:	rpmbuild(macros) >= 1.159
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
Provides:	group(crontab)
Obsoletes:	crontabs
Obsoletes:	hc-cron
Obsoletes:	mcron
Obsoletes:	vixie-cron
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%description
Fcron is a periodical command scheduler which aims at replacing Vixie
Cron, so it implements most of its functionalities. But fcron does not
assume that your system is running neither all the time nor regularly:
you can, for instance, tell fcron to execute tasks every x hours y
minutes of system up time or to do a job only once in a specified
interval of time. You can also set a nice value to a job, run it
depending on the system load average and much more !

%description -l pl
Fcron jest serwerem okresowego uruchamiania poleceñ maj±cym za cel
zast±pienie Vixie Crona, posiadaj±cym zaimplementowane wiêkszo¶æ
spo¶ród jego funkcji. Jednak¿e fcron nie zak³ada, ¿e system dzia³a
ca³y czas, ani ¿e jest uruchamiany regularnie: mo¿na, na przyk³ad,
kazaæ fcronowi uruchamiaæ zadanie co ka¿de x godzin y minut od
uruchomienia systemu lub wykonywaæ zadanie dok³adnie raz w podanym
okresie czasu. Umo¿liwia równie¿ ustawianie warto¶ci nice dla zadania,
uruchamianie go w zale¿no¶ci od obci±¿enia systemu i du¿o wiêcej.

%prep
%setup -q
%patch0 -p1

%build
%configure \
	--with-sysfcrontab=systab \
	--with-spooldir=%{_var}/spool/cron \
	--with-run-non-privileged=no \
	--with-boot-install=no \
	--with-fcrondyn=yes \
	--with-username=crontab \
	--with-groupname=crontab \
	--with-pam=yes \
	--with-selinux=yes \
	--with-boot-install=no

%{__make} OPTION="%{rpmcflags}"

echo "#!/bin/sh" > script/user-group

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT{/var/{log,spool/cron},%{_mandir}} \
	$RPM_BUILD_ROOT/etc/{rc.d/init.d,logrotate.d,sysconfig} \
	$RPM_BUILD_ROOT%{_sysconfdir}/{cron,cron.{d,hourly,daily,weekly,monthly},pam.d}

%{__make} install \
	DESTDIR=$RPM_BUILD_ROOT \
	DESTSBIN=$RPM_BUILD_ROOT%{_sbindir} \
	DESTBIN=$RPM_BUILD_ROOT%{_bindir} \
	DESTMAN=$RPM_BUILD_ROOT%{_mandir} \
	ROOTNAME=$(id -u) \
	ROOTGROUP=$(id -g) \
	USERNAME=$(id -u) \
	GROUPNAME=$(id -g)

#fix premission for rpmbuild
chmod +rw $RPM_BUILD_ROOT/usr/*bin/*

ln -sf %{_bindir}/fcrontab $RPM_BUILD_ROOT%{_bindir}/crontab
mv -f $RPM_BUILD_ROOT%{_sbindir}/fcron $RPM_BUILD_ROOT%{_sbindir}/crond

install %{SOURCE1} $RPM_BUILD_ROOT/etc/rc.d/init.d/crond
install %{SOURCE2} $RPM_BUILD_ROOT/etc/logrotate.d/cron
install %{SOURCE3} $RPM_BUILD_ROOT/etc/sysconfig/cron
install %{SOURCE4} $RPM_BUILD_ROOT/etc/cron.d/crontab
install %{SOURCE5} $RPM_BUILD_ROOT/etc/pam.d/fcron
install %{SOURCE6} $RPM_BUILD_ROOT/etc/fcron.conf
install %{SOURCE7} $RPM_BUILD_ROOT/etc/pam.d/fcrontab
install %{SOURCE8} $RPM_BUILD_ROOT/etc/cron.hourly/fcron.systab

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

if [ -n "`/bin/id -u crontab 2>/dev/null`" ]; then
	if [ "`/bin/id -u crontab`" != "134" ]; then
		echo "Error: user crontab doesn't have uid=134. Correct this before installing %{name}." 1>&2
		exit 1
	fi
else
        /usr/sbin/useradd -u 134 -r -d /var/spool/cron -s /bin/false -c "crontab User" -g crontab crontab 1>&2
fi

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

rm -f /var/spool/cron/systab*

FIND=`find /var/spool/cron -name \*.orig`
for FILE in $FIND; do
	BASENAME=`basename $FILE`
	USER="`echo "$BASENAME"| sed 's/.orig//'`"
	mv -f $FILE /var/spool/cron/$USER >/dev/null 2>&1
	chown $USER:crontab /var/spool/cron/$USER >/dev/null 2>&1
	chmod 600 /var/spool/cron/$USER >/dev/null 2>&1
done
rm -f /var/spool/cron/rm\.*
rm -f /var/spool/cron/fcrontab.sig
rm -f /var/spool/cron/new\.*
fi

%postun
if [ "$1" = "0" ]; then
	%userremove crontab
	%groupremove crontab
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
%doc  doc/HTML doc/olddoc/{FAQ,CHANGES,README,THANKS,TODO}
%attr(0750,root,crontab) %dir %{_sysconfdir}/cron*
%attr(0750,root,root) %{_sysconfdir}/cron.hourly/%{name}.systab
%attr(0640,root,crontab) %config(noreplace) /etc/cron.d/crontab
%attr(0640,root,crontab) %config(noreplace,missingok) %verify(not md5 mtime size) %{_sysconfdir}/cron/cron.allow
%attr(0640,root,crontab) %config(noreplace,missingok) %verify(not md5 mtime size) %{_sysconfdir}/cron/cron.deny
%attr(0640,root,root) %config(noreplace) %verify(not md5 mtime size) /etc/sysconfig/cron
%attr(0644,root,crontab) %config(noreplace) %verify(not md5 size mtime) /etc/pam.d/fcron
%attr(0644,root,crontab) %config(noreplace) %verify(not md5 size mtime) /etc/pam.d/fcrontab
%attr(0754,root,root) /etc/rc.d/init.d/crond
%config(noreplace) %verify(not md5 size mtime) %attr(640,root,root) /etc/logrotate.d/cron
%attr(0640,root,crontab) %config(noreplace) /etc/fcron.conf
%attr(0755,root,root) %{_sbindir}/crond
%attr(6111,crontab,crontab) %{_bindir}/fcrontab
%attr(6111,crontab,crontab) %{_bindir}/crontab
%attr(4711,root,root) %{_bindir}/fcronsighup
%attr(6111,crontab,crontab) %{_bindir}/fcrondyn
%{_mandir}/man1/fcrondyn.1.*
%{_mandir}/man1/fcrontab.1.*
%{_mandir}/man5/fcron.conf.5*
%{_mandir}/man5/fcrontab.5*
%{_mandir}/man8/fcron.8*
%attr(1730,root,crontab) /var/spool/cron
%attr(0660,root,crontab) %ghost /var/log/cron
