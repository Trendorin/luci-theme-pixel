#!/usr/bin/env python3
"""Local preview of luci-theme-pixel: the theme files from this repository, stock LuCI
views from a copy of a router's /www, and read-only ubus calls proxied to a real
router over SSH. Every state-changing call is answered with a stub and never reaches
the router.

    LUCI=~/luci-www-copy ROUTER=openwrt python3 server.py      (then shot.py)

LUCI must contain www/ (and usr/share/ucode/luci/template/) copied from a router.
SANITIZE=1 replaces MACs, IPs, SSIDs, host names and secrets in everything shown,
for public screenshots. Serves http://127.0.0.1:8088/.
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
] + [(re.compile(k), v) for k, v in (json.load(open(S + '/sanitize.local.json')) if os.path.exists(S + '/sanitize.local.json') else {}).items()] + [
    (PUBLIC_IP, '203.0.113.7'),
]
SECRET = re.compile(r'key|psk|pass|secret|private|token', re.I)


def clean(v, key=''):
    if not SANITIZE:
        return v
    if isinstance(v, dict):
        return {k: clean(x, k) for k, x in v.items()}
    if isinstance(v, list):
        return [clean(x, key) for x in v]
    if isinstance(v, str):
        if SECRET.search(key):
            return '********'
        if key == 'hostname' and v == 'root':
            return 'laptop'
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


def ubus(calls):
    out, batch, idx = [None] * len(calls), [], []
    for i, c in enumerate(calls):
        sid, obj, method, args = (c + [None, None, None, None])[:4]
        args = args or {}
        if obj == 'session':
            out[i] = [0, {'access': True}] if method == 'access' else [0, {}]
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
