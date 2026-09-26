#!/usr/bin/env python3
"""Record the sign-in animation of the running preview as a GIF, frame by frame.

    anim.py OUT.gif [dark|light] [seconds] [fps]

Every CSS animation on the page is paused and moved to the same time before each
screenshot (Web Animations API), so frames are exact and evenly spaced however
slow the headless browser is. Needs librewolf and ffmpeg; the preview server
(server.py, ideally with SANITIZE=1) must be running on 127.0.0.1:8088.
"""
import base64, os, shutil, subprocess, sys, tempfile, time

from shot import M

out = os.path.abspath(sys.argv[1])
theme = sys.argv[2] if len(sys.argv) > 2 else 'dark'
secs = float(sys.argv[3]) if len(sys.argv) > 3 else 4.6
fps = float(sys.argv[4]) if len(sys.argv) > 4 else 12.5
base = os.environ.get('BASE', 'http://127.0.0.1:8088')

prof = tempfile.mkdtemp(prefix='lwprof-')
frames = tempfile.mkdtemp(prefix='frames-')
port = 2828 + (os.getpid() % 500)
with open(prof + '/user.js', 'w') as f:
    f.write('user_pref("marionette.port", %d);\n' % port)
    for k, v in [('privacy.resistFingerprinting', 'false'), ('layout.css.devPixelsPerPx', '"1.0"'),
                 ('ui.systemUsesDarkTheme', '1' if theme == 'dark' else '0'),
                 ('layout.css.prefers-color-scheme.content-override', '0' if theme == 'dark' else '1')]:
        f.write('user_pref("%s", %s);\n' % (k, v))
p = subprocess.Popen(['librewolf', '--headless', '--marionette', '--no-remote', '--profile', prof, '--width', '1000', '--height', '820'],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    m = M(port)
    m.cmd('WebDriver:NewSession', {'capabilities': {'alwaysMatch': {'acceptInsecureCerts': True}}})
    m.cmd('WebDriver:SetWindowRect', {'width': 1000, 'height': 820})
    m.cmd('WebDriver:Navigate', {'url': base + '/login'})
    m.cmd('WebDriver:ExecuteScript', {'script': 'try{localStorage.setItem("pixel.theme", arguments[0])}catch(e){}', 'args': [theme]})
    m.cmd('WebDriver:Navigate', {'url': base + '/login'})
    # wait until the wordmark has been built, then freeze everything at t = 0
    for _ in range(100):
        if m.cmd('WebDriver:ExecuteScript', {'script': 'return !!document.querySelector("#px-login-screen.ready svg")'})['value']:
            break
        time.sleep(0.1)
    m.cmd('WebDriver:ExecuteScript', {'script': 'document.activeElement && document.activeElement.blur();'
                                                'document.getAnimations().forEach(a => a.pause());'})
    el = m.cmd('WebDriver:FindElement', {'using': 'css selector', 'value': 'main.px-login'})['value']
    n = int(secs * fps)
    for i in range(n + 1):
        t = i * 1000 / fps
        m.cmd('WebDriver:ExecuteScript', {'script': 'document.getAnimations().forEach(a => { a.currentTime = arguments[0]; });', 'args': [t]})
        png = m.cmd('WebDriver:TakeScreenshot', {'id': list(el.values())[0], 'full': False})['value']
        open(os.path.join(frames, 'f%04d.png' % i), 'wb').write(base64.b64decode(png))
    m.cmd('WebDriver:DeleteSession')
finally:
    p.terminate()
    try:
        p.wait(5)
    except Exception:
        p.kill()

# one shared palette, no dithering: the art is flat greys, so the GIF stays small and crisp
pal = os.path.join(frames, 'pal.png')
inp = ['-framerate', str(fps), '-i', os.path.join(frames, 'f%04d.png')]
subprocess.run(['ffmpeg', '-v', 'error', '-y'] + inp + ['-vf', 'palettegen=max_colors=48:stats_mode=full', pal], check=True)
subprocess.run(['ffmpeg', '-v', 'error', '-y'] + inp + ['-i', pal, '-lavfi', 'paletteuse=dither=none', '-loop', '0', out], check=True)
shutil.rmtree(frames, ignore_errors=True)
shutil.rmtree(prof, ignore_errors=True)
print(out, os.path.getsize(out), 'bytes,', n + 1, 'frames')
