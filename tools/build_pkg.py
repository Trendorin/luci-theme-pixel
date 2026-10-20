#!/usr/bin/env python3
"""Build luci-theme-pixel packages without the OpenWrt SDK.

    tools/build_pkg.py [OUTDIR]        (default: ../luci-theme-pixel-dist)

Produces the same two files as `make package/luci-theme-pixel/compile`:
  luci-theme-pixel-<ver>-r<rel>.apk      OpenWrt 25.12+ (needs `apk` 3.x: `dnf install apk-tools`)
  luci-theme-pixel_<ver>-r<rel>_all.ipk  OpenWrt 23.05 / 24.10
with the file layout, metadata and maintainer scripts of the Makefile (the ipk
script templates are in tools/pkg/, copied from an SDK build). Version, release
and texts are read from the Makefile, so it stays the single source of truth.
"""
import gzip, hashlib, io, os, re, shutil, subprocess, sys, tarfile, tempfile, time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TPL = os.path.join(REPO, 'tools', 'pkg')
OUT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, '..', 'luci-theme-pixel-dist'))
EPOCH = int(os.environ.get('SOURCE_DATE_EPOCH') or time.time())

mk = open(os.path.join(REPO, 'Makefile')).read()
var = lambda k: re.search(r'^%s:=(.*)$' % k, mk, re.M).group(1).strip()
NAME, VER, REL = var('PKG_NAME'), var('PKG_VERSION'), var('PKG_RELEASE')
URL = re.search(r'^\s*URL:=(.*)$', mk, re.M).group(1).strip()
MAINT = var('PKG_MAINTAINER')
DESC = ' '.join(l.strip() for l in re.search(r'define Package/%s/description\n(.*?)\nendef' % NAME, mk, re.S).group(1).splitlines())
FULL = '%s-r%s' % (VER, REL)


def stage(root):
    """Lay the files out as Package/install in the Makefile does."""
    shutil.copytree(os.path.join(REPO, 'htdocs'), os.path.join(root, 'www'))
    shutil.copytree(os.path.join(REPO, 'ucode'), os.path.join(root, 'usr/share/ucode/luci'))
    d = os.path.join(root, 'etc/uci-defaults')
    os.makedirs(d)
    shutil.copy(os.path.join(REPO, 'root/etc/uci-defaults/30_luci-theme-pixel'), d)
    files = []
    for dp, dn, fn in os.walk(root):
        dn.sort()
        for f in sorted(fn):
            files.append('/' + os.path.relpath(os.path.join(dp, f), root))
    for dp, dn, fn in os.walk(root):
        for x in dn + fn:
            p = os.path.join(dp, x)
            os.chmod(p, 0o755 if os.path.isdir(p) or p.endswith('30_luci-theme-pixel') else 0o644)
    return files


def touch_all(root):
    for dp, dn, fn in os.walk(root):
        for x in dn + fn:
            os.utime(os.path.join(dp, x), (EPOCH, EPOCH), follow_symlinks=False)
    os.utime(root, (EPOCH, EPOCH))


def script(name):
    s = open(os.path.join(TPL, name)).read()
    return s.split('\n', 1)[1] if s.startswith('#!') else s


def build_apk(files):
    if not shutil.which('apk'):
        sys.exit('apk (apk-tools 3) is needed for the .apk: dnf install apk-tools / apt install apk-tools')
    with tempfile.TemporaryDirectory() as t:
        root = os.path.join(t, 'root')
        stage(root)
        lst = os.path.join(root, 'lib/apk/packages')
        os.makedirs(lst)
        open(os.path.join(lst, NAME + '.list'), 'w').write('\n'.join(files) + '\n')
        os.chmod(os.path.join(lst, NAME + '.list'), 0o644)
        touch_all(root)

        head = ('#!/bin/sh\n[ "${IPKG_NO_SCRIPT}" = "1" ] && exit 0\n[ -s ${IPKG_INSTROOT}/lib/functions.sh ] || exit 0\n'
                '. ${IPKG_INSTROOT}/lib/functions.sh\nexport root="${IPKG_INSTROOT}"\nexport pkgname="%s"\n' % NAME)
        post = head + 'add_group_and_user\ndefault_postinst\n' + script('postinst-pkg')
        pre = ('#!/bin/sh\n[ -s ${IPKG_INSTROOT}/lib/functions.sh ] || exit 0\n. ${IPKG_INSTROOT}/lib/functions.sh\n'
               'export root="${IPKG_INSTROOT}"\nexport pkgname="%s"\ndefault_prerm\n' % NAME) + script('prerm-pkg')
        upg = post.replace('#!/bin/sh\n', '#!/bin/sh\nexport PKG_UPGRADE=1\n', 1)
        sc = {}
        for k, v in (('post-install', post), ('pre-deinstall', pre), ('post-upgrade', upg)):
            sc[k] = os.path.join(t, k)
            open(sc[k], 'w').write(v)

        out = os.path.join(OUT, '%s-%s.apk' % (NAME, FULL))
        cmd = ['apk', 'mkpkg', '--files', root, '--output', out,
               '--info', 'name:' + NAME, '--info', 'version:' + FULL, '--info', 'description:' + DESC,
               '--info', 'arch:noarch', '--info', 'license:Apache-2.0', '--info', 'origin:feeds/base/' + NAME,
               '--info', 'maintainer:' + MAINT, '--info', 'url:' + URL,
               '--info', 'depends:libc luci-base', '--info', 'provides:%s-any' % NAME]
        for k, p in sc.items():
            cmd += ['--script', '%s:%s' % (k, p)]
        subprocess.run(cmd, check=True)
        return out


def tgz(members):
    """gzip'd tar of (name, bytes|None for dir, mode) with root ownership and fixed times"""
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode='wb', mtime=EPOCH) as gz, tarfile.open(fileobj=gz, mode='w', format=tarfile.GNU_FORMAT) as tar:
        for name, data, mode in members:
            ti = tarfile.TarInfo(name)
            ti.mtime, ti.uid, ti.gid, ti.uname, ti.gname, ti.mode = EPOCH, 0, 0, 'root', 'root', mode
            if data is None:
                ti.type = tarfile.DIRTYPE
                tar.addfile(ti)
            else:
                ti.size = len(data)
                tar.addfile(ti, io.BytesIO(data))
    return buf.getvalue()


def build_ipk():
    with tempfile.TemporaryDirectory() as t:
        root = os.path.join(t, 'root')
        stage(root)
        data, size = [('./', None, 0o755)], 0
        for dp, dn, fn in os.walk(root):
            dn.sort()
            rel = os.path.relpath(dp, root)
            for d in dn:
                data.append(('./' + os.path.normpath(os.path.join(rel, d)) + '/', None, 0o755))
            for f in sorted(fn):
                p = os.path.join(dp, f)
                b = open(p, 'rb').read()
                size += len(b)
                data.append(('./' + os.path.normpath(os.path.join(rel, f)), b, os.stat(p).st_mode & 0o777))
        control = ('Package: %s\nVersion: %s\nDepends: libc, luci-base\nSource: feeds/base/%s\nSourceName: %s\n'
                   'License: Apache-2.0\nLicenseFiles: LICENSE\nSection: luci\nSourceDateEpoch: %d\nURL: %s\n'
                   'Maintainer: %s\nArchitecture: all\nInstalled-Size: %d\nDescription: %s\n') % (
            NAME, FULL, NAME, NAME, EPOCH, URL, MAINT, size, DESC)
        ctl = [('./', None, 0o755), ('./control', control.encode(), 0o644)]
        for s in ('postinst', 'postinst-pkg', 'prerm', 'prerm-pkg'):
            ctl.append(('./' + s, open(os.path.join(TPL, s), 'rb').read(), 0o755))
        out = os.path.join(OUT, '%s_%s_all.ipk' % (NAME, FULL))
        open(out, 'wb').write(tgz([('./debian-binary', b'2.0\n', 0o644),
                                   ('./data.tar.gz', tgz(data), 0o644),
                                   ('./control.tar.gz', tgz(ctl), 0o644)]))
        return out


os.makedirs(OUT, exist_ok=True)
with tempfile.TemporaryDirectory() as t:
    listing = stage(os.path.join(t, 'r'))
built = [build_apk(listing), build_ipk()]
with open(os.path.join(OUT, 'SHA256SUMS'), 'w') as f:
    for p in sorted(built):
        f.write('%s  %s\n' % (hashlib.sha256(open(p, 'rb').read()).hexdigest(), os.path.basename(p)))
for p in built:
    print('%s  %d bytes' % (p, os.path.getsize(p)))
