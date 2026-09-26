#!/usr/bin/env python3
"""Local preview of luci-theme-pixel: the theme files from this repository, stock LuCI
views from a copy of a router's /www, and read-only ubus calls proxied to a real
router over SSH. Every state-changing call is answered with a stub and never reaches
the router.

    LUCI=~/luci-www-copy ROUTER=openwrt python3 server.py      (then shot.py)

LUCI must contain www/ (and usr/share/ucode/luci/template/) copied from a router.
SANITIZE=1 replaces MACs, IPs, SSIDs, host names and secrets in everything shown,
for public screenshots. DEMO=1 also swaps the system and kernel logs for invented
lines (a real log is full of addresses and key fingerprints). Serves http://127.0.0.1:8088/.
"""
import json, os, re, shlex, subprocess, sys, time, threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

S = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(S + '/../..')
LUCI = os.path.expanduser(os.environ.get('LUCI', '~/openwrt-router/luci'))  # stock LuCI files fetched from a router
NEW = REPO + '/htdocs'
OLD = LUCI + '/www'
SSH = ['ssh', '-o', 'ControlMaster=auto', '-o', 'ControlPath=/tmp/pixel-preview-%C', '-o', 'ControlPersist=900', os.environ.get('ROUTER', 'openwrt')]
SANITIZE = os.environ.get('SANITIZE') == '1'
SANFILE = os.environ.get('SANITIZE_FILE', S + '/sanitize.local.json')  # e.g. another board for layout tests
ENV = dict(os.environ)
lock = threading.Lock()


def ssh(cmd, data=None):
    p = subprocess.run(SSH + [cmd], input=data, capture_output=True, env=ENV, timeout=60)
    return p.stdout.decode('utf-8', 'replace')


# the theme templates are rendered on the router from a copy in /tmp/pt
subprocess.run('tar czf - -C %s ucode | %s "rm -rf /tmp/pt; mkdir -p /tmp/pt && tar xzf - -C /tmp/pt"' % (
    shlex.quote(REPO), ' '.join(shlex.quote(a) for a in SSH)), shell=True, env=ENV, check=True)
subprocess.run(SSH + ['cat > /tmp/pt/render.uc'], input=open(S + '/render.uc', 'rb').read(), env=ENV, check=True)
subprocess.run(SSH + ['cat > /tmp/pt/ubusbatch.uc'], input=open(S + '/ubusbatch.uc', 'rb').read(), env=ENV, check=True)


def render(kind, title='', path='admin/status/overview'):
    return ssh('cd /tmp/pt && ucode render.uc %s %s %s x %s' % (
        'blank' if kind == 'sysauth' else 'x', shlex.quote(title or 'x'), shlex.quote(path), kind))


MACS = {}


def fake_mac(m):
    k = m.group(0).lower()
    if k not in MACS:
        n = len(MACS) + 1
        MACS[k] = '02:00:5e:%02x:%02x:%02x' % (0x10 + n, (n * 37) % 256, (n * 91) % 256)
    return MACS[k].upper() if any(c.isupper() for c in m.group(0)) else MACS[k]


PUBLIC_IP = re.compile(r'\b(?!(?:10|127|0)\.)(?!192\.168\.)(?!172\.(?:1[6-9]|2\d|3[01])\.)(?!169\.254\.)(?!100\.(?:6[4-9]|[7-9]\d|1[01]\d|12[0-7])\.)(?!2(?:2[4-9]|[3-5]\d)\.)(?:\d{1,3}\.){3}\d{1,3}\b')
# generic rules; site-specific ones (SSIDs, host names, subnets) go to sanitize.local.json
# as {"regex": "replacement", ...}, which is kept out of git
SUBS = [
    (re.compile(r'(?<![0-9A-Fa-f:])[0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5}(?![0-9A-Fa-f:])'), fake_mac),
] + [(re.compile(k), v) for k, v in (json.load(open(SANFILE)) if os.path.exists(SANFILE) else {}).items()] + [
    (PUBLIC_IP, '203.0.113.7'),
]
SECRET = re.compile(r'key|psk|pass|secret|private|token', re.I)


def clean(v, key=''):
    if not SANITIZE:
        return v
    if isinstance(v, dict):
        # keys too: devices, stations and leases often come keyed by name or MAC
        return {subs(k) if isinstance(k, str) else k: clean(x, k) for k, x in v.items()}
    if isinstance(v, list):
        return [clean(x, key) for x in v]
    if isinstance(v, str):
        if SECRET.search(key):
            return '********'
        if key == 'hostname' and v == 'root':
            return 'laptop'
        v = subs(v)
    return v


def subs(v):
    for rx, rep in SUBS:
        v = rx.sub(rep, v)
    return v


HEADER = clean(render('header'))
FOOTER = clean(render('footer'))
LOGIN = clean(render('sysauth'))
LOGIN_FAIL = clean(ssh('cd /tmp/pt && ucode render.uc blank x x fail sysauth'))

# LuCI's menu tree: a local indexcache.json, or the cache LuCI keeps on the router after a login
if not os.path.exists(S + '/indexcache.json'):
    open(S + '/indexcache.json', 'w').write(ssh('cat $(ls -t /tmp/luci-indexcache*.json | head -1)'))
tree = clean(json.load(open(S + '/indexcache.json')))
admin = tree['children']['admin']['children']
for k in ('nebula', 'nebula_devices'):  # router-specific pages of the author's setup
    admin['status']['children'].pop(k, None)
for k in ('dashboard', 'devices'):
    admin.pop(k, None)
admin['system']['children'].pop('attendedsysupgrade', None)


def node_for(parts):
    node, path = tree, []
    for p in parts:
        ch = (node.get('children') or {}).get(p)
        if ch is None:
            break
        node = ch
        path.append(p)
    # resolve firstchild
    while node.get('action', {}).get('type') == 'firstchild' and node.get('children'):
        kids = sorted([(v.get('order', 999), k, v) for k, v in node['children'].items() if v.get('satisfied', True) and v.get('title')])
        if not kids:
            break
        _, k, node = kids[0]
        path.append(k)
    return node, path


RO = re.compile(r'^(get|list|dump|status|info|board|assoclist|freqlist|txpowerlist|countrylist|htmodelist|devices|state|configs|changes|glance|read|stat|md5|validate)', re.I)
RW = re.compile(r'(scan|set|add|del|apply|commit|reload|restart|start|stop|^up$|^down$|exec|write|remove|init|switch|kick|block|forget|update|password|rename|order|revert|confirm|rollback|destroy|login)', re.I)
EXEC_OK = {'/sbin/logread', '/bin/dmesg', '/usr/sbin/nft', '/sbin/ip', '/usr/sbin/ip', '/bin/cat', '/usr/libexec/luci-peeraddr'}
DEMO = os.environ.get('DEMO') == '1'

# invented log lines for DEMO=1: (seconds before now, syslog priority, message)
DEMO_SYSLOG = [
    (3620, 29, "procd: - init complete -"),
    (3618, 29, "netifd: Interface 'lan' is now up"),
    (3617, 30, "dnsmasq[1402]: started, version 2.90 cachesize 1000"),
    (3617, 30, "dnsmasq-dhcp[1402]: DHCP, IP range 192.168.1.100 -- 192.168.1.249, lease time 12h"),
    (3615, 29, "hostapd: phy0-ap0: interface state UNINITIALIZED->ENABLED"),
    (3615, 29, "hostapd: phy0-ap0: AP-ENABLED"),
    (3612, 29, "hostapd: phy1-ap0: AP-ENABLED"),
    (3604, 6, "[   24.114018] mtk_soc_eth 15100000.ethernet eth0: Link is Up - 1Gbps/Full - flow control rx/tx"),
    (3602, 29, "netifd: wan (2210): udhcpc: lease of 203.0.113.24 obtained from 203.0.113.1, lease time 86400"),
    (3601, 29, "netifd: Interface 'wan' is now up"),
    (3600, 13, "firewall: Reloading firewall due to ifup of wan (eth0)"),
    (3540, 29, "hostapd: phy1-ap0: AP-STA-CONNECTED 02:00:5e:21:25:5b auth_alg=sae"),
    (3539, 30, "dnsmasq-dhcp[1402]: DHCPACK(br-lan) 192.168.1.142 02:00:5e:21:25:5b phone"),
    (3310, 29, "hostapd: phy1-ap0: AP-STA-CONNECTED 02:00:5e:23:7e:91 auth_alg=sae"),
    (3309, 30, "dnsmasq-dhcp[1402]: DHCPACK(br-lan) 192.168.1.118 02:00:5e:23:7e:91 laptop"),
    (2950, 29, "hostapd: phy0-ap1: AP-STA-CONNECTED 02:00:5e:22:4a:b6 auth_alg=open"),
    (2949, 30, "dnsmasq-dhcp[1402]: DHCPACK(br-guest) 192.168.2.117 02:00:5e:22:4a:b6 tv"),
    (2400, 86, "dropbear[3021]: Child connection from 192.168.1.118:51234"),
    (2400, 85, "dropbear[3021]: Pubkey auth succeeded for 'root' with ssh-ed25519 key SHA256:ZGVtby1vbmx5LW5vdC1hLXJlYWwta2V5 from 192.168.1.118:51234"),
    (2210, 86, "dropbear[3021]: Exit (root) from <192.168.1.118:51234>: Disconnect received"),
    (1800, 84, "dispatcher.uc: luci: failed login on /admin/status/overview for root from 192.168.1.142"),
    (1790, 86, "dispatcher.uc: luci: accepted login on /admin/status/overview for root from 192.168.1.142"),
    (1500, 28, "dnsmasq[1402]: possible DNS-rebind attack detected: rebind.example.test"),
    (1200, 29, "hostapd: phy1-ap0: AP-STA-DISCONNECTED 02:00:5e:23:7e:91"),
    (900, 30, "dnsmasq-dhcp[1402]: DHCPREQUEST(br-lan) 192.168.1.142 02:00:5e:21:25:5b"),
    (900, 30, "dnsmasq-dhcp[1402]: DHCPACK(br-lan) 192.168.1.142 02:00:5e:21:25:5b phone"),
    (610, 29, "netifd: wan (2210): udhcpc: sending renew to server 203.0.113.1"),
    (609, 29, "netifd: wan (2210): udhcpc: lease of 203.0.113.24 obtained from 203.0.113.1, lease time 86400"),
    (300, 29, "hostapd: phy1-ap0: AP-STA-CONNECTED 02:00:5e:23:7e:91 auth_alg=sae"),
    (299, 30, "dnsmasq-dhcp[1402]: DHCPACK(br-lan) 192.168.1.118 02:00:5e:23:7e:91 laptop"),
    (40, 86, "dispatcher.uc: luci: accepted login on /admin/status/logs for root from 192.168.1.118"),
]
DEMO_DMESG = '\n'.join([
    '[    0.000000] Booting Linux on physical CPU 0x0000000000 [0x410fd034]',
    '[    0.000000] Machine model: Cudy TR3000 256MB v1',
    '[    0.000000] Linux version 6.12.94 (builder@buildhost) (aarch64-openwrt-linux-musl-gcc (OpenWrt GCC 14.3.0)) #0 SMP',
    '[    0.412871] Memory: 489612K/524288K available',
    '[    1.901225] spi-nand spi0.0: Winbond SPI NAND was found.',
    '[    2.311540] ubi0: attached mtd5 (name "ubi", size 240 MiB)',
    '[    4.106813] VFS: Mounted root (squashfs filesystem) readonly on device 31:0.',
    '[    9.824103] mt798x-wmac 18000000.wifi: HW/SW Version: 0x8a108a10, Build Time: 20240823160845a',
    '[   10.512931] mtk_soc_eth 15100000.ethernet eth0: PHY [mdio-bus:01] driver [MediaTek MT7981 PHY]',
    '[   18.994321] br-lan: port 1(eth1) entered forwarding state',
    '[   24.114018] mtk_soc_eth 15100000.ethernet eth0: Link is Up - 1Gbps/Full - flow control rx/tx',
    '[   25.201774] br-lan: port 2(phy0-ap0) entered forwarding state',
    '[   25.990417] br-lan: port 3(phy1-ap0) entered forwarding state',
])


def demo_log(lines):
    now = int(time.time() * 1000)
    out = [{'msg': m, 'id': 1000 + i, 'priority': p, 'source': 0 if p < 8 else 1, 'time': now - ago * 1000}
           for i, (ago, p, m) in enumerate(DEMO_SYSLOG)]
    return out[-lines:] if lines else out


def ubus(calls):
    out, batch, idx = [None] * len(calls), [], []
    for i, c in enumerate(calls):
        sid, obj, method, args = (c + [None, None, None, None])[:4]
        args = args or {}
        if obj == 'session':
            out[i] = [0, {'access': True}] if method == 'access' else [0, {}]
        elif DEMO and obj == 'log' and method == 'read':
            out[i] = [0, {'log': demo_log(int(args.get('lines') or 0))}]
        elif DEMO and obj == 'file' and method == 'exec' and args.get('command') == '/bin/dmesg':
            out[i] = [0, {'code': 0, 'stdout': DEMO_DMESG + '\n'}]
        elif obj == 'file' and method == 'exec':
            cmd = args.get('command', '')
            if cmd in EXEC_OK:
                batch.append(['@exec', ' '.join(shlex.quote(x) for x in [cmd] + list(args.get('params') or [])) + ' 2>/dev/null', {}]); idx.append((i, 'exec'))
            else:
                out[i] = [0, {'code': 0, 'stdout': ''}]
        elif obj == 'file' and method in ('read', 'list', 'stat', 'md5') and not re.search(r'shadow|key|\.pem|crt', args.get('path', '')):
            batch.append([obj, method, args]); idx.append((i, None))
        elif RO.match(method or '') and not RW.search(method or ''):
            batch.append([obj, method, args]); idx.append((i, None))
        else:
            out[i] = [0, {}]
    if batch:
        with lock:
            raw = ssh('ucode /tmp/pt/ubusbatch.uc', json.dumps(batch).encode())
        try:
            res = json.loads(raw)
        except Exception:
            sys.stderr.write('bad batch reply: %r\n' % raw[:300])
            res = [[4]] * len(batch)
        for (i, m), r in zip(idx, res):
            if m == 'exec' and len(r) > 1:
                r[1] = {'code': 0, 'stdout': r[1].get('stdout', '')}
            out[i] = clean(r)
    return out


class H(BaseHTTPRequestHandler):
    def log_message(self, fmt, *a):
        if os.environ.get('HLOG'):
            sys.stderr.write((fmt % a) + '\n')

    def send(self, code, body, ctype):
        if isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        p = self.path.split('?')[0]
        if p.startswith('/luci-static/'):
            for base in (NEW, OLD):
                f = base + p
                if os.path.isfile(f):
                    ext = f.rsplit('.', 1)[-1]
                    ct = {'css': 'text/css', 'js': 'application/javascript', 'svg': 'image/svg+xml', 'png': 'image/png',
                          'woff2': 'font/woff2', 'gif': 'image/gif', 'json': 'application/json'}.get(ext, 'application/octet-stream')
                    data = open(f, 'rb').read()

                    return self.send(200, data, ct)
            return self.send(404, 'nf', 'text/plain')
        if p in ('/login', '/login-fail'):
            env = {'media': '/luci-static/pixel', 'resource': '/luci-static/resources', 'scriptname': '/cgi-bin/luci',
                   'pathinfo': '/', 'requestpath': [], 'dispatchpath': [], 'pollinterval': 5, 'ubuspath': '/ubus/',
                   'sessionid': None, 'token': None, 'nodespec': {}, 'apply_rollback': 90, 'apply_holdoff': 4,
                   'apply_timeout': 5, 'apply_display': 1.5, 'rollback_token': None}
            page = LOGIN if p == '/login' else LOGIN_FAIL
            boot = '<script src="/luci-static/resources/luci.js"></script><script>L = new LuCI(%s);</script>' % json.dumps(env)
            return self.send(200, page.replace('<main class="px-login">', boot + '<main class="px-login">', 1), 'text/html')
        if p.startswith('/cgi-bin/luci/admin/translations'):
            return self.send(200, 'window.TR={};', 'application/javascript')
        if p == '/cgi-bin/luci/admin/menu':
            return self.send(200, json.dumps(tree), 'application/json')
        if p.startswith('/cgi-bin/luci'):
            parts = [x for x in p[len('/cgi-bin/luci'):].split('/') if x] or ['admin']
            node, path = node_for(parts)
            act = node.get('action', {})
            view = act.get('path') if act.get('type') == 'view' else None
            pre = ''
            if act.get('type') == 'template' and act.get('path') == 'admin_status/index':
                tpl = open(LUCI + '/usr/share/ucode/luci/template/admin_status/index.ut').read()
                helpers = re.search(r'<script>\s*function progressbar.*?</script>', tpl, re.S).group(0)
                view, pre = 'status/index', '<h2 name="content">Status</h2>' + helpers
            if act.get('type') == 'alias':
                node, path = node_for(act['path'].split('/'))
                view = node.get('action', {}).get('path')
            env = {'media': '/luci-static/pixel', 'resource': '/luci-static/resources', 'scriptname': '/cgi-bin/luci',
                   'pathinfo': '/' + '/'.join(path), 'documentroot': '/www', 'requestpath': path, 'dispatchpath': path,
                   'pollinterval': 5, 'ubuspath': '/ubus/', 'sessionid': 'mock', 'token': 'mock',
                   'nodespec': dict(node, children=None), 'apply_rollback': 90, 'apply_holdoff': 4, 'apply_timeout': 5,
                   'apply_display': 1.5, 'rollback_token': None}
            head = re.sub(r'<title>.*?</title>', '<title>%s · OpenWrt</title>' % node.get('title', ''), HEADER, flags=re.S)
            head = head.replace('data-page="admin-status-overview"', 'data-page="%s"' % '-'.join(path))
            body = head + '<script>window.__errs=[];addEventListener("error",function(e){__errs.push(e.message+" @"+e.filename+":"+e.lineno)});addEventListener("unhandledrejection",function(e){__errs.push(String(e.reason&&(e.reason.message+" :: "+e.reason.stack)||e.reason))});</script><script src="/luci-static/resources/luci.js"></script><script>L = new LuCI(%s);</script>' % json.dumps(env)
            if view:
                body += pre + '<div id="view"><div class="spinning">Loading view…</div><script>L.require("ui").then(function(ui){ui.instantiateView(%s);});</script></div>' % json.dumps(view)
            else:
                body += '<div id="view"><p>No view for %s</p></div>' % '/'.join(path)
            return self.send(200, body + FOOTER, 'text/html')
        self.send(404, 'nf', 'text/plain')

    def do_POST(self):
        n = int(self.headers.get('Content-Length', 0))
        req = json.loads(self.rfile.read(n) or b'null')
        single = isinstance(req, dict)
        reqs = [req] if single else req
        calls = [r.get('params') or [] for r in reqs]
        if os.environ.get('HLOG'):
            sys.stderr.write('UBUS %s\n' % [(c[1], c[2]) if len(c) > 2 else c for c in calls])
        res = ubus([c if r.get('method') == 'call' else [None, 'session', 'x', {}] for c, r in zip(calls, reqs)])
        replies = []
        for r, x in zip(reqs, res):
            if r.get('method') == 'list':
                objs = r.get('params') or []
                raw = ssh('ubus -v list ' + ' '.join(shlex.quote(o) for o in objs)) if objs else ssh('ubus list')
                out, cur = {}, None
                for line in raw.splitlines():
                    m = re.match(r"^'([^']+)' @", line)
                    if m:
                        cur = out.setdefault(m.group(1), {})
                        continue
                    m = re.match(r'^\s+"([^"]+)":(\{.*\})$', line)
                    if m and cur is not None:
                        cur[m.group(1)] = json.loads(m.group(2))
                if not objs:
                    out = raw.split()
                replies.append({'jsonrpc': '2.0', 'id': r.get('id'), 'result': out})
            else:
                replies.append({'jsonrpc': '2.0', 'id': r.get('id'), 'result': x})
        self.send(200, json.dumps(replies[0] if single else replies), 'application/json')


if __name__ == '__main__':
    ThreadingHTTPServer(('127.0.0.1', 8088), H).serve_forever()
