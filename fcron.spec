# TODO:
# - write missing files
Summary:	A periodical command scheduler which aims at replacing Vixie Cron
Summary(pl):	Serwer okresowego uruchamiania poleceñ zastepuj±cy Vixie Crona
Name:		fcron
Version:	2.9.5
Release:	0.1
License:	GPL
Group:		Daemons
Source0:	http://fcron.free.fr/archives/%{name}-%{version}.src.tar.gz
# Source0-md5:	73042f2666dff27444789d542bbcd607
Source1:	%{name}.init
Source2:	cron.logrotate
Source3:	cron.sysconfig
Source4:	%{name}.crontab
Source5:	%{name}.pam
Source6:	%{name}.conf
Source7:	fcrontab.pam	
URL:		http://fcron.free.fr/
#BuildRequires:	libselinux-devel
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
Obsoletes:	crondaemon
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

%build
%configure \
	--with-spooldir=%{_var}/spool/cron \
	--with-run-non-privileged=no \
	--with-boot-install=no \
	--with-fcrondyn=yes \
	--with-username=root \
	--with-groupname=crontab \
	--with-pam=yes \
	--with-selinux=no \
	--with-boot-install=no

%{__make}

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

#ln -sf %{_bindir}/fcrontab $RPM_BUILD_ROOT%{_bindir}/crontab

#fix premission for rpmbuild
chmod +rw $RPM_BUILD_ROOT/usr/*bin/*

install %{SOURCE1} $RPM_BUILD_ROOT/etc/rc.d/init.d/crond
install %{SOURCE2} $RPM_BUILD_ROOT/etc/logrotate.d/cron
install %{SOURCE3} $RPM_BUILD_ROOT/etc/sysconfig/cron
install %{SOURCE4} $RPM_BUILD_ROOT/etc/cron.d/crontab
install %{SOURCE5} $RPM_BUILD_ROOT/etc/pam.d/fcron
install %{SOURCE6} $RPM_BUILD_ROOT/etc/fcron.conf
install %{SOURCE7} $RPM_BUILD_ROOT/etc/pam.d/fcrontab

#for a in fi fr id ja ko pl ; do
#	if test -f $a/man1/crontab.1 ; then
#		install -d $RPM_BUILD_ROOT%{_mandir}/$a/man1
#		install $a/man1/crontab.1 $RPM_BUILD_ROOT%{_mandir}/$a/man1
#	fi
#	if test -f $a/man5/crontab.5 ; then
#		install -d $RPM_BUILD_ROOT%{_mandir}/$a/man5
#		install $a/man5/crontab.5 $RPM_BUILD_ROOT%{_mandir}/$a/man5
#	fi
#	if test -f $a/man8/cron.8 ; then
#		install -d $RPM_BUILD_ROOT%{_mandir}/$a/man8
#		install $a/man8/cron.8 $RPM_BUILD_ROOT%{_mandir}/$a/man8
#		echo .so cron.8 > $RPM_BUILD_ROOT%{_mandir}/$a/man8/crond.8
#	fi
#done

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
for FILE in /var/spool/cron/*; do
                mv -f $FILE $FILE.orig
                BASENAME=`basename $FILE`
                FCRONTAB=`echo "$BASENAME"`
                (test ! -z "$FCRONTAB" && fcrontab -u $FCRONTAB -z) > /dev/null 2>&1
done

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

for FILE in /var/spool/cron/*.orig; do
                BASENAME=`basename $FILE`
                mv -f $FILE /var/spool/cron/`echo "$BASENAME"| sed 's/.orig//'` >/dev/null 2>&1
done

%postun
if [ "$1" = "0" ]; then
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
%attr(0644,root,crontab) %config(noreplace) /etc/cron.d/crontab
%attr(0640,root,crontab) %config(noreplace,missingok) %verify(not md5 mtime size) %{_sysconfdir}/cron/cron.allow
%attr(0640,root,crontab) %config(noreplace,missingok) %verify(not md5 mtime size) %{_sysconfdir}/cron/cron.deny
%attr(0640,root,root) %config(noreplace) %verify(not md5 mtime size) /etc/sysconfig/cron
%config(noreplace) %verify(not md5 size mtime) /etc/pam.d/fcron
%config(noreplace) %verify(not md5 size mtime) /etc/pam.d/fcrontab
%attr(0754,root,root) /etc/rc.d/init.d/crond
%config /etc/logrotate.d/cron
%attr(0640,root,root) %config(noreplace) /etc/fcron.conf
%attr(0755,root,root) %{_sbindir}/fcron
%attr(4755,root,crontab) %{_bindir}/fcrontab
%attr(0755,root,crontab) %{_bindir}/fcronsighup
%attr(0755,root,crontab) %{_bindir}/fcrondyn

%{_mandir}/man*/*
#%%lang(fi) %{_mandir}/fi/man*/*
#%%lang(fr) %{_mandir}/fr/man*/*
#%%lang(id) %{_mandir}/id/man*/*
#%%lang(ja) %{_mandir}/ja/man*/*
#%%lang(ko) %{_mandir}/ko/man*/*
#%%lang(pl) %{_mandir}/pl/man*/*

%attr(1730,root,crontab) /var/spool/cron
%attr(0660,root,crontab) %ghost /var/log/cron
