#!/usr/bin/env python3
"""Minimal Marionette client: screenshot pages of the local preview in headless LibreWolf.
usage: shot.py OUTDIR WIDTHxHEIGHT THEME path[#js] [path ...]"""
import base64, json, os, socket, subprocess, sys, tempfile, time

class M:
    def __init__(self, port):
        for _ in range(100):
            try:
                self.s = socket.create_connection(('127.0.0.1', port))
                break
            except OSError:
                time.sleep(0.2)
        self.buf = b''
        self.id = 0
        self.read()

    def read(self):
        while b':' not in self.buf:
            self.buf += self.s.recv(65536)
        n, rest = self.buf.split(b':', 1)
        n = int(n)
        while len(rest) < n:
            rest += self.s.recv(1 << 20)
        self.buf = rest[n:]
        return json.loads(rest[:n])

    def cmd(self, name, params=None):
        self.id += 1
        msg = json.dumps([0, self.id, name, params or {}]).encode()
        self.s.sendall(str(len(msg)).encode() + b':' + msg)
        while True:
            r = self.read()
            if r[0] == 1 and r[1] == self.id:
                if r[2]:
                    raise RuntimeError(r[2])
                return r[3]


def main():
    out, size, theme = sys.argv[1], sys.argv[2], sys.argv[3]
    w, h = map(int, size.split('x'))
    os.makedirs(out, exist_ok=True)
    prof = tempfile.mkdtemp(prefix='lwprof-')
    port = 2828 + (os.getpid() % 500)
    with open(prof + '/user.js', 'w') as f:
        f.write('user_pref("marionette.port", %d);\n' % port)
        for k, v in [('privacy.resistFingerprinting', 'false'), ('privacy.resistFingerprinting.letterboxing', 'false'),
                     ('privacy.fingerprintingProtection', 'false'), ('browser.shell.checkDefaultBrowser', 'false'),
                     ('layout.css.devPixelsPerPx', '"1.0"'), ('gfx.font_rendering.cleartype_params.rendering_mode', '5'),
                     ('ui.systemUsesDarkTheme', '1' if theme == 'dark' else '0'),
                     ('layout.css.prefers-color-scheme.content-override', '0' if theme == 'dark' else '1')]:
            f.write('user_pref("%s", %s);\n' % (k, v))
    p = subprocess.Popen(['librewolf', '--headless', '--marionette', '--no-remote', '--profile', prof,
                          '--width', str(w), '--height', str(h)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        m = M(port)
        m.cmd('WebDriver:NewSession', {'capabilities': {'alwaysMatch': {'acceptInsecureCerts': True}}})
        m.cmd('WebDriver:SetWindowRect', {'width': w, 'height': h})
        first = True
        for spec in sys.argv[4:]:
            path, _, js = spec.partition('#')
            m.cmd('WebDriver:Navigate', {'url': os.environ.get('BASE', 'http://127.0.0.1:8088') + path})
            if first:
                m.cmd('WebDriver:ExecuteScript', {'script': 'try{localStorage.setItem("pixel.theme", arguments[0])}catch(e){}', 'args': [theme]})
                m.cmd('WebDriver:Navigate', {'url': os.environ.get('BASE', 'http://127.0.0.1:8088') + path})
                first = False
            time.sleep(float(os.environ.get('WAIT', '5')))
            if js:
                m.cmd('WebDriver:ExecuteScript', {'script': js})
                time.sleep(1.2)
            errs = m.cmd('WebDriver:ExecuteScript', {'script': 'return [document.querySelector("#view")?.innerText.slice(0,120) || "", (window.__errs||[]).join(" | ").slice(0,1500)]'})
            png = m.cmd('WebDriver:TakeScreenshot', {'full': os.environ.get('FULL', '1') == '1'})['value']
            name = (path.strip('/').replace('/', '_') or 'root') + ('_js' if js else '') + '_%s_%d.png' % (theme, w)
            open(os.path.join(out, name), 'wb').write(base64.b64decode(png))
            print(name, json.dumps(errs['value'] if isinstance(errs, dict) else errs)[:1800])
        m.cmd('WebDriver:DeleteSession')
    finally:
        p.terminate()
        try:
            p.wait(5)
        except Exception:
            p.kill()


if __name__ == '__main__':
    main()
